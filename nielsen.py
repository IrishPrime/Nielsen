#!/usr/bin/env python3
"""
chown, chmod, rename, and organize TV show files.
"""
import argparse
import configparser
import logging
import re
from os import chmod, getenv, makedirs, name, path, rename
from shutil import chown, move

CONFIG = configparser.ConfigParser()
CONFIG['DEFAULT'] = {
	'User': '',
	'Group': '',
	'Mode': '644',
	'LogFile': 'nielsen.log',
	'LogLevel': 'WARNING',
	'MediaPath': '',
	'OrganizeFiles': 'False',
	'DryRun': 'False'
}


def load_config(filename=None):
	"""Load config file specified by path, or check XDG directories for
	configuration file."""
	CONFIG['Options'] = {}

	if filename and path.isfile(filename):
		configfile = filename
	else:
		if name == "posix":
			import xdg.BaseDirectory
			configfile = xdg.BaseDirectory.load_first_config("nielsen/nielsen.ini")
		elif name == "nt":
			configfile = path.join("", getenv("APPDATA"), "nielsen", "nielsen.ini")

	try:
		CONFIG.read(configfile)
	except:
		print("Unable to load config: '{0}'".format(configfile))


def get_file_info(filename):
	"""Get information about an episode from its filename.
	Returns a dictionary with the following keys:
		- series: Series name
		- season: Season number
		- episode: Episode number
		- title: Episode title (if found)
		- extension: File extension
	Filename variants:
		The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi
		the.glades.201.family.matters.hdtv.xvid-fqm.avi
		The Glades -02.01- Family Matters.avi
		The Glades -201- Family Matters.avi
	"""

	patterns = [
		# The.Flash.2014.217.Flash.Back.HDTV.x264-LOL[ettv].mp4
		re.compile(r"(?P<series>.+)\.+(?P<year>\d{4})\.(?P<season>\d{1,2})(?P<episode>\d{2})\.*(?P<title>.*)?\.+(?P<extension>\w+)$", re.IGNORECASE),
		# The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi
		re.compile(r"(?P<series>.+)\.+S(?P<season>\d{2})\.?E(?P<episode>\d{2})\.*(?P<title>.*)?\.+(?P<extension>\w+)$", re.IGNORECASE),
		# the.glades.201.family.matters.hdtv.xvid-fqm.avi
		re.compile(r"(?P<series>.+)\.+S?(?P<season>\d{1,})\.?E?(?P<episode>\d{2,})\.*(?P<title>.*)?\.+(?P<extension>\w+)$", re.IGNORECASE),
		# The Glades -02.01- Family Matters.avi
		re.compile(r"(?P<series>.+)\s+-(?P<season>\d{2})\.(?P<episode>\d{2})-\s*(?P<title>.*)\.(?P<extension>.+)$"),
		# The Glades -201- Family Matters.avi
		re.compile(r"(?P<series>.+)\s+-(?P<season>\d{1,2})(?P<episode>\d{2,})-\s*(?P<title>.*)\.(?P<extension>.+)$"),
	]

	# Check against patterns until a matching one is found
	for p in patterns:
		m = p.match(path.basename(filename))
		if m:
			series = m.group("series").replace('.', ' ').strip()

			# Use title case if everything is lowercase
			if m.group("series").islower():
				series = m.group("series").replace('.', ' ').title()

			# Check series name against filter
			series = filter_series(series)

			# Strip tags and release notes from the episode title
			tags = re.compile(r"(1080p|720p|HDTV|WEB|PROPER|REPACK|RERIP).*", re.IGNORECASE)
			title = re.sub(tags, "", m.group("title")).replace('.', ' ').strip()

			# Use title case if everything is lowercase
			if title.islower():
				title = title.title()

			info = {
				'series': series,
				'season': m.group('season').strip().zfill(2),
				'episode': m.group('episode').strip(),
				'title': title,
				'extension': m.group('extension').strip()
			}

			# Check for double episode files
			# "Bones.S04E01E02.720p.HDTV.X264-DIMENSION.mkv":
			if info['title'].lower().startswith("e") and info['title'][1:3].isnumeric():
				if int(info['title'][1:3]) == int(info['episode']) + 1:
					info['episode'] += "-" + info['title'][1:3]
					info['title'] = info['title'][3:].strip()

			logging.debug("Series: '{0}'".format(info['series']))
			logging.debug("Season: '{0}'".format(info['season']))
			logging.debug("Episode: '{0}'".format(info['episode']))
			logging.debug("Title: '{0}'".format(info['title']))
			logging.debug("Extension: '{0}'".format(info['extension']))

			return info

	# Filename didn't match any pattern in the list
	logging.info("'{0}' did not match any pattern, skipping.".format(filename))
	return None


def organize_file(filename, series, season):
	"""Move files to <MediaPath>/<Series>/Season <Season>."""
	if CONFIG['Options']['MediaPath']:
		new_path = path.join(CONFIG['Options']['MediaPath'], series,
			"Season {0}".format(season))
		logging.debug("Creating and/or moving to: {0}".format(new_path))
		makedirs(new_path, exist_ok=True)

		dst = path.join(new_path, filename)

		# Do not attempt to overwrite existing files
		if path.isfile(dst):
			logging.warning("{0} already exists. File will not be moved.".format(dst))
		else:
			try:
				move(filename, dst)
			except Exception as err:
				logging.error(err)

		return new_path
	else:
		logging.error("No MediaPath defined.")
		return None


def filter_series(series):
	"""Check series name against list and replace with preferred name.
	Use the key/value pairs in the [Filters] section of the config file.
	Match the series name against the left hand side (ignoring case) and
	replace it with the right hand side.
		Castle (2009) = Castle
		Game Of Thrones = Game of Thrones
		Its Always Sunny In Philadelphia = It's Always Sunny in Philadelphia
		Marvel's Agents of S.H.I.E.L.D. = Agents of S.H.I.E.L.D.
		Mr Robot = Mr. Robot
	"""
	if CONFIG.has_option('Filters', series):
		return CONFIG['Filters'][series]
	else:
		return series


def process_file(filename):
	"""Set ownership and permissions for files, then rename."""
	logging.info("Processing '{0}'".format(filename))

	if name == "posix":
		if CONFIG['Options']['User'] or CONFIG['Options']['Group']:
			try:
				chown(filename, CONFIG['Options']['User'] or None,
					CONFIG['Options']['Group'] or None)
			except PermissionError as err:
				logging.error("chown failed. {0}".format(err))

		if CONFIG['Options']['Mode']:
			try:
				chmod(filename, int(CONFIG['Options']['Mode'], 8))
			except PermissionError as err:
				logging.error("chmod failed. {0}".format(err))

	info = get_file_info(filename)
	if info:
		clean = "{0} -{1}.{2}- {3}.{4}".format(
			info['series'],
			info['season'],
			info['episode'],
			info['title'],
			info['extension'])
		logging.info("Rename to: '{0}'".format(clean))

		if CONFIG.getboolean('Options', 'DryRun'):
			print(filename + " → " + clean)
			return

		if path.isfile(clean):
			logging.warning("{0} already exists. File will not be renamed.".format(clean))
		else:
			rename(filename, clean)

		if CONFIG.getboolean('Options', 'OrganizeFiles'):
			organize_file(clean, info['series'], info['season'])


def main():
	# Command line arguments
	PARSER = argparse.ArgumentParser(description=
		"Process episodes of TV shows for storage on a media server.")
	PARSER.add_argument("-u", "--user", dest="user", help="User to own files")
	PARSER.add_argument("-g", "--group", dest="group", help="Group to own files")
	PARSER.add_argument("-m", "--mode", dest="mode", type=str,
		help="File mode (permissions) in octal")
	PARSER.add_argument("-o", "--organize", dest="organize", action="store_true",
		help="Organize files")
	PARSER.add_argument("--no-organize", dest="organize", action="store_false",
		help="Do not organize files")
	PARSER.set_defaults(organize=None)
	PARSER.add_argument("-n", "--dry-run", dest="dry_run", action="store_true",
		help="Do not rename files, just list the renaming actions.")
	PARSER.set_defaults(dry_run=False)
	PARSER.add_argument("-p", "--path", dest="mediapath",
		help="Base directory to organize files into")
	PARSER.add_argument("-l", "--log", dest="log_level", type=str,
		choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
		help="Logging level")
	PARSER.add_argument("-c", "--config", dest="configfile", help="Config file")
	PARSER.add_argument("files", nargs="+", type=str, help="Files to operate on")
	ARGS = PARSER.parse_args()

	# Load XDG configuration file
	load_config(ARGS.configfile)

	# Override the settings in the config file if given on the command line
	if ARGS.user:
		CONFIG['Options']['User'] = ARGS.user

	if ARGS.group:
		CONFIG['Options']['Group'] = ARGS.group

	if ARGS.mode:
		CONFIG['Options']['Mode'] = ARGS.mode

	if ARGS.organize is not None:
		CONFIG['Options']['OrganizeFiles'] = str(ARGS.organize)

	if ARGS.dry_run is not False:
		CONFIG['Options']['DryRun'] = str(ARGS.dry_run)

	if ARGS.mediapath:
		CONFIG['Options']['MediaPath'] = ARGS.mediapath

	if ARGS.log_level:
		CONFIG['Options']['LogLevel'] = ARGS.log_level.upper()

	# Configure logging
	logging.basicConfig(filename=CONFIG['Options']['LogFile'],
		format='%(asctime)-15s %(levelname)-8s %(message)s',
		level=getattr(logging, CONFIG['Options']['LogLevel'], 30))

	logging.debug(dict(CONFIG.items('Options')))

	# Iterate over files
	for f in ARGS.files:
		process_file(f)


if __name__ == "__main__":
	main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

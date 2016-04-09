#!/usr/bin/env python3
"""
chown, chmod, rename, and organize TV show files.
"""
import argparse
import configparser
import logging
import re
import xdg.BaseDirectory
from os import chmod, makedirs, path, rename
from shutil import chown, move


CONFIG = configparser.ConfigParser()
CONFIG['DEFAULT'] = {'User': '',
		'Group': '',
		'Mode': '644',
		'LogLevel': 'WARNING',
		'MediaPath': '',
		'OrganizeFiles': 'False'}


def load_config():
	"""Check XDG directories for configuration files."""
	first_config = xdg.BaseDirectory.load_first_config("nielsen/nielsen.ini")

	try:
		CONFIG.read(first_config)
	except:
		logging.warning("Unable to load config.")
		CONFIG['Options'] = {}


def get_file_info(filename):
	"""Get information about an episode from its filename.
	Returns a dictionary with the following keys:
		- series: Series name
		- season: Season number
		- episode: Episode number
		- title: Episode title (if found)
		- extension: File extension
	Typical filenames are something like:
		The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi
	"""
	logging.info("Processing %s" % filename)

	p = re.compile(r"(?P<series>.*)\s+S?(?P<season>\d{2,})\s?E?(?P<episode>\d{2,})\s*(?P<title>.*)?\s+(?P<extension>\w+)$", re.IGNORECASE)
	m = p.match(re.compile("\.").sub(" ", filename))
	if m:
		series = m.group("series").strip()

		# Use title case if everything is lowercase
		if m.group("series").islower():
			series = m.group("series").title()

		# Check series name against filter
		# series = filter_series(series)

		# Strip tags and release notes from the episode title
		tags = re.compile(r"(HDTV|720p|WEB|PROPER|REPACK|RERIP).*", re.IGNORECASE)
		title = re.sub(tags, "", m.group("title")).strip()

		# Use title case if everything is lowercase
		if title.islower():
			title = title.title()

		info = {
			'series': series,
			'season': m.group('season').strip(),
			'episode': m.group('episode').strip(),
			'title': title,
			'extension': m.group('extension').strip()
		}

		logging.info('Series: {0}'.format(info['series']))
		logging.info('Season: {0}'.format(info['season']))
		logging.info('Episode: {0}'.format(info['episode']))
		logging.info('Title: {0}'.format(info['title']))
		logging.info('Extension: {0}'.format(info['extension']))

		return info
	else:
		logging.info("{0} did not match pattern, skipping.".format(filename))
		return None


def organize_file(filename, series, season):
	"""Move files to <MediaPath>/<Series>/Season <Season>."""
	if CONFIG['Options']['MediaPath']:
		new_path = path.join(CONFIG['Options']['MediaPath'], series,
			"Season {0}".format(season))
		logging.debug("Creating and/or moving to: {0}".format(new_path))
		makedirs(new_path, exist_ok=True)
		move(filename, new_path)
		return new_path
	else:
		logging.error("No MediaPath defined.")
		return None


def process_file(filename):
	"""Set ownership and permissions for files, then rename."""
	if CONFIG['Options']['User'] or CONFIG['Options']['Group']:
		chown(filename, CONFIG['Options']['User'] or None,
			CONFIG['Options']['Group'] or None)

	if CONFIG['Options']['Mode']:
		chmod(filename, int(CONFIG['Options']['Mode'], 8))

	info = get_file_info(filename)
	if info:
		clean = "{0} -{1}.{2}- {3}.{4}".format(
			info['series'],
			info['season'],
			info['episode'],
			info['title'],
			info['extension'])
		logging.info("Rename to: {0}".format(clean))
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
	PARSER.add_argument("-l", "--log", dest="log_level", type=str,
		choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
		help="Logging level")
	PARSER.add_argument("files", nargs="+", type=str, help="Files to operate on")
	ARGS = PARSER.parse_args()

	# Load XDG configuration file
	load_config()

	# Override the settings in the config file if given on the command line
	if ARGS.user:
		CONFIG['Options']['User'] = ARGS.user

	if ARGS.group:
		CONFIG['Options']['Group'] = ARGS.group

	if ARGS.mode:
		CONFIG['Options']['Mode'] = ARGS.mode

	if ARGS.log_level:
		CONFIG['Options']['LogLevel'] = ARGS.log_level.upper()

	# Validate the log level
	logging.basicConfig(filename="nielsen.log",
		level=getattr(logging, CONFIG['Options']['LogLevel'], 30))

	logging.debug("User: '{0}', Group: '{1}', Mode: '{2}', LogLevel: '{3}'".format(
		CONFIG['Options']['User'],
		CONFIG['Options']['Group'],
		CONFIG['Options']['Mode'],
		CONFIG['Options']['LogLevel']))

	# Iterate over files
	for f in ARGS.files:
		logging.info(f)
		process_file(f)


if __name__ == "__main__":
	main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

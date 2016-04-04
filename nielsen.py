#!/usr/bin/env python3
"""
chown, chmod, rename, and organize TV show files.
"""
import argparse
import configparser
import logging
import re
import xdg.BaseDirectory
from os import chmod, rename
from shutil import chown


CONFIG = configparser.ConfigParser()
CONFIG['DEFAULT'] = {'User': '',
		'Group': '',
		'Mode': '644',
		'LogLevel': 'WARNING'}


def load_config():
	"""Check XDG directories for configuration files."""
	first_config = xdg.BaseDirectory.load_first_config("nielsen/nielsen.ini")

	try:
		CONFIG.read(first_config)
	except:
		logging.warning("Unable to load config.")


def clean_file_name(path):
	"""Remove cruft from filenames.
	Typical filenames are something like:
		The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi
	We want:
		The Glades -02.01- Family Matters.avi
	"""
	logging.info("Processing %s" % path)

	p = re.compile(r"(?P<series>.*)\s+S?(?P<season>\d{2,})\s?E?(?P<episode>\d{2,})\s*(?P<title>.*)?\s+(?P<extension>\w+)$", re.IGNORECASE)
	m = p.match(re.compile("\.").sub(" ", path))
	if m:
		series = m.group("series").strip()

		# Use title case if everything is lowercase
		if m.group("series").islower():
			series = m.group("series").title()

		# Strip tags and release notes from the episode title
		tags = re.compile(r"(HDTV|720p|WEB|PROPER|REPACK|RERIP).*", re.IGNORECASE)
		title = re.sub(tags, "", m.group("title")).strip()

		# Use title case if everything is lowercase
		if title.islower():
			title = title.title()

		clean = "{0} -{1}.{2}- {3}.{4}".format(
			series,
			m.group("season").strip(),
			m.group("episode").strip(),
			title,
			m.group("extension").strip())
		logging.info("Change to: {0}".format(clean))
		return clean
	else:
		logging.info("{0} did not match pattern, skipping.".format(path))
		return None


def process_file(path):
	"""Set ownership and permissions for files, then rename."""
	if CONFIG['Options']['User'] or CONFIG['Options']['Group']:
		chown(path, CONFIG['Options']['User'] or None,
			CONFIG['Options']['Group'] or None)

	if CONFIG['Options']['Mode']:
		chmod(path, int(CONFIG['Options']['Mode'], 8))

	clean = clean_file_name(path)
	if clean:
		rename(path, clean)


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

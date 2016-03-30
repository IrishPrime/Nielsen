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


def load_config():
	"""Check XDG directories for configuration files."""
	first_config = xdg.BaseDirectory.load_first_config("nielsen/nielsen.ini")

	try:
		CONFIG.read(first_config)
	except:
		logging.warning("Unable to load config.")


def rename_file(path):
	"""Remove cruft from filenames.
	Typical filenames are something like:
		The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi
	We want:
		The Glades -02.01- Family Matters.avi
	"""
	logging.info("Processing %s" % path)
	p = re.compile(r"(?P<series>.*) S(?P<season>\d+)E(?P<episode>\d+) (?P<title>.*?)?(?P<junk> HDTV.*?)? ?(?P<extension>\S{3,4})$")
	m = p.match(re.compile("\.").sub(" ", path))
	if m:
		clean = "{0} -{1}.{2}- {3}.{4}".format(
			m.group("series"),
			m.group("season"),
			m.group("episode"),
			m.group("title"),
			m.group("extension"))
		logging.info("Moving to: {0}".format(clean))
		rename(path, clean)
	else:
		logging.info("{0} did not match pattern, skipping.".format(path))


def process_file(path):
	"""Set ownership and permissions for files, then rename."""
	chown(path, CONFIG['DEFAULT']['User'], CONFIG['DEFAULT']['Group'])
	chmod(path, int(CONFIG['DEFAULT']['Mode'], 8))
	rename_file(path)


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
		CONFIG['DEFAULT']['User'] = ARGS.user

	if ARGS.group:
		CONFIG['DEFAULT']['Group'] = ARGS.group

	if ARGS.mode:
		CONFIG['DEFAULT']['Mode'] = ARGS.mode

	if ARGS.log_level:
		CONFIG['DEFAULT']['LogLevel'] = ARGS.log_level.upper()

	# Validate the log level
	logging.basicConfig(filename="nielsen.log",
		level=getattr(logging, CONFIG['DEFAULT']['LogLevel'], 30))

	logging.debug("User: {0}, Group: {1}, Mode: {2}, LogLevel: {3}".format(
		CONFIG['DEFAULT']['User'],
		CONFIG['DEFAULT']['Group'],
		CONFIG['DEFAULT']['Mode'],
		CONFIG['DEFAULT']['LogLevel']))

	# Iterate over files
	for f in ARGS.files:
		logging.info(f)
		process_file(f)


if __name__ == "__main__":
	main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

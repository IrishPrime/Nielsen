#!/usr/bin/env python3
"""
Config module for Nielsen.
The CONFIG variable from this module should be imported into other modules as
needed.
"""
import configparser
from os import getenv, name, path

CONFIG = configparser.ConfigParser()
CONFIG.add_section('Options')
CONFIG.add_section('Filters')
CONFIG.add_section('IMDB')
CONFIG['Options'] = {
	'User': '',
	'Group': '',
	'Mode': '644',
	'LogFile': 'nielsen.log',
	'LogLevel': 'WARNING',
	'MediaPath': '',
	'OrganizeFiles': 'False',
	'DryRun': 'False',
	'IMDB': 'False',
}


def load_config(file_name=None):
	"""Load config file specified by file_name, or check XDG directories for
	configuration file."""
	if file_name and path.isfile(file_name):
		config_file = file_name
	else:
		if name == "posix":
			config_file = ["/etc/xdg/nielsen/nielsen.ini",
				"/etc/nielsen/nielsen.ini",
				path.expanduser("~/.config/nielsen/nielsen.ini")]
		elif name == "nt":
			config_file = path.join("", getenv("APPDATA"), "nielsen", "nielsen.ini")

	return CONFIG.read(config_file)


def update_imdb_ids(file_name=None):
	"""Add imdb_ids to IMDB section of file_name or default user file."""
	# Reloading the config will overwrite existing options from filename, but
	# will not unset newly added options, so the IMDB section should be
	# unaffected.
	config_files = load_config(file_name)
	file_name = config_files[-1]
	with open(file_name, 'w') as f:
		CONFIG.write(f)

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

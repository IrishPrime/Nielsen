#!/usr/bin/env python3
'''
Config module for Nielsen.
The CONFIG variable from this module should be imported into other modules as
needed.
'''
import configparser
from os import getenv, name, path

CONFIG = configparser.ConfigParser()
CONFIG.add_section('Options')
CONFIG.add_section('Filters')
CONFIG.add_section('IDs')
CONFIG['Options'] = {
	'User': '',
	'Group': '',
	'Mode': '644',
	'Interactive': 'False',
	'LogFile': 'nielsen.log',
	'LogLevel': 'WARNING',
	'MediaPath': '',
	'OrganizeFiles': 'False',
	'DryRun': 'False',
	'FetchTitles': 'False',
	'ServiceURI': 'http://api.tvmaze.com/',
	'Format': '{series} -{season}.{episode}- {title}.{extension}',
}


def load_config(filename=None):
	'''Load config file specified by filename, or check XDG directories for
	configuration files.'''
	if filename and path.isfile(filename):
		config_file = filename
	else:
		if name == "posix":
			config_file = ["/etc/xdg/nielsen/nielsen.ini",
				"/etc/nielsen/nielsen.ini",
				path.expanduser("~/.config/nielsen/nielsen.ini")]
		elif name == "nt":
			config_file = path.join("", getenv("APPDATA"), "nielsen", "nielsen.ini")

	return CONFIG.read(config_file)


def update_series_ids(filename=None):
	'''Add series_ids to IDs section of filename or default user file.'''
	# Reloading the config will overwrite existing options from filename, but
	# will not unset newly added options, so the IDs section should be
	# unaffected by said reload.
	config_files = load_config(filename)
	filename = config_files[-1]
	with open(filename, 'w') as f:
		CONFIG.write(f)


# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

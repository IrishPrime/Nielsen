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


def load_config(filename=None):
	"""Load config file specified by filename, or check XDG directories for
	configuration file."""
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

	try:
		CONFIG.add_section('Options')
	except configparser.DuplicateSectionError:
		pass

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

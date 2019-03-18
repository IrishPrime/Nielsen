#!/usr/bin/env python3
'''CLI frontend to Nielsen.'''

import argparse
import logging
import nielsen.api
import nielsen.config


def main():
	'''Handle command line arguments and run all files through the process_file
	function.'''

	# Command line arguments
	ap = argparse.ArgumentParser(description=
		"Process episodes of TV shows for storage on a media server.")

	# Config file
	ap.add_argument("-c", "--config", dest="config_file", help="Config file")

	# Ownership and permissions
	ap.add_argument("-u", "--user", dest="user", help="User to own files")
	ap.add_argument("-g", "--group", dest="group", help="Group to own files")
	ap.add_argument("-m", "--mode", dest="mode", type=str,
		help="File mode (permissions) in octal")

	# Organize files
	group = ap.add_mutually_exclusive_group()
	group.add_argument("-o", "--organize", dest="organize", action="store_const",
		const='True', help="Organize files")
	group.add_argument("--no-organize", dest="organize", action="store_const",
		const='False', help="Do not organize files")

	# Fetch titles
	group = ap.add_mutually_exclusive_group()
	group.add_argument("-f", "--fetch", dest="fetch", action="store_const",
		const='True', help="Fetch titles from the web")
	group.add_argument("--no-fetch", dest="fetch", action="store_const",
		const='False', help="Do not fetch titles from the web")

	# Interactive series selection
	group = ap.add_mutually_exclusive_group()
	group.add_argument("-i", "--interactive", dest="interactive",
		action="store_const", const='True', help="Prompt user when needed")
	group.add_argument("--no-interactive", dest="interactive",
		action="store_const", const='False', help="Do not prompt user")

	# Dry run
	ap.add_argument("-n", "--dry-run", dest="dry_run", action="store_const",
		const='True', help="Do not rename files, just list the renaming actions.")

	# Media path
	ap.add_argument("-p", "--path", dest="mediapath",
		help="Base directory to organize files into")

	# Logging
	ap.add_argument("-l", "--log", dest="log_level", type=str,
		choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
		help="Logging level")

	# Files
	ap.add_argument("FILE", nargs="+", type=str, help="File(s) to operate on")
	args = ap.parse_args()

	# Load configuration
	nielsen.config.load_config(args.config_file)

	# Override the settings in the config file if given on the command line
	if args.user:
		nielsen.config.CONFIG.set('Options', 'User', args.user)

	if args.group:
		nielsen.config.CONFIG.set('Options', 'Group', args.group)

	if args.mode:
		nielsen.config.CONFIG.set('Options', 'Mode', args.mode)

	if args.organize:
		nielsen.config.CONFIG.set('Options', 'OrganizeFiles', args.organize)

	if args.fetch:
		nielsen.config.CONFIG.set('Options', 'FetchTitles', args.fetch)

	if args.interactive:
		nielsen.config.CONFIG.set('Options', 'Interactive', args.interactive)

	if args.dry_run:
		nielsen.config.CONFIG.set('Options', 'DryRun', args.dry_run)

	if args.mediapath:
		nielsen.config.CONFIG.set('Options', 'MediaPath', args.mediapath)

	if args.log_level:
		nielsen.config.CONFIG.set('Options', 'LogLevel', args.log_level.upper())

	# Configure logging
	logging.basicConfig(filename=nielsen.config.CONFIG.get('Options', 'LogFile'),
		format='%(asctime)-15s %(levelname)-8s %(message)s',
		level=getattr(logging, nielsen.config.CONFIG.get('Options', 'LogLevel'), 30))

	# Log all configuration options
	logging.debug(dict(nielsen.config.CONFIG.items('Options')))

	# Iterate over files
	for f in args.FILE:
		nielsen.api.process_file(f)

	# Add series IDs to config file
	nielsen.config.update_series_ids(args.config_file)


if __name__ == '__main__':
	main()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

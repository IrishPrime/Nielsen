#!/usr/bin/env python3

'''
System-level file operations needed by the API. These functions operate on the
various Path class objects provided by the pathlib library. These functions
probably won't ever need to be called directly by a client.
'''

import logging
from shutil import chown, move as su_move
from nielsen.config import CONFIG


def set_file_mode(file):
	'''Set the mode of `file` to the value defined in `CONFIG`.'''
	if CONFIG.get('Options', 'Mode'):
		try:
			file.chmod(int(CONFIG.get('Options', 'Mode'), 8))
		except PermissionError as err:
			logging.error("chmod failed. %s", err)
			raise


def set_file_ownership(file):
	'''Set owner and group of `file` to the values defined in `CONFIG`.'''
	if (CONFIG.get('Options', 'User') or CONFIG.get('Options', 'Group')):
		try:
			chown(file, CONFIG.get('Options', 'User') or None,
				CONFIG.get('Options', 'Group') or None)
			status = True
		except PermissionError as err:
			logging.error("chown failed. %s", err)
			raise


def create_hierarchy(file):
	'''Create the directory hierarchy for the given `file`.'''
	try:
		# Create the parent directories of the file path if they don't exist
		file.parent.mkdir(mode=int(CONFIG.get('Options', 'mode'), 8),
				parents=True, exist_ok=True)
		logging.debug('Created: %s', file.parent)
		status = True
	except FileExistsError:
		logging.debug('%s already exists', file.parent)
	except PermissionError as err:
		logging.error(err)
		raise


def move(src, dst):
	'''Move the file `src` to the path `dst`, but do not overwrite existing files.'''
	if dst.exists() or src == dst:
		# If the destination file already exists, or the source and destination
		# point to the same path, take no further actions
		logging.debug('%s already in MediaPath. File will not be moved.', dst)

	try:
		su_move(src, dst)
	except PermissionError as err:
		logging.error(err)
		raise


# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

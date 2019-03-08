#!/usr/bin/env python3
'''
chown, chmod, rename, and organize TV show files.
'''

from nielsen.api import (
	filter_filename,
	filter_series,
	get_file_info,
	organize_file,
	process_file,
)

from nielsen.config import (
	CONFIG,
	load_config,
	update_series_ids,
)

__all__ = ['api', 'tv', 'config']

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

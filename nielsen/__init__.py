#!/usr/bin/env python3
'''
chown, chmod, rename, and organize TV show files.
'''

from .api import (
	filter_series,
	get_file_info,
	organize_file,
	process_file,
)

from .config import (
	CONFIG,
	load_config,
	update_series_ids,
)

from .titles import (
	get_episode_title,
	get_series_id,
)

__all__ = ['api', 'titles', 'config']

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

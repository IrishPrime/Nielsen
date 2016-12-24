#!/usr/bin/env python3
'''Mark this as a package.'''

from .api import (
	filter_series,
	get_file_info,
	organize_file,
	process_file,
)

from .config import (
	CONFIG,
	load_config,
	update_imdb_ids,
)

from .titles import (
	get_episode_title,
	get_imdb_id,
)

__all__ = ['api', 'titles', 'config']

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

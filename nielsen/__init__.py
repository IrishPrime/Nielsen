#!/usr/bin/env python3
'''Mark this as a package.'''


from .nielsen import (
	CONFIG,
	filter_series,
	get_file_info,
)

from nielsen.titles import (
	get_episode_title,
	get_imdb_id,
)

__all__ = ['nielsen', 'titles', 'config', 'version']

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

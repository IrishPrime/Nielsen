#!/usr/bin/env python3
"""
Episode title module for Nielsen.
Fetches information from IMDB through the omdb module.
"""

import logging
import omdb
from .config import CONFIG


def get_imdb_id(series):
	"""Return the IMDB ID of a given series.
	If an ID isn't found in the config, search IMDB and allow the user to
	select a match."""

	if CONFIG.has_option('IMDB', series):
		# Check config for IMDB ID
		imdb_id = CONFIG['IMDB'][series]
	else:
		# Search IMDB for series
		results = omdb.search_series(series)

		if len(results) == 1:
			# If only one result, use it
			imdb_id = results[0]['imdb_id']
		elif len(results) > 1:
			# If multiple results, select one
			print("Search results for '{0}'".format(series))
			for i, result in enumerate(results):
				print("{0}. {1} ({2}) - {3}".format(i, result['title'],
					result['year'], result['imdb_id']))
			print("Other input cancels without selection.")

			try:
				selection = int(input("Select series: "))
				imdb_id = results[int(selection)]['imdb_id']
			except (ValueError, IndexError, EOFError) as e:
				logging.error("Caught exception: {0}".format(e))
				return None

	logging.info("IMDB ID for '{0}': {1}".format(series, imdb_id))
	# Add whatever we find or select back to the config
	CONFIG.set('IMDB', series, imdb_id)

	return imdb_id


def get_episode_title(season, episode, imdb_id=None, series=None):
	"""Return the episode title using the series name or IMDB ID, season, and
	episode number."""
	if imdb_id is None and series:
		imdb_id = get_imdb_id(series)

	if imdb_id:
		logging.info("IMDB ID: {0}, Season: {1}, Episode: {2}".format(imdb_id,
			season, episode))
		return omdb.imdbid(imdb_id, season=season, episode=episode)['title']
	else:
		return None

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

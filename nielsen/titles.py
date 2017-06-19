#!/usr/bin/env python3
'''
Episode title module for Nielsen.
Fetches information from TVmaze.
'''

import logging
import requests
from .config import CONFIG


def get_series_id(series):
	'''Return a unique ID for a given series.
	If an ID isn't found in the config, allow the user to select a match from
	search results.'''
	if CONFIG.has_option('IDs', series):
		# Check config for series ID
		series_id = CONFIG['IDs'][series]
	else:
		# Search for the series
		try:
			r = requests.get('{0}search/shows?q={1}'.
				format(CONFIG['Options']['ServiceURI'], series))
		except:
			logging.error('Unable to retrieve series names.')

		# Get search results as JSON
		results = r.json()

		if len(results) == 1:
			# If only one result, use it
			series_id = results[0]['show']['id']
		elif len(results) > 1:
			# If multiple results, display them for selection
			print("Search results for '{0}'".format(series))
			for i, result in enumerate(results):
				print('{0}. {1} ({2}) - {3}'.format(i, result['show']['name'],
					result['show']['premiered'], result['show']['id']))
			print('Other input cancels without selection.')
			try:
				selection = int(input('Select series: '))
				series_id = results[int(selection)]['show']['id']
			except (ValueError, IndexError, EOFError) as e:
				logging.error('Caught exception: {0}'.format(e))
				return None
		else:
			# No results
			series_id = None

	logging.info("Show ID for '{0}': {1}".format(series, series_id))

	# Add whatever we find or select back to the config
	CONFIG.set('IDs', series, str(series_id))

	return series_id


def get_episode_title(season, episode, series_id=None, series=None):
	'''Return the episode title using the series name or ID, season, and
	episode number.'''
	if series_id is None and series:
		series_id = get_series_id(series)

	if series_id:
		logging.info('Series ID: {0}, Season: {1}, Episode: {2}'.format(series_id,
			season, episode))
		try:
			r = requests.get('{0}shows/{1}/episodebynumber?season={2}&number={3}'
					.format(CONFIG['Options']['ServiceURI'], series_id, season, episode))
			title = r.json()['name']
			logging.info('Title: {}'.format(title))
			return title
		except:
			logging.error('Unable to retrieve episode title.')

	# If all else fails, return an empty string, not None
	return str()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

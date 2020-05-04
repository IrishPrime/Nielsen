#!/usr/bin/env python3
'''
Episode title module for Nielsen.
Fetches information from TVmaze.
'''

import logging
import requests
from nielsen.config import CONFIG


def select_series(series, results):
	'''Return a series from a list of results.'''
	if len(results) == 1:
		# If only one result, use it
		return results[0]['show']['id']

	print("Search results for '{0}'".format(series))
	for i, result in enumerate(results):
		print('{0}. {1} ({2}) - {3}'.format(i, result['show']['name'],
			result['show']['premiered'], result['show']['id']))

	print('Other input cancels without selection.')

	try:
		selection = int(input('Select series: '))
		return results[int(selection)]['show']['id']
	except (ValueError, IndexError, EOFError) as e:
		logging.error('Caught exception: %s', e)
		return None


def get_series_id(series, interactive=CONFIG.get('Options', 'Interactive')):
	'''Return a unique ID for a given series.
	If an ID isn't found in the config, allow the user to select a match from
	search results.'''

	# Check config for series ID
	series_id = CONFIG.get('IDs', series, fallback=None)

	if not series_id:
		# Search for the series
		if interactive:
			endpoint = '{0}/search/shows?q={1}'
		else:
			endpoint = '{0}/singlesearch/shows?q={1}'

		endpoint = endpoint.format(CONFIG['Options']['ServiceURI'], series)

		try:
			response = requests.get(endpoint)
		except IOError as e:
			logging.error('Unable to retrieve series names.')
			logging.debug(e)
			exit()

		# Get search results as JSON
		results = response.json()

		if response.status_code == 200:
			# Only check successful responses
			if interactive:
				# Interactive selection if required
				series_id = select_series(series, results)
			else:
				# The results are structured differently in non-interactive mode
				series_id = results['id']

	logging.info("Show ID for '%s': %s", series, series_id)

	# Add whatever we find or select back to the config
	CONFIG.set('IDs', series, str(series_id))

	return series_id


def get_episode_title(season, episode, series_id=None, series=None):
	'''Return the episode title using the series name or ID, season, and
	episode number.'''
	if series_id is None and series:
		series_id = get_series_id(series)

	if series_id:
		logging.info('Series ID: %s, Season: %s, Episode: %s', series_id,
				season, episode)
		try:
			response = requests.get('{0}shows/{1}/episodebynumber?season={2}&number={3}'
					.format(CONFIG['Options']['ServiceURI'], series_id, season, episode))
			title = response.json()['name']
			logging.info('Title: %s', title)
			return title
		except IOError as e:
			logging.error('Unable to retrieve episode title.')
			logging.debug(e)

	# If all else fails, return an empty string, not None
	return str()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

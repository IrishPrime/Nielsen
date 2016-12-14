#!/usr/bin/env python3
"""Episode title module for nielsen."""

import omdb


def get_imdb_id(series):
	"""Return the IMDB ID of a given series.
	If an ID isn't found in the config, search IMDB and allow the user to
	select a match."""
	results = omdb.search_series(series)

	if len(results) > 1:
		for i, result in enumerate(results):
			print("{0}. {1} ({2}) - {3}".format(i, result['title'], result['year'],
				result['imdb_id']))

		print("C. Cancel without a selection.")
		selection = input("Select series: ")
		return results[int(selection)]['imdb_id']
	elif len(results) == 1:
		return results[0]['imdb_id']
	else:
		return None


def get_episode_title(imdb_id, season, episode):
	"""Return the episode title using the IMDB ID, season, and episode number."""
	return omdb.imdbid(imdb_id, season=season, episode=episode)['title']

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

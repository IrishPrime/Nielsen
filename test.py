#!/usr/bin/env python3
'''Test cases for Nielsen.'''

import unittest
import unittest.mock
import pathlib
import tempfile
import nielsen

# Ensure config is loaded regardless of test order
nielsen.load_config('nielsen.ini')


class TestConfig(unittest.TestCase):
	'''Tests for the config module'''

	def test_load_config(self):
		'''Load the sample config file and check for a non-default value'''
		loaded = nielsen.load_config('nielsen.ini')
		self.assertEqual(loaded, ['nielsen.ini'])
		self.assertEqual(nielsen.CONFIG['Options']['LogFile'], '/var/log/nielsen.log')


class TestAPI(unittest.TestCase):
	'''Tests for the core functionality.'''

	def test_get_file_info(self):
		'''Get info from sample files and compare to expected output.'''
		filenames = {
			"Something.Close.12.mp4":
			None,

			# Very nicely formatted
			"The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			# Needs title casing
			"the.glades.s02e01.family.matters.hdtv.xvid-fqm.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			# Missing title
			"The.Glades.S02E01.HDTV.XviD-FQM.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			# Already processed by nielsen
			"The Glades -02.01- Family Matters.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			# Another common post-processing format
			"The Glades -201- Family Matters.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			# Four digit season/episode code, fewer hyphens
			"Firefly 0101 - Serenity.mkv": {
				"series": "Firefly",
				"season": "01",
				"episode": "01",
				"title": "Serenity",
				"extension": "mkv"
			},

			# Has most necessary information, but formatted strangely
			"Supernatural.S10E15.mp4": {
				"series": "Supernatural",
				"season": "10",
				"episode": "15",
				"title": "The Things They Carried",
				"extension": "mp4"
			},

			# Same as above, but with an extra dot between season and episode
			"Pushing.Daisies.S02.E03.mp4": {
				"series": "Pushing Daisies",
				"season": "02",
				"episode": "03",
				"title": "Bad Habits",
				"extension": "mp4"
			},

			# Nicely formatted, but with an apostrophe in the title
			"Person.of.Interest.S0310.The.Devil's.Share.HDTV.avi": {
				"series": "Person of Interest",
				"season": "03",
				"episode": "10",
				"title": "The Devil's Share",
				"extension": "avi"
			},

			# Title casing this will yield slightly incorrect results
			"person.of.interest.s0310.the.devil's.share.hdtv.avi": {
				"series": "Person of Interest",
				"season": "03",
				"episode": "10",
				"title": "The Devil'S Share",
				"extension": "avi"
			},

			# Testing WEB-RiP tag and series filtering
			"Castle.(2009).S07E18.720p.WEB-RiP.mp4": {
				"series": "Castle",
				"season": "07",
				"episode": "18",
				"title": "At Close Range",
				"extension": "mp4"
			},

			# Same as above, but with all fields
			"Castle.(2009).S01E01.Flowers.for.Your.Grave.720p.WEB-RiP.mp4": {
				"series": "Castle",
				"season": "01",
				"episode": "01",
				"title": "Flowers for Your Grave",
				"extension": "mp4"
			},

			# Four digit season and episode combination
			"supernatural.1117.red.meat.hdtv-lol[ettv].mp4": {
				"series": "Supernatural",
				"season": "11",
				"episode": "17",
				"title": "Red Meat",
				"extension": "mp4"
			},

			# Specifying file within a directory
			"supernatural.1117.hdtv-lol[ettv]/supernatural.1117.red.meat.hdtv-lol[ettv].mp4": {
				"series": "Supernatural",
				"season": "11",
				"episode": "17",
				"title": "Red Meat",
				"extension": "mp4"
			},

			# Four digit year followed by three digit season and episode combination
			"the.flash.(2014).217.flash.back.hdtv-lol[ettv].mp4": {
				"series": "The Flash",
				"season": "02",
				"episode": "17",
				"title": "Flash Back",
				"extension": "mp4"
			},

			# Four digit year with season and episode markers
			"The.Flash.2014.S02E17.Flash.Back.HDTV.x264-LOL[ettv].mp4": {
				"series": "The Flash",
				"season": "02",
				"episode": "17",
				"title": "Flash Back",
				"extension": "mp4"
			},

			# Four digit year followed by three digit season and episode combination
			"The.Flash.2014.217.Flash.Back.HDTV.x264-LOL[ettv].mp4": {
				"series": "The Flash",
				"year": "2014",
				"season": "02",
				"episode": "17",
				"title": "Flash Back",
				"extension": "mp4"
			},

			# Tag removal
			"Game.of.Thrones.S06E07.1080p.HDTV.6CH.ShAaNiG.mkv": {
				"series": "Game of Thrones",
				"season": "06",
				"episode": "07",
				"title": "The Broken Man",
				"extension": "mkv"
			},

			# File in a subdirectory
			"Game.of.Thrones.S07E01.720p.HDTV.x264-AVS[rarbg]/Game.of.Thrones.S07E01.720p.HDTV.x264-AVS.mkv": {
				"series": "Game of Thrones",
				"season": "07",
				"episode": "01",
				"title": "Dragonstone",
				"extension": "mkv"
			},

			# Multi-episode file
			"Bones.S04E01E02.720p.HDTV.X264-DIMENSION.mkv": {
				"series": "Bones",
				"season": "04",
				"episode": "01-02",
				"title": "",
				"extension": "mkv"
			},

			# Single episode with what looks like a second episode marker in the title
			"Sample.Show.S01E01.E19.Protocol.720p.HDTV.X264-DIMENSION.mkv": {
				"series": "Sample Show",
				"season": "01",
				"episode": "01",
				"title": "E19 Protocol",
				"extension": "mkv"
			},

			# Unusual filename for last ditch effort pattern
			"Limitless S01E11 This Is Your Brian on Drugs (1080p x265 Joy).mkv": {
				"series": "Limitless",
				"season": "01",
				"episode": "11",
				"title": "This is Your Brian on Drugs",
				"extension": "mkv"
			},
		}

		for path, info in filenames.items():
			self.assertEqual(nielsen.get_file_info(path), info)


	def test_filter_series(self):
		'''Test mapping series to a preferred name.'''
		self.assertEqual(nielsen.filter_series("Castle (2009)"), "Castle")
		self.assertEqual(nielsen.filter_series("Dc'S Legends Of Tomorrow"),
			"Legends of Tomorrow")
		self.assertEqual(nielsen.filter_series("Game Of Thrones"), "Game of Thrones")
		self.assertEqual(nielsen.filter_series("It's Always Sunny In Philadelphia"),
			"It's Always Sunny in Philadelphia")
		self.assertEqual(nielsen.filter_series("Its Always Sunny In Philadelphia"),
			"It's Always Sunny in Philadelphia")
		self.assertEqual(nielsen.filter_series("Mr Robot"), "Mr. Robot")
		self.assertEqual(nielsen.filter_series("Person Of Interest"),
			"Person of Interest")
		self.assertEqual(nielsen.filter_series("The Flash (2014)"), "The Flash")
		self.assertEqual(nielsen.filter_series("The Flash 2014"), "The Flash")


	def test_sanitize_filename(self):
		'''Test removing invalid characters from filenames.'''
		# Invalid characters for POSIX systems
		self.assertEqual(nielsen.sanitize_filename(
			'Brooklyn Nine-Nine -02.20- AC/DC.mp4'),
			'Brooklyn Nine-Nine -02.20- AC-DC.mp4')


	def test_organize_file(self):
		'''Test for the correct file path/hierarchy.'''
		series = 'Firefly'
		season = '01'
		filename = "Firefly -01.01- Serenity.mkv"

		# Set the MediaPath to a temporary directory to avoid conflicting with
		# real file paths. Set the dryrun argument to True to avoid modifying
		# the filesystem. Test the filesystem afterwards to confirm no
		# directories were created.
		with tempfile.TemporaryDirectory() as tmp:
			nielsen.CONFIG.set('Options', 'MediaPath', tmp)
			dst = nielsen.organize_file(filename, 'Firefly', '01', True)
			self.assertEqual(
				pathlib.PurePath(tmp, series, f'Season {season}', filename),
				dst)
			self.assertFalse(dst.parent.exists())


class TestTV(unittest.TestCase):
	'''Tests for the tv module'''

	tvmaze_api = unittest.mock.Mock()

	@unittest.mock.patch('nielsen.tv.get_series_id')
	def test_get_series_id(self, tvmaze_api):
		'''Test that series names match up with series IDs.'''
		# Create mock returns for the TVmaze API
		tvmaze_api.side_effect = ['31', '3182', '315', '4', '68', '11405',
				'82', '118', '1851', '6393', '1859', '3144', '19', '13', '522',
				'1371']

		# Test series with a variety of names
		self.assertEqual(nielsen.tv.get_series_id('Agents of SHIELD'), '31')
		self.assertEqual(nielsen.tv.get_series_id('American Gods'), '3182')
		self.assertEqual(nielsen.tv.get_series_id('Archer'), '315')
		self.assertEqual(nielsen.tv.get_series_id('Arrow'), '4')
		self.assertEqual(nielsen.tv.get_series_id('Castle'), '68')
		self.assertEqual(nielsen.tv.get_series_id(
			"Dirk Gently's Holistic Detective Agency"), '11405')
		self.assertEqual(nielsen.tv.get_series_id('Game of Thrones'), '82')
		self.assertEqual(nielsen.tv.get_series_id('House'), '118')
		self.assertEqual(nielsen.tv.get_series_id('Legends of Tomorrow'), '1851')
		self.assertEqual(nielsen.tv.get_series_id('Legion'), '6393')
		self.assertEqual(nielsen.tv.get_series_id('Lucifer'), '1859')
		self.assertEqual(nielsen.tv.get_series_id('Preacher'), '3144')
		self.assertEqual(nielsen.tv.get_series_id('Supernatural'), '19')
		self.assertEqual(nielsen.tv.get_series_id('The Flash'), '13')
		self.assertEqual(nielsen.tv.get_series_id('Top Gear'), '522')
		self.assertEqual(nielsen.tv.get_series_id('Westworld'), '1371')

	@unittest.mock.patch('nielsen.tv.get_episode_title')
	def test_get_episode_title(self, tvmaze_api):
		'''Test retrieving episode titles by series name and ID'''
		# Create mock returns for the TVmaze API
		tvmaze_api.side_effect = ['Last Refuge', 'Head Case']

		self.assertEqual(nielsen.tv.get_episode_title(1, 12, series_id='1851'),
			'Last Refuge')
		self.assertEqual(nielsen.tv.get_episode_title(4, 3, series='Castle'),
			'Head Case')


if __name__ == '__main__':
	unittest.main()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

#!/usr/bin/env python3
"""Test cases for nielsen."""

import unittest
import nielsen
import titles
import config


class TestConfig(unittest.TestCase):

	def test_load_config(self):
		config.load_config('nielsen.ini')
		self.assertEqual(config.CONFIG['Options']['LogFile'], '/var/log/nielsen.log')


class TestNielsen(unittest.TestCase):

	def test_get_file_info(self):

		file_names = {
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

			# Missing Title
			"The.Glades.S02E01.HDTV.XviD-FQM.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "",
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

			# Has most necessary information, but formatted strangely
			"Supernatural.S10E15.mp4": {
				"series": "Supernatural",
				"season": "10",
				"episode": "15",
				"title": "",
				"extension": "mp4"
			},

			# Same as above, but with an extra dot between season and episode
			"Pushing.Daisies.S02.E03.mp4": {
				"series": "Pushing Daisies",
				"season": "02",
				"episode": "03",
				"title": "",
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
				"title": "",
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
				"title": "",
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
		}

		for path, info in file_names.items():
			self.assertEqual(nielsen.get_file_info(path), info)

	def test_filter_series(self):
		self.assertEqual(nielsen.filter_series("Castle (2009)"), "Castle")
		self.assertEqual(nielsen.filter_series("Dc'S Legends Of Tomorrow"), "Legends of Tomorrow")
		self.assertEqual(nielsen.filter_series("Game Of Thrones"), "Game of Thrones")
		self.assertEqual(nielsen.filter_series("It's Always Sunny In Philadelphia"), "It's Always Sunny in Philadelphia")
		self.assertEqual(nielsen.filter_series("Its Always Sunny In Philadelphia"), "It's Always Sunny in Philadelphia")
		self.assertEqual(nielsen.filter_series("Mr Robot"), "Mr. Robot")
		self.assertEqual(nielsen.filter_series("Person Of Interest"), "Person of Interest")
		self.assertEqual(nielsen.filter_series("The Flash (2014)"), "The Flash")
		self.assertEqual(nielsen.filter_series("The Flash 2014"), "The Flash")


class TestTitles(unittest.TestCase):

	def test_get_imdb_id(self):
		self.assertEqual(titles.get_imdb_id('Agents of SHIELD'), 'tt2364582')

	def test_get_episode_title(self):
		self.assertEqual(titles.get_episode_title(1, 12, imdb_id='tt4532368'), 'Last Refuge')
		self.assertEqual(titles.get_episode_title(4, 2, series='Castle'), 'Heroes and Villains')


if __name__ == "__main__":
	unittest.main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

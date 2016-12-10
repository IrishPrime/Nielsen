#!/usr/bin/env python3
"""Test cases for nielsen."""

import unittest
import nielsen


class TestNielsen(unittest.TestCase):

	nielsen.load_config()

	def test_get_file_info(self):
		file_names = {
			"Something.Close.12.mp4":
			None,

			"The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			"the.glades.s02e01.family.matters.hdtv.xvid-fqm.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			"The.Glades.S02E01.HDTV.XviD-FQM.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "",
				"extension": "avi"
			},

			"The Glades -02.01- Family Matters.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			"The Glades -201- Family Matters.avi": {
				"series": "The Glades",
				"season": "02",
				"episode": "01",
				"title": "Family Matters",
				"extension": "avi"
			},

			"Supernatural.S10E15.mp4": {
				"series": "Supernatural",
				"season": "10",
				"episode": "15",
				"title": "",
				"extension": "mp4"
			},

			"Pushing.Daisies.S02.E03.mp4": {
				"series": "Pushing Daisies",
				"season": "02",
				"episode": "03",
				"title": "",
				"extension": "mp4"
			},

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

			"Castle.(2009).S07E18.720p.WEB-RiP.mp4": {
				"series": "Castle",
				"season": "07",
				"episode": "18",
				"title": "",
				"extension": "mp4"
			},

			"Castle.(2009).S01E01.Flowers.for.Your.Grave.720p.WEB-RiP.mp4": {
				"series": "Castle",
				"season": "01",
				"episode": "01",
				"title": "Flowers for Your Grave",
				"extension": "mp4"
			},

			"supernatural.1117.red.meat.hdtv-lol[ettv].mp4": {
				"series": "Supernatural",
				"season": "11",
				"episode": "17",
				"title": "Red Meat",
				"extension": "mp4"
			},

			"supernatural.1117.hdtv-lol[ettv]/supernatural.1117.red.meat.hdtv-lol[ettv].mp4": {
				"series": "Supernatural",
				"season": "11",
				"episode": "17",
				"title": "Red Meat",
				"extension": "mp4"
			},

			"the.flash.(2014).217.flash.back.hdtv-lol[ettv].mp4": {
				"series": "The Flash",
				"season": "02",
				"episode": "17",
				"title": "Flash Back",
				"extension": "mp4"
			},

			"The.Flash.2014.S02E17.Flash.Back.HDTV.x264-LOL[ettv].mp4": {
				"series": "The Flash",
				"season": "02",
				"episode": "17",
				"title": "Flash Back",
				"extension": "mp4"
			},

			"The.Flash.2014.217.Flash.Back.HDTV.x264-LOL[ettv].mp4": {
				"series": "The Flash",
				"season": "02",
				"episode": "17",
				"title": "Flash Back",
				"extension": "mp4"
			},

			"Game.of.Thrones.S06E07.1080p.HDTV.6CH.ShAaNiG.mkv": {
				"series": "Game of Thrones",
				"season": "06",
				"episode": "07",
				"title": "",
				"extension": "mkv"
			},

			"Bones.S04E01E02.720p.HDTV.X264-DIMENSION.mkv": {
				"series": "Bones",
				"season": "04",
				"episode": "01-02",
				"title": "",
				"extension": "mkv"
			},

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


if __name__ == "__main__":
	unittest.main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

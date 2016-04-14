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
				"series": "Person Of Interest",
				"season": "03",
				"episode": "10",
				"title": "The Devil'S Share",
				"extension": "avi"
			},

			"Castle.(2009).S07E18.720p.WEB-RiP.mp4": {
				"series": "Castle (2009)",
				"season": "07",
				"episode": "18",
				"title": "",
				"extension": "mp4"
			},

			"Castle.(2009).S01E01.Flowers.for.Your.Grave.720p.WEB-RiP.mp4": {
				"series": "Castle (2009)",
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

			# "Bones.S04E01E02.720p.HDTV.X264-DIMENSION.mkv":
			# "Bones -04.01-02- .mkv",
		}

		for path, info in file_names.items():
			self.assertEqual(nielsen.get_file_info(path), info)


if __name__ == "__main__":
	unittest.main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

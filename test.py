#!/usr/bin/env python3
"""Test cases for nielsen."""

import unittest
import nielsen


class TestNielsen(unittest.TestCase):

	def test_clean_file_name(self):
		file_names = {
			"Something.Close.12.mp4":
			None,

			"The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi":
			"The Glades -02.01- Family Matters.avi",

			"The.Glades.S02E01.HDTV.XviD-FQM.avi":
			"The Glades -02.01- .avi",

			"Supernatural.S10E15.mp4":
			"Supernatural -10.15- .mp4",

			"Pushing.Daisies.S02.E03.mp4":
			"Pushing Daisies -02.03- .mp4",

			"Person.of.Interest.S0310.The.Devil's.Share.HDTV.avi":
			"Person of Interest -03.10- The Devil's Share.avi",

			"person.of.interest.s0349.episode.hdtv.avi":
			"Person Of Interest -03.49- Episode.avi",

			"Castle.(2009).S07E18.720p.WEB-RiP.mp4":
			"Castle (2009) -07.18- .mp4",

			"Castle.(2009).S01E01.Flowers.for.Your.Grave.720p.WEB-RiP.mp4":
			"Castle (2009) -01.01- Flowers for Your Grave.mp4",

			"supernatural.1117.red.meat.hdtv-lol[ettv].mp4":
			"Supernatural -11.17- Red Meat.mp4",
		}

		for original, clean in file_names.items():
			self.assertEqual(nielsen.clean_file_name(original), clean)


if __name__ == "__main__":
	unittest.main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

#!/usr/bin/env python3
"""Setup for Nielsen."""

from distutils.core import setup
from nielsen.version import VERSION

setup(
	name='Nielsen',
	version=VERSION,
	author="Michael 'Irish' O'Neill",
	author_email="irish.dot@gmail.com",
	url='https://github.com/IrishPrime/nielsen/',
	description='Rename and organize TV show files.',
	long_description='Rename, chown, chmod, and organize TV show files from the command line.',
	keywords=['media', 'rename', 'organize', 'tv'],
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'Intended Audience :: End Users/Desktop',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
		'Operating System :: Microsoft :: Windows',
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python',
		'Topic :: Desktop Environment :: File Managers',
		'Topic :: Multimedia :: Video',
	],
	platforms='linux',
	license='GNU General Public License v3 (GPLv3)',
	packages=['nielsen'],
)

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

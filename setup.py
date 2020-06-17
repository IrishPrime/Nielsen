#!/usr/bin/env python3
'''Setup for Nielsen.'''

from setuptools import setup

setup(
	name='Nielsen',
	version='2.2.2',
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
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python',
		'Topic :: Desktop Environment :: File Managers',
		'Topic :: Multimedia :: Video',
	],
	requires=['requests'],
	install_requires=['requests'],
	provides=['nielsen'],
	entry_points={
		'console_scripts': ['nielsen=bin.cli:main'],
	},
	platforms='linux',
	license='GNU General Public License v3 (GPLv3)',
	packages=['nielsen'],
)

# vim: tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab

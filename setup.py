#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

import versioneer

versioneer.VCS = 'git'
versioneer.versionfile_source = 'src/speview/_version.py'
versioneer.tag_prefix = '' # tags are like 1.2.0
versioneer.parentdir_prefix = 'speview-' # dirname like 'myproject-1.2.0'

setup(
    name='speview',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='Roman Kiselev',
    author_email='roman.kiselew@gmail.com',
    packages=["speview"],
    package_dir={"speview": "src/speview"},
    scripts=['src/speviewer'],
    url='https://github.com/ximeg/speview',
    license='LICENSE.txt',
    description='Program to display binary SPE files containing Raman spectra',
    long_description=open('README.md').read(),
    install_requires=[
        "numpy",
        "matplotlib",
        "scipy>=0.11.0",
        "xcal-raman>=0.1.5",
        "PyZenity>=0.1.4"
        ]
)


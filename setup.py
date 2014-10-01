#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='speview',
    version='0.2.0',
    author='Roman Kiselev',
    author_email='roman.kiselew@gmail.com',
    scripts=['speview.py'],
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


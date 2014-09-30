from setuptools import setup


setup(
    name='speview',
    version='0.1.0',
    author='Roman Kiselev',
    author_email='roman.kiselew@gmail.com',
    scripts=['speview.py'],
    url='https://github.com/ximeg/speview',
    license='LICENSE.txt',
    description='Program to display binary SPE files with Raman spectra',
    long_description=open('README.md').read(),
    install_requires=[
        "argparse>=1.2.1",
        "mock>=1.0.1",
        "nose>=1.3.4",
        "pyparsing>=2.0.2",
        "python-dateutil>=2.2",
        "six>=1.8.0",
        "wsgiref>=0.1.2",
        "xcal-raman>=0.1.5",
        "PySide>=1.2.2",
        "matplotlib>=1.4.0",
        "scipy>=0.14.0",
        "numpy>=1.9.0",
        "PyZenity>=0.1.4"
        ]
)


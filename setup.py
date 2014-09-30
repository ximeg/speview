from setuptools import setup

with open('requirements.txt') as f:
    lines = [x.strip() for x in f.read().splitlines()]
    reqs = [x for x in lines if not (x.startswith("#") or len(x) == 0)]

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
    install_requires=reqs
)


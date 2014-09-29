from distutils.core import setup

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
        "xcal_raman >= 0.1.5",
        "matplotlib",
    ],
)


from setuptools import setup, find_packages # Always prefer setuptools over distutils
from codecs import open 					# To use a consistent encoding
from os import path
here = path.abspath(path.dirname(__file__))
# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
	long_description = f.read()
setup(
	name = 'peasoup',
	version='0.1.2',
	description = 'Common tools for application deployment!',
	long_description =long_description,
	url = 'https://github.com/timeyyy/apptools',
	author='timothy eichler',
	author_email='tim_eichler@hotmail.com',
	license='BSD3',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'Topic :: Software Development :: Build Tools',
		'License :: OSI Approved :: BSD License',
		'Programming Language :: Python :: 3',
	],

	keywords = 'gui programming apptools python3 permissions deployment application',

	packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
)

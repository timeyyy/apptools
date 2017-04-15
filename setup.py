from setuptools import setup, find_packages # Always prefer setuptools over distutils
from os import path
setup(
	name = 'peasoup',
	version='0.1.5',
	description = 'Common tools for application deployment!',
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
        install_requires = [
            'tkquick',
            'psutil',
            'appdirs',
            'timstools'
        ],

	keywords = 'gui programming apptools python3 permissions deployment application',

	packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
)

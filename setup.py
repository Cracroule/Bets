__author__ = 'rpil'

from setuptools import setup, find_packages
from distutils.core import setup

setup(
    version='0.0.0.1',
    name='bets_project',
    description='personal project about bets',
    license='rpil',
    package_dir={'': 'src'},
    packages=['bets_project'],
    scripts=['scripts/validation.py'],
    install_requires=[]
)

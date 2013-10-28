#!/usr/bin/env python
# -*-coding: utf-8 -*-
import sys
import re
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

init_py = open("wbpy/__init__.py").read()
METADATA = dict(re.findall("__([a-z]+)__ = \"([^\"]+)\"", init_py))

kw = {}
if sys.version_info >= (3,):
    kw["use_2to3"] = True

setup(  
    name=METADATA["name"],
    version=METADATA["version"],
    license=METADATA["license"],
    author="Matthew Duck",
    author_email=METADATA["email"],
    description="A Python interface to the World Bank Indicators and Climate APIs",
    long_description=open('README.rst').read(),
    url="https://github.com/mattduck/wbpy",
    packages=['wbpy', 'wbpy.tests'],
    provides=['wbpy'],
    package_data={"wbpy": ["non_ISO_region_codes.json"]},
    install_requires=["pycountry"],
    tests_require=["tox"],
    classifiers=[
        'Development Status :: 4 - Beta',
         'Intended Audience :: Developers', 
         'Intended Audience :: Science/Research', 
         'License :: OSI Approved :: MIT License',
         'Operating System :: OS Independent', 
         'Programming Language :: Python', 
         'Programming Language :: Python 3', 
         'Topic :: Scientific/Engineering', 
        ],
    **kw)

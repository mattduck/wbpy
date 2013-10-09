#!/usr/bin/env python
import re
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

init_py = open("wbpy/__init__.py").read()
METADATA = dict(re.findall("__([a-z]+)__ = \"([^\"]+)\"", init_py))

setup(  
    name=METADATA["name"],
    version=METADATA["version"],
    license=METADATA["license"],
    author="Matthew Duck",
    author_email=METADATA["email"],
    description="A Python interface to the World Bank Indicators and Climate APIs",
    long_description=open('README.rst').read(),
    url="https://github.com/mattduck/wbpy",
    packages=['wbpy'],
    provides=['wbpy'],
    package_data={"wbpy": ["non_ISO_region_codes.json"]},
    install_requires=['pycountry'],
    classifiers=[
        'Development Status :: 4 - Beta',
         'Intended Audience :: Developers', 
         'Intended Audience :: Science/Research', 
         'License :: OSI Approved :: MIT License',
         'Operating System :: OS Independent', 
         'Programming Language :: Python', 
         'Topic :: Scientific/Engineering', 
        ]
    )

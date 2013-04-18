#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(  
    name="wbpy",
    version="0.2.1",
    license="MIT",
    author="Matthew Duck",
    author_email="matt@mattduck.com",
    description="A Python interface to the World Bank Indicators and Climate APIs",
    long_description=open('README.rst').read(),
    url="https://github.com/mattduck/wbpy",
    packages=['wbpy'],
    provides=['wbpy'],
    install_requires=['pycountry'],
    classifiers=['Development Status :: 3 - Alpha',
                 'Intended Audience :: Developers', 
                 'Intended Audience :: Science/Research', 
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: OS Independent', 
                 'Programming Language :: Python', 
                 'Topic :: Scientific/Engineering', 
                ]
 )

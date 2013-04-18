#!/usr/bin/env python
from distutils.core import setup

setup(  name="wbpy",
        version="0.2.0",
        license="MIT",
        description="A simpler interface to the World Bank APIs",
        long_description=open('README.rst').read(),
        author="Matthew Duck",
        author_email="matt@mattduck.com",
        url="https://github.com/mattduck/wbpy",
        packages=['wbpy'],
        install_requires=['pycountry'],
     )

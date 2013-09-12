#!/usr/bin/bash
# Builds README from ipython notebook, and makes Sphinx docs (which use the
# README). 
ipython nbconvert --to rst README.ipynb 
pushd "docs"; make html; popd

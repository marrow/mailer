#!/bin/bash
set -e
set -x

git config --global user.email "alice+travis@gothcandy.com"
git config --global user.name "Travis: Marrow"

pip install --upgrade setuptools 'pip<8.0.0' pytest
pip install codecov

pip install -e .[develop]

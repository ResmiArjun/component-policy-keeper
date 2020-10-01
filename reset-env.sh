#!/bin/bash

set -ex

PDIR=env/pk

echo "Reseting '$PDIR'"

rm -rf "$PDIR"

virtualenv -p python3 "$PDIR"
source "$PDIR"/bin/activate
pip install --upgrade pip
pip install -r requirements.txt 


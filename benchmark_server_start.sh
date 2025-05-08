#!/bin/sh
sudo chmod -R 777 .
sudo python3 ./server/frameworks/build_all_images.py

cd ./server/src/

sudo python3 -m venv ./venv
source venv/bin/activate

sudo $(printenv VIRTUAL_ENV)/bin/pip3 install -r requirements.txt
sudo $(printenv VIRTUAL_ENV)/bin/python3 ./main.py
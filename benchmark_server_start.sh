#!/bin/sh
sudo chmod -R 777 .
sudo python3 ./server/frameworks/build_all_images.py

alias spip='sudo $(printenv VIRTUAL_ENV)/bin/pip3'
alias spython='sudo $(printenv VIRTUAL_ENV)/bin/python3'

cd ./server/src/

sudo python3 -m venv ./venv
source venv/bin/activate

sudo spip install -r requirements.txt
sudo spython ./main.py
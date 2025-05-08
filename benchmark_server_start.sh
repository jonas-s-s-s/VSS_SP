#!/bin/sh

echo "Setting chmod -R 777 permissions for current directory..."
sudo chmod -R 777 .

echo "Do you want to run build_all_images? (y/n): "
read run_build

if [ "$run_build" = "y" ] || [ "$run_build" = "Y" ]; then
    echo "Running build_all_images.py..."
    sudo python3 ./server/frameworks/build_all_images.py
else
    echo "Skipped build_all_images.py"
fi

echo "Changing to source directory..."
cd ./server/src/

echo "Creating Python virtual environment..."
sudo python3 -m venv ./venv

echo "Activating virtual environment..."
. ./venv/bin/activate

echo "Installing required Python packages..."
sudo $(printenv VIRTUAL_ENV)/bin/pip3 install -r requirements.txt

echo "Executing python main.py..."
sudo $(printenv VIRTUAL_ENV)/bin/python3 ./main.py

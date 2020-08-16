#! /bin/sh

cd ~ || exit
sudo apt install git
git clone https://github.com/arecarn/dotfiles.git
cd dotfiles || exit
sudo apt install python3
sudo apt install python3-pip
sudo apt-get install python3-venv
pip3 install --user poetry
sudo apt install ansible
poetry install

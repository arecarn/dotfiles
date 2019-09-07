#! /bin/sh

cd ~ || exit
sudo apt install git
git clone git@github.com/arecarn/dotfiles.git
ssh-keygen -t rsa -b 4096
sudo apt install python3
sudo apt install python3-pip
sudo apt install ansible
cd dotfiles || exit
pip3 install -r requirements.txt
python3 -m invoke stow
python3 -m invoke provision

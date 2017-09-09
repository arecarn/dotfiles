#!/bin/sh

path="$(echo /opt/homebrew-cask/Caskroom/spectacle/*/*.app)";
logged_in_user=$(/bin/ls -l /dev/console | /usr/bin/awk '{ print $3 }')
sudo su "${logged_in_user}" -c  'osascript -e '\''tell application "System Events" to make new login item with properties { path: "'"$path"'" } at end'\'

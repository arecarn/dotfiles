#!/bin/sh

path="$(echo /opt/homebrew-cask/Caskroom/spectacle/*/*.app)";
eval 'osascript -e '\''tell application "System Events" to make new login item with properties { path: "'"$path"'" } at end'\'

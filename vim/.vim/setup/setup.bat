REM this is the setup script for vim on windows
@echo OFF

if not exist %HOMEDRIVE%%HOMEPATH%\vimfiles (
mkdir %HOMEDRIVE%%HOMEPATH%\vimfiles ) else (
echo "you allready created vimfiles ;)"   )

if not exist %HOMEDRIVE%%HOMEPATH%\vimfiles\utils  ( 
mklink /d %HOMEDRIVE%%HOMEPATH%\vimfiles\utils  %HOMEDRIVE%%HOMEPATH%\Dropbox\data\vimfiles\utils ) else (
echo "you allready created utils ;)" )

if not exist %HOMEDRIVE%%HOMEPATH%\vimfiles\colors (
 mklink /d %HOMEDRIVE%%HOMEPATH%\vimfiles\colors %HOMEDRIVE%%HOMEPATH%\Dropbox\data\vimfiles\colors ) else (
echo "you allready created colors ;)" )


REM the /d flag isnt used becasue this is a file
if not exist %HOMEDRIVE%%HOMEPATH%\vimfiles\vimrc  (
 mklink %HOMEDRIVE%%HOMEPATH%\vimfiles\vimrc  %HOMEDRIVE%%HOMEPATH%\Dropbox\data\vimfiles\vimrc ) else (
echo "you allready created vimrc ;)" )

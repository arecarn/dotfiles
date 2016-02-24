:: run the following once for this file to be run at cmd.exe startup
:: reg add "HKEY_CURRENT_USER\Software\Microsoft\Command Processor" /v AutoRun /t REG_SZ /d %%HOME%%.cmdrc.bat
@echo off

set PATH=%PATH%;%HOME%dotfiles\bin

:: ALIASES
doskey g=git $*
doskey cd=cd /d $*
doskey searchf=dir /S /P $*
doskey searchd=dir /S /P /A:D $*


:: run this last
"C:\Program Files\clink\0.4.7\clink.bat" inject --autorun --profile ~\clink

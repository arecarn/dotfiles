" open diff in preview window 
pedit GitDiffCached
wincmd w
set filetype=git
read !git diff --cached
wincmd p

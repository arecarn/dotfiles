" open diff in preview window 
new
wincmd J 
setlocal buftype=nofile
setlocal filetype=git
read !git diff --cached
wincmd p

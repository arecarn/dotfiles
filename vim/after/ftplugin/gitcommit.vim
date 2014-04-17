" open diff in preview window when commiting
if expand('%') == ".git/COMMIT_EDITMSG"

    let allready_open = 0
    for buffer_number in  tabpagebuflist(tabpagenr())
        if buffer_name(buffer_number) == "GIT_DIFF_CACHED"
            let allready_open = 1
        endif
    endfor
    if allready_open == 0
        vnew GIT_DIFF_CACHED
        setlocal buftype=nofile
        setlocal filetype=git
        read !git diff --cached
        normal! gg
        wincmd p
    endif
endif

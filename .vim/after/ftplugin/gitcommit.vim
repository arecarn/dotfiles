" Open diff in preview window when committing

if !exists("g:stuff_git_guy")
    function s:stuff()
        let g:stuff_git_guy = 1
        if expand('%') == ".git/COMMIT_EDITMSG"
            let switchbuf_save = &switchbuf
            setlocal switchbuf=usetab


            if bufnr("GIT_DIFF_CACHED") != -1
                bd GIT_DIFF_CACHE
                vnew GIT_DIFF_CACHED
                setlocal buftype=nofile
                setlocal filetype=gitcommit
            else
                vnew GIT_DIFF_CACHED
                setlocal buftype=nofile
                setlocal filetype=gitcommit
            endif

            read !git diff --cached
            normal! gg
            wincmd p

            let &l:switchbuf = switchbuf_save
        endif
    endfunction
endif

call s:stuff()

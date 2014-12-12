augroup GIT
    autocmd!
    autocmd FileType gitcommit call CachedPreview(18)
augroup END

function! CachedPreview(max_height)
    if (!&previewwindow) && (expand('%:t') !~# 'index')
        DiffGitCached

        let lines = line('$')

        "close if empty
        if lines == 0
            pclose
            wincmd p
            finish

            " resize to show maximum or less
        elseif line('$') > a:max_height
            let size = a:max_height
        else
            let size = line('$')
        endif
        execute 'resize '.size

        "go to previous window
        wincmd p
    endif
endfunction

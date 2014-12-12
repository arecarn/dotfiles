function! Spellgewd()
    if &spell
        let colPos = getpos(".")[2]
        let oldLen = len(getline('.'))

        execute "normal! \<ESC>[s"
        sleep 1m
        normal! gs1z=gi


        let newLen = len(getline('.'))


        let lenDifference =  oldLen - newLen
        if oldLen > newLen
            if oldLen != colPos
                execute "normal! ". lenDifference ."h"
            endif
        elseif newLen > oldLen
            let lenDifference = abs(lenDifference)
            execute "normal! ". lenDifference ."l"
        endif

        call feedkeys("a")
    else
        echohl WarningMsg | echo "spelling no enabled" | echohl None
    endif
endfunction

inoremap <C-S> <ESC>:call Spellgewd()<CR>

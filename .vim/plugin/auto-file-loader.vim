"Works when autoread is  set
if has("autocmd")
    augroup AUTOREAD
        autocmd CursorHold * call s:Timer()
    augroup END
endif
function! s:Timer()
    if expand("%") == "[Command Line]"
    else
        call feedkeys("f\e")
        checktime
    endif
endfunction

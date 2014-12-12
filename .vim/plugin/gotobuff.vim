nnoremap gb :<C-U>exec "call Go2Buff('forward',".v:count.")"<CR>
nnoremap gB :<C-U>exec "call Go2Buff('backward',".v:count.")"<CR>
function! Go2Buff(forwardOrBackward, count)
    if a:count == 0
        echom a:count. " using bn"
        if a:forwardOrBackward == "forward"
            execute "normal! :bn\<CR>"
        elseif a:forwardOrBackward == "backward"
            execute "normal! :bp\<CR>"
        endif
    else
        execute "normal! :".a:count."b\<CR>"
    endif
endfunction

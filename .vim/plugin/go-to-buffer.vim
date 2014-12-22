nnoremap <unique> <script> <plug>GoToBuffForward <SID>GoToBuffForward
nnoremap <SID>GoToBuffForward :<C-U>exec "call GoToBuff('forward',".v:count.")"<CR>
if !hasmapto('<Plug>GoToBuffForward')
    nmap <unique> gb <Plug>GoToBuffForward
endif

nnoremap <unique> <script> <plug>GoToBuffBackward <SID>GoToBuffBackward
nnoremap <SID>GoToBuffBackward :<C-U>exec "call GoToBuff('backward',".v:count.")"<CR>
if !hasmapto('<Plug>GoToBuffBackward')
    nmap <unique> gB <Plug>GoToBuffBackward
endif

function! GoToBuff(forwardOrBackward, count)
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

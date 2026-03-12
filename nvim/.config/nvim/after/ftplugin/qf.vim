let b:is_location_list = !empty(getloclist(0))

if b:is_location_list
    nnoremap <buffer> ]] :lnewer<CR>:lhistory<CR>
    nnoremap <buffer> [[ :lolder<CR>:lhistory<CR>
else
    nnoremap <buffer> ]] :cnewer<CR>:chistory<CR>
    nnoremap <buffer> [[ :colder<CR>:chistory<CR>
endif

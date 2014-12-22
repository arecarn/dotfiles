nnoremap <unique> <script> <plug>MixedCaseOperator <SID>MixedCaseOperator
nnoremap <SID>MixedCaseOperator :<C-U>set opfunc=<SID>MixedCase<CR>g@
if !hasmapto('<Plug>MixedCaseOperator')
    nmap <unique> gM <Plug>MixedCaseOperator
endif

nnoremap <unique> <script> <plug>MixedCaseOperatorLine <SID>MixedCaseOperatorLine
nnoremap <SID>MixedCaseOperatorLine :<C-U>set opfunc=<SID>MixedCase<bar>exe 'norm! 'v:count1.'g@_'<CR>
if !hasmapto('<plug>MixedCaseOperatorLine')
    nmap <unique> gMM <plug>MixedCaseOperatorLine
endif

xnoremap <unique> <script> <plug>VisualMixedCaseOperator  <SID>VisualMixedCaseOperator
xnoremap <SID>VisualMixedCaseOperator :<C-U>call <SID>MixedCase(visualmode())<CR>
if !hasmapto('<Plug>VisualMixedCaseOperator')
    xmap <unique> gM <Plug>VisualMixedCaseOperator
endif


function! s:MixedCase(type)
    "Backup Settings That We Will Change
    let sel_save = &selection
    let cb_save = &clipboard
    "make selection and clipboard work the way we need
    set selection=inclusive clipboard-=unnamed clipboard-=unnamedplus
    "Backup The Unnamed Register, Which We Will Be Yanking Into    "Backup The Unnamed Register, Which We Will Be Yanking Into
    let reg_save = @@

    if a:type =~ '^.$'
        "if type is 'v', 'V', or '<C-V>' (i.e. 0x16) then reselect the visual region
        silent exe "normal! `<" . a:type . "`>y"
        let type=a:type
    elseif a:type == 'block'
        silent exe "normal! `[\<C-V>`]y"
        let type=''
    elseif a:type == 'line'
        "line-based text motion
        silent exe "normal! `[V`]y"
        let type='V'
    else
        silent exe "normal! `[v`]y"
        let type='v'
    endif
    let regtype = type

    let repl = substitute(@@, '\w\+', '\u\L&', 'g')
    "don't capitalize the  t in can't or the re in your're
    let repl = substitute(repl, '\w\+', '\u&', 'g')

    call setreg('@', repl, regtype)

    normal! gvp
    set nohlsearch

    "Restore Saved Settings And Register Value
    let @@ = reg_save
    let &selection = sel_save
    let &clipboard = cb_save
endfunction

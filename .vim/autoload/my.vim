
function! my#Rand()
    return str2nr(matchstr(reltimestr(reltime()), '\v\.@<=\d+')[1:])
endfunction 

"CommentLine""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""{{{3
function! my#CommentLine(char, width)
    let b:multiline_str_start = matchstr(&commentstring, '.\+\ze%s.*')
    let b:multiline_str_end = matchstr(&commentstring, '.\+%s\zs.*')
    " echom '[' . b:multiline_str_end . '] = the end'
    " echom '[' . b:multiline_str_start . '] = the start'
    if  b:multiline_str_end == '' || b:multiline_str_end == ' '
        let b:multilinecomment = 0
    else 
        let b:multilinecomment = 1
    endif
    let b:comment_length = strlen(&commentstring)-2
    let b:commentLine = ""

    while strlen(b:commentLine) + b:comment_length + col('.') - 1 <= a:width
        let b:commentLine = b:commentLine.a:char 
    endwhile
    return substitute(&commentstring,'%s', b:commentLine, '')
endfunction
"fun2
function! my#Comment_line()
    let b:comment_length = strlen(&commentstring)-2
    let b:commentLine = ""
    while strlen(b:commentLine) + b:comment_length + col('.') != 80
        let b:commentLine = b:commentLine . '=' 
    endwhile
    let b:line = printf(&commentstring,b:commentLine)
    call setline('.', b:line)
endfunction                                                               
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""}}}3

"CommentStr"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""{{{3
function! my#CommnetStr(str)
    let b:multiline_str = substitute(&commentstring, '%s\ze', '')
    echo b:multiline_str
    let b:comment_length = strlen(&commentstring)-2
    let b:commentLine = ""
    while strlen(b:commentLine) + b:comment_length != a:width
        let b:commentLine = b:commentLine . a:char 
    endwhile
    return substitute(&commentstring,'%s', b:commentLine, '')
endfunction
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""}}}3

"CommentBox()"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""{{{3
function! my#CommentBox(char, width)
    let b:multiline_str_start = matchstr(&commentstring, '.\+\ze%s.*')
    let b:multiline_str_end = matchstr(&commentstring, '.\+%s\zs.*')
    "echom '[' . b:multiline_str_end . '] = the end'
    "echom '[' . b:multiline_str_start . '] = the start'
    if  b:multiline_str_end == '' || b:multiline_str_end == ' '
        let b:multilinecomment = 0
    else 
        let b:multilinecomment = 1
    endif
    if b:multilinecomment == 1
        let b:line1 = b:multiline_str_start . repeat(a:char, a:width-strlen(b:multiline_str_start)) . "\n"
        let b:line2 = '*' . repeat(' ', a:width) . "\n"
        let b:line3 = repeat(a:char, a:width-strlen(b:multiline_str_end)) . b:multiline_str_end
    else
        let b:line1 = b:multiline_str_start . repeat(a:char, a:width-strlen(b:multiline_str_start)) . "\n"
        let b:line2 = b:multiline_str_start . repeat(' ', a:width) . "\n"
        let b:line3 = b:multiline_str_start . repeat(a:char, a:width-strlen(b:multiline_str_start))
    endif 
    return b:line1 . b:line2 . b:line3 
endfunction
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""}}}3

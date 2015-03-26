function! fold#toggle() abort

    let line = getline('.')
    let top_level = foldlevel()

    " find the highest fold
    "find the end of fold
    let done = 0
    let i = 1
    while !done
        let level = foldlevel(line + i)

        if foldlevel(line + i) < top_level
            let done = 1
        endif

        if 

        let i = i + 1
    endwhile
    let last_line = i + line


endfunction


"handle fl = 0 case
function! g:fold#find_end()

    let line = line('.')
    let fold_level = foldlevel('.')

    "skip current level
    let i = 1
    while fold_level == foldlevel(line + i)
        let i = i + 1
    endwhile


    let done = 0
    while !done

        " if line + i > getline('$')
        "     return -1
        " endif

        let level = foldlevel(line + i)

        if level <= fold_level
           return line + i - 1
        endif

        let i = i + 1
    endwhile
endfunction



" when current cursor is at the start of a fold

" on each of the lowest fold levels make sure they are closed


" find the start of each fold

" if all the lowest fold levels are closed consider the next up and close
" those
"
"
" states
"
" 1 all closed
" 2 all 1 level folds open
" 3 all 2 level folds open
" n all n level folds open
"
" if not one of these states return to state 1


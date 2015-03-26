function! fold#find_end()
    " maybe don't always skip current level
    " find end of fold path not last end of of the last fold path

    let line = line('.')
    let fold_level = foldlevel(line)

    if fold_level == 0
        return -1
    endif

    "skip current level
    let i = 1
    while fold_level == foldlevel(line + i)
        let i = i + 1
    endwhile


    let done = 0
    while !done


        let level = foldlevel(line + i)

        if level <= fold_level
            return line + i - 1
        endif

        let i = i + 1
    endwhile

endfunction

function! fold#find_branch_end()
    let current_line = getline('.')
    let current_fold_level = foldlevel('.')

    if current_fold_level == 1
        return fold#find_end()
    endif

    while 1
        let line = fold#find_next()
        if line == -1
            return fold#find_end()
        endif

        if foldlevel(line) <= current_fold_level
            return line - 1
        endif
    endwhile

endfunction

function! fold#find_next() abort
    "handle case fold isn't found

    let view = winsaveview()
    let old_line = line('.')
    normal! zj
    let line = line('.')
    call winrestview(view)
    if old_line == line
        return -1
    else
        return line
    endif
endfunction


function! fold#find_max_level() abort
    max = 
endfunction

function! fold#is_start() abort
    " check to see if this is a start of a fold
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


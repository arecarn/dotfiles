function! s:nr2str(n, base) abort
  let xs = map(range(0x30, 0x39) + range(0x41, 0x5A), 'nr2char(v:val)')
  let rest = a:n
  let str = ''
  while 0 < rest
    let str = xs[rest % a:base] . str
    let rest = rest / a:base
  endwhile
  return str
endfunction

let s:font_size_pat = '\d\+'

function! Gui_adjust_font_size(amount) abort
    let font = s:gui_get_font()
    let font_size = s:gui_get_font_size(font)
    let base = 10
    let new_fontsize = s:nr2str(font_size + a:amount, base)
    call s:gui_set_font_size(font, new_fontsize)
endfunction

function! Gui_set_font_size(new_size) abort
    let font = s:gui_get_font()
    call s:gui_set_font_size(font, a:new_size)
endfunction

function! s:gui_set_font_size(font, new_size) abort
    let new_font = substitute(a:font, s:font_size_pat, a:new_size, '')
    silent execute 'GuiFont! ' . new_font
endfunction

function! s:gui_get_font() abort
    redir => font
    silent GuiFont
    redir END
    let font = trim(font)
    return font
endfunction

function! s:gui_get_font_size(font) abort
    let fontsize_str = matchstr(a:font, s:font_size_pat)
    let font_size = str2nr(fontsize_str)
    return font_size
endfunction

command! -nargs=1 GuiFontSize call Gui_set_font_size(<args>)

noremap <silent> <C-=> :<C-u>call Gui_adjust_font_size(1)<CR>
noremap <silent> <C--> :<C-u>call Gui_adjust_font_size(-1)<CR>
inoremap <silent> <C-=> <Esc>:<C-u>call Gui_adjust_font_size(1)<CR>a
inoremap <silent> <C--> <Esc>:<C-u>call Gui_adjust_font_size(-1)<CR>a

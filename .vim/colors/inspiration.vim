" Generated by Color Theme Generator at Sweyla
" http://themes.sweyla.com/seed/682066/

set background=dark

hi clear

if exists("syntax_on")
  syntax reset
endif

" Set environment to 256 colours
set t_Co=256

let colors_name = "sweyla682066"

if version >= 700
  hi CursorLine     guibg=#000E02 ctermbg=16
  hi CursorColumn   guibg=#000E02 ctermbg=16
  hi MatchParen     guifg=#D4FFFF guibg=#000E02 gui=bold ctermfg=195 ctermbg=16 cterm=bold
  hi Pmenu          guifg=#FFFFFF guibg=#323232 ctermfg=255 ctermbg=236
  hi PmenuSel       guifg=#FFFFFF guibg=#67B053 ctermfg=255 ctermbg=71
endif

" Background and menu colors
hi Cursor           guifg=NONE guibg=#FFFFFF ctermbg=255 gui=none
hi Normal           guifg=#FFFFFF guibg=#000E02 gui=none ctermfg=255 ctermbg=16 cterm=none
hi NonText          guifg=#FFFFFF guibg=#0F1D11 gui=none ctermfg=255 ctermbg=233 cterm=none
hi LineNr           guifg=#FFFFFF guibg=#19271B gui=none ctermfg=255 ctermbg=234 cterm=none
hi StatusLine       guifg=#FFFFFF guibg=#142E12 gui=italic ctermfg=255 ctermbg=233 cterm=italic
hi StatusLineNC     guifg=#FFFFFF guibg=#28362A gui=none ctermfg=255 ctermbg=236 cterm=none
hi VertSplit        guifg=#FFFFFF guibg=#19271B gui=none ctermfg=255 ctermbg=234 cterm=none
hi Folded           guifg=#FFFFFF guibg=#000E02 gui=none ctermfg=255 ctermbg=16 cterm=none
hi Title            guifg=#67B053 guibg=NONE	gui=bold ctermfg=71 ctermbg=NONE cterm=bold
hi Visual           guifg=#E0FF69 guibg=#323232 gui=none ctermfg=191 ctermbg=236 cterm=none
hi SpecialKey       guifg=#D8D7FB guibg=#0F1D11 gui=none ctermfg=189 ctermbg=233 cterm=none
"hi DiffChange       guibg=#4C5601 gui=none ctermbg=58 cterm=none
"hi DiffAdd          guibg=#252F4D gui=none ctermbg=236 cterm=none
"hi DiffText         guibg=#663A67 gui=none ctermbg=241 cterm=none
"hi DiffDelete       guibg=#3F0A01 gui=none ctermbg=52 cterm=none
 
hi DiffChange       guibg=#4C4C09 gui=none ctermbg=234 cterm=none
hi DiffAdd          guibg=#252556 gui=none ctermbg=17 cterm=none
hi DiffText         guibg=#66326E gui=none ctermbg=22 cterm=none
hi DiffDelete       guibg=#3F000A gui=none ctermbg=0 ctermfg=196 cterm=none
hi TabLineFill      guibg=#5E5E5E gui=none ctermbg=235 ctermfg=228 cterm=none
hi TabLineSel       guifg=#FFFFD7 gui=bold ctermfg=230 cterm=bold


" Syntax highlighting
hi Comment guifg=#67B053 gui=none ctermfg=71 cterm=none
hi Constant guifg=#D8D7FB gui=none ctermfg=189 cterm=none
hi Number guifg=#D8D7FB gui=none ctermfg=189 cterm=none
hi Identifier guifg=#B176FF gui=none ctermfg=141 cterm=none
hi Statement guifg=#D4FFFF gui=none ctermfg=195 cterm=none
hi Function guifg=#EFE0FF gui=none ctermfg=225 cterm=none
hi Special guifg=#2DFFE1 gui=none ctermfg=50 cterm=none
hi PreProc guifg=#2DFFE1 gui=none ctermfg=50 cterm=none
hi Keyword guifg=#D4FFFF gui=none ctermfg=195 cterm=none
hi String guifg=#E0FF69 gui=none ctermfg=191 cterm=none
hi Type guifg=#ECFFEE gui=none ctermfg=255 cterm=none
hi pythonBuiltin guifg=#B176FF gui=none ctermfg=141 cterm=none
hi TabLineFill guifg=#596E2B gui=none ctermfg=58 cterm=none

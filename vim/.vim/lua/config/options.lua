-------------------------------------------------------------------------------}}}
-- OPTIONS                                                                    {{{
--------------------------------------------------------------------------------
-- Neovim options migrated from vimrc
-- These are loaded before vimrc to ensure they're set early

local opt = vim.opt
local g = vim.g

-------------------------------------------------------------------------------}}}
-- ENCODING                                                                   {{{
--------------------------------------------------------------------------------
opt.encoding = 'utf-8'
vim.scriptencoding = 'utf-8'
opt.fileformats = { 'unix', 'dos' }

-------------------------------------------------------------------------------}}}
-- COMMAND LINE                                                               {{{
--------------------------------------------------------------------------------
opt.history = 10000
opt.wildmode = 'full'
opt.wildcharm = ('\t'):byte()  -- <Tab>
opt.wildignore = { '*.o', '*.obj', '*.pyc', '*.DS_Store', '*.out', '*.i', 'tags*', '*.elf' }
opt.suffixes = { '.bak', '~', '.o', '.info', '.swp', '.obj', '.git', '.hg', '.svn' }
opt.path = { '.', '', '**' }

-------------------------------------------------------------------------------}}}
-- CURSOR SETTINGS                                                            {{{
--------------------------------------------------------------------------------
opt.scrolloff = 5
opt.sidescrolloff = 5
opt.mouse = 'a'

-------------------------------------------------------------------------------}}}
-- UNDO & SWAP                                                                {{{
--------------------------------------------------------------------------------
opt.undofile = true
opt.undolevels = 20000
opt.swapfile = false

-- undodir is set in vimrc due to path complexity

-------------------------------------------------------------------------------}}}
-- BACKUP                                                                     {{{
--------------------------------------------------------------------------------
opt.backup = true

-- backupdir handled by vim-backup-tree plugin

-------------------------------------------------------------------------------}}}
-- LINE WRAPPING                                                              {{{
--------------------------------------------------------------------------------
opt.textwidth = 80
opt.linebreak = true
opt.breakindent = true
opt.wrap = false

g.man_hardwrap = 1

-------------------------------------------------------------------------------}}}
-- SPELLING                                                                   {{{
--------------------------------------------------------------------------------
opt.spell = true
opt.spelllang = 'en_us'

-- spellfile and thesaurus set in vimrc due to path complexity

-------------------------------------------------------------------------------}}}
-- TABS & INDENTING                                                           {{{
--------------------------------------------------------------------------------
opt.expandtab = true
opt.tabstop = 4
opt.shiftwidth = 4
opt.softtabstop = 4
opt.smarttab = true
opt.autoindent = true

opt.formatoptions:append('n')  -- recognize lists
opt.formatoptions:append('j')  -- delete comment character when joining
opt.formatoptions:remove('t') -- don't auto wrap based on textwidth

-------------------------------------------------------------------------------}}}
-- FOLDING                                                                    {{{
--------------------------------------------------------------------------------
opt.foldcolumn = '2'
opt.foldnestmax = 3
opt.foldlevelstart = 99

-------------------------------------------------------------------------------}}}
-- SEARCHING                                                                  {{{
--------------------------------------------------------------------------------
opt.wrapscan = true
opt.ignorecase = true
opt.smartcase = true
opt.maxmempattern = 2000000

-------------------------------------------------------------------------------}}}
-- TAGS                                                                       {{{
--------------------------------------------------------------------------------
opt.tags = 'tags;/'

-------------------------------------------------------------------------------}}}
-- GENERAL BEHAVIOR                                                           {{{
--------------------------------------------------------------------------------
opt.clipboard = 'unnamedplus'
opt.splitright = true
opt.nrformats:remove('octal')
opt.belloff = 'all'
opt.startofline = false
opt.autowriteall = true
opt.autoread = true
opt.virtualedit = 'all'
opt.modeline = true
opt.inccommand = 'nosplit'

opt.diffopt:append('vertical')
opt.diffopt:append('linematch:60')
opt.diffopt:append('indent-heuristic')
opt.diffopt:append('algorithm:histogram')

-------------------------------------------------------------------------------}}}
-- UI OPTIONS                                                                 {{{
--------------------------------------------------------------------------------
opt.confirm = true
opt.shortmess:append('a')
opt.shortmess:remove('S')

opt.number = true
opt.relativenumber = true

opt.showcmd = true
opt.laststatus = 2
opt.showtabline = 2

opt.list = true
opt.listchars = {
    trail = '·',
    tab = '→‸',
    extends = '▶',
    precedes = '◀',
    nbsp = '‾',
}

opt.signcolumn = 'yes'
opt.termguicolors = true
opt.background = 'dark'

-------------------------------------------------------------------------------}}}
-- TIMING                                                                     {{{
--------------------------------------------------------------------------------
opt.updatetime = 1000

-------------------------------------------------------------------------------}}}
-- LEADER                                                                     {{{
--------------------------------------------------------------------------------
g.mapleader = ' '

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

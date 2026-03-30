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
opt.encoding = "utf-8"
vim.scriptencoding = "utf-8"
opt.fileformats = { "unix", "dos" }

-------------------------------------------------------------------------------}}}
-- COMMAND LINE                                                               {{{
--------------------------------------------------------------------------------
opt.history = 10000
opt.wildmode = "full"
opt.wildcharm = ("\t"):byte() -- <Tab>
opt.wildignore = { "*.o", "*.obj", "*.pyc", "*.DS_Store", "*.out", "*.i", "tags*", "*.elf" }
opt.suffixes = { ".bak", "~", ".o", ".info", ".swp", ".obj", ".git", ".hg", ".svn" }
opt.path = { ".", "", "**" }

-------------------------------------------------------------------------------}}}
-- CURSOR SETTINGS                                                            {{{
--------------------------------------------------------------------------------
opt.scrolloff = 5
opt.sidescrolloff = 5
opt.mouse = "a"

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
opt.spelllang = "en_us"

local config_path = vim.fn.stdpath("config") .. "/"
opt.spellfile = config_path .. "utils/spell/spellfile.add"
opt.thesaurus = config_path .. "utils/thesaurus/thesaurus.txt"

-- Generate help tags for custom help files
vim.cmd("silent! helptags " .. config_path .. "doc")

-------------------------------------------------------------------------------}}}
-- TABS & INDENTING                                                           {{{
--------------------------------------------------------------------------------
opt.expandtab = true
opt.tabstop = 4
opt.shiftwidth = 4
opt.softtabstop = 4
opt.smarttab = true
opt.autoindent = true

opt.formatoptions:append("n") -- recognize lists
opt.formatoptions:append("j") -- delete comment character when joining
opt.formatoptions:remove("t") -- don't auto wrap based on textwidth

-- Extend formatlistpat to recognize markdown lists
opt.formatlistpat:append([[\|^\s*[-*]\s*]])

-------------------------------------------------------------------------------}}}
-- FOLDING                                                                    {{{
--------------------------------------------------------------------------------
opt.foldcolumn = "2"
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
-- GREP                                                                       {{{
--------------------------------------------------------------------------------
opt.grepformat = "%f:%l:%c:%m"

if vim.fn.executable("rg") == 1 then
    opt.grepprg = "rg --vimgrep $*"
elseif vim.fn.executable("ag") == 1 then
    opt.grepprg = "ag --vimgrep $*"
end

-------------------------------------------------------------------------------}}}
-- TAGS                                                                       {{{
--------------------------------------------------------------------------------
opt.tags = "tags;/"

-------------------------------------------------------------------------------}}}
-- GENERAL BEHAVIOR                                                           {{{
--------------------------------------------------------------------------------
-- Use OSC 52 for clipboard over SSH (works with WezTerm).
-- Paste falls back to unnamed register since WezTerm doesn't support OSC 52
-- clipboard queries. Use Ctrl+Shift+V to paste from host clipboard.
vim.schedule(function()
    opt.clipboard:append("unnamedplus")

    if vim.env.SSH_CLIENT or vim.env.SSH_TTY then
        local function paste()
            return vim.split(vim.fn.getreg('"'), "\n")
        end
        vim.g.clipboard = {
            name = "OSC 52",
            copy = {
                ["+"] = require("vim.ui.clipboard.osc52").copy("+"),
                ["*"] = require("vim.ui.clipboard.osc52").copy("*"),
            },
            paste = {
                ["+"] = paste,
                ["*"] = paste,
            },
        }
    end
end)
opt.splitright = true
opt.nrformats:remove("octal")
opt.belloff = "all"
opt.startofline = false
opt.autowriteall = true
opt.autoread = true
opt.virtualedit = "all"
opt.modeline = true
opt.inccommand = "nosplit"

opt.diffopt:append("vertical")
opt.diffopt:append("linematch:60")
opt.diffopt:append("indent-heuristic")
opt.diffopt:append("algorithm:histogram")

-------------------------------------------------------------------------------}}}
-- UI OPTIONS                                                                 {{{
--------------------------------------------------------------------------------
opt.confirm = true
opt.shortmess:append("a")
opt.shortmess:remove("S")

opt.number = true
opt.relativenumber = true
opt.conceallevel = 2

opt.showcmd = true
opt.laststatus = 2
opt.showtabline = 2

opt.list = true
opt.listchars = {
    trail = "·",
    tab = "→→",
    extends = "▶",
    precedes = "◀",
    nbsp = "‾",
}

opt.signcolumn = "yes"
opt.termguicolors = true
opt.background = "dark"
opt.winborder = "rounded"

-------------------------------------------------------------------------------}}}
-- TIMING                                                                     {{{
--------------------------------------------------------------------------------
opt.updatetime = 1000

-------------------------------------------------------------------------------}}}
-- LEADER                                                                     {{{
--------------------------------------------------------------------------------
g.mapleader = " "
g.maplocalleader = "\\"

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

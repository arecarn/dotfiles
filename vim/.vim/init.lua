-------------------------------------------------------------------------------}}}
-- INIT.LUA                                                                   {{{
--------------------------------------------------------------------------------
-- Neovim configuration entry point
-- Uses lazy.nvim for plugin management

-- Load options first (includes mapleader)
require('config.options')

-- Load plugins via lazy.nvim
require('plugins')

-- Load keymaps after plugins
require('config.keymaps')

-- Load autocmds
require('config.autocmds')

-- Source vimrc for remaining vimscript (utility functions, etc.)
vim.cmd('source ~/.config/nvim/vimrc')

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

-------------------------------------------------------------------------------}}}
-- INIT.LUA                                                                   {{{
--------------------------------------------------------------------------------
-- Phase 1: Source existing vimrc for gradual migration
-- As we migrate sections to Lua, we can remove them from vimrc

-- Load Lua config modules
require('config.options')
require('config.keymaps')

-- Source the existing vimrc for everything else
vim.cmd('source ~/.config/nvim/vimrc')

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

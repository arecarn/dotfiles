-------------------------------------------------------------------------------}}}
-- INIT.LUA                                                                   {{{
--------------------------------------------------------------------------------
-- Neovim configuration entry point
-- Uses lazy.nvim for plugin management

-- Load paths first (sets up directories, undodir)
require('config.paths')

-- Load options (includes mapleader)
require('config.options')

-- Load statusline functions (must be before plugins for lightline)
require('config.statusline')

-- Load plugins via lazy.nvim
require('plugins')

-- Load keymaps after plugins
require('config.keymaps')

-- Load autocmds
require('config.autocmds')

-- Source vimrc for remaining vimscript (utility functions, etc.)
vim.cmd('source ~/.config/nvim/vimrc')

-------------------------------------------------------------------------------}}}
-- LOCAL CONFIG                                                               {{{
--------------------------------------------------------------------------------
-- Source project-local vimrc if it exists
if vim.fn.filereadable('.vimrc_project') == 1 then
    vim.cmd('source .vimrc_project')
end

-- Source user-local vimrc if it exists
local local_vimrc = vim.fn.expand('~/.vimrc_local')
if vim.fn.filereadable(local_vimrc) == 1 then
    vim.cmd('source ' .. local_vimrc)
end

-------------------------------------------------------------------------------}}}
-- PLUGIN UTILITIES                                                           {{{
--------------------------------------------------------------------------------
-- Check if a plugin is installed via lazy.nvim
---@param plugin_name string
---@return boolean
function _G.Is_plugin_installed(plugin_name)
    local ok, lazy_config = pcall(require, 'lazy.core.config')
    return ok and lazy_config.plugins[plugin_name] ~= nil
end

-- Load cfilter if not already loaded
if not vim.fn.exists(':CFilter') then
    vim.cmd('packadd cfilter')
end

-- Call local plugin config function if it exists
if vim.fn.exists('*Vimrc_local_plugin_config') == 1 then
    vim.cmd('call Vimrc_local_plugin_config()')
end

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

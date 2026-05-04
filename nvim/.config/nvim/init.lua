------------------------------------------------------------------------------}}}
-- INIT.LUA                                                                   {{{
--------------------------------------------------------------------------------
-- Neovim configuration entry point
-- Uses lazy.nvim for plugin management

-- Load paths first (sets up directories, undodir)
require("config.paths")

-- Load options (includes mapleader)
require("config.options")

-- Load statusline functions (must be before plugins for lightline)
require("config.statusline")

-- Load plugins via lazy.nvim
require("plugins")

-- Load keymaps after plugins
require("config.keymaps")

-- Load autocmds
require("config.autocmds")

-------------------------------------------------------------------------------}}}
-- PLUGIN UTILITIES                                                           {{{
--------------------------------------------------------------------------------
-- Check if a plugin is installed via lazy.nvim
---@param plugin_name string
---@return boolean
function _G.Is_plugin_installed(plugin_name)
    local ok, lazy_config = pcall(require, "lazy.core.config")
    return ok and lazy_config.plugins[plugin_name] ~= nil
end

-------------------------------------------------------------------------------}}}
-- LOCAL CONFIG                                                               {{{
--------------------------------------------------------------------------------
-- Source project-local vimrc if it exists
if vim.fn.filereadable(".vimrc_project") == 1 then
    vim.cmd("source .vimrc_project")
end

-- Load user-local Lua config if it exists
local local_lua = vim.fn.expand("~/.config/nvim/init_local.lua")
if vim.fn.filereadable(local_lua) == 1 then
    dofile(local_lua)
end

-- Load cfilter if not already loaded
if vim.fn.exists(":CFilter") == 0 then
    vim.cmd("packadd cfilter")
end

-- GUI font (Neovide)
if vim.g.neovide then
	vim.o.guifont = "DejaVuSansM Nerd Font Mono:h14"
	vim.g.neovide_cursor_trail_size = 0
	vim.g.neovide_cursor_animation_length = 0
	vim.g.neovide_scroll_animation_length = 0
end

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

-------------------------------------------------------------------------------}}}
-- PATHS                                                                      {{{
--------------------------------------------------------------------------------
-- Path utilities and directory setup migrated from vimrc
-- Uses Neovim's stdpath() which handles XDG paths automatically

local M = {}

-------------------------------------------------------------------------------}}}
-- PLATFORM DETECTION                                                         {{{
--------------------------------------------------------------------------------
M.is_windows = vim.fn.has('win32') == 1 or vim.fn.has('win64') == 1
M.path_sep = M.is_windows and '\\' or '/'

-- Expose to vimscript for compatibility
vim.g.os_path_sep = M.path_sep

-------------------------------------------------------------------------------}}}
-- STANDARD PATHS                                                             {{{
--------------------------------------------------------------------------------
-- Use Neovim's stdpath for XDG-compliant paths
M.config_path = vim.fn.stdpath('config') .. M.path_sep
M.data_path = vim.fn.stdpath('data') .. M.path_sep
M.cache_path = vim.fn.stdpath('cache') .. M.path_sep
M.app_path = vim.fn.stdpath('config') .. M.path_sep

-- Expose to vimscript for compatibility
vim.g.app = 'nvim'
vim.g.config_path = M.config_path
vim.g.data_path = M.data_path
vim.g.cache_path = M.cache_path

-------------------------------------------------------------------------------}}}
-- DIRECTORY UTILITIES                                                        {{{
--------------------------------------------------------------------------------
--- Create a directory with private permissions (0700)
---@param path string
function M.make_private_directory(path)
    if vim.fn.isdirectory(path) == 0 then
        vim.fn.mkdir(path, 'p', tonumber('700', 8))
    end
end

--- Get path string in cache directory
---@param name string
---@return string
function M.cache_path_str(name)
    return M.cache_path .. name
end

--- Get path string in data directory
---@param name string
---@return string
function M.data_path_str(name)
    return M.data_path .. name
end

--- Create and return a directory in cache path
---@param dir_name string
---@return string
function M.make_cache_directory(dir_name)
    local path = M.cache_path_str(dir_name)
    M.make_private_directory(path)
    return path
end

--- Create and return a directory in data path
---@param dir_name string
---@return string
function M.make_data_directory(dir_name)
    local path = M.data_path_str(dir_name)
    M.make_private_directory(path)
    return path
end

-------------------------------------------------------------------------------}}}
-- UNDO DIRECTORY                                                             {{{
--------------------------------------------------------------------------------
local undo_path = M.make_data_directory('undo')
-- Double slash means full path encoded in filename
vim.opt.undodir = undo_path .. (M.is_windows and '\\\\' or '//')

-------------------------------------------------------------------------------}}}
-- UNDO CLEAN COMMAND                                                         {{{
--------------------------------------------------------------------------------
--- Remove undo files for files that no longer exist
local function undo_clean()
    local undodir = vim.fn.expand(vim.o.undodir:gsub('//+$', ''))
    local undo_files = vim.fn.glob(undodir .. '/*', false, true)

    for _, undo_file in ipairs(undo_files) do
        -- Extract the real file path from the undo filename
        local real_file = undo_file:gsub(vim.pesc(undodir) .. M.path_sep, '')

        if M.is_windows then
            real_file = real_file:gsub('%%%%', ':\\')
            real_file = real_file:gsub('%%', '\\')
        else
            real_file = real_file:gsub('%%', '/')
        end

        if vim.fn.filereadable(real_file) == 0 then
            print(undo_file)
            vim.fn.delete(undo_file)
        end
    end
end

vim.api.nvim_create_user_command('UndoClean', undo_clean, {
    desc = 'Remove undo files for files that no longer exist',
})

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

return M

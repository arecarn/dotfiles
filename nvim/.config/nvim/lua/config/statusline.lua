-------------------------------------------------------------------------------}}}
-- STATUSLINE                                                                 {{{
--------------------------------------------------------------------------------
-- Lightline component functions migrated from vimrc
-- These are exposed globally for lightline's component_function

local M = {}

-------------------------------------------------------------------------------}}}
-- HELPER PATTERNS                                                            {{{
--------------------------------------------------------------------------------
local special_ft_pattern = 'help|dirvish|fern|qf'

-------------------------------------------------------------------------------}}}
-- COMPONENT FUNCTIONS                                                        {{{
--------------------------------------------------------------------------------

--- Modified indicator
---@return string
function M.modified()
    local ft = vim.bo.filetype
    if ft:match(special_ft_pattern) then
        return ''
    end
    if vim.bo.modified then
        return '+'
    end
    if not vim.bo.modifiable then
        return '-'
    end
    return ''
end

--- Readonly indicator
---@return string
function M.readonly()
    local ft = vim.bo.filetype
    if ft:match('help|dirvish') then
        return ''
    end
    return vim.bo.readonly and 'RO' or ''
end

--- Filename with path compression for narrow windows
---@return string
function M.filename()
    local name = vim.fn.bufname('%')
    if name == '' then
        name = '[No Name]'
    else
        -- Compress path if window is narrow
        if vim.fn.winwidth(0) - #name < 40 then
            -- Replace directory names with first character
            name = name:gsub('([^/\\:])([^/\\:]*[/\\])', '%1/')
        end
    end

    -- Build full display: [RO] filename [+/-]
    local ro = M.readonly()
    local mod = M.modified()
    local result = ''
    if ro ~= '' then
        result = ro .. ' '
    end
    result = result .. name
    if mod ~= '' then
        result = result .. ' ' .. mod
    end
    return result
end

--- Git branch from fugitive
---@return string
function M.fugitive()
    local ft = vim.bo.filetype
    if ft:match('dirvish') then
        return ''
    end
    if vim.fn.winwidth(0) <= 80 then
        return ''
    end
    if vim.fn.exists('*FugitiveHead') == 1 then
        local branch = vim.fn.FugitiveHead()
        if branch ~= '' then
            return '±' .. branch
        end
    end
    return ''
end

--- File format (hidden in narrow windows)
---@return string
function M.fileformat()
    return vim.fn.winwidth(0) > 80 and vim.bo.fileformat or ''
end

--- File type (hidden in narrow windows)
---@return string
function M.filetype()
    if vim.fn.winwidth(0) <= 80 then
        return ''
    end
    local ft = vim.bo.filetype
    return ft ~= '' and ft or 'no ft'
end

--- File encoding (hidden in narrow windows)
---@return string
function M.fileencoding()
    if vim.fn.winwidth(0) <= 80 then
        return ''
    end
    local enc = vim.bo.fileencoding
    return enc ~= '' and enc or vim.o.encoding
end

--- Window number
---@return integer
function M.winnr()
    return vim.fn.winnr()
end

--- Buffer number with prefix
---@return string
function M.bufnr()
    return 'b:' .. vim.fn.bufnr('%')
end

-------------------------------------------------------------------------------}}}
-- EXPOSE GLOBALLY FOR LIGHTLINE                                              {{{
--------------------------------------------------------------------------------
-- Lightline calls functions by name, so we expose them globally
_G.Lightline_modified = M.modified
_G.Lightline_readonly = M.readonly
_G.Lightline_filename = M.filename
_G.Lightline_fugitive = M.fugitive
_G.Lightline_fileformat = M.fileformat
_G.Lightline_filetype = M.filetype
_G.Lightline_fileencoding = M.fileencoding
_G.Lightline_winnr = M.winnr
_G.Lightline_bufnr = M.bufnr

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

return M

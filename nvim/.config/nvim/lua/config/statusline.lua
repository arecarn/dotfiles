-------------------------------------------------------------------------------}}}
-- STATUSLINE                                                                 {{{
--------------------------------------------------------------------------------
-- Component functions consumed by lualine (see config/plugins.lua)

local M = {}

-------------------------------------------------------------------------------}}}
-- HELPER PATTERNS                                                            {{{
--------------------------------------------------------------------------------
-- Filetypes where modified/readonly/git indicators are hidden
local special_ft = { help = true, fern = true, qf = true }

-------------------------------------------------------------------------------}}}
-- COMPONENT FUNCTIONS                                                        {{{
--------------------------------------------------------------------------------

--- Modified indicator
---@return string
function M.modified()
    local ft = vim.bo.filetype
    if special_ft[ft] then
        return ""
    end
    if vim.bo.modified then
        return "+"
    end
    if not vim.bo.modifiable then
        return "-"
    end
    return ""
end

--- Readonly indicator
---@return string
function M.readonly()
    local ft = vim.bo.filetype
    if special_ft[ft] then
        return ""
    end
    return vim.bo.readonly and "RO" or ""
end

--- Filename with path compression for narrow windows
---@return string
function M.filename()
    local name = vim.fn.bufname("%")
    if name == "" then
        name = "[No Name]"
    else
        -- Compress path if window is narrow
        if vim.fn.winwidth(0) - #name < 40 then
            -- Replace directory names with first character
            name = name:gsub("([^/\\:])([^/\\:]*[/\\])", "%1/")
        end
    end

    -- Build full display: [RO] filename [+/-]
    local ro = M.readonly()
    local mod = M.modified()
    local result = ""
    if ro ~= "" then
        result = ro .. " "
    end
    result = result .. name
    if mod ~= "" then
        result = result .. " " .. mod
    end
    return result
end

--- Git branch from fugitive
---@return string
function M.fugitive()
    local ft = vim.bo.filetype
    if special_ft[ft] then
        return ""
    end
    if vim.fn.winwidth(0) <= 80 then
        return ""
    end
    if vim.fn.exists("*FugitiveHead") == 1 then
        local branch = vim.fn.FugitiveHead()
        if branch ~= "" then
            return "±" .. branch
        end
    end
    return ""
end

--- File format (hidden in narrow windows)
---@return string
function M.fileformat()
    return vim.fn.winwidth(0) > 80 and vim.bo.fileformat or ""
end

--- File type (hidden in narrow windows)
---@return string
function M.filetype()
    if vim.fn.winwidth(0) <= 80 then
        return ""
    end
    local ft = vim.bo.filetype
    return ft ~= "" and ft or "no ft"
end

--- File encoding (hidden in narrow windows)
---@return string
function M.fileencoding()
    if vim.fn.winwidth(0) <= 80 then
        return ""
    end
    local enc = vim.bo.fileencoding
    return enc ~= "" and enc or vim.o.encoding
end

--- Window number
---@return integer
function M.winnr()
    return vim.fn.winnr()
end

--- Buffer number with prefix
---@return string
function M.bufnr()
    return "b:" .. vim.fn.bufnr("%")
end

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

return M

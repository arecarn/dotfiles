-------------------------------------------------------------------------------}}}
-- KEYMAPS                                                                    {{{
--------------------------------------------------------------------------------
-- Core keymaps migrated from vimrc
-- Plugin-specific keymaps remain in vimrc until lazy.nvim migration

local map = vim.keymap.set

-------------------------------------------------------------------------------}}}
-- LEADER SETUP                                                               {{{
--------------------------------------------------------------------------------

-- [myleader] is a secondary leader mapped to 'go'
map('n', '[myleader]', '<Nop>')
map('x', '[myleader]', '<Nop>')
map('n', 'go', '[myleader]', { remap = true })
map('x', 'go', '[myleader]', { remap = true })

-- [cmdleader] for command mode
map('c', '[cmdleader]', '<Nop>')
map('c', '<C-j>', '[cmdleader]', { remap = true })

-------------------------------------------------------------------------------}}}
-- NAVIGATION                                                                 {{{
--------------------------------------------------------------------------------
-- When 'wrap' is enabled, navigate visual lines instead of actual lines
map('n', 'k', function() return vim.v.count == 0 and 'gk' or 'k' end, { expr = true })
map('n', 'j', function() return vim.v.count == 0 and 'gj' or 'j' end, { expr = true })
map('n', 'gk', 'k')
map('n', 'gj', 'j')
map('x', 'k', function() return vim.v.count == 0 and 'gk' or 'k' end, { expr = true })
map('x', 'j', function() return vim.v.count == 0 and 'gj' or 'j' end, { expr = true })
map('x', 'gk', 'k')
map('x', 'gj', 'j')

-------------------------------------------------------------------------------}}}
-- WINDOW & TAB MANAGEMENT                                                    {{{
--------------------------------------------------------------------------------
-- CTRL-6 alternate buffer (nvim-qt compatibility)
map('n', '<C-6>', '<C-^>')

-- Break out tab into new window without leaving current tab
map('n', '<C-w><C-t>', function()
    return vim.fn.winnr('$') ~= 1 and '<C-w>TgT' or ''
end, { expr = true })

-- Open current buffer in new tab without breaking it out
map('n', 'g<C-w>t', ':tabedit %<CR>')

-- Close tab
map('n', '<C-w>Q', ':tabclose<CR>')

-- Delete buffer
map('n', '<C-W>d', ':bd<CR>')

-------------------------------------------------------------------------------}}}
-- EDITING                                                                    {{{
--------------------------------------------------------------------------------
-- Replace selection with spaces and enter replace mode
map('x', 'gr', 'r<Space>gvo<Esc>R')

-- Retab
map({ 'n', 'v' }, '<leader>rt', ':retab<CR>', { silent = true })

-- Format current paragraph in insert mode
map('i', '<C-f>', '<Esc>gw{zea')

-- Yank to end of line (like D or C)
map('n', 'Y', 'y$')

-- Reselect pasted or last changed text
map('n', 'gpv', function()
    return '`[' .. vim.fn.getregtype():sub(1, 1) .. '`]'
end, { expr = true })

-------------------------------------------------------------------------------}}}
-- UNDO BREAK POINTS                                                          {{{
--------------------------------------------------------------------------------
-- Create undo points in insert mode for better undo granularity
map('i', '<C-u>', '<C-g>u<C-u>')
map('i', '<C-w>', '<C-g>u<C-w>')
map('i', '<BS>', '<C-g>u<BS>')
map('i', '<Del>', '<C-g>u<Del>')
map('i', '<End>', '<C-g>u<End>')
map('i', '<Space>', '<C-g>u<Space>')

-------------------------------------------------------------------------------}}}
-- SEARCH TEXT OBJECTS                                                        {{{
--------------------------------------------------------------------------------
-- Visual selection text objects for search matches
map('x', 'a/', 'gn')
map('o', 'a/', 'gn')
map('x', 'i/', 'gn')
map('o', 'i/', 'gn')
map('x', 'i?', 'gN')
map('o', 'i?', 'gN')
map('x', 'a?', 'gN')
map('o', 'a?', 'gN')

-------------------------------------------------------------------------------}}}
-- MACROS & REPEAT                                                            {{{
--------------------------------------------------------------------------------
-- Disable Ex mode, use Q to repeat last macro
map('n', 'Q', '@q')
-- Replay q macro for each line of visual selection
map('x', 'Q', ':normal! @q<CR>')
-- Repeat last command for each line of visual selection
map('x', '.', ':normal! .<CR>')

-------------------------------------------------------------------------------}}}
-- DIRECTORY NAVIGATION                                                       {{{
--------------------------------------------------------------------------------
-- Set path to current file's directory
map('n', 'cdl', ':lcd! %:h<CR>:pwd<CR>')
map('n', 'cd', ':cd! %:h<CR>:pwd<CR>')

-------------------------------------------------------------------------------}}}
-- VISUAL PASTE                                                               {{{
--------------------------------------------------------------------------------
-- Paste after visual block/line selection
map('v', 'gp', function()
    return '<C-v>A<C-r>' .. vim.v.register .. '<Esc>'
end, { expr = true })
-- Paste before visual block/line selection
map('v', 'gP', function()
    return '<C-v>I<C-r>' .. vim.v.register .. '<Esc>'
end, { expr = true })

-------------------------------------------------------------------------------}}}
-- COMMAND LINE                                                               {{{
--------------------------------------------------------------------------------
-- Emacs-style navigation in command line
map('c', '<C-p>', '<UP>')
map('c', '<C-n>', '<DOWN>')
map('c', '<C-b>', '<LEFT>')
map('c', '<C-f>', '<RIGHT>')
map('c', '<C-a>', '<HOME>')
map('c', '<C-e>', '<END>')
-- Expand abbreviations
map('c', '<C-x>', '<C-]>')
-- Open command-line window
map('c', '<C-v>', '<C-f>')

-- Accept completion (requires wildcharm = <Tab>)
map('c', '<C-Y>', '<Space><bs><Tab>')
map('c', '<C-y>', '<Space><BS><Tab>')

-- Date insertion
map('c', '%%date', function() return os.date('%Y-%m-%d') end, { expr = true })
map('i', '%%date', function() return os.date('%Y-%m-%d') end, { expr = true })

-- Directory shortcuts
map('c', '~f', '~/files')
map('c', '~p', '~/files/projects')
map('c', '~df', '~/dotfiles')
map('c', '~dfl', '~/dotfiles_local')

-------------------------------------------------------------------------------}}}
-- FILE PATH YANK                                                             {{{
--------------------------------------------------------------------------------
-- Yank various file path components to clipboard
-- <leader>y<suffix> yanks to all registers (*, +, ")
-- %<suffix> in command mode inserts the value

local path_sep = vim.g.os_path_sep or '/'

--- Get file path component
---@param kind string The type of path to get
---@return string
local function get_path(kind)
    local handlers = {
        -- fn: file name (foo.txt)
        fn = function() return vim.fn.expand('%:t') end,
        -- afp: absolute file path (/something/src/foo.txt)
        afp = function() return vim.fn.expand('%:p') end,
        -- fp: file path relative (src/foo.txt)
        fp = function() return vim.fn.expand('%') end,
        -- ofn: other file name - filename stem with trailing dot (foo.)
        ofn = function()
            local name = vim.fn.expand('%:t:r')
            return name ~= '' and name .. '.' or ''
        end,
        -- aofp: absolute other file path - full path stem with trailing dot
        aofp = function()
            local stem = vim.fn.expand('%:p:r')
            return stem ~= '' and stem .. '.' or ''
        end,
        -- ofp: other file path relative - relative path stem with trailing dot
        ofp = function()
            local stem = vim.fn.expand('%:r')
            return stem ~= '' and stem .. '.' or ''
        end,
        -- adp: absolute directory path (/something/src/)
        adp = function() return vim.fn.expand('%:p:h') .. path_sep end,
        -- dp: directory path relative (src/)
        dp = function()
            local dir = vim.fn.expand('%:h')
            return dir ~= '' and dir .. path_sep or ''
        end,
        -- pwd: present working directory
        pwd = function() return vim.fn.getcwd() end,
    }
    local handler = handlers[kind]
    return handler and handler() or ''
end

--- Yank value to all clipboard registers
---@param value string
local function yank_to_all(value)
    vim.fn.setreg('*', value)
    vim.fn.setreg('+', value)
    vim.fn.setreg('"', value)
    print('Yanked: ' .. value)
end

-- Define all path mappings
local path_maps = {
    { suffix = 'fn',   desc = 'file name' },
    { suffix = 'afp',  desc = 'absolute file path' },
    { suffix = 'fp',   desc = 'relative file path' },
    { suffix = 'ofn',  desc = 'file name stem' },
    { suffix = 'aofp', desc = 'absolute path stem' },
    { suffix = 'ofp',  desc = 'relative path stem' },
    { suffix = 'adp',  desc = 'absolute directory' },
    { suffix = 'dp',   desc = 'relative directory' },
    { suffix = 'pwd',  desc = 'working directory' },
}

for _, m in ipairs(path_maps) do
    -- Normal mode: <leader>y<suffix> yanks to all registers
    map('n', '<leader>y' .. m.suffix, function()
        yank_to_all(get_path(m.suffix))
    end, { silent = true, desc = 'Yank ' .. m.desc })

    -- Command mode: %<suffix> inserts the value
    map('c', '%' .. m.suffix, function()
        return get_path(m.suffix)
    end, { expr = true })
end

-------------------------------------------------------------------------------}}}
-- TERMINAL                                                                   {{{
--------------------------------------------------------------------------------
-- Exit terminal mode
map('t', '<C-\\><C-\\>', '<C-\\><C-n>')
map('s', '<C-\\><C-\\>', '<C-\\><C-n>')
map('i', '<C-\\><C-\\>', '<C-\\><C-n>')
map('n', '<C-\\><C-\\>', '<C-\\><C-n>')

-- Paste into terminal
map('t', '<C-\\>p', '<C-\\><C-n>pi')

-- Paste register into terminal
map('t', '<C-\\><C-r>', function()
    local char = vim.fn.nr2char(vim.fn.getchar())
    return '<C-\\><C-N>"' .. char .. 'pi'
end, { expr = true })

-- Open terminal
map('n', '+', ':<C-u>terminal<CR>')

-------------------------------------------------------------------------------}}}
-- OPTION TOGGLES                                                             {{{
--------------------------------------------------------------------------------
-- "yo" = "yoggle option" (toggle options)
map('n', 'yosb', ':<C-U>set scrollbind!<CR>:set scrollbind?<CR>')
map('n', 'yocb', ':<C-U>set cursorbind!<CR>:set cursorbind?<CR>')
map('n', 'yomd', ':<C-U>set modifiable!<CR>:set modifiable?<CR>')
map('n', 'yoro', ':<C-U>set readonly!<CR>:set readonly?<CR>')
map('n', 'yot', ':<C-U>set textwidth=')
map('n', 'yocl', ':<C-U>setlocal conceallevel=')
map('n', 'yosw', ':<C-U>set shiftwidth=')

-- Toggle scratch buffer (nofile)
map('n', 'yonf', function()
    if vim.bo.buftype:match('nofile') then
        vim.bo.buftype = ''
    else
        vim.bo.buftype = 'nofile'
    end
    vim.cmd('set buftype?')
end, { silent = true, desc = 'Toggle scratch buffer' })

--- Toggle formatoptions and display status
---@param options string Single characters to toggle (e.g., 't' or 'aw')
---@param message string Description of what's being toggled
local function format_options_toggle(options, message)
    local fo = vim.bo.formatoptions
    local action = 'on'

    for char in options:gmatch('.') do
        if fo:find(char, 1, true) then
            vim.bo.formatoptions = fo:gsub(char, '')
            action = 'off'
        else
            vim.bo.formatoptions = vim.bo.formatoptions .. char
        end
        fo = vim.bo.formatoptions
    end

    vim.cmd('set formatoptions?')
    print(action .. ': ' .. message)
end

-- Toggle auto wrap using textwidth (formatoption 't')
map('n', 'yotw', function()
    format_options_toggle('t', 'auto wrap using textwidth')
end, { desc = 'Toggle auto wrap' })

-- Toggle auto formatting of paragraphs (formatoptions 'a' and 'w')
map('n', 'yopw', function()
    format_options_toggle('aw', 'auto formatting of paragraphs')
end, { desc = 'Toggle paragraph auto-format' })

-------------------------------------------------------------------------------}}}
-- SPELLING                                                                   {{{
--------------------------------------------------------------------------------
-- Repeat spell replacement for all matches
map('n', '!z=', ':<C-u>spellrepall<CR>')

-------------------------------------------------------------------------------}}}
-- SEARCH & SUBSTITUTE                                                        {{{
--------------------------------------------------------------------------------
-- Substitute shortcuts with hlsearch enabled
map('n', 'sal', ':set hlsearch<CR>:redraw<CR>:substitute///gc<Left><Left><Left>')
map('n', 'sG', ':set hlsearch<CR>:redraw<CR>:.,$substitute///gc<Left><Left><Left>')
map('n', 'sae', ':set hlsearch<CR>:redraw<CR>:%substitute///gc<Left><Left><Left>')

-- Clear search highlighting and redraw
map('n', '<C-L>', function()
    vim.cmd('redraw!')
    vim.cmd('nohlsearch')
    if vim.fn.has('diff') == 1 then
        vim.cmd('diffupdate')
    end
    return '<C-l>'
end, { expr = true, silent = true })

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

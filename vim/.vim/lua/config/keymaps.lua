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

-- Underline current line with character of choice
map('n', '<leader>u', function()
    local char = vim.fn.nr2char(vim.fn.getchar())
    if char == '' or char == '\27' then return end  -- Escape pressed
    char = vim.fn.escape(char, '\\')
    vim.cmd('normal! yyp')
    vim.cmd([[s#\m\S.*\S\|\S#\=repeat(']] .. char .. [[',strlen(submatch(0)))#ge]])
    vim.cmd('nohlsearch')
end, { silent = true, desc = 'Underline with character' })

-- Reverse visual selection characters
map('x', '<leader>rev', function()
    -- Save registers
    local old_reg_a = vim.fn.getreg('a')
    local old_reg = vim.fn.getreg('"')

    -- Yank selection to register a
    vim.cmd('normal! gv"ay')

    -- Reverse the string
    local text = vim.fn.getreg('a')
    local reversed = text:reverse()

    -- Replace selection with reversed text
    vim.fn.setreg('a', reversed)
    vim.cmd('normal! gvc')
    vim.cmd('normal! "aP')

    -- Restore registers
    vim.fn.setreg('a', old_reg_a)
    vim.fn.setreg('"', old_reg)
end, { silent = true, desc = 'Reverse selection' })

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
-- FIND & BUFFER                                                              {{{
--------------------------------------------------------------------------------
local path_sep = vim.g.os_path_sep or '/'

-- Find file starting from current file's directory
map('n', '<leader>F', function()
    return ':find ' .. vim.fn.expand('%:h') .. path_sep
end, { expr = true, desc = 'Find from current dir' })

-- Find file with same stem (other extension)
map('n', '<leader>fo', function()
    local stem = vim.fn.expand('%:t:r')
    return ':find ' .. stem .. '.*' .. string.char(9)  -- Tab character
end, { expr = true, desc = 'Find file with same stem' })

-- Split find from current directory
map('n', '<leader>S', function()
    return ':sfind ' .. vim.fn.expand('%:h') .. path_sep
end, { expr = true, desc = 'Split find from current dir' })

-- Vertical split find from current directory
map('n', '<leader>V', function()
    return ':vert sfind ' .. vim.fn.expand('%:h') .. path_sep
end, { expr = true, desc = 'Vert split find from current dir' })

-- Tab find from current directory
map('n', '<leader>T', function()
    return ':tabfind ' .. vim.fn.expand('%:h') .. path_sep
end, { expr = true, desc = 'Tab find from current dir' })

-- Buffer selection
map('n', '<leader>b', ':ls<CR>:buffer<Space>', { desc = 'List and select buffer' })
map('n', '<leader>bs', ':ls<CR>:sbuffer<Space>', { desc = 'List and split buffer' })

-- Open buffer with same stem
map('n', '<leader>bo', function()
    local stem = vim.fn.expand('%:t:r')
    return ':buffer ' .. stem .. '.*' .. string.char(9)
end, { expr = true, desc = 'Buffer with same stem' })

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

--- Add word or selection to search pattern (OR)
---@param mode string 'n' for normal, 'x' for visual
local function add_to_search(mode)
    local save_reg = vim.fn.getreg('@')

    -- Add OR separator if search pattern is not empty
    if vim.fn.getreg('/') ~= '' then
        vim.fn.setreg('/', vim.fn.getreg('/') .. '\\|')
    end

    -- Get text to add
    if mode == 'x' then
        vim.cmd('normal! gvy')
    elseif mode == 'n' then
        vim.cmd('normal! yiw')
    else
        vim.fn.setreg('@', save_reg)
        return
    end

    -- Append to search register
    vim.fn.setreg('/', vim.fn.getreg('/') .. vim.fn.getreg('@'))
    vim.fn.setreg('@', save_reg)
end

-- Add word under cursor to search pattern
map('n', 'g**', function() add_to_search('n') end, { desc = 'Add word to search' })
-- Add visual selection to search pattern
map('x', 'g*', function() add_to_search('x') end, { desc = 'Add selection to search' })

-- Preview tag jump
map('n', '<leader>tp', ':ptjump <C-r><C-w><CR>', { desc = 'Preview tag jump' })

-- Clear search highlighting and redraw
map('n', '<C-L>', function()
    vim.cmd('redraw!')
    vim.cmd('nohlsearch')
    if vim.wo.diff then
        vim.cmd('diffupdate')
    end
    return '<C-l>'
end, { expr = true, silent = true })

-------------------------------------------------------------------------------}}}
-- ENVIRONMENT SHORTCUTS                                                      {{{
--------------------------------------------------------------------------------
-- File shortcuts accessible via :e $var
local config_path = vim.fn.stdpath('config') .. '/'
vim.env.zsh = '~/.zshrc'
vim.env.zshl = '~/.zshrc_local'
vim.env.shf = '~/.config/shell/functions.sh'
vim.env.git = '~/.gitconfig'
vim.env.gitl = '~/.gitconfig_local'
vim.env.nvim = vim.env.MYVIMRC or ''
vim.env.posh = '~/Documents/WindowsPowerShell/profile.ps1'
vim.env.tmux = '~/.tmux.conf'
vim.env.i = '~/files/inbox.md'

-------------------------------------------------------------------------------}}}
-- COMMAND ABBREVIATIONS                                                      {{{
--------------------------------------------------------------------------------
-- Number lines (for use in visual mode ranges)
-- Usage: :'<,'>numend or :'<,'>numfront
vim.cmd([[cabbrev numend s/$/\=1-line("'<")+line(".")/c]])
vim.cmd([[cabbrev numfront s/^/\=1-line("'<")+line(".")/c]])

-------------------------------------------------------------------------------}}}
-- UTILITY FUNCTIONS                                                          {{{
--------------------------------------------------------------------------------
--- Generate a random number from reltime
---@return integer
function _G.Rand()
    local time_str = vim.fn.reltimestr(vim.fn.reltime())
    local digits = time_str:match('%.(%d+)')
    return digits and tonumber(digits:sub(2)) or 0
end

-------------------------------------------------------------------------------}}}
-- COMMANDS                                                                   {{{
--------------------------------------------------------------------------------
-- Create a tab for copying (useful when in terminal)
vim.api.nvim_create_user_command('CopyTab', function()
    local winview = vim.fn.winsaveview()
    vim.cmd('tabedit %')
    vim.opt_local.number = false
    vim.opt_local.relativenumber = false
    vim.opt_local.signcolumn = 'no'
    vim.opt_local.foldcolumn = '0'
    vim.fn.winrestview(winview)
end, { desc = 'Open buffer in new tab for copying' })

-- Reverse lines in range
vim.api.nvim_create_user_command('Reverse', function(opts)
    local line1 = opts.line1
    local line2 = opts.line2
    vim.cmd(string.format('%d,%dg/^/m%d', line1, line2, line1 - 1))
    vim.cmd('nohlsearch')
end, { range = '%', bar = true, desc = 'Reverse lines in range' })

-- Split sentences onto separate lines (requires Split/Join plugin)
vim.api.nvim_create_user_command('SentenceSplit', function(opts)
    local line1 = opts.line1
    local line2 = opts.line2
    -- Join lines first, then split on sentence boundaries
    vim.cmd(string.format('%d,%dJoin', line1, line2))
    vim.cmd(string.format([[%d,%dSplit/[.?!;:—]\zs\s\+/]], line1, line2))
end, { range = '%', bar = true, desc = 'Split sentences onto separate lines' })

-- Generate sequence of lines from a template
-- Usage: :5Seq Item {i}: {i*10}     -> generates 5 lines with i from 0-4
--        :5Seq! Item {i}: {i*10}    -> generates 5 lines with i from 1-5
-- Expressions in {braces} are evaluated as Lua with 'i' as the index
vim.api.nvim_create_user_command('Seq', function(opts)
    local count = opts.count > 0 and opts.count or 1
    local template = opts.args
    local start_idx = opts.bang and 1 or 0

    if template == '' then
        vim.notify('Seq: template required', vim.log.levels.ERROR)
        return
    end

    local lines = {}
    for idx = start_idx, start_idx + count - 1 do
        -- Replace {expr} with evaluated Lua expression
        local line = template:gsub('{(.-)}', function(expr)
            -- Create environment with 'i' as the index variable
            local env = setmetatable({ i = idx }, { __index = _G })
            local fn, err = load('return ' .. expr, 'seq', 't', env)
            if fn then
                local ok, result = pcall(fn)
                return ok and tostring(result) or expr
            end
            return expr
        end)
        table.insert(lines, line)
    end

    -- Insert lines after current line
    local cur_line = vim.fn.line('.')
    vim.api.nvim_buf_set_lines(0, cur_line, cur_line, false, lines)
end, { nargs = '*', count = true, bang = true, desc = 'Generate sequence from template' })

-- Renumber sequential numbers in a range
-- Usage: :'<,'>Renumber    -> renumbers starting from 1
--        :'<,'>Renumber!   -> renumbers starting from 0
-- Finds the first number on each line and replaces sequentially
vim.api.nvim_create_user_command('Renumber', function(opts)
    local line1 = opts.line1
    local line2 = opts.line2
    local idx = opts.bang and 0 or 1

    for lnum = line1, line2 do
        local line = vim.fn.getline(lnum)
        -- Replace first number found on the line
        local new_line, count = line:gsub('^([^%d]-)%d+', '%1' .. idx, 1)
        if count > 0 then
            vim.fn.setline(lnum, new_line)
            idx = idx + 1
        end
    end
end, { range = true, bang = true, desc = 'Renumber lines sequentially' })

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

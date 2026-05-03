-------------------------------------------------------------------------------}}}
-- AUTOCMDS                                                                   {{{
--------------------------------------------------------------------------------
-- Autocommands migrated from vimrc

local augroup = vim.api.nvim_create_augroup
local autocmd = vim.api.nvim_create_autocmd

-------------------------------------------------------------------------------}}}
-- VIMRC RELOAD                                                               {{{
--------------------------------------------------------------------------------
-- Reload config on save
augroup("vimrc", { clear = true })
autocmd("BufWritePost", {
	group = "vimrc",
	pattern = { "*vimrc*", "init.vim", "init.lua", "*/lua/config/*.lua", "*/lua/plugins.lua" },
	callback = function()
		vim.cmd("source $MYVIMRC")
	end,
	nested = true,
})

-------------------------------------------------------------------------------}}}
-- AUTO SAVE                                                                  {{{
--------------------------------------------------------------------------------
-- Save all files when focus is lost
augroup("AllFiles", { clear = true })
autocmd("FocusLost", {
	group = "AllFiles",
	pattern = "*",
	command = "silent! wall",
})

-------------------------------------------------------------------------------}}}
-- COLOR COLUMN                                                               {{{
--------------------------------------------------------------------------------
-- Set colorcolumn position based on textwidth
augroup("colorcolumn", { clear = true })
autocmd({ "BufNewFile", "BufWinEnter" }, {
	group = "colorcolumn",
	pattern = "*",
	callback = function()
		local tw = vim.bo.textwidth
		vim.wo.colorcolumn = tw == 0 and "" or tostring(tw + 1)
	end,
})

-------------------------------------------------------------------------------}}}
-- TODO HIGHLIGHT                                                             {{{
--------------------------------------------------------------------------------
-- Highlight TODO, FIXME, NOTE, etc.
vim.api.nvim_set_hl(0, "MyTodo", { link = "Todo", default = true })

augroup("todo", { clear = true })
autocmd("Syntax", {
	group = "todo",
	pattern = "*",
	callback = function()
		vim.fn.matchadd("MyTodo", [[\v<(NOTE|INFO|IDEA|IMPROVEMENT|QUESTION|TODO|FIXME|BUG|HACK|TRICKY|XXX)>]])
	end,
})

-------------------------------------------------------------------------------}}}
-- TERMINAL                                                                   {{{
--------------------------------------------------------------------------------
-- Disable spell checking in terminal buffers
augroup("terminal", { clear = true })
autocmd("TermOpen", {
	group = "terminal",
	pattern = "*",
	callback = function()
		vim.opt_local.spell = false
	end,
})

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

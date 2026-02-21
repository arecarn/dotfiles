-----------------------------------------------------------------------------}}}
-- SETUP NVIM-CMP                                                            {{{
--------------------------------------------------------------------------------
function setup_nvim_snacks()
    local snacks = require('snacks')
    config = {
        input = { enabled = true },
        indent = { enabled = true },
        picker = {},
    }
    snacks.setup(config)
end

function setup_overseer()
    require("overseer").setup()

    vim.api.nvim_create_user_command("Make", function(params)
      -- Insert args at the '$*' in the makeprg
      local cmd, num_subs = vim.o.makeprg:gsub("%$%*", params.args)
      if num_subs == 0 then
        cmd = cmd .. " " .. params.args
      end
      local task = require("overseer").new_task({
        cmd = vim.fn.expandcmd(cmd),
        components = {
          { "on_output_quickfix", open = not params.bang, open_height = 8 },
          "default",
        },
      })
      task:start()
    end, {
      desc = "Run your makeprg as an Overseer task",
      nargs = "*",
      bang = true,
    })
end

function setup_nvim_cmp()

    local cmp = require('cmp')

    cmp.setup{
        snippet = {
            -- REQUIRED - you must specify a snippet engine
            expand = function(args)
                vim.fn["vsnip#anonymous"](args.body) -- For `vsnip` users.
            end,
        },

        window = {
            completion = cmp.config.window.bordered(),
            documentation = cmp.config.window.bordered(),
        },

        mapping = cmp.mapping.preset.insert({
            ['<C-b>'] = cmp.mapping.scroll_docs(-4),
            ['<C-f>'] = cmp.mapping.scroll_docs(4),
            ['<C-n'] = cmp.mapping.complete(),
            ['<C-e>'] = cmp.mapping.abort(),

            -- Accept currently selected item. Set `select` to `false` to only confirm
            -- explicitly selected items.
            ['<C-y>'] = cmp.mapping.confirm({ select = true }),
        }),

        sources = cmp.config.sources({
            { name = 'nvim_lsp' },
            { name = 'vsnip' }, -- For vsnip users.
        }, {
            { name = 'buffer' },
        })
    }

    -- Use buffer source for `/` and `?` (if you enabled `native_menu`, this won't
    -- work anymore).
    cmp.setup.cmdline(
    { '/', '?' },
    {
        mapping = cmp.mapping.preset.cmdline(),
        sources = {
            { name = 'buffer' }
        }
    }
    )

    -- Use cmdline & path source for ':' (if you enabled `native_menu`, this won't
    -- work anymore).
    -- cmp.setup.cmdline(
    --     ':',
    --     {
    --     mapping = cmp.mapping.preset.cmdline(),
    --     sources = cmp.config.sources(
    --         {
    --           { name = 'path' }
    --         },
    --         {
    --           { name = 'cmdline' }
    --         }
    --     )
    --     }
    -- )

    -- Set LSP capabilities globally for all servers (nvim-cmp integration)
    local capabilities = require('cmp_nvim_lsp').default_capabilities()
    vim.lsp.config('*', {
        capabilities = capabilities,
    })
end

-----------------------------------------------------------------------------}}}
-- SETUP MASON & LSPCONFIG                                                   {{{
--------------------------------------------------------------------------------
--
function setup_mason_dap_and_lspconfig()
    vim.cmd([[
        hi BqfPreviewBorder guifg=#3e8e2d ctermfg=71
        hi BqfPreviewTitle guifg=#3e8e2d ctermfg=71
        hi BqfPreviewThumb guibg=#3e8e2d ctermbg=71
        hi link BqfPreviewRange Search
    ]])

    require('bqf').setup({
        auto_enable = true,
        auto_resize_height = true, -- highly recommended enable
        preview = {
            win_height = 12,
            win_vheight = 12,
            delay_syntax = 80,
            border = {'┏', '━', '┓', '┃', '┛', '━', '┗', '┃'},
            show_title = false,
            should_preview_cb = function(bufnr, qwinid)
                local ret = true
                local bufname = vim.api.nvim_buf_get_name(bufnr)
                local fsize = vim.fn.getfsize(bufname)
                if fsize > 100 * 1024 then
                    -- skip file size greater than 100k
                    ret = false
                elseif bufname:match('^fugitive://') then
                    -- skip fugitive buffer
                    ret = false
                end
                return ret
            end
        },
        -- make `drop` and `tab drop` to become preferred
        func_map = {
            drop = 'o',
            openc = 'O',
            split = '<C-s>',
            tabdrop = '<C-t>',
            -- set to empty string to disable
            tabc = '',
            ptogglemode = 'z,',
        },
        filter = {
            fzf = {
                action_for = {['ctrl-s'] = 'split', ['ctrl-t'] = 'tab drop'},
                extra_opts = {'--bind', 'ctrl-o:toggle-all', '--prompt', '> '}
            }
        }
    })

    -- local fn = vim.fn

    -- function _G.qftf(info)
    --     local items
    --     local ret = {}
    --     -- The name of item in list is based on the directory of quickfix window.
    --     -- Change the directory for quickfix window make the name of item shorter.
    --     -- It's a good opportunity to change current directory in quickfixtextfunc :)
    --     --
    --     -- local alterBufnr = fn.bufname('#') -- alternative buffer is the buffer before enter qf window
    --     -- local root = getRootByAlterBufnr(alterBufnr)
    --     -- vim.cmd(('noa lcd %s'):format(fn.fnameescape(root)))
    --     --
    --     if info.quickfix == 1 then
    --         items = fn.getqflist({id = info.id, items = 0}).items
    --     else
    --         items = fn.getloclist(info.winid, {id = info.id, items = 0}).items
    --     end
    --     local limit = 31
    --     local fnameFmt1, fnameFmt2 = '%-' .. limit .. 's', '…%.' .. (limit - 1) .. 's'
    --     local validFmt = '%s │%5d:%-3d│%s %s'
    --     for i = info.start_idx, info.end_idx do
    --         local e = items[i]
    --         local fname = ''
    --         local str
    --         if e.valid == 1 then
    --             if e.bufnr > 0 then
    --                 fname = fn.bufname(e.bufnr)
    --                 if fname == '' then
    --                     fname = '[No Name]'
    --                 else
    --                     fname = fname:gsub('^' .. vim.env.HOME, '~')
    --                 end
    --                 -- char in fname may occur more than 1 width, ignore this issue in order to keep performance
    --                 if #fname <= limit then
    --                     fname = fnameFmt1:format(fname)
    --                 else
    --                     fname = fnameFmt2:format(fname:sub(1 - limit))
    --                 end
    --             end
    --             local lnum = e.lnum > 99999 and -1 or e.lnum
    --             local col = e.col > 999 and -1 or e.col
    --             local qtype = e.type == '' and '' or ' ' .. e.type:sub(1, 1):upper()
    --             str = validFmt:format(fname, lnum, col, qtype, e.text)
    --         else
    --             str = e.text
    --         end
    --         table.insert(ret, str)
    --     end
    --     return ret
    -- end

-- vim.o.qftf = '{info -> v:lua._G.qftf(info)}'

-- Adapt fzf's delimiter in nvim-bqf
require('bqf').setup({
    filter = {
        fzf = {
            extra_opts = {'--bind', 'ctrl-o:toggle-all', '--delimiter', '│'}
        }
    }
})

    require("mason").setup()

    require("mason-lspconfig").setup{
        ensure_installed = {
            "yamlls",
            "bashls",
            "clangd",
            "cmake",
            "pyright",
            "vimls",
            "prosemd_lsp",
        },
    }

    -- Use Neovim 0.11+ native vim.lsp.config API
    -- See :help lspconfig-nvim-0.11

    -- YAML
    vim.lsp.config.yamlls = {
        cmd = { 'yaml-language-server', '--stdio' },
        filetypes = { 'yaml', 'yaml.docker-compose', 'yaml.gitlab' },
        root_markers = { '.git' },
        settings = {
            yaml = {
                completion = { enable = true }
            }
        }
    }

    -- Bash
    vim.lsp.config.bashls = {
        cmd = { 'bash-language-server', 'start' },
        filetypes = { 'sh', 'bash' },
        root_markers = { '.git' },
    }

    -- CMake
    vim.lsp.config.cmake = {
        cmd = { 'cmake-language-server' },
        filetypes = { 'cmake' },
        root_markers = { 'CMakeLists.txt', '.git' },
    }

    -- Python
    vim.lsp.config.pyright = {
        cmd = { 'pyright-langserver', '--stdio' },
        filetypes = { 'python' },
        root_markers = { 'pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt', '.git' },
    }

    -- Vimscript
    vim.lsp.config.vimls = {
        cmd = { 'vim-language-server', '--stdio' },
        filetypes = { 'vim' },
        root_markers = { '.git' },
    }

    -- Prose/Markdown
    vim.lsp.config.prosemd_lsp = {
        cmd = { 'prosemd-lsp', '--stdio' },
        filetypes = { 'markdown' },
        root_markers = { '.git' },
    }

    -- C/C++
    vim.lsp.config.clangd = {
        cmd = { 'clangd' },
        filetypes = { 'c', 'cpp', 'objc', 'objcpp', 'cuda', 'proto' },
        root_markers = { 'compile_commands.json', 'compile_flags.txt', '.git' },
    }

    -- Enable all configured LSP servers
    vim.lsp.enable('yamlls')
    vim.lsp.enable('bashls')
    vim.lsp.enable('cmake')
    vim.lsp.enable('pyright')
    vim.lsp.enable('vimls')
    vim.lsp.enable('prosemd_lsp')
    vim.lsp.enable('clangd')

    -- Clangd-specific keymap for switching between source/header
    vim.api.nvim_create_autocmd("FileType", {
        pattern = { "c", "cpp" },
        callback = function()
            vim.keymap.set('n', '<leader>of', '<Cmd>ClangdSwitchSourceHeader<CR>',
                { buffer = true, desc = "Switch source/header" })
        end,
        group = vim.api.nvim_create_augroup("clangd_mappings", { clear = true })
    })

    local signs = { Error = " ", Warn = " ", Hint = " ", Info = " " }
    for type, icon in pairs(signs) do
        local hl = "DiagnosticSign" .. type
        vim.fn.sign_define(hl, { text = icon, texthl = hl, numhl = hl     })
    end

    local config = {
        -- disable virtual text
        virtual_text = false,
        -- show signs
        signs = { active = signs },
        update_in_insert = true,
        underline = true,
        severity_sort = true,
        float = {
            focusable = false,
            style = "minimal",
            border = "rounded",
            source = "always",
            header = "",
            prefix = "",
        },
    }

    vim.diagnostic.config(config)

    -- Function to check if a floating dialog exists and if not
    -- then check for diagnostics under the cursor
    function OpenDiagnosticIfNoFloat()
        for _, winid in pairs(vim.api.nvim_tabpage_list_wins(0)) do
            if vim.api.nvim_win_get_config(winid).zindex then
                return
            end
        end

        -- THIS IS FOR BUILTIN LSP
        vim.diagnostic.open_float(0, {
            scope = "line",
            focusable = false,
            close_events = {
                "CursorMoved",
                "CursorMovedI",
                "BufHidden",
                "InsertCharPre",
                "WinLeave",
            },
        })
    end
    -- Show diagnostics under the cursor when holding position
    vim.api.nvim_create_augroup("lsp_diagnostics_hold", { clear = true })
    vim.api.nvim_create_autocmd({ "CursorHold" }, {
        pattern = "*",
        command = "lua OpenDiagnosticIfNoFloat()",
        group = "lsp_diagnostics_hold",
    })



    -- Global mappings.
    -- See `:help vim.diagnostic.*` for documentation on the below functions
    vim.keymap.set('n', '<leader>e', vim.diagnostic.open_float)
    vim.keymap.set('n', '[d', vim.diagnostic.goto_prev)
    vim.keymap.set('n', ']d', vim.diagnostic.goto_next)
    vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist)

    -- Use LspAttach autocommand to only map the following keys after the
    -- language server attaches to the current buffer
    vim.api.nvim_create_autocmd(
    'LspAttach',
    {
        group = vim.api.nvim_create_augroup('UserLspConfig', {}),
        callback = function(ev)

            vim.lsp.handlers["textDocument/hover"] = vim.lsp.with(vim.lsp.handlers.hover, { border = "rounded" })
            vim.lsp.handlers["textDocument/signatureHelp"] = vim.lsp.with(vim.lsp.handlers.signature_help, { border = "rounded" })

            -- Buffer local mappings.
            -- See `:help vim.lsp.*` for documentation on any of the below functions
            local opts = { buffer = ev.buf }
            vim.keymap.set('n', 'gld', vim.lsp.buf.declaration, opts)
            vim.keymap.set('n', 'glD', vim.lsp.buf.definition, opts)
            vim.keymap.set('n', 'glt', vim.lsp.buf.type_definition, opts)
            vim.keymap.set('n', 'gl?', vim.lsp.buf.hover, opts)
            vim.keymap.set('n', 'gl??', vim.lsp.buf.signature_help, opts)
            vim.keymap.set('n', 'gli', vim.lsp.buf.implementation, opts)
            vim.keymap.set('n', 'glr', vim.lsp.buf.references, opts)
            vim.keymap.set('n', 'gls', vim.lsp.buf.rename, opts)
            vim.keymap.set({ 'n', 'v' }, 'gla', vim.lsp.buf.code_action, opts)
            vim.keymap.set('n', 'glf', function()
                vim.lsp.buf.format { async = true }
            end, opts)
            vim.keymap.set('n', 'glwa', vim.lsp.buf.add_workspace_folder, opts)
            vim.keymap.set('n', 'glwr', vim.lsp.buf.remove_workspace_folder, opts)
            vim.keymap.set('n', 'glwl', function()
                print(vim.inspect(vim.lsp.buf.list_workspace_folders()))
            end, opts)
        end,
    }
    )
end

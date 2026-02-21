-------------------------------------------------------------------------------}}}
-- PLUGINS (lazy.nvim)                                                        {{{
--------------------------------------------------------------------------------
-- Migrated from vim-plug to lazy.nvim
-- Plugin configs are inline with declarations

-------------------------------------------------------------------------------}}}
-- BOOTSTRAP LAZY.NVIM                                                        {{{
--------------------------------------------------------------------------------
local lazypath = vim.fn.stdpath('data') .. '/lazy/lazy.nvim'
if not vim.uv.fs_stat(lazypath) then
    vim.fn.system({
        'git', 'clone', '--filter=blob:none',
        'https://github.com/folke/lazy.nvim.git',
        '--branch=stable',
        lazypath,
    })
end
vim.opt.rtp:prepend(lazypath)

-------------------------------------------------------------------------------}}}
-- PLUGIN SPECS                                                               {{{
--------------------------------------------------------------------------------
local plugins = {

    ---------------------------------------------------------------------------}}}
    -- TEXT OBJECTS                                                           {{{
    ---------------------------------------------------------------------------
    { 'kana/vim-textobj-user', event = 'VeryLazy' },
    { 'saihoooooooo/vim-textobj-space', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    {
        'Julian/vim-textobj-variable-segment',
        commit = '51c323dca5c44f7a8e5a689b9156ef818d02188e',
        dependencies = 'kana/vim-textobj-user',
        event = 'VeryLazy',
    },
    { 'kana/vim-textobj-entire', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    { 'kana/vim-textobj-indent', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    { 'kana/vim-textobj-line', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    { 'kana/vim-textobj-syntax', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    { 'mattn/vim-textobj-url', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    { 'glts/vim-textobj-comment', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    {
        'thinca/vim-textobj-between',
        dependencies = 'kana/vim-textobj-user',
        event = 'VeryLazy',
        init = function()
            vim.g.textobj_between_no_default_key_mappings = 1
        end,
        config = function()
            vim.keymap.set({ 'x', 'o' }, 'am', '<Plug>(textobj-between-a)')
            vim.keymap.set({ 'x', 'o' }, 'im', '<Plug>(textobj-between-i)')
        end,
    },
    { 'osyo-manga/vim-textobj-multiblock', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    { 'sgur/vim-textobj-parameter', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },
    { 'osyo-manga/vim-textobj-blockwise', dependencies = 'kana/vim-textobj-user', event = 'VeryLazy' },

    ---------------------------------------------------------------------------}}}
    -- OPERATORS                                                              {{{
    ---------------------------------------------------------------------------
    { 'kana/vim-operator-user', event = 'VeryLazy' },
    {
        'kana/vim-operator-replace',
        dependencies = 'kana/vim-operator-user',
        event = 'VeryLazy',
        config = function()
            vim.keymap.set('', '_', '<Plug>(operator-replace)')
        end,
    },
    { 'arecarn/vim-operator-mixed-case', dependencies = 'kana/vim-operator-user', event = 'VeryLazy' },
    { 'machakann/vim-sandwich', event = 'VeryLazy' },
    { 'tommcdo/vim-exchange', event = 'VeryLazy' },
    { 'tpope/vim-commentary', event = 'VeryLazy' },
    { 'tpope/vim-repeat', event = 'VeryLazy' },
    { 'vim-scripts/visualrepeat', event = 'VeryLazy' },

    ---------------------------------------------------------------------------}}}
    -- FUZZY FINDING                                                          {{{
    ---------------------------------------------------------------------------
    { 'nvim-lua/plenary.nvim', lazy = true },
    {
        'nvim-telescope/telescope.nvim',
        dependencies = 'nvim-lua/plenary.nvim',
        cmd = 'Telescope',
        keys = {
            { 'z=', '<cmd>Telescope spell_suggest theme=cursor<CR>', desc = 'Spell suggest' },
            { 'gof', '<cmd>Telescope find_files<CR>', desc = 'Find files' },
            { 'gos', '<cmd>Telescope live_grep<CR>', desc = 'Live grep' },
            { 'gor', '<cmd>Telescope oldfiles<CR>', desc = 'Recent files' },
        },
    },
    { 'junegunn/fzf', build = ':call fzf#install()', event = 'VeryLazy' },
    { 'junegunn/fzf.vim', dependencies = 'junegunn/fzf', event = 'VeryLazy' },

    ---------------------------------------------------------------------------}}}
    -- FOLDS                                                                  {{{
    ---------------------------------------------------------------------------
    {
        'arecarn/vim-clean-fold',
        event = 'VeryLazy',
        config = function()
            vim.opt.foldmethod = 'expr'
            vim.opt.foldtext = 'clean_fold#fold_text_minimal()'
            vim.opt.foldexpr = 'clean_fold#fold_expr(v:lnum)'
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- VISUAL ENHANCEMENTS                                                    {{{
    ---------------------------------------------------------------------------
    {
        'folke/snacks.nvim',
        priority = 1000,
        lazy = false,
        config = function()
            require('snacks').setup({
                input = { enabled = true },
                indent = { enabled = true },
                picker = {},
            })
        end,
    },
    {
        'itchyny/lightline.vim',
        lazy = false,
        init = function()
            vim.g.lightline = {
                colorscheme = 'apprentice',
                active = {
                    right = { { 'winnr' }, { 'fugitive', 'filename', 'bufnr' } },
                    left = { { 'paste', 'lineinfo' }, { 'percent' }, { 'fileformat', 'fileencoding', 'filetype' } },
                },
                inactive = {
                    right = { { 'winnr' }, { 'filename', 'bufnr' } },
                    left = { { 'lineinfo' }, { 'percent' }, { 'fileformat', 'fileencoding', 'filetype' } },
                },
                component_function = {
                    modified = 'Lightline_modified',
                    readonly = 'Lightline_readonly',
                    fugitive = 'Lightline_fugitive',
                    filename = 'Lightline_filename',
                    fileformat = 'Lightline_fileformat',
                    filetype = 'Lightline_filetype',
                    fileencoding = 'Lightline_fileencoding',
                    winnr = 'Lightline_winnr',
                    bufnr = 'Lightline_bufnr',
                },
            }
        end,
    },
    { 'chreekat/vim-paren-crosshairs', event = 'VeryLazy' },
    {
        'junegunn/goyo.vim',
        cmd = 'Goyo',
        keys = {
            { 'yof', function()
                local count = vim.v.count
                if count == 0 then
                    vim.cmd('Goyo')
                else
                    vim.cmd('Goyo ' .. count)
                end
            end, desc = 'Toggle Goyo' },
        },
        init = function()
            local signcolumn_width = vim.o.signcolumn ~= 'no' and 2 or 0
            vim.g.goyo_width = 80 + signcolumn_width + vim.o.foldcolumn
        end,
    },
    {
        'nathanaelkane/vim-indent-guides',
        event = 'VeryLazy',
        init = function()
            vim.g.indent_guides_enable_on_vim_startup = 0
            vim.g.indent_guides_default_mapping = 0
            vim.g.indent_guides_guide_size = 1
            vim.g.indent_guides_start_level = 2
        end,
        config = function()
            vim.keymap.set('n', 'coig', '<Plug>IndentGuidesToggle', { silent = true })
        end,
    },
    {
        'nvim-treesitter/nvim-treesitter',
        build = ':TSUpdate',
        event = { 'BufReadPost', 'BufNewFile' },
    },
    {
        'edkolev/tmuxline.vim',
        cond = vim.fn.has('win32') == 0 and vim.fn.has('win64') == 0,
        event = 'VeryLazy',
        init = function()
            vim.g.tmuxline_powerline_separators = 0
            vim.g.tmuxline_separators = {
                left = '', left_alt = '|', right = '', right_alt = '|', space = ' '
            }
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- TASK RUNNER                                                            {{{
    ---------------------------------------------------------------------------
    {
        'stevearc/overseer.nvim',
        cmd = { 'OverseerRun', 'OverseerToggle', 'OverseerOpen', 'Make' },
        keys = {
            { 'm<Space>', ':Make<Space>', desc = 'Make' },
            { '<leader>oo', '<cmd>OverseerOpen<CR>', desc = 'Overseer open' },
            { '<leader>ot', '<cmd>OverseerToggle<CR>', desc = 'Overseer toggle' },
        },
        config = function()
            require('overseer').setup()
            -- Make command is defined in nvim_plugin.lua
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- FILE TYPE + SYNTAX                                                     {{{
    ---------------------------------------------------------------------------
    { 'stephpy/vim-yaml', ft = 'yaml' },
    {
        'tpope/vim-markdown',
        ft = 'markdown',
        init = function()
            vim.g.markdown_fenced_languages = { 'python', 'c', 'cpp', 'bash=sh' }
            vim.g.markdown_syntax_conceal = 0
            vim.g.markdown_folding = 1
        end,
    },
    {
        'iamcco/markdown-preview.nvim',
        build = function() vim.fn['mkdp#util#install']() end,
        ft = 'markdown',
        init = function()
            vim.g.mkdp_auto_close = 0
            vim.g.mkdp_echo_preview_url = 1
            vim.g.mkdp_port = '6419'
            vim.g.mkdp_preview_options = {
                mkit = {}, katex = {}, uml = {}, maid = {},
                disable_sync_scroll = 1,
                sync_scroll_type = 'middle',
                hide_yaml_meta = 1,
                sequence_diagrams = {},
                flowchart_diagrams = {},
                content_editable = false,
            }
        end,
    },
    { 'jkramer/vim-checkbox', ft = 'markdown' },
    { 'aklt/plantuml-syntax', ft = 'plantuml' },
    {
        'kevinhwang91/nvim-bqf',
        ft = 'qf',
        config = function()
            vim.cmd([[
                hi BqfPreviewBorder guifg=#3e8e2d ctermfg=71
                hi BqfPreviewTitle guifg=#3e8e2d ctermfg=71
                hi BqfPreviewThumb guibg=#3e8e2d ctermbg=71
                hi link BqfPreviewRange Search
            ]])
            require('bqf').setup({
                auto_enable = true,
                auto_resize_height = true,
                preview = {
                    win_height = 12,
                    win_vheight = 12,
                    delay_syntax = 80,
                    border = { '┏', '━', '┓', '┃', '┛', '━', '┗', '┃' },
                    show_title = false,
                    should_preview_cb = function(bufnr)
                        local bufname = vim.api.nvim_buf_get_name(bufnr)
                        local fsize = vim.fn.getfsize(bufname)
                        if fsize > 100 * 1024 then return false end
                        if bufname:match('^fugitive://') then return false end
                        return true
                    end,
                },
                func_map = {
                    drop = 'o', openc = 'O', split = '<C-s>', tabdrop = '<C-t>',
                    tabc = '', ptogglemode = 'z,',
                },
                filter = {
                    fzf = {
                        action_for = { ['ctrl-s'] = 'split', ['ctrl-t'] = 'tab drop' },
                        extra_opts = { '--bind', 'ctrl-o:toggle-all', '--delimiter', '│' },
                    },
                },
            })
        end,
    },
    { 'octol/vim-cpp-enhanced-highlight', ft = { 'c', 'cpp' } },
    { 'hynek/vim-python-pep8-indent', ft = 'python' },
    { 'Shougo/Deol.nvim', cmd = 'Deol', init = function() vim.g['deol#prompt_pattern'] = '.\\{-} \\d\\d:\\d\\d:\\d\\d %' end },
    { 'elzr/vim-json', ft = 'json', init = function() vim.g.vim_json_syntax_conceal = 0 end },
    {
        'chrisbra/csv.vim',
        ft = 'csv',
        config = function()
            vim.api.nvim_create_autocmd('CursorHold', {
                pattern = '*.csv',
                command = 'WhatColumn!',
            })
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- COLORS                                                                 {{{
    ---------------------------------------------------------------------------
    { 'rktjmp/lush.nvim', lazy = false },
    {
        'adisen99/apprentice.nvim',
        lazy = false,
        priority = 1000,
        dependencies = 'rktjmp/lush.nvim',
        config = function()
            vim.g.colors_name = 'apprentice'
            require('lush')(require('apprentice').setup({
                plugins = {
                    'buftabline', 'cmp', 'fzf', 'lsp', 'lspsaga', 'signify', 'telescope', 'treesitter',
                },
                langs = {
                    'c', 'clojure', 'coffeescript', 'csharp', 'css', 'elixir', 'golang', 'haskell',
                    'html', 'java', 'js', 'json', 'jsx', 'lua', 'markdown', 'moonscript', 'objc',
                    'ocaml', 'purescript', 'python', 'ruby', 'rust', 'scala', 'typescript', 'viml', 'xml',
                },
            }))
        end,
    },
    { 'jonsmithers/apprentice-lightline-experimental', lazy = false },

    ---------------------------------------------------------------------------}}}
    -- LSP & COMPLETION                                                       {{{
    ---------------------------------------------------------------------------
    {
        'williamboman/mason.nvim',
        cmd = 'Mason',
        build = ':MasonUpdate',
        config = function() require('mason').setup() end,
    },
    {
        'williamboman/mason-lspconfig.nvim',
        event = { 'BufReadPre', 'BufNewFile' },
        dependencies = { 'williamboman/mason.nvim', 'neovim/nvim-lspconfig' },
        config = function()
            require('mason-lspconfig').setup({
                ensure_installed = { 'yamlls', 'bashls', 'clangd', 'cmake', 'pyright', 'vimls', 'prosemd_lsp' },
            })

            -----------------------------------------------------------------
            -- LSP Server Configurations (Neovim 0.11+ native API)
            -----------------------------------------------------------------
            vim.lsp.config.yamlls = {
                cmd = { 'yaml-language-server', '--stdio' },
                filetypes = { 'yaml', 'yaml.docker-compose', 'yaml.gitlab' },
                root_markers = { '.git' },
                settings = { yaml = { completion = { enable = true } } },
            }

            vim.lsp.config.bashls = {
                cmd = { 'bash-language-server', 'start' },
                filetypes = { 'sh', 'bash' },
                root_markers = { '.git' },
            }

            vim.lsp.config.cmake = {
                cmd = { 'cmake-language-server' },
                filetypes = { 'cmake' },
                root_markers = { 'CMakeLists.txt', '.git' },
            }

            vim.lsp.config.pyright = {
                cmd = { 'pyright-langserver', '--stdio' },
                filetypes = { 'python' },
                root_markers = { 'pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt', '.git' },
            }

            vim.lsp.config.vimls = {
                cmd = { 'vim-language-server', '--stdio' },
                filetypes = { 'vim' },
                root_markers = { '.git' },
            }

            vim.lsp.config.prosemd_lsp = {
                cmd = { 'prosemd-lsp', '--stdio' },
                filetypes = { 'markdown' },
                root_markers = { '.git' },
            }

            vim.lsp.config.clangd = {
                cmd = { 'clangd' },
                filetypes = { 'c', 'cpp', 'objc', 'objcpp', 'cuda', 'proto' },
                root_markers = { 'compile_commands.json', 'compile_flags.txt', '.git' },
            }

            -- Enable all LSP servers
            vim.lsp.enable('yamlls')
            vim.lsp.enable('bashls')
            vim.lsp.enable('cmake')
            vim.lsp.enable('pyright')
            vim.lsp.enable('vimls')
            vim.lsp.enable('prosemd_lsp')
            vim.lsp.enable('clangd')

            -----------------------------------------------------------------
            -- Clangd-specific keymap
            -----------------------------------------------------------------
            vim.api.nvim_create_autocmd('FileType', {
                pattern = { 'c', 'cpp' },
                callback = function()
                    vim.keymap.set('n', '<leader>of', '<Cmd>ClangdSwitchSourceHeader<CR>',
                        { buffer = true, desc = 'Switch source/header' })
                end,
                group = vim.api.nvim_create_augroup('clangd_mappings', { clear = true }),
            })

            -----------------------------------------------------------------
            -- Diagnostic configuration
            -----------------------------------------------------------------
            local signs = { Error = ' ', Warn = ' ', Hint = ' ', Info = ' ' }
            for type, icon in pairs(signs) do
                local hl = 'DiagnosticSign' .. type
                vim.fn.sign_define(hl, { text = icon, texthl = hl, numhl = hl })
            end

            vim.diagnostic.config({
                virtual_text = false,
                signs = { active = signs },
                update_in_insert = true,
                underline = true,
                severity_sort = true,
                float = {
                    focusable = false,
                    style = 'minimal',
                    border = 'rounded',
                    source = 'always',
                    header = '',
                    prefix = '',
                },
            })

            -----------------------------------------------------------------
            -- Diagnostic float on CursorHold
            -----------------------------------------------------------------
            local function open_diagnostic_if_no_float()
                for _, winid in pairs(vim.api.nvim_tabpage_list_wins(0)) do
                    if vim.api.nvim_win_get_config(winid).zindex then return end
                end
                vim.diagnostic.open_float(0, {
                    scope = 'line',
                    focusable = false,
                    close_events = { 'CursorMoved', 'CursorMovedI', 'BufHidden', 'InsertCharPre', 'WinLeave' },
                })
            end

            vim.api.nvim_create_augroup('lsp_diagnostics_hold', { clear = true })
            vim.api.nvim_create_autocmd('CursorHold', {
                pattern = '*',
                callback = open_diagnostic_if_no_float,
                group = 'lsp_diagnostics_hold',
            })

            -----------------------------------------------------------------
            -- Global diagnostic keymaps
            -----------------------------------------------------------------
            vim.keymap.set('n', '<leader>e', vim.diagnostic.open_float)
            vim.keymap.set('n', '[d', vim.diagnostic.goto_prev)
            vim.keymap.set('n', ']d', vim.diagnostic.goto_next)
            vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist)

            -----------------------------------------------------------------
            -- LSP Attach keymaps
            -----------------------------------------------------------------
            vim.api.nvim_create_autocmd('LspAttach', {
                group = vim.api.nvim_create_augroup('UserLspConfig', {}),
                callback = function(ev)
                    vim.lsp.handlers['textDocument/hover'] = vim.lsp.with(
                        vim.lsp.handlers.hover, { border = 'rounded' }
                    )
                    vim.lsp.handlers['textDocument/signatureHelp'] = vim.lsp.with(
                        vim.lsp.handlers.signature_help, { border = 'rounded' }
                    )

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
                    vim.keymap.set('n', 'glf', function() vim.lsp.buf.format({ async = true }) end, opts)
                    vim.keymap.set('n', 'glwa', vim.lsp.buf.add_workspace_folder, opts)
                    vim.keymap.set('n', 'glwr', vim.lsp.buf.remove_workspace_folder, opts)
                    vim.keymap.set('n', 'glwl', function()
                        print(vim.inspect(vim.lsp.buf.list_workspace_folders()))
                    end, opts)
                end,
            })
        end,
    },
    { 'neovim/nvim-lspconfig', lazy = true },
    { 'mfussenegger/nvim-dap', lazy = true },
    { 'jay-babu/mason-nvim-dap.nvim', dependencies = { 'williamboman/mason.nvim', 'mfussenegger/nvim-dap' }, lazy = true },
    { 'rcarriga/nvim-dap-ui', dependencies = { 'mfussenegger/nvim-dap', 'nvim-neotest/nvim-nio' }, lazy = true },
    {
        'hrsh7th/nvim-cmp',
        event = { 'InsertEnter', 'CmdlineEnter' },
        dependencies = {
            'hrsh7th/cmp-nvim-lsp',
            'hrsh7th/cmp-buffer',
            'hrsh7th/cmp-path',
            'hrsh7th/cmp-cmdline',
            'hrsh7th/cmp-vsnip',
            'hrsh7th/vim-vsnip',
        },
        config = function()
            local cmp = require('cmp')
            cmp.setup({
                snippet = {
                    expand = function(args) vim.fn['vsnip#anonymous'](args.body) end,
                },
                window = {
                    completion = cmp.config.window.bordered(),
                    documentation = cmp.config.window.bordered(),
                },
                mapping = cmp.mapping.preset.insert({
                    ['<C-b>'] = cmp.mapping.scroll_docs(-4),
                    ['<C-f>'] = cmp.mapping.scroll_docs(4),
                    ['<C-n>'] = cmp.mapping.complete(),
                    ['<C-e>'] = cmp.mapping.abort(),
                    ['<C-y>'] = cmp.mapping.confirm({ select = true }),
                }),
                sources = cmp.config.sources(
                    { { name = 'nvim_lsp' }, { name = 'vsnip' } },
                    { { name = 'buffer' } }
                ),
            })
            cmp.setup.cmdline({ '/', '?' }, {
                mapping = cmp.mapping.preset.cmdline(),
                sources = { { name = 'buffer' } },
            })

            -- Set capabilities globally
            local capabilities = require('cmp_nvim_lsp').default_capabilities()
            vim.lsp.config('*', { capabilities = capabilities })
        end,
    },
    { 'hrsh7th/cmp-nvim-lsp', lazy = true },
    { 'hrsh7th/cmp-buffer', lazy = true },
    { 'hrsh7th/cmp-path', lazy = true },
    { 'hrsh7th/cmp-cmdline', lazy = true },
    { 'hrsh7th/cmp-vsnip', lazy = true },
    { 'hrsh7th/vim-vsnip', event = 'InsertEnter' },

    ---------------------------------------------------------------------------}}}
    -- GIT / VCS                                                              {{{
    ---------------------------------------------------------------------------
    {
        'tpope/vim-fugitive',
        cmd = { 'Git', 'G', 'Gdiff', 'Gread', 'Gwrite', 'Ggrep', 'GMove', 'GDelete', 'GBrowse' },
        keys = {
            { '<leader>gs', '<cmd>Git<CR>', desc = 'Git status' },
            { '<leader>gd', '<cmd>Gdiff<CR>', desc = 'Git diff' },
            { '<leader>gd1', '<cmd>Gdiff HEAD~1<CR>', desc = 'Git diff HEAD~1' },
            { '<leader>gd2', '<cmd>Gdiff HEAD~2<CR>', desc = 'Git diff HEAD~2' },
        },
    },
    { 'lambdalisue/gina.vim', cmd = 'Gina' },
    { 'jreybert/vimagit', cmd = 'Magit' },
    { 'airblade/vim-rooter', event = 'VeryLazy', init = function() vim.g.rooter_manual_only = 1 end },
    { 'cohama/agit.vim', cmd = { 'Agit', 'AgitFile' } },
    { 'mhinz/vim-signify', event = { 'BufReadPre', 'BufNewFile' } },

    ---------------------------------------------------------------------------}}}
    -- DIFF                                                                   {{{
    ---------------------------------------------------------------------------
    {
        'AndrewRadev/linediff.vim',
        cmd = 'Linediff',
        keys = { { '<leader>lnd', ':Linediff<CR>', mode = 'x', desc = 'Line diff' } },
    },
    { 'vim-scripts/diffchanges.vim', cmd = 'DiffChangesDiffToggle' },
    { 'arecarn/vim-diff-utils', branch = 'visual_mapping', event = 'VeryLazy' },
    {
        'chrisbra/vim-diff-enhanced',
        event = 'VeryLazy',
        config = function()
            vim.o.diffexpr = 'EnhancedDiff#Diff("git diff", "--diff-algorithm=patience")'
        end,
    },
    { 'will133/vim-dirdiff', cmd = 'DirDiff' },

    ---------------------------------------------------------------------------}}}
    -- FILE EXPLORER                                                          {{{
    ---------------------------------------------------------------------------
    {
        'lambdalisue/fern.vim',
        dependencies = 'lambdalisue/fern-hijack.vim',
        cmd = 'Fern',
        keys = { { '-', '<cmd>Fern %:p:h<CR>', desc = 'Open Fern' } },
        init = function() vim.g['fern#default_hidden'] = 1 end,
        config = function()
            local function init_fern()
                local opts = { buffer = true }
                vim.keymap.set('n', '<BS>', '<Plug>(fern-action-collapse)', opts)
                vim.keymap.set('n', '<CR>', '<Plug>(fern-action-open-or-expand)', opts)
                vim.keymap.set('n', 'h', '<Plug>(fern-action-leave)', opts)
                vim.keymap.set('n', 'l', '<Plug>(fern-action-open-or-enter)', opts)
                vim.keymap.set('n', 'H', '<Plug>(fern-action-hidden)', opts)
                vim.keymap.set('n', '<F1>', '<Plug>(fern-action-help:all)', opts)
            end
            vim.api.nvim_create_autocmd('FileType', {
                pattern = 'fern',
                callback = init_fern,
            })
            vim.api.nvim_create_autocmd('User', {
                pattern = 'FernHighlight',
                callback = function()
                    vim.cmd('highlight link FernRootSymbol Title')
                    vim.cmd('highlight link FernRootText Title')
                end,
            })
        end,
    },
    { 'lambdalisue/fern-hijack.vim', lazy = true },

    ---------------------------------------------------------------------------}}}
    -- TEXT MANIPULATION                                                      {{{
    ---------------------------------------------------------------------------
    {
        'godlygeek/tabular',
        cmd = 'Tabularize',
        keys = {
            { '<leader>a', ':Tabularize/', mode = { 'n', 'x' }, desc = 'Tabularize' },
        },
    },
    { 'arecarn/vim-split-join', cmd = { 'Split', 'Join' } },
    { 'AndrewRadev/splitjoin.vim', keys = { 'gS', 'gJ' } },
    {
        't9md/vim-textmanip',
        keys = {
            { '<C-j>', '<Plug>(textmanip-move-down)', mode = 'x' },
            { '<C-k>', '<Plug>(textmanip-move-up)', mode = 'x' },
            { '<C-h>', '<Plug>(textmanip-move-left)', mode = 'x' },
            { '<C-l>', '<Plug>(textmanip-move-right)', mode = 'x' },
            { 'g<C-j>', '<Plug>(textmanip-duplicate-down)', mode = 'x' },
            { 'g<C-k>', '<Plug>(textmanip-duplicate-up)', mode = 'x' },
            { 'g<C-h>', '<Plug>(textmanip-duplicate-left)', mode = 'x' },
            { 'g<C-l>', '<Plug>(textmanip-duplicate-right)', mode = 'x' },
            { 'yotm', '<Plug>(textmanip-toggle-mode)', mode = 'n' },
        },
    },
    { 'vim-scripts/ingo-library', lazy = true },
    {
        'vim-scripts/FormatToWidth',
        dependencies = 'vim-scripts/ingo-library',
        keys = { { 'gQ', '<Plug>FormatToWidth', mode = 'x' } },
    },

    ---------------------------------------------------------------------------}}}
    -- ENHANCEMENTS                                                           {{{
    ---------------------------------------------------------------------------
    { 'kana/vim-niceblock', event = 'VeryLazy' },
    { 'tpope/vim-speeddating', keys = { '<C-a>', '<C-x>' } },
    { 'tpope/vim-unimpaired', event = 'VeryLazy' },
    { 'vim-scripts/UnconditionalPaste', event = 'VeryLazy' },
    { 'arecarn/vim-auto-autoread', event = 'VeryLazy' },
    {
        'arecarn/vim-backup-tree',
        event = 'VeryLazy',
        config = function()
            local data_path = vim.fn.stdpath('data')
            vim.fn.mkdir(data_path .. '/backup', 'p')
            vim.g.backup_tree = data_path .. '/backup'
        end,
    },
    { 'thinca/vim-qfreplace', cmd = 'Qfreplace' },
    { 'tpope/vim-eunuch', cmd = { 'Delete', 'Unlink', 'Move', 'Rename', 'Chmod', 'Mkdir', 'SudoWrite', 'SudoEdit' } },
    { 'arecarn/vim-spell-utils', event = 'VeryLazy' },
    { 'tpope/vim-abolish', cmd = { 'Abolish', 'Subvert' }, keys = { 'cr' } },
    { 'mg979/vim-visual-multi', event = 'VeryLazy', init = function() vim.g.VM_mouse_mappings = 1 end },

    ---------------------------------------------------------------------------}}}
    -- WORD HIGHLIGHTING                                                      {{{
    ---------------------------------------------------------------------------
    {
        't9md/vim-quickhl',
        keys = {
            { 'gm', '<Plug>(quickhl-manual-this)', mode = { 'n', 'x' } },
            { 'gmx', '<Plug>(quickhl-manual-reset)', mode = { 'n', 'x' } },
        },
    },
    {
        'dominikduda/vim_current_word',
        event = 'VeryLazy',
        init = function() vim.g['vim_current_word#highlight_current_word'] = 0 end,
    },

    ---------------------------------------------------------------------------}}}
    -- SEARCH                                                                 {{{
    ---------------------------------------------------------------------------
    { 'pgdouyon/vim-evanesco', event = 'VeryLazy' },
    {
        'mhinz/vim-grepper',
        cmd = 'Grepper',
        keys = {
            { 'gog:', '<cmd>Grepper<CR>', desc = 'Grepper' },
            { 'gog', '<Plug>(GrepperOperator)', mode = { 'n', 'x' } },
        },
        config = function()
            vim.cmd('runtime plugin/grepper.vim')
            vim.g.grepper = { tools = { 'rg', 'git', 'grep' } }
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- UTILITIES                                                              {{{
    ---------------------------------------------------------------------------
    {
        'talek/obvious-resize',
        keys = {
            { '<Left>', '<cmd>ObviousResizeLeft<CR>', silent = true },
            { '<Down>', '<cmd>ObviousResizeDown<CR>', silent = true },
            { '<Up>', '<cmd>ObviousResizeUp<CR>', silent = true },
            { '<Right>', '<cmd>ObviousResizeRight<CR>', silent = true },
        },
    },
    { 'vim-scripts/cmdalias.vim', event = 'VeryLazy' },
    {
        'arecarn/Preserve.vim',
        cmd = { 'PreserveSave', 'PreserveRestore' },
        event = 'VeryLazy',
        config = function()
            vim.api.nvim_create_user_command('TrimTrail', 'PreserveSave|%s,\\s\\+$,,ge|PreserveRestore', { range = '%' })
            vim.api.nvim_create_user_command('TrimLead', 'PreserveSave|%s,^\\s\\+,,ge|PreserveRestore', { range = '%' })
            vim.keymap.set('n', 'd<Space>t', '<cmd>TrimTrail<CR>', { silent = true })
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- INTERACTIVE TOOLS                                                      {{{
    ---------------------------------------------------------------------------
    {
        'dhruvasagar/vim-table-mode',
        cmd = { 'TableModeToggle', 'TableModeEnable' },
        init = function()
            vim.g.table_mode_corner = '|'
            vim.g.table_mode_separator = '|'
        end,
    },
    { 'arecarn/vim-selection', lazy = true },
    {
        'arecarn/vim-crunch',
        dependencies = 'arecarn/vim-selection',
        cmd = 'Crunch',
        init = function()
            vim.g.crunch_user_variables = { e = math.exp(1), pi = math.pi }
            vim.g.crunch_result_type_append = 2
        end,
    },
    { 'chrisbra/NrrwRgn', cmd = { 'NR', 'NW', 'NRP', 'NRM' } },
    {
        'mbbill/undotree',
        cmd = 'UndotreeToggle',
        keys = { { 'gout', '<cmd>UndotreeToggle<CR><cmd>UndotreeFocus<CR>', desc = 'Undotree' } },
    },
    { 'arecarn/vim-binascii', cmd = { 'BinaryOn', 'BinaryOff', 'BinaryToggle' } },
    { 'arecarn/vim-frisk', cmd = 'Frisk' },

    ---------------------------------------------------------------------------}}}
    -- PROJECT MANAGEMENT                                                     {{{
    ---------------------------------------------------------------------------
    {
        'ludovicchabant/vim-gutentags',
        event = { 'BufReadPre', 'BufNewFile' },
        init = function()
            vim.g.gutentags_project_root = { '.project_root' }
            vim.g.gutentags_define_advanced_commands = 1
        end,
    },
    { 'liuchengxu/vista.vim', cmd = 'Vista' },
    { 'tpope/vim-projectionist', event = 'VeryLazy' },
}

-------------------------------------------------------------------------------}}}
-- SETUP LAZY.NVIM                                                            {{{
--------------------------------------------------------------------------------
require('lazy').setup(plugins, {
    defaults = {
        lazy = true,
    },
    install = {
        colorscheme = { 'apprentice' },
    },
    ui = {
        border = 'rounded',
    },
    performance = {
        rtp = {
            disabled_plugins = {
                'gzip',
                'matchit',
                'matchparen',
                'netrwPlugin',
                'tarPlugin',
                'tohtml',
                'tutor',
                'zipPlugin',
            },
        },
    },
})

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

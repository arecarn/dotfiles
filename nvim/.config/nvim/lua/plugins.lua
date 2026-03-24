-------------------------------------------------------------------------------}}}
-- PLUGINS (lazy.nvim)                                                        {{{
--------------------------------------------------------------------------------

-------------------------------------------------------------------------------}}}
-- BOOTSTRAP LAZY.NVIM                                                        {{{
--------------------------------------------------------------------------------
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
    vim.fn.system({
        "git",
        "clone",
        "--filter=blob:none",
        "https://github.com/folke/lazy.nvim.git",
        "--branch=stable",
        lazypath,
    })
end
vim.opt.rtp:prepend(lazypath)

-------------------------------------------------------------------------------}}}
-- PLUGIN SPECS                                                               {{{
--------------------------------------------------------------------------------
local plugins = {

    ---------------------------------------------------------------------------}}}
    -- MINI.NVIM (Modern Text Objects & Operators)                           {{{
    ---------------------------------------------------------------------------
    {
        "echasnovski/mini.nvim",
        version = false,
        event = "VeryLazy",
        config = function()
            -- Better Text Objects
            local ai = require("mini.ai")
            ai.setup({
                mappings = {
                    inside_last = "i.",
                    around_last = "a.",
                },
                custom_textobjects = {
                    -- Entire buffer
                    e = function()
                        local n_lines = vim.api.nvim_buf_line_count(0)
                        return {
                            from = { line = 1, col = 1 },
                            to = {
                                line = n_lines,
                                col = math.max(1, #vim.api.nvim_buf_get_lines(0, n_lines - 1, n_lines, false)[1]),
                            },
                        }
                    end,
                    -- Indent-based (simple implementation)
                    i = function()
                        local line = vim.fn.line(".")
                        local indent = vim.fn.indent(line)
                        local n_lines = vim.api.nvim_buf_line_count(0)
                        local start_line, end_line = line, line
                        while
                            start_line > 1
                            and (vim.fn.indent(start_line - 1) >= indent or #vim.fn.getline(start_line - 1) == 0)
                        do
                            start_line = start_line - 1
                        end
                        while
                            end_line < n_lines
                            and (vim.fn.indent(end_line + 1) >= indent or #vim.fn.getline(end_line + 1) == 0)
                        do
                            end_line = end_line + 1
                        end
                        return {
                            from = { line = start_line, col = 1 },
                            to = { line = end_line, col = #vim.fn.getline(end_line) },
                        }
                    end,
                    -- Line
                    l = function()
                        local line = vim.fn.line(".")
                        local len = #vim.fn.getline(line)
                        if len == 0 then return { from = { line = line, col = 1 } } end
                        return {
                            from = { line = line, col = 1 },
                            to = { line = line, col = len },
                        }
                    end,
                    -- Arguments/Parameters
                    a = ai.gen_spec.argument(),
                    -- Between (matches your old 'am/im' mappings for underscores)
                    m = ai.gen_spec.pair("_", "_", { type = "greedy" }),
                },
            })

            -- Surround (replaces vim-sandwich)
            require("mini.surround").setup({
                mappings = {
                    add = "sa",
                    delete = "sd",
                    find = "sf",
                    find_left = "sF",
                    highlight = "sh",
                    replace = "sr",
                    update_n_lines = "sn",
                },
            })

            -- Operators (replaces vim-operator-replace)
            require("mini.operators").setup({
                replace = { prefix = "_" }, -- matches your old '_' mapping
            })

            -- Move (replaces textmanip)
            require("mini.move").setup({
                mappings = {
                    left = "<C-h>",
                    right = "<C-l>",
                    down = "<C-j>",
                    up = "<C-k>",
                    line_left = "",
                    line_right = "",
                    line_down = "",
                    line_up = "",
                },
            })

            require("mini.cursorword").setup()

            -- Trailspace (replaces Preserve.vim trimming)
            require("mini.trailspace").setup()

            require("mini.splitjoin").setup()

            require("mini.align").setup()

            -- Comment (robust commenting)
            require("mini.comment").setup()

            -- Bracketed (replaces vim-unimpaired)
            require("mini.bracketed").setup({
                comment = { suffix = "/" },
            })

            -- Bufremove (clean buffer delete)
            require("mini.bufremove").setup()

            -- Map (global minimap)
            require("mini.map").setup()

            -- Animate (smooth scrolling and cursor)
            require("mini.animate").setup({
                -- Example: shorter times for faster, snappier animations
                cursor = { timing = require("mini.animate").gen_timing.linear({ duration = 1, unit = "step" }) },
                scroll = { timing = require("mini.animate").gen_timing.linear({ duration = 3, unit = "step" }) },
                resize = { timing = require("mini.animate").gen_timing.linear({ duration = 3, unit = "step" }) },
                open = { timing = require("mini.animate").gen_timing.linear({ duration = 3, unit = "step" }) },
                close = { timing = require("mini.animate").gen_timing.linear({ duration = 3, unit = "step" }) },
            })

            -- Hipatterns (highlight colors and patterns)
            local hipatterns = require("mini.hipatterns")
            hipatterns.setup({
                highlighters = {
                    hex_color = hipatterns.gen_highlighter.hex_color(),
                },
            })

            -- Clue (keybinding hints)
            local miniclue = require("mini.clue")
            miniclue.setup({
                triggers = {
                    -- Leader triggers
                    { mode = "n", keys = "<Leader>" },
                    { mode = "x", keys = "<Leader>" },

                    -- Built-in completion
                    { mode = "i", keys = "<C-x>" },

                    -- G keys
                    { mode = "n", keys = "g" },
                    { mode = "x", keys = "g" },

                    -- Marks
                    { mode = "n", keys = "'" },
                    { mode = "n", keys = "`" },
                    { mode = "x", keys = "'" },
                    { mode = "x", keys = "`" },

                    -- Registers
                    { mode = "n", keys = '"' },
                    { mode = "x", keys = '"' },
                    { mode = "i", keys = "<C-r>" },
                    { mode = "c", keys = "<C-r>" },

                    -- Window commands
                    { mode = "n", keys = "<C-w>" },

                    -- Z keys
                    { mode = "n", keys = "z" },
                    { mode = "x", keys = "z" },

                    -- Option toggles (unimpaired style)
                    { mode = "n", keys = "yo" },
                },

                clues = {
                    miniclue.gen_clues.builtin_completion(),
                    miniclue.gen_clues.g(),
                    miniclue.gen_clues.marks(),
                    miniclue.gen_clues.registers(),
                    miniclue.gen_clues.windows(),
                    miniclue.gen_clues.z(),
                    { mode = "n", keys = "yo", desc = "+toggles" },
                },
            })
        end,
    },
    {
        "gregorias/toggle.nvim",
        keys = { { "yo", desc = "Toggle Options" } },
        opts = {
            toggles = {
                { "s", "spell",          "Spell" },
                { "w", "wrap",           "Wrap" },
                { "n", "number",         "Number" },
                { "r", "relativenumber", "Relative Number" },
                { "l", "list",           "List" },
                { "h", "hlsearch",       "Search Highlight" },
                { "c", "cursorline",     "Cursor Line" },
                { "b", "scrollbind",     "Scroll Bind" },
                { "C", "cursorbind",     "Cursor Bind" },
                { "m", "modifiable",     "Modifiable" },
                { "R", "readonly",       "Read Only" },
            },
        },
    },
    { "tpope/vim-repeat",         event = "VeryLazy" },
    { "vim-scripts/visualrepeat", event = "VeryLazy" },

    ---------------------------------------------------------------------------}}}
    -- FUZZY FINDING                                                          {{{
    ---------------------------------------------------------------------------
    {
        "ibhagwan/fzf-lua",
        cmd = "FzfLua",
        keys = {
            { "z=",  "<cmd>FzfLua spell_suggest<CR>", desc = "Spell suggest" },
            { "gof", "<cmd>FzfLua files<CR>",         desc = "Find files" },
            { "gos", "<cmd>FzfLua live_grep<CR>",     desc = "Live grep" },
            { "gor", "<cmd>FzfLua oldfiles<CR>",      desc = "Recent files" },
        },
        opts = {
            keymap = {
                fzf = {
                    ["ctrl-n"] = "down",
                    ["ctrl-p"] = "up",
                    ["ctrl-a"] = "beginning-of-line",
                    ["ctrl-e"] = "end-of-line",
                    ["ctrl-f"] = "forward-char",
                    ["ctrl-b"] = "backward-char",
                    ["ctrl-d"] = "delete-char",
                },
            },
            fzf_opts = { ["--layout"] = "reverse" },
        },
        config = function(_, opts)
            require("fzf-lua").setup(opts)
            require("fzf-lua").register_ui_select()
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- FOLDS                                                                  {{{
    ---------------------------------------------------------------------------
    {
        "arecarn/vim-clean-fold",
        event = "VeryLazy",
        config = function()
            vim.opt.foldmethod = "expr"
            vim.opt.foldtext = "clean_fold#fold_text_minimal()"
            vim.opt.foldexpr = "clean_fold#fold_expr(v:lnum)"
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- VISUAL ENHANCEMENTS                                                    {{{
    ---------------------------------------------------------------------------
    {
        "folke/snacks.nvim",
        priority = 1000,
        lazy = false,
        config = function()
            require("snacks").setup({
                bigfile = { enabled = true },
                dashboard = { enabled = true },
                input = { enabled = true },
                indent = { enabled = true },
                notifier = { enabled = true },
                quickfile = { enabled = true },
                statuscolumn = { enabled = true },
                terminal = { enabled = true },
            })
            vim.api.nvim_create_user_command("Notifications", function()
                Snacks.notifier.show_history()
            end, {})
            vim.keymap.set("n", "<leader>st", function()
                Snacks.terminal()
            end, { desc = "Toggle Terminal" })
            vim.keymap.set("n", "coig", function()
                if Snacks.indent.enabled then
                    Snacks.indent.disable()
                else
                    Snacks.indent.enable()
                end
            end, { silent = true })
        end,
    },
    {
        "nvim-lualine/lualine.nvim",
        dependencies = { "nvim-tree/nvim-web-devicons" },
        lazy = false,
        config = function()
            local statusline = require("config.statusline")
            require("lualine").setup({
                options = {
                    theme = "auto",
                    component_separators = { left = "|", right = "|" },
                    section_separators = { left = "", right = "" },
                    globalstatus = true,
                },
                sections = {
                    lualine_a = { "mode" },
                    lualine_b = {
                        { "location" },
                        { "progress" },
                    },
                    lualine_c = {
                        {
                            function()
                                return statusline.fileformat()
                            end,
                        },
                        {
                            function()
                                return statusline.fileencoding()
                            end,
                        },
                        {
                            function()
                                return statusline.filetype()
                            end,
                        },
                    },
                    lualine_x = {
                        {
                            function()
                                return statusline.fugitive()
                            end,
                        },
                    },
                    lualine_y = {
                        {
                            function()
                                return statusline.filename()
                            end,
                        },
                    },
                    lualine_z = {
                        {
                            function()
                                return statusline.bufnr()
                            end,
                        },
                        {
                            function()
                                return "w:" .. statusline.winnr()
                            end,
                        },
                    },
                },
                inactive_sections = {
                    lualine_a = {},
                    lualine_b = {},
                    lualine_c = {
                        {
                            function()
                                return statusline.filename()
                            end,
                        },
                    },
                    lualine_x = { { "location" } },
                    lualine_y = {},
                    lualine_z = {},
                },
            })
        end,
    },
    { "chreekat/vim-paren-crosshairs", event = "VeryLazy" },
    {
        "junegunn/goyo.vim",
        cmd = "Goyo",
        keys = {
            {
                "yof",
                function()
                    local count = vim.v.count
                    if count == 0 then
                        vim.cmd("Goyo")
                    else
                        vim.cmd("Goyo " .. count)
                    end
                end,
                desc = "Toggle Goyo",
            },
        },
        init = function()
            local signcolumn_width = vim.o.signcolumn ~= "no" and 2 or 0
            vim.g.goyo_width = 80 + signcolumn_width + vim.o.foldcolumn
        end,
    },
    {
        "nvim-treesitter/nvim-treesitter",
        build = ":TSUpdate",
        event = { "BufReadPost", "BufNewFile" },
        config = function()
            require("nvim-treesitter").setup({
                ensure_installed = {
                    "bash",
                    "c",
                    "cpp",
                    "cmake",
                    "dockerfile",
                    "json",
                    "lua",
                    "make",
                    "markdown",
                    "markdown_inline",
                    "python",
                    "vim",
                    "vimdoc",
                    "yaml",
                },
            })
        end,
    },
    {
        "edkolev/tmuxline.vim",
        cond = vim.fn.has("win32") == 0 and vim.fn.has("win64") == 0,
        event = "VeryLazy",
        init = function()
            vim.g.tmuxline_powerline_separators = 0
            vim.g.tmuxline_separators = {
                left = "",
                left_alt = "|",
                right = "",
                right_alt = "|",
                space = " ",
            }
        end,
        config = function()
            if vim.env.TMUX == nil then
                return
            end
            local snapshot = vim.fn.expand("~/.cache/tmux/statusline.conf")
            if vim.fn.filereadable(snapshot) == 0 then
                vim.cmd("Tmuxline")
                vim.cmd("TmuxlineSnapshot! " .. snapshot)
            end
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- TASK RUNNER                                                            {{{
    ---------------------------------------------------------------------------
    {
        "stevearc/overseer.nvim",
        cmd = { "OverseerRun", "OverseerToggle", "OverseerOpen", "Make" },
        keys = {
            { "m<Space>",   ":Make<Space>",            desc = "Make" },
            { "<leader>oo", "<cmd>OverseerOpen<CR>",   desc = "Overseer open" },
            { "<leader>ot", "<cmd>OverseerToggle<CR>", desc = "Overseer toggle" },
        },
        config = function()
            require("overseer").setup()

            local function get_makefile_targets()
                local targets = {}
                local makefile = nil

                -- Check in same order as GNU make
                for _, name in ipairs({ "GNUmakefile", "makefile", "Makefile" }) do
                    if vim.fn.filereadable(name) == 1 then
                        makefile = name
                        break
                    end
                end

                if not makefile then
                    return targets
                end

                for line in io.lines(makefile) do
                    local target = line:match("^([%w%-_%.]+):")
                    if target and target ~= ".PHONY" then
                        table.insert(targets, target)
                    end
                end
                return targets
            end

            vim.api.nvim_create_user_command("Make", function(params)
                local cmd, num_subs = vim.o.makeprg:gsub("%%$%%*", params.args)
                if num_subs == 0 then
                    cmd = cmd .. " " .. params.args
                end
                local task = require("overseer").new_task({
                    cmd = vim.fn.expandcmd(cmd),
                    components = {
                        { "open_output",        direction = "dock", on_start = "always", on_complete = "never" },
                        { "on_output_quickfix", open = false },
                        { "unique",             replace = true },
                        "default",
                    },
                })
                task:subscribe("on_complete", function()
                    vim.cmd("copen")
                    vim.cmd("OverseerClose")
                end)
                task:start()
            end, {
                desc = "Run your makeprg as an Overseer task",
                nargs = "*",
                bang = true,
                complete = function(ArgLead)
                    local targets = get_makefile_targets()
                    return vim.tbl_filter(function(v)
                        return v:find(ArgLead, 1, true) == 1
                    end, targets)
                end,
            })
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- FILE TYPE + SYNTAX                                                     {{{
    ---------------------------------------------------------------------------
    { "stephpy/vim-yaml",              ft = "yaml" },
    {
        "tpope/vim-markdown",
        ft = "markdown",
        init = function()
            vim.g.markdown_fenced_languages = { "python", "c", "cpp", "bash=sh" }
            vim.g.markdown_syntax_conceal = 0
            vim.g.markdown_folding = 1
        end,
    },
    {
        "iamcco/markdown-preview.nvim",
        build = function()
            vim.fn["mkdp#util#install"]()
        end,
        ft = "markdown",
        init = function()
            vim.g.mkdp_auto_close = 0
            vim.g.mkdp_echo_preview_url = 1
            vim.g.mkdp_port = "6419"
            vim.g.mkdp_preview_options = {
                mkit = {},
                katex = {},
                uml = {},
                maid = {},
                disable_sync_scroll = 1,
                sync_scroll_type = "middle",
                hide_yaml_meta = 1,
                sequence_diagrams = {},
                flowchart_diagrams = {},
                content_editable = false,
            }
        end,
    },
    { "jkramer/vim-checkbox", ft = "markdown" },
    {
        "MeanderingProgrammer/render-markdown.nvim",
        dependencies = { "nvim-treesitter/nvim-treesitter", "nvim-tree/nvim-web-devicons" },
        ft = { "markdown", "agentic", "AgenticChat" },
        opts = {
            file_types = { "markdown", "agentic", "AgenticChat" },
        },
    },
    { "aklt/plantuml-syntax", ft = "plantuml" },
    {
        "kevinhwang91/nvim-bqf",
        ft = "qf",
        config = function()
            vim.cmd([[
                hi BqfPreviewBorder guifg=#3e8e2d ctermfg=71
                hi BqfPreviewTitle guifg=#3e8e2d ctermfg=71
                hi BqfPreviewThumb guibg=#3e8e2d ctermbg=71
                hi link BqfPreviewRange Search
            ]])
            require("bqf").setup({
                auto_enable = true,
                auto_resize_height = true,
                preview = {
                    win_height = 12,
                    win_vheight = 12,
                    delay_syntax = 80,
                    border = { "┏", "━", "┓", "┃", "┛", "━", "┗", "┃" },
                    show_title = false,
                    should_preview_cb = function(bufnr)
                        local bufname = vim.api.nvim_buf_get_name(bufnr)
                        local fsize = vim.fn.getfsize(bufname)
                        if fsize > 100 * 1024 then
                            return false
                        end
                        if bufname:match("^fugitive://") then
                            return false
                        end
                        return true
                    end,
                },
                func_map = {
                    drop = "o",
                    openc = "O",
                    split = "<C-s>",
                    tabdrop = "<C-t>",
                    tabc = "",
                    ptogglemode = "z,",
                },
                filter = {
                    fzf = {
                        action_for = { ["ctrl-s"] = "split", ["ctrl-t"] = "tab drop" },
                        extra_opts = { "--bind", "ctrl-o:toggle-all", "--delimiter", "│" },
                    },
                },
            })
        end,
    },
    { "octol/vim-cpp-enhanced-highlight", ft = { "c", "cpp" } },
    { "hynek/vim-python-pep8-indent",     ft = "python" },
    {
        "Shougo/Deol.nvim",
        cmd = "Deol",
        init = function()
            vim.g["deol#prompt_pattern"] = ".\\{-} \\d\\d:\\d\\d:\\d\\d %"
        end,
    },
    {
        "elzr/vim-json",
        ft = "json",
        init = function()
            vim.g.vim_json_syntax_conceal = 0
        end,
    },
    {
        "chrisbra/csv.vim",
        ft = "csv",
        config = function()
            vim.api.nvim_create_autocmd("CursorHold", {
                pattern = "*.csv",
                command = "WhatColumn!",
            })
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- COLORS                                                                 {{{
    ---------------------------------------------------------------------------
    { "rktjmp/lush.nvim",      lazy = false },
    {
        "adisen99/apprentice.nvim",
        lazy = false,
        priority = 1000,
        dependencies = "rktjmp/lush.nvim",
        config = function()
            vim.g.colors_name = "apprentice"
            require("lush")(require("apprentice").setup({
                plugins = {
                    "buftabline",
                    "gitsigns",
                    "lsp",
                    "lspsaga",
                    "treesitter",
                },
                langs = {
                    "c",
                    "clojure",
                    "coffeescript",
                    "csharp",
                    "css",
                    "elixir",
                    "golang",
                    "haskell",
                    "html",
                    "java",
                    "js",
                    "json",
                    "jsx",
                    "lua",
                    "markdown",
                    "moonscript",
                    "objc",
                    "ocaml",
                    "purescript",
                    "python",
                    "ruby",
                    "rust",
                    "scala",
                    "typescript",
                    "viml",
                    "xml",
                },
            }))
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- AI
    ---------------------------------------------------------------------------
    {
        "carlos-algms/agentic.nvim",

        opts = function()
            local provider = "gemini-acp"
            if vim.fn.executable("claude") == 1 then
                provider = "claude-agent-acp"
            end
            return {
                provider = provider,
                spinner_chars = {
                    thinking = { "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏" },
                },
            }
        end,
        -- these are just suggested keymaps; customize as desired
        keys = {
            {
                "<leader>at",
                function()
                    require("agentic").toggle()
                end,
                mode = { "n" },
                desc = "Toggle Agentic Chat",
            },
            {
                "<leader>av",
                function()
                    require("agentic").add_selection_or_file_to_context()
                end,
                mode = { "n", "v" },
                desc = "Add file or selection to Agentic to Context",
            },
            {
                "<leader>an",
                function()
                    require("agentic").new_session()
                end,
                mode = { "n" },
                desc = "New Agentic Session",
            },
            {
                "<leader>ar", -- ai Restore
                function()
                    require("agentic").restore_session()
                end,
                desc = "Agentic Restore session",
                silent = true,
                mode = { "n" },
            },
            {
                "<leader>ad", -- ai Diagnostics
                function()
                    require("agentic").add_current_line_diagnostics()
                end,
                desc = "Add current line diagnostic to Agentic",
                mode = { "n" },
            },
            {
                "<leader>aD", -- ai all Diagnostics
                function()
                    require("agentic").add_buffer_diagnostics()
                end,
                desc = "Add all buffer diagnostics to Agentic",
                mode = { "n" },
            },
        },
    },

    ---------------------------------------------------------------------------}}}
    -- LSP & COMPLETION                                                       {{{
    ---------------------------------------------------------------------------
    {
        "williamboman/mason.nvim",
        cmd = "Mason",
        build = ":MasonUpdate",
        config = function()
            require("mason").setup()
        end,
    },
    {
        "WhoIsSethDaniel/mason-tool-installer.nvim",
        dependencies = { "williamboman/mason.nvim" },
        config = function()
            require("mason-tool-installer").setup({
                ensure_installed = {
                    "selene",
                    "stylua",
                    "shellcheck",
                    "shfmt",
                },
                auto_install = true,
            })
        end,
    },
    {
        "williamboman/mason-lspconfig.nvim",
        event = { "BufReadPre", "BufNewFile" },
        dependencies = { "williamboman/mason.nvim", "neovim/nvim-lspconfig" },
        config = function()
            require("mason-lspconfig").setup({
                ensure_installed = {
                    "yamlls",
                    "bashls",
                    "clangd",
                    "cmake",
                    "pyright",
                    "vimls",
                    "prosemd_lsp",
                    "lua_ls",
                },
            })

            -----------------------------------------------------------------
            -- LSP Server Configurations (Neovim 0.11+ native API)
            -----------------------------------------------------------------
            vim.lsp.config.yamlls = {
                cmd = { "yaml-language-server", "--stdio" },
                filetypes = { "yaml", "yaml.docker-compose", "yaml.gitlab" },
                root_markers = { ".git" },
                settings = { yaml = { completion = { enable = true } } },
            }

            vim.lsp.config.bashls = {
                cmd = { "bash-language-server", "start" },
                filetypes = { "sh", "bash" },
                root_markers = { ".git" },
            }

            vim.lsp.config.cmake = {
                cmd = { "cmake-language-server" },
                filetypes = { "cmake" },
                root_markers = { "CMakeLists.txt", ".git" },
            }

            vim.lsp.config.pyright = {
                cmd = { "pyright-langserver", "--stdio" },
                filetypes = { "python" },
                root_markers = { "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", ".git" },
            }

            vim.lsp.config.vimls = {
                cmd = { "vim-language-server", "--stdio" },
                filetypes = { "vim" },
                root_markers = { ".git" },
            }

            vim.lsp.config.prosemd_lsp = {
                cmd = { "prosemd-lsp", "--stdio" },
                filetypes = { "markdown" },
                root_markers = { ".git" },
            }

            vim.lsp.config.clangd = {
                cmd = { "clangd" },
                filetypes = { "c", "cpp", "objc", "objcpp", "cuda", "proto" },
                root_markers = { "compile_commands.json", "compile_flags.txt", ".git" },
            }

            vim.lsp.config.lua_ls = {
                cmd = { "lua-language-server" },
                filetypes = { "lua" },
                root_markers = { ".git", "init.lua" },
                settings = {
                    Lua = {
                        runtime = { version = "LuaJIT" },
                        diagnostics = { globals = { "vim" } },
                        workspace = {
                            library = vim.api.nvim_get_runtime_file("", true),
                            checkThirdParty = false,
                        },
                        telemetry = { enabled = false },
                    },
                },
            }

            -- Enable all LSP servers
            vim.lsp.enable("yamlls")
            vim.lsp.enable("bashls")
            vim.lsp.enable("cmake")
            vim.lsp.enable("pyright")
            vim.lsp.enable("vimls")
            vim.lsp.enable("prosemd_lsp")
            vim.lsp.enable("clangd")
            vim.lsp.enable("lua_ls")

            -----------------------------------------------------------------
            -- Clangd-specific keymap
            -----------------------------------------------------------------
            vim.api.nvim_create_autocmd("FileType", {
                pattern = { "c", "cpp" },
                callback = function()
                    vim.keymap.set(
                        "n",
                        "<leader>of",
                        "<Cmd>ClangdSwitchSourceHeader<CR>",
                        { buffer = true, desc = "Switch source/header" }
                    )
                end,
                group = vim.api.nvim_create_augroup("clangd_mappings", { clear = true }),
            })

            -----------------------------------------------------------------
            -- Diagnostic configuration
            -----------------------------------------------------------------
            local signs = { Error = " ", Warn = " ", Hint = " ", Info = " " }
            for type, icon in pairs(signs) do
                local hl = "DiagnosticSign" .. type
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
                    style = "minimal",
                    border = "rounded",
                    source = true,
                    header = "",
                    prefix = "",
                },
            })

            -----------------------------------------------------------------
            -- Diagnostic float on CursorHold
            -----------------------------------------------------------------
            local function open_diagnostic_if_no_float()
                for _, winid in pairs(vim.api.nvim_tabpage_list_wins(0)) do
                    if vim.api.nvim_win_get_config(winid).zindex then
                        return
                    end
                end
                vim.diagnostic.open_float({
                    scope = "line",
                    focusable = false,
                    close_events = { "CursorMoved", "CursorMovedI", "BufHidden", "InsertCharPre", "WinLeave" },
                })
            end

            vim.api.nvim_create_augroup("lsp_diagnostics_hold", { clear = true })
            vim.api.nvim_create_autocmd("CursorHold", {
                pattern = "*",
                callback = open_diagnostic_if_no_float,
                group = "lsp_diagnostics_hold",
            })

            -----------------------------------------------------------------
            -- Global diagnostic keymaps
            -----------------------------------------------------------------
            vim.keymap.set("n", "<leader>e", vim.diagnostic.open_float)
            vim.keymap.set("n", "[d", vim.diagnostic.goto_prev)
            vim.keymap.set("n", "]d", vim.diagnostic.goto_next)
            vim.keymap.set("n", "<leader>q", vim.diagnostic.setloclist)

            -----------------------------------------------------------------
            -- LSP Attach keymaps
            -----------------------------------------------------------------
            vim.api.nvim_create_autocmd("LspAttach", {
                group = vim.api.nvim_create_augroup("UserLspConfig", {}),
                callback = function(ev)
                    vim.lsp.handlers["textDocument/hover"] =
                        vim.lsp.with(vim.lsp.handlers.hover, { border = "rounded" })
                    vim.lsp.handlers["textDocument/signatureHelp"] =
                        vim.lsp.with(vim.lsp.handlers.signature_help, { border = "rounded" })

                    local opts = { buffer = ev.buf }
                    vim.keymap.set("n", "gld", vim.lsp.buf.declaration, opts)
                    vim.keymap.set("n", "glD", vim.lsp.buf.definition, opts)
                    vim.keymap.set("n", "glt", vim.lsp.buf.type_definition, opts)
                    vim.keymap.set("n", "gl?", vim.lsp.buf.hover, opts)
                    vim.keymap.set("n", "gl??", vim.lsp.buf.signature_help, opts)
                    vim.keymap.set("n", "gli", vim.lsp.buf.implementation, opts)
                    vim.keymap.set("n", "glr", vim.lsp.buf.references, opts)
                    vim.keymap.set("n", "gls", vim.lsp.buf.rename, opts)
                    vim.keymap.set({ "n", "v" }, "gla", vim.lsp.buf.code_action, opts)
                    vim.keymap.set("n", "glf", function()
                        vim.lsp.buf.format({ async = true })
                    end, opts)
                    vim.keymap.set("n", "glwa", vim.lsp.buf.add_workspace_folder, opts)
                    vim.keymap.set("n", "glwr", vim.lsp.buf.remove_workspace_folder, opts)
                    vim.keymap.set("n", "glwl", function()
                        print(vim.inspect(vim.lsp.buf.list_workspace_folders()))
                    end, opts)
                end,
            })
        end,
    },
    {
        "mfussenegger/nvim-lint",
        event = { "BufReadPost", "BufNewFile" },
        config = function()
            local lint = require("lint")
            lint.linters.selene.args = {
                "--display-style", "quiet",
                "--config", vim.fn.stdpath("config") .. "/selene.toml",
                "-",
            }
            lint.linters_by_ft = {
                lua = { "selene" },
                sh = { "shellcheck" },
            }

            vim.api.nvim_create_autocmd({ "BufWritePost", "BufEnter" }, {
                group = vim.api.nvim_create_augroup("lint", { clear = true }),
                callback = function()
                    lint.try_lint()
                end,
            })
        end,
    },
    {
        "stevearc/conform.nvim",
        event = { "BufWritePre" },
        cmd = { "ConformInfo" },
        keys = {
            {
                "glf",
                function()
                    require("conform").format({ async = true, lsp_fallback = true })
                end,
                mode = "",
                desc = "Format buffer",
            },
        },
        opts = {
            formatters_by_ft = {
                lua = { "stylua" },
                sh = { "shfmt" },
            },
            format_on_save = {
                timeout_ms = 500,
                lsp_fallback = true,
            },
        },
    },
    {
        "folke/trouble.nvim",
        opts = {}, -- for default options, refer to the configuration section for custom setup.
        cmd = "Trouble",
        keys = {
            {
                "<leader>xx",
                "<cmd>Trouble diagnostics toggle<cr>",
                desc = "Diagnostics (Trouble)",
            },
            {
                "<leader>xX",
                "<cmd>Trouble diagnostics toggle filter.buf=0<cr>",
                desc = "Buffer Diagnostics (Trouble)",
            },
            {
                "<leader>cs",
                "<cmd>Trouble symbols toggle focus=false<cr>",
                desc = "Symbols (Trouble)",
            },
            {
                "<leader>cl",
                "<cmd>Trouble lsp toggle focus=false win.position=right<cr>",
                desc = "LSP Definitions / references / ... (Trouble)",
            },
            {
                "<leader>xL",
                "<cmd>Trouble loclist toggle<cr>",
                desc = "Location List (Trouble)",
            },
            {
                "<leader>xQ",
                "<cmd>Trouble qflist toggle<cr>",
                desc = "Quickfix List (Trouble)",
            },
        },
    },
    { "neovim/nvim-lspconfig", lazy = true },
    { "mfussenegger/nvim-dap", lazy = true },
    {
        "jay-babu/mason-nvim-dap.nvim",
        dependencies = { "williamboman/mason.nvim", "mfussenegger/nvim-dap" },
        lazy = true,
    },
    { "rcarriga/nvim-dap-ui", dependencies = { "mfussenegger/nvim-dap", "nvim-neotest/nvim-nio" }, lazy = true },
    {
        "saghen/blink.cmp",
        version = "1.*",
        event = { "InsertEnter", "CmdlineEnter" },
        ---@module 'blink.cmp'
        ---@type blink.cmp.Config
        opts = {
            keymap = {
                ["<C-b>"] = { "scroll_documentation_up" },
                ["<C-f>"] = { "scroll_documentation_down" },
                ["<C-n>"] = { "show", "select_next", "fallback" },
                ["<C-p>"] = { "show", "select_prev", "fallback" },
                ["<C-e>"] = { "cancel" },
                ["<C-y>"] = { "accept", "fallback" },
            },
            completion = {
                documentation = { auto_show = true, window = { border = "rounded" } },
                menu = { border = "rounded" },
            },
            sources = {
                default = { "lsp", "snippets", "buffer", "path" },
            },
            cmdline = {
                enabled = true,
                keymap = {
                    ["<C-n>"] = { "show", "select_next", "fallback" },
                    ["<C-p>"] = { "show", "select_prev", "fallback" },
                    ["<C-e>"] = { "cancel" },
                    ["<C-y>"] = { "accept", "fallback" },
                },
            },
            fuzzy = { implementation = "prefer_rust_with_warning" },
        },
    },

    ---------------------------------------------------------------------------}}}
    -- GIT / VCS                                                              {{{
    ---------------------------------------------------------------------------
    {
        "tpope/vim-fugitive",
        cmd = { "Git", "G", "Gdiffsplit", "Gread", "Gwrite", "Ggrep", "GMove", "GDelete", "GBrowse" },
        keys = {
            { "<leader>gs",  "<cmd>Git<CR>",               desc = "Git status" },
            { "<leader>gd",  "<cmd>Gdiffsplit<CR>",        desc = "Git diff" },
            { "<leader>gd1", "<cmd>Gdiffsplit HEAD~1<CR>", desc = "Git diff HEAD~1" },
            { "<leader>gd2", "<cmd>Gdiffsplit HEAD~2<CR>", desc = "Git diff HEAD~2" },
        },
    },
    { "lambdalisue/gina.vim", cmd = "Gina" },
    { "jreybert/vimagit",     cmd = "Magit" },
    {
        "airblade/vim-rooter",
        event = "VeryLazy",
        init = function()
            vim.g.rooter_manual_only = 1
        end,
    },
    { "cohama/agit.vim",             cmd = { "Agit", "AgitFile" } },
    {
        "lewis6991/gitsigns.nvim",
        event = { "BufReadPre", "BufNewFile" },
        opts = {
            on_attach = function(bufnr)
                local gs = require("gitsigns")
                local map = function(mode, l, r, desc)
                    vim.keymap.set(mode, l, r, { buffer = bufnr, desc = desc })
                end
                map("n", "]c", function()
                    if vim.wo.diff then return "]c" end
                    vim.schedule(gs.next_hunk)
                    return "<Ignore>"
                end, "Next hunk")
                map("n", "[c", function()
                    if vim.wo.diff then return "[c" end
                    vim.schedule(gs.prev_hunk)
                    return "<Ignore>"
                end, "Prev hunk")
                map("n", "<leader>hs", gs.stage_hunk, "Stage hunk")
                map("n", "<leader>hr", gs.reset_hunk, "Reset hunk")
                map("n", "<leader>hp", gs.preview_hunk, "Preview hunk")
                map("n", "<leader>hb", gs.toggle_current_line_blame, "Toggle line blame")
                map({ "o", "x" }, "ih", gs.select_hunk, "Hunk text object")
            end,
        },
    },

    ---------------------------------------------------------------------------}}}
    -- DIFF                                                                   {{{
    ---------------------------------------------------------------------------
    {
        "AndrewRadev/linediff.vim",
        cmd = "Linediff",
        keys = { { "<leader>lnd", ":Linediff<CR>", mode = "x", desc = "Line diff" } },
    },
    { "vim-scripts/diffchanges.vim", cmd = "DiffChangesDiffToggle" },
    { "arecarn/vim-diff-utils",      branch = "visual_mapping",    event = "VeryLazy" },
    {
        "chrisbra/vim-diff-enhanced",
        event = "VeryLazy",
        config = function()
            vim.o.diffexpr = 'EnhancedDiff#Diff("git diff", "--diff-algorithm=patience")'
        end,
    },
    { "will133/vim-dirdiff",         cmd = "DirDiff" },

    ---------------------------------------------------------------------------}}}
    -- FILE EXPLORER                                                          {{{
    ---------------------------------------------------------------------------
    {
        "lambdalisue/fern.vim",
        dependencies = "lambdalisue/fern-hijack.vim",
        cmd = "Fern",
        keys = { { "-", "<cmd>Fern %:p:h<CR>", desc = "Open Fern" } },
        init = function()
            vim.g["fern#default_hidden"] = 1
        end,
        config = function()
            local function init_fern()
                local opts = { buffer = true }
                vim.keymap.set("n", "<BS>", "<Plug>(fern-action-collapse)", opts)
                vim.keymap.set("n", "<CR>", "<Plug>(fern-action-open-or-expand)", opts)
                vim.keymap.set("n", "h", "<Plug>(fern-action-leave)", opts)
                vim.keymap.set("n", "l", "<Plug>(fern-action-open-or-enter)", opts)
                vim.keymap.set("n", "H", "<Plug>(fern-action-hidden)", opts)
                vim.keymap.set("n", "<F1>", "<Plug>(fern-action-help:all)", opts)
            end
            vim.api.nvim_create_autocmd("FileType", {
                pattern = "fern",
                callback = init_fern,
            })
            vim.api.nvim_create_autocmd("User", {
                pattern = "FernHighlight",
                callback = function()
                    vim.cmd("highlight link FernRootSymbol Title")
                    vim.cmd("highlight link FernRootText Title")
                end,
            })
        end,
    },
    { "lambdalisue/fern-hijack.vim", lazy = true },

    ---------------------------------------------------------------------------}}}
    -- TEXT MANIPULATION                                                      {{{
    ---------------------------------------------------------------------------
    -- {
    --     'godlygeek/tabular',
    --     cmd = 'Tabularize',
    --     keys = {
    --         { '<leader>t', ':Tabularize/', mode = { 'n', 'x' }, desc = 'Tabularize' },
    --     },
    -- },
    { "arecarn/vim-split-join",      cmd = { "Split", "Join" } },
    { "vim-scripts/ingo-library",    lazy = true },
    {
        "vim-scripts/FormatToWidth",
        dependencies = "vim-scripts/ingo-library",
        keys = { { "gQ", "<Plug>FormatToWidth", mode = "x" } },
    },

    ---------------------------------------------------------------------------}}}
    -- ENHANCEMENTS                                                           {{{
    ---------------------------------------------------------------------------
    { "kana/vim-niceblock",             event = "VeryLazy" },
    { "tpope/vim-speeddating",          keys = { "<C-a>", "<C-x>" } },
    -- { 'tpope/vim-unimpaired', event = 'VeryLazy' },
    { "vim-scripts/UnconditionalPaste", event = "VeryLazy" },
    { "arecarn/vim-auto-autoread",      event = "VeryLazy" },
    {
        "arecarn/vim-backup-tree",
        event = "VeryLazy",
        config = function()
            local data_path = vim.fn.stdpath("data")
            vim.fn.mkdir(data_path .. "/backup", "p")
            vim.g.backup_tree = data_path .. "/backup"
        end,
    },
    { "thinca/vim-qfreplace",    cmd = "Qfreplace" },
    { "tpope/vim-eunuch",        cmd = { "Delete", "Unlink", "Move", "Rename", "Chmod", "Mkdir", "SudoWrite", "SudoEdit" } },
    { "arecarn/vim-spell-utils", event = "VeryLazy" },
    { "tpope/vim-abolish",       cmd = { "Abolish", "Subvert" },                                                           keys = { "cr" } },
    {
        "mg979/vim-visual-multi",
        event = "VeryLazy",
        init = function()
            vim.g.VM_mouse_mappings = 1
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- WORD HIGHLIGHTING                                                      {{{
    ---------------------------------------------------------------------------
    {
        "t9md/vim-quickhl",
        keys = {
            { "gm",  "<Plug>(quickhl-manual-this)",  mode = { "n", "x" } },
            { "gmx", "<Plug>(quickhl-manual-reset)", mode = { "n", "x" } },
        },
    },
    -- {
    --     'dominikduda/vim_current_word',
    --     event = 'VeryLazy',
    --     init = function() vim.g['vim_current_word#highlight_current_word'] = 0 end,
    -- },

    ---------------------------------------------------------------------------}}}
    -- SEARCH                                                                 {{{
    ---------------------------------------------------------------------------
    { "pgdouyon/vim-evanesco",    event = "VeryLazy" },
    {
        "mhinz/vim-grepper",
        cmd = "Grepper",
        keys = {
            { "gog:", "<cmd>Grepper<CR>",        desc = "Grepper" },
            { "gog",  "<Plug>(GrepperOperator)", mode = { "n", "x" } },
        },
        config = function()
            vim.cmd("runtime plugin/grepper.vim")
            vim.g.grepper = { tools = { "rg", "git", "grep" } }
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- UTILITIES                                                              {{{
    ---------------------------------------------------------------------------
    {
        "talek/obvious-resize",
        keys = {
            { "<Left>",  "<cmd>ObviousResizeLeft<CR>",  silent = true },
            { "<Down>",  "<cmd>ObviousResizeDown<CR>",  silent = true },
            { "<Up>",    "<cmd>ObviousResizeUp<CR>",    silent = true },
            { "<Right>", "<cmd>ObviousResizeRight<CR>", silent = true },
        },
    },
    { "vim-scripts/cmdalias.vim", event = "VeryLazy" },
    {
        "arecarn/Preserve.vim",
        cmd = { "PreserveSave", "PreserveRestore" },
        event = "VeryLazy",
        config = function()
            vim.api.nvim_create_user_command(
                "TrimTrail",
                "PreserveSave|%s,\\s\\+$,,ge|PreserveRestore",
                { range = "%" }
            )
            vim.api.nvim_create_user_command("TrimLead", "PreserveSave|%s,^\\s\\+,,ge|PreserveRestore", { range = "%" })
            vim.keymap.set("n", "d<Space>t", "<cmd>TrimTrail<CR>", { silent = true })
        end,
    },

    ---------------------------------------------------------------------------}}}
    -- INTERACTIVE TOOLS                                                      {{{
    ---------------------------------------------------------------------------
    {
        "dhruvasagar/vim-table-mode",
        cmd = { "TableModeToggle", "TableModeEnable" },
        init = function()
            vim.g.table_mode_corner = "|"
            vim.g.table_mode_separator = "|"
        end,
    },
    { "arecarn/vim-selection", lazy = true },
    {
        "arecarn/vim-crunch",
        dependencies = "arecarn/vim-selection",
        cmd = "Crunch",
        init = function()
            vim.g.crunch_user_variables = { e = math.exp(1), pi = math.pi }
            vim.g.crunch_result_type_append = 2
        end,
    },
    { "chrisbra/NrrwRgn",      cmd = { "NR", "NW", "NRP", "NRM" } },
    {
        "mbbill/undotree",
        cmd = "UndotreeToggle",
        keys = { { "gout", "<cmd>UndotreeToggle<CR><cmd>UndotreeFocus<CR>", desc = "Undotree" } },
    },
    { "arecarn/vim-binascii", cmd = { "BinaryOn", "BinaryOff", "BinaryToggle" } },
    { "arecarn/vim-frisk",    cmd = "Frisk" },

    ---------------------------------------------------------------------------}}}
    -- PROJECT MANAGEMENT                                                     {{{
    ---------------------------------------------------------------------------
    -- {
    --  "ludovicchabant/vim-gutentags",
    --  event = { "BufReadPre", "BufNewFile" },
    --  init = function()
    --      vim.g.gutentags_project_root = { ".project_root" }
    --      vim.g.gutentags_define_advanced_commands = 1
    --  end,
    -- },
    {
        "linrongbin16/gentags.nvim",
        config = function()
            require("gentags").setup()
        end,
    },
    { "liuchengxu/vista.vim",    cmd = "Vista" },
    { "tpope/vim-projectionist", event = "VeryLazy" },
}

-------------------------------------------------------------------------------}}}
-- SETUP LAZY.NVIM                                                            {{{
--------------------------------------------------------------------------------
require("lazy").setup(plugins, {
    defaults = {
        lazy = true,
    },
    install = {
        colorscheme = { "apprentice" },
    },
    ui = {
        border = "rounded",
    },
    performance = {
        rtp = {
            disabled_plugins = {
                "gzip",
                "matchit",
                "matchparen",
                "netrwPlugin",
                "tarPlugin",
                "tohtml",
                "tutor",
                "zipPlugin",
            },
        },
    },
})

-------------------------------------------------------------------------------}}}
-- vim: foldmethod=marker

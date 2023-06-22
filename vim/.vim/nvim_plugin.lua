-----------------------------------------------------------------------------}}}
-- SETUP NVIM-CMP                                                            {{{
--------------------------------------------------------------------------------
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
    -- completion = cmp.config.window.bordered(),
    -- documentation = cmp.config.window.bordered(),
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
local capabilities = require('cmp_nvim_lsp').default_capabilities()
end

-----------------------------------------------------------------------------}}}
-- SETUP MASON & LSPCONFIG                                                   {{{
--------------------------------------------------------------------------------
--
function setup_mason_dap_and_lspconfig()
    require("mason").setup()

    require("mason-nvim-dap").setup{
        ensure_installed = {'python', 'cppdbg'},
        handlers = {}, -- sets up dap in the predefined manner
    }
    require("dapui").setup()

    require("mason-lspconfig").setup{
        ensure_installed = {
            "bashls",
            "clangd",
            "cmake",
            "pyright",
            "vimls"

        },
    }

    require("lspconfig").bashls.setup{}
    require("lspconfig").cmake.setup{}
    require("lspconfig").pyright.setup{}
    require("lspconfig").vimls.setup{}

    require("lspconfig").clangd.setup{}
    vim.api.nvim_create_autocmd("FileType",
        {
          pattern = "c,cpp",
          callback = function(ev)
              vim.keymap.set(
                  'n',
                  '<leader>of',
                  '<Cmd>ClangdSwitchSourceHeader<CR>',
                  {buffer=true, noremap}
              )
          end,
          group = clangd
        }
    )

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

            -- Buffer local mappings.
            -- See `:help vim.lsp.*` for documentation on any of the below functions
            local opts = { buffer = ev.buf }
            vim.keymap.set('n', 'gld', vim.lsp.buf.definition, opts)
            vim.keymap.set('n', 'gldd', vim.lsp.buf.declaration, opts)
            vim.keymap.set('n', 'gltd', vim.lsp.buf.type_definition, opts)
            vim.keymap.set('n', 'glh', vim.lsp.buf.hover, opts)
            vim.keymap.set('n', 'glhh', vim.lsp.buf.signature_help, opts)
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

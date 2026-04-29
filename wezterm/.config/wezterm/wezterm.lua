local wezterm = require("wezterm")
local config = wezterm.config_builder()

config.color_scheme = "Apprentice (Gogh)"
config.hide_tab_bar_if_only_one_tab = false
config.tab_bar_at_bottom = true
config.window_close_confirmation = "NeverPrompt"
config.check_for_updates = false

if wezterm.target_triple == "x86_64-pc-windows-msvc" then
	config.default_prog = { "powershell.exe" }
end

-- Leader key (like tmux prefix: C-Space)
config.leader = { key = "Space", mods = "CTRL", timeout_milliseconds = 1000 }

config.keys = {
  -- Pass through C-Space to terminal
  { key = "Space", mods = "LEADER|CTRL", action = wezterm.action.SendKey({ key = "Space", mods = "CTRL" }) },

  -- Splits (prefix + - / \)
  { key = "-",          mods = "LEADER", action = wezterm.action.SplitVertical({ domain = "CurrentPaneDomain" }) },
  { key = "\\",         mods = "LEADER", action = wezterm.action.SplitHorizontal({ domain = "CurrentPaneDomain" }) },

  -- Pane navigation (vim-like)
  { key = "h",          mods = "LEADER", action = wezterm.action.ActivatePaneDirection("Left") },
  { key = "j",          mods = "LEADER", action = wezterm.action.ActivatePaneDirection("Down") },
  { key = "k",          mods = "LEADER", action = wezterm.action.ActivatePaneDirection("Up") },
  { key = "l",          mods = "LEADER", action = wezterm.action.ActivatePaneDirection("Right") },

  -- Resize panes (arrow keys)
  { key = "LeftArrow",  mods = "LEADER", action = wezterm.action.AdjustPaneSize({ "Left", 5 }) },
  { key = "DownArrow",  mods = "LEADER", action = wezterm.action.AdjustPaneSize({ "Down", 5 }) },
  { key = "UpArrow",    mods = "LEADER", action = wezterm.action.AdjustPaneSize({ "Up", 5 }) },
  { key = "RightArrow", mods = "LEADER", action = wezterm.action.AdjustPaneSize({ "Right", 5 }) },

  -- Tabs (= tmux windows)
  { key = "c",          mods = "LEADER", action = wezterm.action.SpawnTab("CurrentPaneDomain") },
  { key = "[",          mods = "LEADER", action = wezterm.action.ActivateTabRelative(-1) },
  { key = "]",          mods = "LEADER", action = wezterm.action.ActivateTabRelative(1) },
  { key = "|",          mods = "LEADER", action = wezterm.action.ActivateLastTab },

  -- Rename tab (prefix + n)
  { key = "n", mods = "LEADER", action = wezterm.action.PromptInputLine({
    description = "Rename tab",
    action = wezterm.action_callback(function(window, _, line)
      if line then window:active_tab():set_title(line) end
    end),
  }) },

  -- Kill pane / tab
  { key = "x",          mods = "LEADER", action = wezterm.action.CloseCurrentPane({ confirm = false }) },
  { key = "X",          mods = "LEADER", action = wezterm.action.CloseCurrentTab({ confirm = true }) },

  -- Zoom pane
  { key = "z",          mods = "LEADER", action = wezterm.action.TogglePaneZoomState },

  -- Copy mode (prefix + Escape)
  { key = "Escape",     mods = "LEADER", action = wezterm.action.ActivateCopyMode },

  -- Paste (prefix + p)
  { key = "p",          mods = "LEADER", action = wezterm.action.PasteFrom("Clipboard") },

  -- Reload config (prefix + s)
  { key = "s",          mods = "LEADER", action = wezterm.action.ReloadConfiguration },

  -- Workspaces (= tmux sessions)
  { key = "W",          mods = "LEADER", action = wezterm.action.ShowLauncherArgs({ flags = "WORKSPACES" }) },
  { key = "(",          mods = "LEADER", action = wezterm.action.SwitchWorkspaceRelative(-1) },
  { key = ")",          mods = "LEADER", action = wezterm.action.SwitchWorkspaceRelative(1) },

  -- New workspace (prefix + C)
  { key = "C", mods = "LEADER", action = wezterm.action.PromptInputLine({
    description = "New workspace name",
    action = wezterm.action_callback(function(window, pane, line)
      if line then
        window:perform_action(wezterm.action.SwitchToWorkspace({ name = line }), pane)
      end
    end),
  }) },

  -- Rename workspace (prefix + N)
  { key = "N", mods = "LEADER", action = wezterm.action.PromptInputLine({
    description = "Rename workspace",
    action = wezterm.action_callback(function(window, pane, line)
      if line then
        wezterm.mux.rename_workspace(wezterm.mux.get_active_workspace(), line)
      end
    end),
  }) },
}

-- Tab switching: LEADER + 1-9
for i = 1, 9 do
  table.insert(config.keys, {
    key = tostring(i), mods = "LEADER",
    action = wezterm.action.ActivateTab(i - 1),
  })
end

-- Copy mode vi bindings: y yanks to clipboard and exits
config.key_tables = {
  copy_mode = {
    { key = "y", action = wezterm.action.Multiple({
      wezterm.action.CopyTo("ClipboardAndPrimarySelection"),
      wezterm.action.CopyMode("Close"),
    }) },
  },
}

-- Scrollback
config.scrollback_lines = 50000

-- Status bar: workspace name + leader indicator
wezterm.on("update-status", function(window, pane)
  local ws = window:active_workspace()
  local leader = window:leader_is_active() and " [WAIT]" or ""
  window:set_left_status(wezterm.format({
    { Text = leader .. " " .. ws .. " " },
  }))
end)

return config

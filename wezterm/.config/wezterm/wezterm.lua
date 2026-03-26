local wezterm = require("wezterm")
local config = wezterm.config_builder()

config.color_scheme = "Apprentice (Gogh)"
config.hide_tab_bar_if_only_one_tab = true
config.window_close_confirmation = "NeverPrompt"
config.check_for_updates = false

if wezterm.target_triple == "x86_64-pc-windows-msvc" then
	config.default_prog = { "powershell.exe" }
end

return config

# Also take into account the following problem. You may have the following error
# while executing the file located in $profile:
#     "Microsoft.PowerShell_profile.ps" cannot be loaded because the execution
#     of scripts is disabled on this system. Please see "get-help about_signing"
#     for more details.
#
# Solution: Check the current execution-policy
#     PS C:\Windows\System32> Get-ExecutionPolicy
#     Restricted
#
# To change the execution policy to allow PowerShell to execute scripts from
# local files, run the following command:
#     PS C:\Windows\System32> Set-Executionpolicy RemoteSigned -Scope CurrentUser
#
Set-Executionpolicy RemoteSigned -Scope CurrentUser

Set-PSReadLineOption -EditMode Emacs
# Ensure PSReadLine is loaded before version check
Import-Module PSReadLine -ErrorAction SilentlyContinue
$psrl = Get-Module PSReadLine
if ($psrl -and $psrl.Version -ge [version]"2.1.0") {
    Set-PSReadLineOption -PredictionSource History
    # Only try to set view style if the parameter exists
    $cmd = Get-Command Set-PSReadLineOption
    if ($cmd.Parameters.ContainsKey('PredictionViewStyle')) {
        Set-PSReadLineOption -PredictionViewStyle ListView
    }
}

Set-PSReadLineKeyHandler -Chord 'Ctrl+p' -Function HistorySearchBackward
Set-PSReadLineKeyHandler -Chord 'Ctrl+n' -Function HistorySearchForward
# Accept prediction with RightArrow or Ctrl+f
Set-PSReadLineKeyHandler -Chord 'Ctrl+f' -Function ForwardChar

# oh-my-posh
if (Get-Command oh-my-posh -ErrorAction SilentlyContinue) {
    $ompConfig = oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\emodipt-extend.omp.json" | Out-String
    if ($ompConfig) { Invoke-Expression $ompConfig }
}

# zoxide (smarter cd)
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    $zoxideInit = zoxide init powershell | Out-String
    if ($zoxideInit) { Invoke-Expression $zoxideInit }
}

# posh-git
if (Get-Module -ListAvailable posh-git) {
    Import-Module posh-git
}

# fzf
if (Get-Module -ListAvailable PSFzf) {
    Import-Module PSFzf
    # Resolve ambiguity: Use specific chord providers instead of the generic -PSReadLine flag
    Set-PsFzfOption -PSReadlineChordProvider 'Ctrl+t' -PSReadlineChordReverseHistory 'Ctrl+r'
}

# Aliases and modern tool replacements
if (Get-Command eza -ErrorAction SilentlyContinue) {
    function global:ls { eza --icons --git $args }
    function global:l { eza -l --icons --git $args }
    function global:la { eza -la --icons --git $args }
    function global:lt { eza --tree --icons $args }
}

if (Get-Command bat -ErrorAction SilentlyContinue) {
    # Correct alias syntax: name, value
    New-Alias -Name cat -Value bat -Force -ErrorAction SilentlyContinue
}

# git delta (if installed)
if (Get-Command delta -ErrorAction SilentlyContinue) {
    $env:GIT_PAGER = "delta"
}

# add a display for use with ssh
$env:DISPLAY="127.0.0.1:0"

set-variable -Name posh -Value $PROFILE.CurrentUserAllHosts
set-variable -Name VISUAL -Value nvim-qt.exe

# Convenience function to call ssh with X forwarding enabled
function sshx { ssh -Y $args }

set-alias g git
set-alias e nvim

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

function install_ps_modules
{
    # TODO functions to update modules
    Install-Module PSFzf -Scope CurrentUser
}

Set-PSReadLineOption -EditMode Emacs
Set-PSReadLineKeyHandler -Chord 'Ctrl+p' -Function HistorySearchBackward
Set-PSReadLineKeyHandler -Chord 'Ctrl+n' -Function HistorySearchForward
Remove-PSReadlineKeyHandler 'Ctrl+r'
Remove-PSReadlineKeyHandler 'Ctrl+t'
Import-Module PSFzf
Enable-PsFzfAliases


# add a display for use with ssh
$env:DISPLAY="127.0.0.1:0"

# Convenience function to call ssh with X forwarding enabled
function sshx { ssh -Y $args }

set-alias g git
set-alias e nvim-qt.exe

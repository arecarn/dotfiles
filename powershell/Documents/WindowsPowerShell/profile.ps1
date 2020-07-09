# Also take into account the following problem. You may have the following error while executing the file located in $profile:
#     "Microsoft.PowerShell_profile.ps" cannot be loaded because the execution of scripts is disabled on this system. Please see "get-help about_signing" for more details.
#
# Solution: Check the current execution-policy
#     PS C:\Windows\System32> Get-ExecutionPolicy
#     Restricted
#
# To change the execution policy to allow PowerShell to execute scripts from local files, run the following command:
#     PS C:\Windows\System32> Set-Executionpolicy RemoteSigned -Scope CurrentUser
#

Set-PSReadLineOption -EditMode Emacs

set-alias g git
set-alias e nvim-qt.exe

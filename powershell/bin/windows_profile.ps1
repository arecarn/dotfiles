# Set environmental variables
[Environment]::SetEnvironmentVariable("EDITOR", "nvim", "User")
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$HOME\bin", "User")
# oh-my-posh path and themes are managed by Chocolatey at the Machine level

# Set environmental variables
[Environment]::SetEnvironmentVariable("EDITOR", "nvim-qt", "User")
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$HOME\bin", "User")

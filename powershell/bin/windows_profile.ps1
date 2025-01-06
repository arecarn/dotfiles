# Set environmental variables
[Environment]::SetEnvironmentVariable("EDITOR", "nvim-qt", "User")
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$HOME\bin", "User")
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$HOME\AppData\Local\Programs\oh-my-posh\bin", "User")

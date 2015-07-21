from os.path import join
from os.path import expanduser
from os import mkdir
from os import rename
from os import name
import os
import datetime

if os.name == "nt":
    isWindows = True
    def symlink_ms(source, link_name):
        import ctypes
        csl = ctypes.windll.kernel32.CreateSymbolicLinkW
        csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        csl.restype = ctypes.c_ubyte
        flags = 1 if os.path.isdir(source) else 0
        try:
            if csl(link_name, source.replace('/', '\\'), flags) == 0:
                raise ctypes.WinError()
        except:
            pass
    os.symlink = symlink_ms


def timeStamped(fname, fmt='{fname}_%Y-%m-%d-%H-%M-%S'):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

home = expanduser("~")
dotfiles_dir = join(home, 'dotfiles')
dotfiles_old_dir = join(home, timeStamped('dotfiles_old'))


dotfiles = [
    ".inputrc",
    ".tmux.conf",
    ".mutt",
    ".gitconfig",
    # ".gitignore_global",
    ".zshrc",
    ".oh-my-zsh",
    ".vim",
    ".ctags",
]

blank_files = [
    join(home, ".zshrc_local"),
    join(home, ".vim/vimrc_local"),
    join(home, ".Trash"),
    join(home, ".gitconfig_local"),
]


print("Creating blank local config files")
for blank_file in blank_files:
    open(blank_file, "w")

print("Creating %s for backup of any existing dotfiles in %s") % (dotfiles_old_dir, home)
mkdir(dotfiles_old_dir)


print("Moving any existing dotfiles from %s to %s") % (dotfiles_dir, dotfiles_old_dir)
for dotfile in dotfiles:
    source = join(home, dotfile)
    target = join(dotfiles_old_dir, dotfile)
    try:
        rename(source, target)
    except:
        pass

    print("Creating symlink to %s") % (dotfile)
    if isWindows:
        symlink_ms(source, target)
    else:
        os.symlink(source, target)

print("All Done ")



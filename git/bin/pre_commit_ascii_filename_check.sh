#!/bin/sh

#
# Git pre-commit hook to check for non-ASCII file names
#

# Check if this is the initial commit
if git rev-parse --verify HEAD >/dev/null 2>&1
then
    against=HEAD
else
    # Initial commit: diff against an empty tree object
    against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# If you want to allow non-ASCII filenames set this variable to true.
allow_non_ascii=$(git config hooks.allownonascii)

# Redirect output to stderr.
exec 1>&2

# Cross platform projects tend to avoid non-ASCII filenames; prevent
# them from being added to the repository. We exploit the fact that the
# printable range starts at the space character and ends with tilde.
if [ "$allow_non_ascii" != "true" ]; then
    file_list=$(git diff --cached --name-only --diff-filter=A -z "${against}")
    # Note that the use of brackets around a tr range is ok here, (it's even
    # required, for portability to Solaris 10's /usr/bin/tr), since the square
    # bracket bytes happen to fall in the designated range.
    non_ascii_chars=$(printf "%s" "${file_list}" | LC_ALL=C tr -d '[ -~]\0')
    num_non_ascii_chars=$(printf "%s" "${non_ascii_chars}" | wc -c )
    num_non_ascii_chars_spaces_trimed=$(printf "%s" "${num_non_ascii_chars}" | tr -d ' ')

    if [ "${num_non_ascii_chars_spaces_trimed}" != "0" ]; then
        cat <<\EOF
pre-commit: Aborting commit due to non-ASCII file name.

This can cause problems if you want to work with people on other platforms. To
be portable it is advisable to rename the file. If you know what you are doing
you can disable this check using:

git config hooks.allownonascii true

EOF
        exit 1
    fi

fi

#!/bin/sh

#
# Git pre-push hook An example hook script to verify the branch being pushed has
# a valid branch name.
#
# This hook is called with the following parameters:
#
# $1 -- Name of the remote to which the push is being done
# $2 -- URL to which the push is being done
#
# If pushing without using a named remote those arguments will be equal.
#
# Information about the commits which are being pushed is supplied as lines to
# the standard input in the form:
#
#   <local ref> <local sha1> <remote ref> <remote sha1>

local_branch="$(git rev-parse --abbrev-ref HEAD)"
valid_chars="[a-z0-9_-]"

if ! echo $local_branch | grep -q "^${valid_chars}\+$"; then
    echo "pre-push: Aborting push due to invalid branch name \"$local_branch\". Use the following characters $valid_chars instead"
    exit 1
fi

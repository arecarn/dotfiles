#!/bin/sh

#
# Git pre-push hook to prevents pushing commits where the log message starts
# with "fixup!" or "squash!" (i.e. commits generated with --fixup or --squash)
# and "WIP" (work in progress).
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
#   <local ref> <local SHA1> <remote ref> <remote SHA1>


# NOTE: if a ref does not yet exist the <remote SHA-1> will be 40 zeros
zero_40_hash=0000000000000000000000000000000000000000

while read local_ref local_sha remote_ref remote_sha
do
  if [ "${local_sha}" = ${zero_40_hash} ]; then
    # ignore delete
    :
  else
    if [ "${remote_sha}" = ${zero_40_hash} ]
    then
      # New branch, examine all commits since master
      range=$(git merge-base "${local_sha}" master).."${local_sha}"
    else
      # Update to existing branch, examine new commits
      range="${remote_sha}..${local_sha}"
    fi

    # check for WIP commits
    commit=$(git rev-list -n 1 --grep '^WIP' "${range}")
    if [ -n "${commit}" ]
    then
      echo "pre-push: Aborting push due to detected WIP commit"
      exit 1
    fi

    # check for autosquash commits
    commit=$(git rev-list -n 1 --grep '^\(fixup\|squash\)!' "${range}")
    if [ -n "${commit}" ]
    then
      echo 'pre-push: Aborting push due to detected autosquash commit (starts with "!fixup"i or "!squash"'
      exit 1
    fi
  fi
done

exit 0

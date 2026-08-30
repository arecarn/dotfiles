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

# $1 is the remote's name. Saved before the loop because the range is built with
# `set --`, which overwrites the positional parameters.
remote_name=${1:-origin}

# shellcheck disable=SC2034
# local_ref and remote_ref are not used in this pre-push hook but are
# instructive of what is passed to the script
while read -r local_ref local_sha remote_ref remote_sha
do
  if [ "${local_sha}" = ${zero_40_hash} ]; then
    # ignore delete
    :
  else
    if [ "${remote_sha}" = ${zero_40_hash} ]
    then
      # New branch: every commit on it the remote does not already have.
      # Hardcoding a base branch name here was wrong -- where it did not
      # resolve, computing the merge base failed, the range silently collapsed
      # to HEAD..<sha>, and the check scanned the wrong commits while still
      # exiting 0. The remote's own refs answer this without naming a branch.
      set -- "${local_sha}" --not "--remotes=${remote_name}"
    else
      # Update to existing branch, examine new commits
      set -- "${remote_sha}..${local_sha}"
    fi

    # Only the subject line decides. `--grep '^WIP'` was not equivalent: git
    # matches it against the whole message, and `^` anchors to any line within
    # it, so a body that wrapped a line onto "WIP..." rejected a perfectly good
    # commit -- as a commit message describing this very check did.
    for commit in $(git rev-list "$@")
    do
      subject=$(git log -1 --format=%s "${commit}")
      case "${subject}" in
        WIP*)
          echo "pre-push: Aborting push due to detected WIP commit"
          exit 1
          ;;
        fixup!*|squash!*)
          echo 'pre-push: Aborting push due to detected autosquash commit (starts with "fixup!" or "squash!")'
          exit 1
          ;;
      esac
    done
  fi
done

exit 0

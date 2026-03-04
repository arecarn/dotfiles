setopt prompt_subst
autoload -Uz vcs_info
zstyle ':vcs_info:*' stagedstr 'M'
zstyle ':vcs_info:*' unstagedstr 'M'
zstyle ':vcs_info:*' check-for-changes true
zstyle ':vcs_info:*' actionformats '%F{green}+%b%f %F{red}%a %m%f'
zstyle ':vcs_info:*' formats       '%F{green}+%b%f %m%F{green}%c%f%F{red}%u%f'
zstyle ':vcs_info:git*+set-message:*' hooks git-untracked git-aheadbehind git-stash
zstyle ':vcs_info:*' enable git

+vi-git-untracked() {
local number_of_untracked_files=$(git ls-files --other --directory --exclude-standard --no-empty-directory 2> /dev/null | wc -l | tr -d ' ')

if [[ $number_of_untracked_files != 0 ]]; then
    hook_com[unstaged]+='%F{red}??%f'
fi
}

### git: Show +N/-N when your local branch is ahead-of or behind remote HEAD.
# Make sure you have added misc to your 'formats': %m
+vi-git-aheadbehind() {
local ahead=$(git rev-list ${hook_com[branch]}@{upstream}..HEAD 2> /dev/null | wc -l | tr -d ' ')
local behind=$(git rev-list HEAD..${hook_com[branch]}@{upstream} 2> /dev/null | wc -l | tr -d ' ')
local -a gitstatus

(($ahead)) && gitstatus+=(" %B%F{blue}+${ahead}%f%b")
(($behind)) && gitstatus+=("%B%F{red}-${behind}%f%b")
hook_com[misc]+=${(j::)gitstatus}
}

# Show count of stashed changes
+vi-git-stash() {
if [[ -s ${hook_com[base]}/.git/refs/stash ]]; then
    local stashes=$(git stash list 2> /dev/null | wc -l | tr -d ' ')
    hook_com[misc]+=" %F{yellow}#${stashes}%f"
fi
}

VI_INSERT_MODE='-- INSERT --'
VI_OTHER_MODES='            '
PROMPT_VALUE='${VI_MODE} %~ ${TIME_STAMP} %# '

set-prompt(){
    case ${KEYMAP} in
        viins|main)
            VI_MODE="${VI_INSERT_MODE}";;
        *)
            VI_MODE="${VI_OTHER_MODES}";;
    esac
    PROMPT="${PROMPT_VALUE}"
}

precmd(){
    vcs_info
    print ""
    # the grep filter prevents lines associated with chaining the current
    # directory
    JOBS_COUNT=$(jobs -p | grep "^\[.*$" | wc -l)
    if [[ ${JOBS_COUNT} == 0 ]]; then
        JOBS_MSG=""
    else
        JOBS_MSG="%F{yellow}[${JOBS_COUNT}]%f"
    fi
    print -rP " %n%F{blue}@%m%f ${JOBS_MSG} ${vcs_info_msg_0_}"
    VI_MODE="${VI_INSERT_MODE}"
    TIME_STAMP=$(date +"%T")
    PROMPT="${PROMPT_VALUE}"
}

zle-line-init() zle-keymap-select() {
    set-prompt
    zle reset-prompt
}
zle -N zle-line-init
zle -N zle-keymap-select

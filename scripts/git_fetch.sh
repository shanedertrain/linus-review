#!/bin/bash
# Clone commit history only (tree:0 filter) of the repos into raw/git/<name>.git. Resumable: skips existing.
# Sequential, one host at a time. Never runs hooks/builds; only clone/fetch.
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p raw/git
export GIT_TERMINAL_PROMPT=0
declare -a REPOS=(
 "sparse https://git.kernel.org/pub/scm/devel/sparse/sparse.git"
 "subsurface https://github.com/subsurface/subsurface.git"
 "git https://git.kernel.org/pub/scm/git/git.git"
 "history https://git.kernel.org/pub/scm/linux/kernel/git/tglx/history.git"
 "linux https://github.com/torvalds/linux.git"
)
for e in "${REPOS[@]}"; do
  set -- $e; name=$1; url=$2; dest=raw/git/$name.git
  if [ -f "$dest/.clone-complete" ]; then echo "skip $name (complete)"; continue; fi
  rm -rf "$dest"
  echo "== $name $url $(date -u +%FT%TZ)"
  if git clone --bare --filter=tree:0 "$url" "$dest"; then
    touch "$dest/.clone-complete"; echo "ok $name"
  else
    echo "FAILED $name (filter or url); not falling back automatically"; rm -rf "$dest"
  fi
  sleep 2
done

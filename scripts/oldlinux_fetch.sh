#!/bin/sh
# Sparse, blob-filtered clone of github.com/oldlinux-web/oldlinux-files, only mail-archive/
# (linux-activists, linux-devel, linux-admin, linux-misc digests 1991-94; funet kernel list 1993-95; early Usenet dumps).
set -e
D="$(dirname "$0")/../raw/usenet/oldlinux-files"
if [ ! -d "$D/.git" ]; then
  git clone --filter=blob:none --no-checkout --depth 1 https://github.com/oldlinux-web/oldlinux-files.git "$D"
  git -C "$D" sparse-checkout set --no-cone /mail-archive/
fi
git -C "$D" checkout

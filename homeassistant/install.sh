#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
[[ $# == 2 ]] || { echo 'Usage: install.sh config.local.json output-directory'; exit 2; }
python3 install.py --config "$1" --output "$2"

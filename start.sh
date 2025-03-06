#!/usr/bin/env bash
set -e

# 1. Install CF CLI
bash cf-cli-install.sh

# 2. (Optional) echo path info for debugging
echo "PATH before re-export: $PATH"
export PATH="$HOME/bin:$PATH"
echo "PATH after re-export: $PATH"

# 3. Confirm that the cf binary is actually present and executable
ls -l "$HOME/bin/cf"
which cf

# 4. Finally, run Flask
python app.py
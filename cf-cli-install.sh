#!/usr/bin/env bash
set -e

echo "Downloading CF CLI..."
wget -qO cf-cli.tgz "https://github.com/cloudfoundry/cli/releases/download/v8.5.0/cf8-cli_8.5.0_linux_x86-64.tgz"
tar -xzf cf-cli.tgz

mkdir -p "$HOME/bin"
mv cf8 "$HOME/bin/cf"
chmod +x "$HOME/bin/cf"

# Put CF in PATH for subsequent commands in this script/session
export PATH="$HOME/bin:$PATH"

echo "Downloading MultiApps Plugin..."
wget -qO multiapps-plugin "https://github.com/cloudfoundry-incubator/multiapps-cli-plugin/releases/download/v3.4.1/multiapps-plugin.linux64"
chmod +x multiapps-plugin

echo "Installing MultiApps Plugin..."
cf install-plugin multiapps-plugin -f

echo "CF CLI and MultiApps plugin installed successfully."
#!/bin/bash

# Run your Python installer script
python3 Azul_installer.py

# Reloads the shell environment so JAVA_HOME/PATH takes effect immediately
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
elif [ -f ~/.profile ]; then
    source ~/.profile
fi

# Verify Installation

echo
echo "✅ Java is ready to use. Checking Java version..."
java -version
#!/bin/bash

# List of hosts from inventory.ini with their passwords
declare -A HOST_PASSWORDS
HOST_PASSWORDS=(
  ["192.168.40.240"]="P@ssword1376" # MASTER
  ["192.168.40.241"]="P@ssword1376" # G-241
  ["192.168.40.242"]="P@ssword1376" # G-242
  ["192.168.40.243"]="P@ssword1376" # G-243
  ["192.168.40.244"]="P@ssword1376" # G-244
)

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
  echo "sshpass is not installed. Installing it now..."
  sudo apt-get update
  sudo apt-get install -y sshpass
fi

# Ensure .ssh directory exists
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Generate SSH key if it doesn't exist
if [ ! -f ~/.ssh/id_rsa ]; then
  ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
  echo "SSH key pair generated."
else
  echo "SSH key pair already exists."
fi

# Copy SSH key to each host
for host in "${!HOST_PASSWORDS[@]}"; do
  password="${HOST_PASSWORDS[$host]}"
  echo "Setting up passwordless SSH for $host..."
  
  # Check if we can already SSH without password
  ssh -o BatchMode=yes -o ConnectTimeout=5 gpadmin@$host exit &>/dev/null
  if [ $? -eq 0 ]; then
    echo "Passwordless SSH already set up for $host."
    continue
  fi
  
  # Copy SSH key to remote host using sshpass
  echo "Copying SSH key to $host..."
  sshpass -p "$password" ssh-copy-id -o StrictHostKeyChecking=no gpadmin@$host
  
  if [ $? -eq 0 ]; then
    echo "Successfully set up passwordless SSH for $host."
  else
    echo "Failed to set up passwordless SSH for $host."
  fi
done

echo "SSH setup complete." 
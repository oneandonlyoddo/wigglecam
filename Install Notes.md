sudo apt install -y python3-picamera2
sudo apt install git
git clone git@github.com:oneandonlyoddo/wigglecam.git
sudo apt update


Adding machines to ssh config for vs code remote access

create key
ssh-keygen -t ed25519

push key to server
ssh-copy-id -i ~/.ssh/key.pub username@host

add hosts to ~/.ssh/config

Host [hostname]
  HostName 192.168.0.xxx
  port 22
  User [username]
  IdentityFile [path to ssh key] # use \\ on windows
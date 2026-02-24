# Install Notes

## Dependencies

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-flask python3-opencv git
```

## Clone the repo

```bash
git clone git@github.com:oneandonlyoddo/wigglecam.git
```

## SSH key setup (for VS Code remote access)

**Generate a key** (on your local machine):
```bash
ssh-keygen -t ed25519
```

**Push the key to each Pi:**
```bash
ssh-copy-id -i ~/.ssh/key.pub username@host
```

**Add each Pi to `~/.ssh/config`:**
```
Host [hostname]
  HostName 192.168.0.xxx
  Port 22
  User [username]
  IdentityFile [path/to/key]   # use \\ on Windows
```

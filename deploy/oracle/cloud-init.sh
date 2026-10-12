#!/bin/bash
# CheckAI on an Oracle Cloud Always Free server (Ubuntu, Ampere A1).
# Paste this whole file into "Advanced options > Management > Paste cloud-init script"
# when you create the instance. It installs Docker, builds CheckAI with the
# Qwen2.5-0.5B models and serves it on port 80. Progress is logged to
# /var/log/checkai-setup.log; the first build takes about 15-25 minutes.
set -eux
exec > >(tee -a /var/log/checkai-setup.log) 2>&1
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y docker.io curl
systemctl enable --now docker

# Oracle's Ubuntu images only allow SSH through the local firewall
iptables -I INPUT -p tcp --dport 80 -j ACCEPT
apt-get install -y iptables-persistent && netfilter-persistent save || true

# A little swap so the image build never runs out of memory
if [ ! -f /swapfile ]; then
  fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

cat > /usr/local/bin/checkai-update <<'SCRIPT'
#!/bin/bash
# Rebuild CheckAI from the latest code on GitHub and restart it.
set -eux
mkdir -p /opt/checkai
curl -fsSL https://raw.githubusercontent.com/kipoikibo995-sys/checkai/main/deploy/huggingface/Dockerfile -o /opt/checkai/Dockerfile
docker build -t checkai /opt/checkai
docker rm -f checkai 2>/dev/null || true
docker run -d --name checkai --restart unless-stopped -p 80:7860 checkai
SCRIPT
chmod +x /usr/local/bin/checkai-update
/usr/local/bin/checkai-update
echo "CheckAI is running on port 80"

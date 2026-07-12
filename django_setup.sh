#!/bin/bash

# ============================================================
# Django + MySQL + Nginx + Gunicorn Auto Setup Script
# ============================================================

set -e

# ============================================================
# LOGGING
# ============================================================

LOG_FILE="$HOME/django_setup_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE") 2>&1

trap 'echo ""; echo "[ERROR] Script failed at line $LINENO"; echo "Check log file: $LOG_FILE"; exit 1' ERR

echo "============================================================"
echo "      Django Production Server Auto Setup Script"
echo "============================================================"
echo "Started at: $(date)"
echo "Log file: $LOG_FILE"

# ============================================================
# HELPER FUNCTION
# ============================================================

run_step() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

# ============================================================
# PRE-FLIGHT CHECKS
# ============================================================

run_step "Pre-flight Checks"

if [ ! -f /etc/os-release ]; then
    echo "[ERROR] Cannot detect OS. This script is Ubuntu-only."
    exit 1
fi

source /etc/os-release

if [ "$ID" != "ubuntu" ]; then
    echo "[ERROR] This script requires Ubuntu. Detected: $ID"
    exit 1
fi

UBUNTU_VERSION="$VERSION_ID"
echo "Detected Ubuntu $UBUNTU_VERSION"

case "$UBUNTU_VERSION" in
    "20.04"|"22.04"|"24.04")
        echo "Ubuntu $UBUNTU_VERSION is supported"
        ;;
    *)
        echo "[WARNING] Ubuntu $UBUNTU_VERSION is untested. Proceeding anyway..."
        ;;
esac

REQUIRED_CMDS=("sudo" "apt" "sed" "tee" "systemctl")

for cmd in "${REQUIRED_CMDS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "[ERROR] Required command not found: $cmd"
        exit 1
    fi
done

echo "All required system commands found"

# ============================================================
# PYTHON VERSION CHECK
# ============================================================

run_step "Detecting Python Version"

PYTHON_CMD=$(command -v python3.12 2>/dev/null || \
             command -v python3.11 2>/dev/null || \
             command -v python3.10 2>/dev/null || \
             command -v python3.9  2>/dev/null || \
             command -v python3.8  2>/dev/null || \
             command -v python3    2>/dev/null || true)

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] No suitable Python 3.8+ found on this machine"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Using Python: $PYTHON_CMD ($PYTHON_VERSION)"

# ============================================================
# USER INPUTS
# ============================================================

run_step "USER INPUT REQUIRED"

read -p "Enter Ubuntu username: " UBUNTU_USER
read -p "Enter server IP address: " SERVER_IP

# Get the directory where the script itself is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Everything is relative to that
PROJECT_ROOT="$SCRIPT_DIR/web_appV2"
PROJECT_PATH="$PROJECT_ROOT/data_access_app"
VENV_PATH="$PROJECT_PATH/.venv"
SQL_DUMP_PATH="$SCRIPT_DIR/Dump20260707.sql"

# ============================================================
# INPUT VALIDATION
# ============================================================

run_step "Validating Inputs"

if ! id "$UBUNTU_USER" &>/dev/null; then
    echo "[ERROR] User '$UBUNTU_USER' does not exist on this machine"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "[ERROR] Project root not found: $PROJECT_ROOT"
    exit 1
fi

if [ ! -d "$PROJECT_PATH" ]; then
    echo "[ERROR] Project path not found: $PROJECT_PATH"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "[ERROR] requirements.txt not found at $PROJECT_ROOT"
    exit 1
fi

if [ ! -f "$SQL_DUMP_PATH" ]; then
    echo "[ERROR] SQL dump file not found: $SQL_DUMP_PATH"
    exit 1
fi

echo "All inputs validated successfully"

# ============================================================
# PYTHON TOOLS SETUP
# ============================================================

run_step "Ensuring Python Tools Are Available"

sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev

# Required to build mysqlclient (common Django MySQL package)
sudo apt install -y pkg-config libmysqlclient-dev build-essential

echo "Python tools are ready"


# ============================================================
# NGINX SETUP
# ============================================================

run_step "Checking For Port Conflicts"

if sudo ss -tlnp | grep -q ':80 '; then
    echo "[WARNING] Port 80 is already in use:"
    sudo ss -tlnp | grep ':80 '
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
fi

if systemctl is-active --quiet apache2; then
    echo "[WARNING] Apache2 is running. Stopping and disabling it to free port 80..."
    sudo systemctl stop apache2
    sudo systemctl disable apache2
fi

run_step "Installing Nginx"

sudo apt install nginx -y

sudo systemctl start nginx
sudo systemctl enable nginx

run_step "Creating Nginx Configuration"

sudo tee /etc/nginx/sites-available/data_access_app > /dev/null <<EOF
server {

    listen 80;

    server_name $SERVER_IP;

    location /static/ {
        alias $PROJECT_PATH/static/;
    }

    location /media/ {
        alias $PROJECT_PATH/media/;
    }

    location / {

        include proxy_params;

        proxy_pass http://unix:$PROJECT_PATH/gunicorn.sock;

    }

}
EOF

run_step "Enabling Nginx Site"

if [ ! -L /etc/nginx/sites-enabled/data_access_app ]; then
    sudo ln -sf \
    /etc/nginx/sites-available/data_access_app \
    /etc/nginx/sites-enabled/data_access_app
fi

sudo rm -f /etc/nginx/sites-enabled/default

run_step "Testing Nginx Configuration"

sudo nginx -t

run_step "Restarting Nginx"

sudo systemctl restart nginx
sudo systemctl enable nginx

sudo systemctl is-active --quiet nginx

if [ $? -eq 0 ]; then
    echo "Nginx is running successfully"
else
    echo "Nginx failed"
    exit 1
fi
# ============================================================
# USING EXISTING VIRTUAL ENVIRONMENT
# ============================================================

run_step "Using Existing Virtual Environment"

if [ ! -d "$VENV_PATH" ]; then
    echo "[ERROR] Virtual environment not found:"
    echo "$VENV_PATH"
    exit 1
fi

source "$VENV_PATH/bin/activate"

echo "Using virtual environment:"
echo "$VENV_PATH"

# ============================================================
# INTERNET CONNECTIVITY CHECK
# ============================================================

run_step "Checking Internet Connectivity"

# Each entry is: "index_url|download_test_url|trusted_host"
# The download_test_url is the actual host pip fetches .whl files from.
# pypi.org uses files.pythonhosted.org (Fastly CDN) for downloads — tested separately.
# Mirrors (Alibaba, TUNA) serve both metadata AND files from their own servers.
PYPI_SOURCES=(
    "https://pypi.org/simple/|https://files.pythonhosted.org|files.pythonhosted.org"
    "https://mirrors.aliyun.com/pypi/simple/|https://mirrors.aliyun.com|mirrors.aliyun.com"
    "https://pypi.tuna.tsinghua.edu.cn/simple/|https://pypi.tuna.tsinghua.edu.cn|pypi.tuna.tsinghua.edu.cn"
)

WORKING_INDEX=""
WORKING_TRUSTED=""

echo "Detecting reachable PyPI source (testing actual download hosts)..."

for ENTRY in "${PYPI_SOURCES[@]}"; do
    INDEX_URL=$(echo "$ENTRY"    | cut -d'|' -f1)
    DOWNLOAD_URL=$(echo "$ENTRY" | cut -d'|' -f2)
    TRUSTED=$(echo "$ENTRY"      | cut -d'|' -f3)

    echo "  Testing download host: $DOWNLOAD_URL"

    if curl -sf --max-time 15 "$DOWNLOAD_URL" > /dev/null 2>&1; then
        echo "  [OK] Reachable: $INDEX_URL"
        WORKING_INDEX="$INDEX_URL"
        WORKING_TRUSTED="$TRUSTED"
        break
    else
        echo "  [SKIP] Download host not reachable: $DOWNLOAD_URL"
    fi
done

if [ -z "$WORKING_INDEX" ]; then
    echo "[ERROR] No PyPI source is reachable from this server."
    echo ""
    echo "Possible causes:"
    echo "  1. Outbound port 443 is blocked in your firewall/security group"
    echo "  2. DNS resolution is failing (try: nslookup pypi.org)"
    echo "  3. A proxy is required (set https_proxy env variable)"
    echo "  4. No internet connection on this server"
    exit 1
fi

echo "Using PyPI source: $WORKING_INDEX"

# Write pip.conf so every pip call in this script uses the working source.
# This covers both metadata (index) and file downloads since mirrors
# serve everything from their own servers, bypassing blocked CDNs.
mkdir -p ~/.config/pip
cat > ~/.config/pip/pip.conf <<EOF
[global]
index-url = $WORKING_INDEX
trusted-host = $WORKING_TRUSTED
timeout = 120
retries = 5
no-cache-dir = false
EOF

echo "pip configured to use: $WORKING_INDEX"

# ============================================================
# INSTALLING REQUIREMENTS
# ============================================================

run_step "Installing Requirements"

pip_install_with_retry() {
    local MAX_ATTEMPTS=3
    local ATTEMPT=1
    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        echo "Attempt $ATTEMPT of $MAX_ATTEMPTS: pip $*"
        if pip install "$@"; then
            return 0
        fi
        echo "[WARNING] pip install failed on attempt $ATTEMPT"
        ATTEMPT=$((ATTEMPT + 1))
        sleep 5
    done
    echo "[ERROR] pip install failed after $MAX_ATTEMPTS attempts"
    return 1
}

pip_install_with_retry --upgrade pip
pip_install_with_retry -r "$PROJECT_ROOT/requirements.txt"

# ============================================================
# GUNICORN SETUP
# ============================================================

run_step "Installing Gunicorn"

pip_install_with_retry gunicorn

gunicorn --version

run_step "Creating Gunicorn Service"

sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOF
[Unit]
Description=Gunicorn Django Service
After=network.target

[Service]

User=$UBUNTU_USER
Group=www-data

# UMask=0007 means the socket file is created as srwxrwx---
# owned by $UBUNTU_USER:www-data so Nginx (which runs as www-data)
# can access it immediately — no logout/login required after usermod
UMask=0007

WorkingDirectory=$PROJECT_PATH

ExecStart=$VENV_PATH/bin/gunicorn \\
--workers 3 \\
--bind unix:$PROJECT_PATH/gunicorn.sock \\
data_access_app.wsgi:application

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

run_step "Configuring Socket Permissions"

sudo usermod -aG www-data "$UBUNTU_USER"

sudo chmod 755 "/home/$UBUNTU_USER"
sudo chmod 755 "$PROJECT_ROOT"
sudo chmod 755 "$PROJECT_PATH"

echo "Socket permissions configured"

sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl enable gunicorn

sudo systemctl is-active --quiet gunicorn

if [ $? -eq 0 ]; then
    echo "Gunicorn is running successfully"
else
    echo "Gunicorn failed"
    exit 1
fi

# ============================================================
# DJANGO SETTINGS UPDATE
# ============================================================

run_step "Automatically Updating settings.py"

SETTINGS_FILE="$PROJECT_PATH/data_access_app/settings.py"

cp "$SETTINGS_FILE" "${SETTINGS_FILE}.backup"

sed -i "s/DEBUG = True/DEBUG = False/g" "$SETTINGS_FILE"

"$PYTHON_CMD" <<EOF
from pathlib import Path
import re, sys

settings_path = Path("$SETTINGS_FILE")

content = settings_path.read_text()

new_content = re.sub(
    r"ALLOWED_HOSTS\s*=\s*\[.*?\]",
    "ALLOWED_HOSTS = ['$SERVER_IP', '127.0.0.1', 'localhost']",
    content,
    flags=re.DOTALL
)

if "ALLOWED_HOSTS" not in new_content:
    print("[ERROR] Failed to update ALLOWED_HOSTS in settings.py")
    sys.exit(1)

new_db = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '$DB_NAME',
        'USER': '$DB_USER',
        'PASSWORD': '$DB_PASSWORD',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
"""

new_content = re.sub(
    r'DATABASES\s*=\s*\{.*?\n\}',
    new_db,
    new_content,
    flags=re.DOTALL
)

if "'ENGINE'" not in new_content:
    print("[ERROR] Failed to update DATABASES in settings.py")
    sys.exit(1)

settings_path.write_text(new_content)

print("settings.py updated successfully")
EOF

# ============================================================
# COLLECT STATIC
# ============================================================

run_step "Collecting Static Files"

cd "$PROJECT_PATH"

source "$VENV_PATH/bin/activate"

python manage.py collectstatic --noinput

# ============================================================
# FIREWALL SETUP
# ============================================================

run_step "Configuring Firewall"

if ! command -v ufw &> /dev/null; then
    sudo apt install -y ufw
fi

sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'

echo "y" | sudo ufw enable

sudo ufw status

# ============================================================
# FINAL RESTART
# ============================================================

run_step "Restarting Services"

sudo systemctl restart gunicorn
sudo systemctl restart nginx

# ============================================================
# MACHINE SIMULATOR
# ============================================================

run_step "Machine Simulator Configuration"

SIMULATOR_CONFIG="/home/$UBUNTU_USER/final_sql_webapp_dump_final/machine_simulator_singleV2_latest/apiConfig.ini"

if [ -f "$SIMULATOR_CONFIG" ]; then

    sed -i "s|^api_base_host *=.*|api_base_host = $SERVER_IP|g" "$SIMULATOR_CONFIG"

    echo "apiConfig.ini updated successfully"

else

    echo "machine simulator config file not found"

fi

# ============================================================
# FINAL STATUS
# ============================================================

run_step "SETUP COMPLETED SUCCESSFULLY"

echo ""
echo "Website URL:"
echo "http://$SERVER_IP"

echo ""
echo "Log File:"
echo "$LOG_FILE"

echo ""
echo "Useful Commands:"
echo "sudo systemctl status gunicorn"
echo "sudo systemctl status nginx"
echo "sudo journalctl -u gunicorn -f"

#!/bin/bash

# Script to create a custom Tiny Core Linux-based OS with BERKE0S.py
# Downloads BERKE0S.py, packages it as .tcz, configures autostart, and customizes system
# Uses Python 3.9, includes robust error handling, and fixes udev/hwdb issues

# Exit on any error (unless handled explicitly)
set -e

# Variables
GITHUB_URL="https://raw.githubusercontent.com/B3rk3-0ruc/BERKE0S-LINUX/main/BERKE0S.py"
TCZ_NAME="BERKE0S.tcz"
TCZ_DIR="/tmp/tce/optional"
WORK_DIR="/tmp/berke0s"
CONFIG_DIR="/home/tc/.berke0s"
STARTUP_SCRIPT="/opt/bootlocal.sh"
FILETOOL_LST="/opt/.filetool.lst"
BOOT_MSG="/boot/boot.msg"
ISOLINUX_CFG="/boot/isolinux/isolinux.cfg"
XSESSION="/home/tc/.Xsession"
UDEV_RULE="/etc/udev/rules.d/90-framebuffer.rules"

# Function to check internet connectivity
check_internet() {
    echo "Checking internet connectivity..."
    if ! ping -c 1 8.8.8.8 &>/dev/null; then
        echo "Error: No internet connection. Please connect to a network and try again."
        exit 1
    fi
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log errors and exit
log_error() {
    echo "Error: $1" >&2
    exit 1
}

# Step 1: Validate environment
echo "Validating environment..."
if [ "$(whoami)" != "tc" ]; then
    log_error "This script must be run as user 'tc'."
fi
if ! command_exists tce-load; then
    log_error "tce-load not found. Ensure Tiny Core Linux is properly set up."
fi
check_internet

# Step 2: Install required tools and dependencies
echo "Installing required tools and dependencies..."
DEPENDENCIES=(
    squashfs-tools python3.9 tk tcl python3.9-pip alsa bluez
    e2fsprogs nano htop bash network-manager tar zip dosfstools
    syslinux perl5 mpv scrot libnotify alsa-utils wireless-tools
    espeak util-linux Xvesa fbcon vesafb
)
for pkg in "${DEPENDENCIES[@]}"; do
    if ! tce-load -wi "$pkg.tcz" 2>/dev/null; then
        echo "Warning: Failed to install $pkg.tcz. Checking if already installed..."
        if ! tce-status -i | grep -q "^$pkg$"; then
            log_error "Failed to install $pkg.tcz and it's not present."
        fi
    fi
done

# Install Python dependencies
echo "Installing Python dependencies..."
if ! command_exists pip3; then
    log_error "pip3 not found after installing python3.9-pip.tcz."
fi
PYTHON_DEPS=(psutil Pillow flask)
for dep in "${PYTHON_DEPS[@]}"; do
    if ! sudo pip3 install "$dep" --no-cache-dir 2>/dev/null; then
        log_error "Failed to install Python module $dep."
    fi
done

# Step 3: Create working directory and download BERKE0S.py
echo "Creating working directory and downloading BERKE0S.py..."
if ! mkdir -p "$WORK_DIR"; then
    log_error "Failed to create working directory $WORK_DIR."
fi
cd "$WORK_DIR" || log_error "Failed to change to $WORK_DIR."
if ! wget -O BERKE0S.py "$GITHUB_URL" 2>/dev/null; then
    log_error "Failed to download BERKE0S.py from $GITHUB_URL."
fi
if [ ! -s BERKE0S.py ]; then
    log_error "Downloaded BERKE0S.py is empty."
fi
chmod +x BERKE0S.py

# Step 4: Create directory structure for .tcz package
echo "Creating .tcz package structure..."
mkdir -p squashfs-root/usr/local/bin squashfs-root/home/tc/.berke0s/{themes,plugins} || log_error "Failed to create .tcz directory structure."
cp BERKE0S.py squashfs-root/usr/local/bin/ || log_error "Failed to copy BERKE0S.py to .tcz structure."
cd squashfs-root || log_error "Failed to change to squashfs-root."

# Step 5: Create .tcz package
echo "Creating $TCZ_NAME..."
if ! mksquashfs . "$TCZ_DIR/$TCZ_NAME" -b 4k -noappend 2>/dev/null; then
    log_error "Failed to create $TCZ_NAME."
fi
cd ..
rm -rf squashfs-root

# Step 6: Add .tcz to onboot list
echo "Configuring $TCZ_NAME to load on boot..."
mkdir -p /tmp/tce || log_error "Failed to create /tmp/tce."
if ! grep -q "$TCZ_NAME" /tmp/tce/onboot.lst 2>/dev/null; then
    echo "$TCZ_NAME" | sudo tee -a /tmp/tce/onboot.lst || log_error "Failed to add $TCZ_NAME to onboot.lst."
fi

# Step 7: Configure startup script
echo "Configuring startup script..."
if ! grep -q "BERKE0S.py" "$STARTUP_SCRIPT" 2>/dev/null; then
    {
        echo "# Load framebuffer modules"
        echo "modprobe fbcon"
        echo "modprobe vesafb"
        echo "# Start X server and BERKE0S.py"
        echo "startx &"
        echo "/usr/local/bin/BERKE0S.py &"
    } | sudo tee -a "$STARTUP_SCRIPT" || log_error "Failed to update $STARTUP_SCRIPT."
fi
sudo chmod +x "$STARTUP_SCRIPT" || log_error "Failed to make $STARTUP_SCRIPT executable."

# Step 8: Configure X session
echo "Configuring X session..."
if [ ! -f "$XSESSION" ]; then
    echo "exec /usr/local/bin/BERKE0S.py" | sudo tee "$XSESSION" || log_error "Failed to create $XSESSION."
    sudo chmod +x "$XSESSION" || log_error "Failed to make $XSESSION executable."
fi

# Step 9: Create framebuffer udev rule
echo "Creating framebuffer udev rule..."
if [ ! -f "$UDEV_RULE" ]; then
    echo 'SUBSYSTEM=="graphics", KERNEL=="fb[0-9]*", MODE="0666"' | sudo tee "$UDEV_RULE" || log_error "Failed to create $UDEV_RULE."
fi

# Step 10: Update hwdb
echo "Updating hardware database..."
if command_exists systemd-hwdb; then
    sudo systemd-hwdb update || echo "Warning: Failed to run systemd-hwdb update."
elif command_exists udevadm; then
    sudo udevadm hwdb --update || echo "Warning: Failed to run udevadm hwdb --update."
else
    echo "Warning: Neither systemd-hwdb nor udevadm found. Skipping hwdb update."
fi
if command_exists udevadm; then
    sudo udevadm control --reload-rules || echo "Warning: Failed to reload udev rules."
    sudo udevadm trigger || echo "Warning: Failed to trigger udev."
fi

# Step 11: Ensure persistence
echo "Ensuring persistence..."
PERSIST_PATHS=(
    usr/local/bin/BERKE0S.py
    tce/optional/"$TCZ_NAME"
    tce/onboot.lst
    home/tc/.berke0s
    etc/udev/rules.d
    "$STARTUP_SCRIPT"
    "$XSESSION"
)
for path in "${PERSIST_PATHS[@]}"; do
    if ! grep -q "^$path$" "$FILETOOL_LST" 2>/dev/null; then
        echo "$path" | sudo tee -a "$FILETOOL_LST" || log_error "Failed to add $path to $FILETOOL_LST."
    fi
done

# Step 12: Customize system branding
echo "Customizing system branding..."
[ -f "$BOOT_MSG" ] && sudo sed -i 's/Tiny Core/Berke0S/g' "$BOOT_MSG" || echo "Warning: $BOOT_MSG not found."
[ -f "$ISOLINUX_CFG" ] && sudo sed -i 's/Tiny Core/Berke0S/g' "$ISOLINUX_CFG" || echo "Warning: $ISOLINUX_CFG not found."
find /etc -type f -exec sudo sed -i 's/Tiny Core/Berke0S/g' {} + 2>/dev/null || echo "Warning: Some /etc files could not be modified."

# Step 13: Save changes
echo "Saving changes..."
if ! filetool.sh -b 2>/dev/null; then
    log_error "Failed to save changes with filetool.sh."
fi

# Step 14: Clean up
echo "Cleaning up..."
rm -rf "$WORK_DIR" || echo "Warning: Failed to clean up $WORK_DIR."

# Step 15: Inform user
echo "Installation complete! Reboot to apply changes."
echo "BERKE0S.py will run automatically on startup with Python 3.9."
echo "System branding updated to Berke0S."
echo "Run 'sudo reboot' to start using Berke0S."

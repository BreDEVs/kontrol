#!/bin/bash

# Script to create a custom Tiny Core Linux-based OS with BERKE0S.py
# Downloads BERKE0S.py, packages it as .tcz, configures autostart, and customizes system
# Uses Python 3.9, includes robust error handling, fixes udev/hwdb issues, handles missing boot.msg/isolinux.cfg,
# and ensures persistence with filetool.sh -b

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

# Function to find boot files (boot.msg, isolinux.cfg, syslinux.cfg)
find_boot_files() {
    local file="$1"
    local found_files=()
    # Check common locations
    for path in /boot /mnt/*/boot /mnt/*/boot/isolinux; do
        if [ -f "$path/$file" ]; then
            found_files+=("$path/$file")
        fi
    done
    echo "${found_files[@]}"
}

# Function to find and configure persistent storage
find_persistent_storage() {
    echo "Checking for persistent storage..."
    local tce_dir=""
    # Look for /mnt/*/tce directories
    for dir in /mnt/*/tce; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            tce_dir="$dir"
            break
        fi
    done
    # If no tce directory found, try to create one on a writable partition
    if [ -z "$tce_dir" ]; then
        echo "No persistent storage found. Attempting to set up..."
        for dev in /mnt/*; do
            if [ -d "$dev" ] && [ -w "$dev" ]; then
                if mkdir -p "$dev/tce" 2>/dev/null; then
                    tce_dir="$dev/tce"
                    echo "Created $tce_dir for persistence."
                    break
                fi
            fi
        done
    fi
    if [ -z "$tce_dir" ]; then
        echo "Error: No writable storage device found for persistence."
        echo "Please mount a writable device (e.g., USB drive) and create /mnt/<device>/tce/."
        echo "Example: sudo mkdir -p /mnt/sda1/tce"
        exit 1
    fi
    echo "Using $tce_dir for persistent storage."
    echo "$tce_dir"
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
    squashfs-tools python3.9 python3.9-pip alsa bluez
    e2fsprogs nano htop bash tar zip dosfstools
    syslinux perl5 mpv scrot libnotify util-linux
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
if [ ! -f "/home/tc/.Xsession" ]; then
    echo "exec /usr/local/bin/BERKE0S.py" | sudo tee /home/tc/.Xsession || log_error "Failed to create /home/tc/.Xsession."
    sudo chmod +x /home/tc/.Xsession || log_error "Failed to make /home/tc/.Xsession executable."
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
    home/tc/.Xsession
)
# Create /opt/.filetool.lst if it doesn't exist
if [ ! -f "$FILETOOL_LST" ]; then
    sudo touch "$FILETOOL_LST" || log_error "Failed to create $FILETOOL_LST."
fi
for path in "${PERSIST_PATHS[@]}"; do
    if ! grep -q "^$path$" "$FILETOOL_LST" 2>/dev/null; then
        echo "$path" | sudo tee -a "$FILETOOL_LST" || log_error "Failed to add $path to $FILETOOL_LST."
    fi
done

# Step 12: Verify and configure persistent storage
TCE_DIR=$(find_persistent_storage)
# Ensure /opt/.filetool.lst is writable
sudo chmod u+w "$FILETOOL_LST" || log_error "Failed to set permissions on $FILETOOL_LST."

# Step 13: Customize system branding
echo "Customizing system branding..."
BOOT_MSG_FILES=($(find_boot_files boot.msg))
ISOLINUX_FILES=($(find_boot_files isolinux.cfg))
SYSLINUX_FILES=($(find_boot_files syslinux.cfg))
for file in "${BOOT_MSG_FILES[@]}"; do
    sudo sed -i 's/Tiny Core/Berke0S/g' "$file" && echo "Updated branding in $file" || echo "Warning: Failed to update $file."
done
for file in "${ISOLINUX_FILES[@]}" "${SYSLINUX_FILES[@]}"; do
    sudo sed -i 's/Tiny Core/Berke0S/g' "$file" && echo "Updated branding in $file" || echo "Warning: Failed to update $file."
done
find /etc -type f -exec sudo sed -i 's/Tiny Core/Berke0S/g' {} + 2>/dev/null || echo "Warning: Some /etc files could not be modified."

# Step 14: Save changes
echo "Saving changes..."
if ! filetool.sh -b 2>&1 | tee /tmp/filetool.log; then
    echo "Error: filetool.sh -b failed. Log output:"
    cat /tmp/filetool.log
    echo "Possible causes:"
    echo "- No writable storage device mounted at $TCE_DIR."
    echo "- Insufficient disk space on the storage device."
    echo "- Filesystem is read-only or corrupted."
    echo "Steps to fix:"
    echo "1. Check mounted devices: ls /mnt"
    echo "2. Ensure $TCE_DIR exists and is writable: ls -ld $TCE_DIR"
    echo "3. Mount a writable device, e.g., sudo mount /dev/sda1 /mnt/sda1"
    echo "4. Create $TCE_DIR if missing: sudo mkdir -p $TCE_DIR"
    echo "5. Re-run: sudo filetool.sh -b"
    log_error "Persistence setup failed."
fi
rm -f /tmp/filetool.log

# Step 15: Clean up
echo "Cleaning up..."
rm -rf "$WORK_DIR" || echo "Warning: Failed to clean up $WORK_DIR."

# Step 16: Inform user
echo "Installation complete! Reboot to apply changes."
echo "BERKE0S.py will run automatically on startup with Python 3.9."
echo "System branding updated to Berke0S where possible."
echo "Run 'sudo reboot' to start using Berke0S."

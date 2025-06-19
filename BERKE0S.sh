#!/bin/bash

# Script to create a custom Tiny Core Linux-based OS with BERKE0S.py
# Downloads BERKE0S.py, packages it as .tcz, configures autostart, and customizes system
# Uses Python 3.9, includes robust error handling, fixes udev/hwdb issues, handles missing boot.msg/isolinux.cfg,
# ensures persistence with filetool.sh -b, and downloads missing .tcz packages from multiple mirrors

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
LOG_FILE="/tmp/berke0s_install.log"

# Detect Tiny Core version and architecture
TC_VERSION=$(cat /etc/release 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+' || echo "14.x")
ARCH=$(uname -m | grep -q x86_64 && echo "x86_64" || echo "x86")
REPO_MIRRORS=(
    "http://repo.tinycorelinux.net/${TC_VERSION}/${ARCH}/tcz"
    "http://distro.ibiblio.org/tinycorelinux/${TC_VERSION}/${ARCH}/tcz"
    "http://mirror.csclub.uwaterloo.ca/tinycorelinux/${TC_VERSION}/${ARCH}/tcz"
)

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Function to check internet connectivity
check_internet() {
    log_message "Checking internet connectivity..."
    if ! ping -c 1 8.8.8.8 &>/dev/null; then
        log_error "No internet connection. Please connect to a network and try again."
    fi
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log errors and exit
log_error() {
    log_message "Error: $1"
    exit 1
}

# Function to find boot files (boot.msg, isolinux.cfg, syslinux.cfg)
find_boot_files() {
    local file="$1"
    local found_files=()
    for path in /boot /mnt/*/boot /mnt/*/boot/isolinux /mnt/*/boot/syslinux; do
        if [ -f "$path/$file" ]; then
            found_files+=("$path/$file")
        fi
    done
    echo "${found_files[@]}"
}

# Function to download and install .tcz package
install_tcz() {
    local pkg="$1"
    local tcz_file="/tmp/$pkg.tcz"
    local alt_pkgs=("$pkg" "${pkg}8.6" "${pkg}8.5") # Fallback package names (e.g., tk8.6)
    if tce-status -i | grep -q "^$pkg$"; then
        log_message "$pkg.tcz is already installed."
        return 0
    fi
    log_message "Installing $pkg.tcz..."
    if tce-load -wi "$pkg.tcz" 2>/dev/null; then
        log_message "Successfully installed $pkg.tcz via tce-load."
        return 0
    fi
    log_message "tce-load failed for $pkg.tcz. Attempting direct download..."
    for alt_pkg in "${alt_pkgs[@]}"; do
        for mirror in "${REPO_MIRRORS[@]}"; do
            local url="$mirror/$alt_pkg.tcz"
            log_message "Trying $alt_pkg.tcz from $url..."
            if wget -q -O "$tcz_file" "$url" 2>/dev/null; then
                if tce-load -i "$tcz_file" 2>/dev/null; then
                    log_message "Successfully installed $alt_pkg.tcz."
                    rm -f "$tcz_file"
                    return 0
                fi
                rm -f "$tcz_file"
            fi
        done
    done
    log_error "$pkg.tcz and alternatives not found in any mirror."
}

# Function to find and configure persistent storage
find_persistent_storage() {
    log_message "Checking for persistent storage..."
    local tce_dir=""
    # Check existing /mnt/*/tce directories
    for dir in /mnt/*/tce; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            tce_dir="$dir"
            break
        fi
    done
    # Try to mount and create tce directory
    if [ -z "$tce_dir" ]; then
        log_message "No persistent storage found. Scanning devices..."
        local devices=$(lsblk -dno NAME,TYPE,FSTYPE | grep disk | awk '{print "/dev/"$1}')
        for dev in $devices; do
            local mount_point="/mnt/$(basename $dev)"
            if [ ! -d "$mount_point" ]; then
                sudo mkdir -p "$mount_point" || continue
            fi
            if ! mount | grep -q "$mount_point"; then
                log_message "Attempting to mount $dev to $mount_point..."
                if sudo mount "$dev" "$mount_point" 2>/dev/null; then
                    log_message "Mounted $dev to $mount_point."
                else
                    log_message "Failed to mount $dev."
                    continue
                fi
            fi
            if [ -w "$mount_point" ]; then
                if sudo mkdir -p "$mount_point/tce" 2>/dev/null; then
                    tce_dir="$mount_point/tce"
                    log_message "Created $tce_dir for persistence."
                    break
                fi
            else
                log_message "$mount_point is not writable."
            fi
        done
    fi
    if [ -z "$tce_dir" ]; then
        log_message "No writable storage device found."
        lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT | tee -a "$LOG_FILE"
        log_error "No persistent storage available. Insert a USB drive, format it (e.g., sudo mkfs.ext4 /dev/sda1), mount it (sudo mount /dev/sda1 /mnt/sda1), create /tce/ (sudo mkdir -p /mnt/sda1/tce), and re-run the script."
    fi
    # Check disk space
    local free_space=$(df -k "$tce_dir" | tail -1 | awk '{print $4}')
    if [ "$free_space" -lt 10240 ]; then
        log_error "Insufficient disk space in $tce_dir ($free_space KB available). Need at least 10MB."
    fi
    log_message "Using $tce_dir for persistent storage."
    echo "$tce_dir"
}

# Initialize log file
: > "$LOG_FILE"
log_message "Starting BERKE0S installation on Tiny Core $TC_VERSION ($ARCH)"

# Step 1: Validate environment
log_message "Validating environment..."
if [ "$(whoami)" != "tc" ]; then
    log_error "This script must be run as user 'tc'."
fi
if ! command_exists tce-load; then
    log_error "tce-load not found. Ensure Tiny Core Linux is properly set up."
fi
check_internet

# Step 2: Install required tools and dependencies
log_message "Installing required tools and dependencies..."
DEPENDENCIES=(
    squashfs-tools python3.9 tk tcl python3.9-pip alsa bluez
    e2fsprogs nano htop bash network-manager tar zip dosfstools
    syslinux perl5 mpv scrot libnotify alsa-utils wireless-tools
    espeak util-linux Xvesa fbcon vesafb
)
for pkg in "${DEPENDENCIES[@]}"; do
    install_tcz "$pkg"
done

# Install Python dependencies
log_message "Installing Python dependencies..."
if ! command_exists pip3; then
    log_error "pip3 not found after installing python3.9-pip.tcz."
fi
PYTHON_DEPS=(psutil Pillow flask)
for dep in "${PYTHON_DEPS[@]}"; do
    if ! sudo pip3 install "$dep" --no-cache-dir 2>>"$LOG_FILE"; then
        log_error "Failed to install Python module $dep."
    fi
done

# Step 3: Create working directory and download BERKE0S.py
log_message "Creating working directory and downloading BERKE0S.py..."
if ! mkdir -p "$WORK_DIR"; then
    log_error "Failed to create working directory $WORK_DIR."
fi
cd "$WORK_DIR" || log_error "Failed to change to $WORK_DIR."
if ! wget -q -O BERKE0S.py "$GITHUB_URL" 2>>"$LOG_FILE"; then
    log_error "Failed to download BERKE0S.py from $GITHUB_URL."
fi
if [ ! -s BERKE0S.py ]; then
    log_error "Downloaded BERKE0S.py is empty."
fi
chmod +x BERKE0S.py

# Step 4: Create directory structure for .tcz package
log_message "Creating .tcz package structure..."
mkdir -p squashfs-root/usr/local/bin squashfs-root/home/tc/.berke0s/{themes,plugins} || log_error "Failed to create .tcz directory structure."
cp BERKE0S.py squashfs-root/usr/local/bin/ || log_error "Failed to copy BERKE0S.py to .tcz structure."
cd squashfs-root || log_error "Failed to change to squashfs-root."

# Step 5: Create .tcz package
log_message "Creating $TCZ_NAME..."
if ! mksquashfs . "$TCZ_DIR/$TCZ_NAME" -b 4k -noappend 2>>"$LOG_FILE"; then
    log_error "Failed to create $TCZ_NAME."
fi
cd ..
rm -rf squashfs-root

# Step 6: Add .tcz to onboot list
log_message "Configuring $TCZ_NAME to load on boot..."
mkdir -p /tmp/tce || log_error "Failed to create /tmp/tce."
if ! grep -q "$TCZ_NAME" /tmp/tce/onboot.lst 2>/dev/null; then
    echo "$TCZ_NAME" | sudo tee -a /tmp/tce/onboot.lst 2>>"$LOG_FILE" || log_error "Failed to add $TCZ_NAME to onboot.lst."
fi

# Step 7: Configure startup script
log_message "Configuring startup script..."
if ! grep -q "BERKE0S.py" "$STARTUP_SCRIPT" 2>/dev/null; then
    {
        echo "# Load framebuffer modules"
        echo "modprobe fbcon 2>/dev/null"
        echo "modprobe vesafb 2>/dev/null"
        echo "# Start X server and BERKE0S.py"
        echo "startx &"
        echo "/usr/local/bin/BERKE0S.py &"
    } | sudo tee -a "$STARTUP_SCRIPT" 2>>"$LOG_FILE" || log_error "Failed to update $STARTUP_SCRIPT."
fi
sudo chmod +x "$STARTUP_SCRIPT" || log_error "Failed to make $STARTUP_SCRIPT executable."

# Step 8: Configure X session
log_message "Configuring X session..."
if [ ! -f "/home/tc/.Xsession" ]; then
    echo "exec /usr/local/bin/BERKE0S.py" | sudo tee /home/tc/.Xsession 2>>"$LOG_FILE" || log_error "Failed to create /home/tc/.Xsession."
    sudo chmod +x /home/tc/.Xsession || log_error "Failed to make /home/tc/.Xsession executable."
fi

# Step 9: Create framebuffer udev rule
log_message "Creating framebuffer udev rule..."
if [ ! -f "$UDEV_RULE" ]; then
    echo 'SUBSYSTEM=="graphics", KERNEL=="fb[0-9]*", MODE="0666"' | sudo tee "$UDEV_RULE" 2>>"$LOG_FILE" || log_error "Failed to create $UDEV_RULE."
fi

# Step 10: Update hwdb
log_message "Updating hardware database..."
if command_exists systemd-hwdb; then
    sudo systemd-hwdb update 2>>"$LOG_FILE" || log_message "Warning: Failed to run systemd-hwdb update."
elif command_exists udevadm; then
    sudo udevadm hwdb --update 2>>"$LOG_FILE" || log_message "Warning: Failed to run udevadm hwdb --update."
else
    log_message "Warning: Neither systemd-hwdb nor udevadm found. Skipping hwdb update."
fi
if command_exists udevadm; then
    sudo udevadm control --reload-rules 2>>"$LOG_FILE" || log_message "Warning: Failed to reload udev rules."
    sudo udevadm trigger 2>>"$LOG_FILE" || log_message "Warning: Failed to trigger udev."
fi

# Step 11: Ensure persistence
log_message "Ensuring persistence..."
PERSIST_PATHS=(
    usr/local/bin/BERKE0S.py
    tce/optional/"$TCZ_NAME"
    tce/onboot.lst
    home/tc/.berke0s
    etc/udev/rules.d
    "$STARTUP_SCRIPT"
    home/tc/.Xsession
)
if [ ! -f "$FILETOOL_LST" ]; then
    sudo touch "$FILETOOL_LST" 2>>"$LOG_FILE" || log_error "Failed to create $FILETOOL_LST."
fi
for path in "${PERSIST_PATHS[@]}"; do
    if ! grep -q "^$path$" "$FILETOOL_LST" 2>/dev/null; then
        echo "$path" | sudo tee -a "$FILETOOL_LST" 2>>"$LOG_FILE" || log_error "Failed to add $path to $FILETOOL_LST."
    fi
done

# Step 12: Verify and configure persistent storage
TCE_DIR=$(find_persistent_storage)
sudo chmod u+w "$FILETOOL_LST" 2>>"$LOG_FILE" || log_error "Failed to set permissions on $FILETOOL_LST."

# Step 13: Customize system branding
log_message "Customizing system branding..."
BOOT_MSG_FILES=($(find_boot_files boot.msg))
ISOLINUX_FILES=($(find_boot_files isolinux.cfg))
SYSLINUX_FILES=($(find_boot_files syslinux.cfg))
for file in "${BOOT_MSG_FILES[@]}"; do
    sudo sed -i 's/Tiny Core/Berke0S/g' "$file" 2>>"$LOG_FILE" && log_message "Updated branding in $file" || log_message "Warning: Failed to update $file."
done
for file in "${ISOLINUX_FILES[@]}" "${SYSLINUX_FILES[@]}"; do
    sudo sed -i 's/Tiny Core/Berke0S/g' "$file" 2>>"$LOG_FILE" && log_message "Updated branding in $file" || log_message "Warning: Failed to update $file."
done
find /etc -type f -exec sudo sed -i 's/Tiny Core/Berke0S/g' {} + 2>>"$LOG_FILE" || log_message "Warning: Some /etc files could not be modified."

# Step 14: Save changes
log_message "Saving changes..."
if ! sudo filetool.sh -b 2>&1 | tee /tmp/filetool.log; then
    log_message "Error: filetool.sh -b failed. Log output:"
    cat /tmp/filetool.log >> "$LOG_FILE"
    log_message "Possible causes:"
    log_message "- No writable storage device at $TCE_DIR."
    log_message "- Insufficient disk space: $(df -h "$TCE_DIR")"
    log_message "- Filesystem is read-only or corrupted: $(lsblk -f)"
    log_message "Steps to fix:"
    log_message "1. Check mounted devices: ls /mnt"
    log_message "2. Ensure $TCE_DIR exists and is writable: ls -ld $TCE_DIR"
    log_message "3. Mount a device: sudo mount /dev/sda1 /mnt/sda1"
    log_message "4. Create $TCE_DIR: sudo mkdir -p $TCE_DIR"
    log_message "5. Re-run: sudo filetool.sh -b"
    log_error "Persistence setup failed."
fi
if [ -f "$TCE_DIR/mydata.tgz" ] && [ -s "$TCE_DIR/mydata.tgz" ]; then
    log_message "Backup created successfully: $TCE_DIR/mydata.tgz"
else
    log_error "Backup file $TCE_DIR/mydata.tgz not found or empty."
fi
rm -f /tmp/filetool.log

# Step 15: Clean up
log_message "Cleaning up..."
rm -rf "$WORK_DIR" /tmp/*.tcz || log_message "Warning: Failed to clean up some temporary files."

# Step 16: Inform user
log_message "Installation complete! Reboot to apply changes."
log_message "BERKE0S.py will run automatically on startup with Python 3.9."
log_message "System branding updated to Berke0S where possible."
log_message "Log file: $LOG_FILE"
log_message "Run 'sudo reboot' to start using Berke0S."
echo "Installation complete. Check $LOG_FILE for details."
echo "Run 'sudo reboot' to apply changes."

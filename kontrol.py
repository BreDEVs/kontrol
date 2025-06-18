import os
import sys
import time
import subprocess
import curses
import shutil
import signal
import json
import logging
import logging.handlers
import hashlib
from typing import List, Tuple, Optional
from pathlib import Path
import socket
import urllib.request
import urllib.error

# Configuration
SYSTEM_NAME = "BERKE OS"
BASE_DIR: Optional[Path] = None
TCE_DIR: Optional[Path] = None
APP_DIR: Optional[Path] = None
LOG_DIR = Path("/var/log/berke")
LOG_FILE = LOG_DIR / "install.log"
REPORT_FILE = LOG_DIR / "setup_report.txt"
EDEX_DIR: Optional[Path] = None
NODE_VERSION = "16.20.2"
NODE_URLS = [
    f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz",
    f"https://nodejs.org/download/release/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
]
NODE_CHECKSUM = "4f34f7f2e66ca676b9c831f6fb3b6c5b0c1f687a6e5f2f51dceda28e6b0a1ca8"
EDEX_URL = "https://github.com/GitSquared/edex-ui.git"
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "git", "wget", "curl", "tar", "coreutils", "util-linux", "busybox", "tce"]
REQUIRED_COMMANDS = ["python3.9", "wget", "curl", "git", "tar", "tce-load", "mount", "tce-status", "blkid", "busybox"]
MIN_TERM_SIZE = (20, 50)
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 10
USER = "tc"
GROUP = "staff"
MIN_DISK_SPACE_GB = 2
MAX_LOG_AGE_DAYS = 7
SUPPORTED_FILESYSTEMS = ["ext4", "vfat", "ext3", "ntfs", "fat32", "exfat", "btrfs"]
MIRROR_URLS = [
    "http://repo.tinycorelinux.net/",
    "http://mirror1.tinycorelinux.net/",
    "http://mirror2.tinycorelinux.net/",
    "http://distro.ibiblio.org/tinycorelinux/"
]

# Environment setup
os.environ["PATH"] = f"{os.environ.get('PATH', '')}:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin"
os.environ["HOME"] = f"/home/{USER}"

# Logger setup
def setup_logger() -> Optional[logging.Logger]:
    """Initialize logger with rotating file handler."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fix_permissions(LOG_DIR)
        for log in LOG_DIR.glob("install.log.*"):
            if log.stat().st_mtime < time.time() - MAX_LOG_AGE_DAYS * 86400:
                log.unlink(missing_ok=True)
        logger = logging.getLogger('BerkeOS')
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(str(LOG_FILE), maxBytes=1048576, backupCount=5)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        fix_permissions(LOG_FILE)
        logger.info("Logger initialized")
        print(f"[{SYSTEM_NAME}] Logging initialized at {LOG_FILE}")
        return logger
    except Exception as e:
        print(f"[{SYSTEM_NAME}] ERROR: Logger setup failed: {e}", file=sys.stderr)
        try:
            with open("/tmp/install_fallback.log", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: Logger setup failed: {e}\n")
        except Exception:
            pass
        return None

# Clean temporary files
def clean_temp(logger: Optional[logging.Logger] = None) -> None:
    """Remove temporary files older than 24 hours."""
    try:
        temp_dir = Path("/tmp")
        if temp_dir.exists():
            cutoff = time.time() - 86400
            for item in temp_dir.iterdir():
                try:
                    if item.stat().st_mtime < cutoff:
                        if item.is_file():
                            item.unlink(missing_ok=True)
                        elif item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                except Exception as e:
                    log_message(f"Failed to clean {item}: {e}", logger, "warning")
        log_message("Temporary files cleaned", logger)
    except Exception as e:
        log_message(f"Temporary files cleanup failed: {e}", logger, "error")

# Log message with fallback
def log_message(message: str, logger: Optional[logging.Logger] = None, level: str = "info") -> None:
    """Log message to file and console with fallback."""
    try:
        if logger:
            getattr(logger, level)(message)
        else:
            fallback_log = Path("/tmp/install_fallback.log")
            if fallback_log.parent.exists() and os.access(fallback_log.parent, os.W_OK):
                with open(fallback_log, "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{level.upper()}]: {message}\n")
            print(f"[{SYSTEM_NAME}] {level.upper()}: {message}", file=sys.stderr)
    except Exception:
        print(f"[{SYSTEM_NAME}] ERROR: Failed to log message: {message}", file=sys.stderr)

# Center text for curses
def center_text(text: str, width: int) -> Tuple[str, int]:
    """Center text within given width."""
    text = text[:width-4]
    padding = (width - len(text)) // 2
    return text, padding

# Error display
def display_error(stdscr, stage: str, error_msg: str, logger: Optional[logging.Logger], suggestion: str = "") -> None:
    """Display error message in curses or terminal."""
    specific_suggestions = {
        "DEPENDENCIES": (
            "Ensure internet connection: 'ping 8.8.8.8'. "
            "Try: 'sudo tce-load -wi <package>' (e.g., coreutils, util-linux, busybox, Xorg-7.7). "
            "Verify: 'which mount blkid tce-load tce-status busybox wget tar Xorg node npm'. "
            "Check mirror: 'cat /opt/tcemirror'. "
            "Set mirror: 'echo \"http://repo.tinycorelinux.net/\" | sudo tee /opt/tcemirror'."
        ),
        "DISK SETUP": (
            "Verify disk connection and format (ext4/vfat/ext3/ntfs/fat32/exfat/btrfs). "
            "Check: 'cat /proc/partitions', 'ls /dev/sd* /dev/nvme* /dev/mmcblk*', 'blkid'. "
            "Mount manually: 'sudo mount /dev/sda1 /mnt/disk'. "
            "Install util-linux: 'sudo tce-load -wi util-linux'."
        ),
        "eDEX-UI DOWNLOAD": (
            "Ensure GitHub access and git: 'sudo tce-load -wi git'. "
            "Check internet: 'ping 8.8.8.8'."
        ),
        "eDEX-UI INSTALL": (
            "Verify Node.js: 'node -v', 'npm -v'. "
            "Install npm dependencies: 'cd /mnt/disk/apps/edex-ui && npm install'. "
            "Check disk space: 'df -h /mnt/disk'."
        ),
        "eDEX-UI START": (
            "Check Xorg: 'sudo tce-load -wi Xorg-7.7'. "
            "Verify: 'echo $DISPLAY', 'which Xorg'. "
            "Check Node.js: 'which node npm', 'node -v'. "
            "Start manually: 'cd /mnt/disk/apps/edex-ui && npm start'."
        )
    }
    suggestion = suggestion or specific_suggestions.get(stage, "Check logs for details.")
    error_summary = f"""
[{SYSTEM_NAME}] ERROR!
Stage: {stage}
Error: {error_msg}
Logs: {LOG_FILE}, /tmp/install_fallback.log
Suggestion: {suggestion}
View logs: cat {LOG_FILE}
Report: github.com/BreDEVs/kontrol/issues
"""
    log_message(f"Error in {stage}: {error_msg}", logger, "error")
    if stdscr:
        try:
            stdscr.clear()
            rows, cols = stdscr.getmaxyx()
            lines = [
                ("BERKE OS - ERROR!", curses.A_BOLD | curses.color_pair(1), 2),
                (f"Stage: {stage}", curses.color_pair(2), 4),
                (f"Error: {error_msg}", curses.color_pair(2), 6),
                (f"Logs: {LOG_FILE}, /tmp/install_fallback.log", curses.color_pair(2), 8),
                (f"Suggestion: {suggestion}", curses.color_pair(2), 10),
                ("View logs: cat /var/log/berke/install.log", curses.color_pair(2), 12),
                ("Report: github.com/BreDEVs/kontrol/issues", curses.color_pair(2), 14),
                ("Press any key to exit", curses.color_pair(1), 16)
            ]
            for text, attr, row in lines:
                formatted_text, x = center_text(text, cols)
                stdscr.addstr(row, x, formatted_text, attr)
            stdscr.refresh()
            stdscr.getch()
        except Exception as e:
            log_message(f"Curses error display failed: {e}", logger, "error")
            print(error_summary, file=sys.stderr)
    else:
        print(error_summary, file=sys.stderr)
    sys.exit(1)

# Main display for curses
def update_display(stdscr, stages: List[Tuple[str, str]], current_stage: int, sub_status: str, logger: Optional[logging.Logger]) -> None:
    """Update curses display with installation progress."""
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        title, title_x = center_text("BERKE OS - Setup", cols)
        stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))
        total_stages = len(stages)
        for i, (stage_name, status) in enumerate(stages):
            row = 5 + i * 2
            if row >= rows - 2:
                break
            progress = "█" * int((i + 1 if status == "DONE" else i) * 10 / total_stages)
            stage_text = f"{i+1}. {stage_name[:16]}: [{'*' if i == current_stage and status == '/' else 'DONE' if status == 'DONE' else '-'}] {progress}"
            text, x = center_text(stage_text, cols)
            attr = curses.color_pair(3) | curses.A_BOLD if i == current_stage and status == "/" else curses.color_pair(4) if status == "DONE" else curses.color_pair(2)
            stdscr.addstr(row, x, text, attr)
            if i == current_stage and status == "/":
                sub_text, sub_x = center_text(f"{sub_status[:26]}", cols)
                stdscr.addstr(row + 1, sub_x, sub_text, curses.color_pair(3))
        stdscr.refresh()
    except Exception as e:
        log_message(f"Display update failed: {e}", logger, "error")

# Fix permissions
def fix_permissions(path: Path, logger: Optional[logging.Logger] = None) -> None:
    """Fix permissions recursively for a path."""
    try:
        parent = path.parent
        while parent != parent.parent:
            if parent.exists() and not os.access(parent, os.W_OK):
                os.chmod(parent, 0o775)
                try:
                    os.chown(parent, os.getuid(), os.getgid())
                except Exception as e:
                    log_message(f"Chown failed for {parent}: {e}", logger, "warning")
                log_message(f"Permissions fixed for parent {parent}", logger)
            parent = parent.parent
        if path.exists():
            if not os.access(path, os.W_OK):
                os.chmod(path, 0o775 if path.is_dir() else 0o664)
                try:
                    os.chown(path, os.getuid(), os.getgid())
                except Exception as e:
                    log_message(f"Chown failed for {path}: {e}", logger, "warning")
                log_message(f"Permissions fixed for {path}", logger)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            fix_permissions(path.parent, logger)
    except Exception as e:
        log_message(f"Permission fix failed for {path}: {e}", logger, "error")
        raise Exception(f"Permission fix failed: {e}")

# Configure TCE mirror
def configure_tce_mirror(logger: Optional[logging.Logger]) -> None:
    """Set a working TCE mirror."""
    try:
        tce_mirror_file = Path("/opt/tcemirror")
        for mirror in MIRROR_URLS:
            try:
                urllib.request.urlopen(mirror, timeout=5)
                with open(tce_mirror_file, "w") as f:
                    f.write(mirror)
                fix_permissions(tce_mirror_file, logger)
                log_message(f"TCE mirror set to {mirror}", logger)
                print(f"[{SYSTEM_NAME}] TCE mirror set to {mirror}")
                return
            except Exception as e:
                log_message(f"Mirror {mirror} failed: {e}", logger, "warning")
        raise Exception("No working TCE mirror found. Check internet: 'ping 8.8.8.8'. Set manually: 'echo \"http://repo.tinycorelinux.net/\" | sudo tee /opt/tcemirror'")
    except Exception as e:
        log_message(f"TCE mirror configuration failed: {e}", logger, "error")
        raise

# Detect disk
def detect_disk(logger: Optional[logging.Logger], stdscr=None) -> Tuple[Path, str]:
    """Detect and mount a suitable disk with user selection."""
    try:
        mount_point = Path("/mnt/disk")
        mount_point.mkdir(parents=True, exist_ok=True)
        fix_permissions(mount_point, logger)
        mount_cmd = shutil.which("mount")
        if not mount_cmd:
            raise Exception("mount command not found. Install coreutils or busybox: 'sudo tce-load -wi coreutils' or 'sudo tce-load -wi busybox'")

        # Check /proc/partitions for available disks
        available_disks = []
        try:
            with open("/proc/partitions", "r") as f:
                lines = f.readlines()
                for line in lines[2:]:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        disk_name = f"/dev/{parts[3]}"
                        if any(disk_name.startswith(prefix) for prefix in ["/dev/sd", "/dev/nvme", "/dev/hd", "/dev/mmcblk"]) and disk_name[-1].isdigit():
                            available_disks.append(disk_name)
        except FileNotFoundError:
            raise Exception("/proc/partitions not found. Ensure kernel supports partitions.")

        if not available_disks:
            disk_list = "None detected"
            try:
                disk_list = ", ".join(os.listdir("/dev") if os.path.exists("/dev") else ["No /dev"])
            except Exception:
                pass
            raise Exception(
                f"No suitable disk found. Available devices: {disk_list}. "
                "Ensure a disk is connected (USB, SATA, NVMe, SD card). Check: 'ls /dev/sd* /dev/nvme* /dev/mmcblk*'"
            )

        log_message(f"Detected disks: {', '.join(available_disks)}", logger)
        print(f"[{SYSTEM_NAME}] Detected disks: {', '.join(available_disks)}")

        # Gather disk info
        blkid_cmd = shutil.which("blkid")
        disk_info = []
        for disk in available_disks:
            info = {"device": disk, "fstype": "Unknown", "size": "Unknown"}
            if blkid_cmd:
                try:
                    result = subprocess.run([blkid_cmd, disk], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            if "TYPE=" in line:
                                info["fstype"] = line.split("TYPE=")[1].strip('"')
                                break
                except Exception as e:
                    log_message(f"blkid failed for {disk}: {e}", logger, "warning")
            try:
                with open("/proc/partitions", "r") as f:
                    for line in f.readlines()[2:]:
                        parts = line.strip().split()
                        if len(parts) >= 4 and f"/dev/{parts[3]}" == disk:
                            size_mb = int(parts[2]) / 1024
                            info["size"] = f"{size_mb:.2f} MB"
                            break
            except Exception:
                pass
            disk_info.append(info)

        # Check /proc/mounts for mounted disks
        for disk in available_disks:
            try:
                with open("/proc/mounts", "r") as f:
                    mounts = f.readlines()
                    for line in mounts:
                        if disk in line:
                            parts = line.split()
                            mount_fstype = parts[2]
                            if mount_fstype not in SUPPORTED_FILESYSTEMS:
                                log_message(f"Disk {disk} has unsupported filesystem: {mount_fstype}", logger, "warning")
                                continue
                            current_mount = parts[1]
                            if current_mount != str(mount_point):
                                try:
                                    subprocess.run([mount_cmd, "-o", "remount,rw", current_mount], check=True, timeout=TIMEOUT_SECONDS, capture_output=True, text=True)
                                    log_message(f"Disk {disk} remounted read-write at {current_mount}", logger)
                                    return Path(current_mount), disk
                                except subprocess.CalledProcessError as e:
                                    log_message(f"Failed to remount {disk} at {current_mount}: {e.stderr}", logger, "warning")
                                    continue
                            log_message(f"Disk {disk} already mounted at {current_mount}", logger)
                            return Path(current_mount), disk

                # Try mounting unmounted disk
                disk_fstype = next((info["fstype"] for info in disk_info if info["device"] == disk), "Unknown")
                if disk_fstype != "Unknown" and disk_fstype not in SUPPORTED_FILESYSTEMS:
                    log_message(f"Disk {disk} has unsupported filesystem: {disk_fstype}", logger, "warning")
                    continue
                try:
                    result = subprocess.run([mount_cmd, disk, str(mount_point)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True, text=True)
                    subprocess.run([mount_cmd, "-o", "remount,rw", str(mount_point)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True, text=True)
                    fix_permissions(mount_point, logger)
                    log_message(f"Disk {disk} mounted at {mount_point}", logger)
                    print(f"[{SYSTEM_NAME}] Disk {disk} mounted at {mount_point}")
                    return mount_point, disk
                except subprocess.CalledProcessError as e:
                    log_message(f"Failed to mount {disk} at {mount_point}: {e.stderr}", logger, "warning")
                    continue
            except Exception as e:
                log_message(f"Error processing disk {disk}: {e}", logger, "warning")
                continue

        # Interactive disk selection
        error_msg = (
            f"No suitable disk found. Supported formats: {', '.join(SUPPORTED_FILESYSTEMS)}.\n"
            f"Detected disks:\n"
        )
        for info in disk_info:
            error_msg += f"  {info['device']}: FS={info['fstype']}, Size={info['size']}\n"
        error_msg += (
            "Try: 'cat /proc/partitions', 'ls /dev/sd* /dev/nvme* /dev/mmcblk*', 'blkid'. "
            "Mount manually: 'sudo mount /dev/sda1 /mnt/disk'"
        )
        log_message(f"Disk detection failed: {error_msg}", logger, "error")
        if stdscr is None:
            print(f"[{SYSTEM_NAME}] ERROR: Disk detection failed:\n{error_msg}", file=sys.stderr)
            print(f"[{SYSTEM_NAME}] Select a disk (e.g., /dev/sda1) or press Enter to exit:")
            for i, info in enumerate(disk_info, 1):
                print(f"  {i}. {info['device']} (FS: {info['fstype']}, Size: {info['size']})")
            print(f"[{SYSTEM_NAME}] Enter disk number or device path: ", end="")
            user_input = input().strip()
            if not user_input:
                sys.exit(1)
            if user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(disk_info):
                    disk_input = disk_info[idx]["device"]
                else:
                    raise Exception(f"Invalid selection: {user_input}. Choose a number between 1 and {len(disk_info)}.")
            else:
                disk_input = user_input
            if not os.path.exists(disk_input) or not any(disk_input.startswith(prefix) for prefix in ["/dev/sd", "/dev/nvme", "/dev/hd", "/dev/mmcblk"]):
                raise Exception(f"Invalid disk: {disk_input}. Check: 'ls /dev/sd* /dev/nvme* /dev/mmcblk*'")
            try:
                subprocess.run([mount_cmd, disk_input, str(mount_point)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True, text=True)
                subprocess.run([mount_cmd, "-o", "remount,rw", str(mount_point)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True, text=True)
                fix_permissions(mount_point, logger)
                log_message(f"Manually mounted {disk_input} at {mount_point}", logger)
                return mount_point, disk_input
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to mount {disk_input}: {e.stderr}")
        raise Exception(error_msg)
    except Exception as e:
        log_message(f"Disk detection failed: {e}", logger, "error")
        raise

# Check internet connection
def check_internet(logger: Optional[logging.Logger]) -> bool:
    """Verify internet connectivity."""
    try:
        # Test DNS and HTTP
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        socket.create_connection(("1.1.1.1", 53), timeout=5)
        urllib.request.urlopen("https://www.google.com", timeout=5)
        log_message("Internet connection established", logger)
        return True
    except Exception as e:
        log_message(f"Internet connection failed: {e}", logger, "error")
        return False

# Install dependencies
def install_dependencies(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    """Install required packages and commands."""
    log_message("Installing dependencies", logger)
    print(f"[{SYSTEM_NAME}] Installing dependencies...")
    sub_status = ""

    try:
        clean_temp(logger)
        if not check_internet(logger):
            raise Exception("No internet connection. Check: 'ping 8.8.8.8'. Connect to a network and try again.")
        configure_tce_mirror(logger)
        # Ensure tce is installed first
        tce_load_cmd = shutil.which("tce-load")
        if not tce_load_cmd:
            sub_status = "Installing tce..."
            if stdscr:
                update_display(stdscr, stages, current_stage, sub_status, logger)
            try:
                result = subprocess.run(["/usr/bin/tce-load", "-w", "-i", "tce"], check=True, timeout=300, capture_output=True, text=True)
                log_message(f"tce installed: {result.stdout}", logger)
                print(f"[{SYSTEM_NAME}] tce installed")
            except subprocess.CalledProcessError as e:
                raise Exception(f"tce installation failed: {e.stderr}. Try: 'sudo tce-load -wi tce'")
        for cmd in REQUIRED_COMMANDS:
            sub_status = f"Checking {cmd}..."
            if stdscr:
                update_display(stdscr, stages, current_stage, sub_status, logger)
            cmd_path = shutil.which(cmd)
            if not cmd_path:
                pkg = (
                    "coreutils" if cmd == "mount" else
                    "util-linux" if cmd == "blkid" else
                    "busybox" if cmd == "busybox" else
                    cmd
                )
                tce_load_cmd = shutil.which("tce-load")
                if not tce_load_cmd:
                    raise Exception("tce-load not found. Install tce: 'sudo tce-load -wi tce'")
                for attempt in range(RETRY_ATTEMPTS):
                    try:
                        result = subprocess.run([tce_load_cmd, "-w", "-i", pkg], check=True, timeout=300, capture_output=True, text=True)
                        log_message(f"{pkg} installed for {cmd}: {result.stdout}", logger)
                        print(f"[{SYSTEM_NAME}] {pkg} installed for {cmd}")
                        cmd_path = shutil.which(cmd)
                        if not cmd_path:
                            raise Exception(f"Command {cmd} not found after installing {pkg}")
                        break
                    except subprocess.CalledProcessError as e:
                        if attempt == RETRY_ATTEMPTS - 1:
                            suggestion = f"Install {cmd}: 'sudo tce-load -wi {pkg}'. Check mirror: 'cat /opt/tcemirror'"
                            raise Exception(f"Required command {cmd} not found. {suggestion}. Error: {e.stderr}")
                        log_message(f"Retrying {pkg} installation (attempt {attempt+2}/{RETRY_ATTEMPTS})", logger)
                        time.sleep(2)
            log_message(f"{cmd} found: {cmd_path}", logger)
            print(f"[{SYSTEM_NAME}] {cmd} found: {cmd_path}")
        for pkg in REQUIRED_TCE_PACKAGES:
            sub_status = f"Installing {pkg}..."
            if stdscr:
                update_display(stdscr, stages, current_stage, sub_status, logger)
            tce_status_cmd = shutil.which("tce-status")
            if not tce_status_cmd:
                raise Exception("tce-status not found. Install tce: 'sudo tce-load -wi tce'")
            result = subprocess.run([tce_status_cmd, "-i"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
            if pkg not in result.stdout:
                tce_load_cmd = shutil.which("tce-load")
                if not tce_load_cmd:
                    raise Exception("tce-load not found. Install tce: 'sudo tce-load -wi tce'")
                for attempt in range(RETRY_ATTEMPTS):
                    try:
                        result = subprocess.run([tce_load_cmd, "-w", "-i", pkg], check=True, timeout=300, capture_output=True, text=True)
                        log_message(f"{pkg} installed: {result.stdout}", logger)
                        print(f"[{SYSTEM_NAME}] {pkg} installed")
                        break
                    except subprocess.CalledProcessError as e:
                        if attempt == RETRY_ATTEMPTS - 1:
                            raise Exception(f"Failed to install {pkg} after {RETRY_ATTEMPTS} attempts: {e.stderr}. Try: 'sudo tce-load -wi {pkg}'")
                        log_message(f"Retrying {pkg} installation (attempt {attempt+2}/{RETRY_ATTEMPTS})", logger)
                        time.sleep(2)
            fix_permissions(TCE_DIR, logger)
        sub_status = "Installing Node.js..."
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        node_cmd = shutil.which("node")
        if not node_cmd or f"v{NODE_VERSION}" not in subprocess.run([node_cmd, "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS).stdout:
            node_tar = Path("/tmp/node.tar.xz")
            target_dir = Path("/usr/local/node")
            wget_cmd = shutil.which("wget")
            if not wget_cmd:
                tce_load_cmd = shutil.which("tce-load")
                if not tce_load_cmd:
                    raise Exception("tce-load not found. Install tce: 'sudo tce-load -wi tce'")
                subprocess.run([tce_load_cmd, "-w", "-i", "wget"], check=True, timeout=300, capture_output=True, text=True)
                wget_cmd = shutil.which("wget")
                if not wget_cmd:
                    raise Exception("wget not found after installation. Try: 'sudo tce-load -wi wget'")
            for url in NODE_URLS:
                for attempt in range(RETRY_ATTEMPTS):
                    try:
                        result = subprocess.run([wget_cmd, "-O", str(node_tar), url], check=True, timeout=300, capture_output=True, text=True)
                        log_message(f"Node.js downloaded from {url}: {result.stdout}", logger)
                        with open(node_tar, "rb") as f:
                            if hashlib.sha256(f.read()).hexdigest() != NODE_CHECKSUM:
                                log_message("Node.js checksum mismatch, trying next URL", logger, "warning")
                                continue
                        break
                    except subprocess.CalledProcessError as e:
                        if attempt == RETRY_ATTEMPTS - 1:
                            log_message(f"Node.js download failed from {url}: {e.stderr}", logger, "warning")
                            continue
                        log_message(f"Retrying Node.js download from {url} (attempt {attempt+2}/{RETRY_ATTEMPTS})", logger)
                        time.sleep(2)
                if node_tar.exists():
                    break
            if not node_tar.exists():
                raise Exception(f"Node.js download failed from all URLs after {RETRY_ATTEMPTS} attempts")
            target_dir.mkdir(parents=True, exist_ok=True)
            tar_cmd = shutil.which("tar")
            if not tar_cmd:
                tce_load_cmd = shutil.which("tce-load")
                if not tce_load_cmd:
                    raise Exception("tce-load not found. Install tce: 'sudo tce-load -wi tce'")
                subprocess.run([tce_load_cmd, "-w", "-i", "tar"], check=True, timeout=300, capture_output=True, text=True)
                tar_cmd = shutil.which("tar")
                if not tar_cmd:
                    raise Exception("tar not found after installation. Try: 'sudo tce-load -wi tar'")
            result = subprocess.run([tar_cmd, "-xJf", str(node_tar), "-C", str(target_dir), "--strip-components=1"], check=True, timeout=300, capture_output=True, text=True)
            log_message(f"Node.js extracted: {result.stdout}", logger)
            for binary in ["node", "npm"]:
                binary_path = target_dir / "bin" / binary
                link_path = Path(f"/usr/local/bin/{binary}")
                if link_path.exists():
                    link_path.unlink(missing_ok=True)
                os.symlink(binary_path, link_path)
            fix_permissions(target_dir, logger)
            node_cmd = shutil.which("node")
            if not node_cmd or f"v{NODE_VERSION}" not in subprocess.run([node_cmd, "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS).stdout:
                raise Exception(f"Node.js v{NODE_VERSION} installation verification failed")
            log_message(f"Node.js v{NODE_VERSION} installed", logger)
            print(f"[{SYSTEM_NAME}] Node.js v{NODE_VERSION} installed")
        sub_status = "Dependencies installed"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] Dependencies installed successfully")
    except Exception as e:
        log_message(f"Dependency installation failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)

# Verify disk
def verify_disk(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger], disk_device: str) -> None:
    """Verify disk space and setup directories."""
    log_message(f"Verifying disk {disk_device}", logger)
    print(f"[{SYSTEM_NAME}] Verifying disk {disk_device}...")
    sub_status = ""

    try:
        clean_temp(logger)
        sub_status = "Checking disk space..."
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        disk_usage = shutil.disk_usage(BASE_DIR)
        free_space_gb = disk_usage.free / (1024 ** 3)
        if free_space_gb < MIN_DISK_SPACE_GB:
            raise Exception(f"Insufficient disk space: {free_space_gb:.2f} GB available, need {MIN_DISK_SPACE_GB} GB")
        sub_status = "Creating directories..."
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        APP_DIR.mkdir(parents=True, exist_ok=True)
        fix_permissions(APP_DIR, logger)
        sub_status = "Disk verified"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] Disk {disk_device} verified successfully")
    except Exception as e:
        log_message(f"Disk verification failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)

# Download eDEX-UI
def download_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    """Clone eDEX-UI repository."""
    log_message("Downloading eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Downloading eDEX-UI...")
    sub_status = ""

    try:
        clean_temp(logger)
        if not check_internet(logger):
            raise Exception("No internet connection. Check: 'ping 8.8.8.8'. Connect to a network and try again.")
        sub_status = "Cloning eDEX-UI..."
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        if EDEX_DIR.exists():
            shutil.rmtree(EDEX_DIR, ignore_errors=True)
        git_cmd = shutil.which("git")
        if not git_cmd:
            raise Exception("git command not found. Install git: 'sudo tce-load -wi git'")
        for attempt in range(RETRY_ATTEMPTS):
            try:
                result = subprocess.run([git_cmd, "clone", "--depth", "1", EDEX_URL, str(EDEX_DIR)], check=True, timeout=600, capture_output=True, text=True)
                log_message(f"eDEX-UI cloned: {result.stdout}", logger)
                break
            except subprocess.CalledProcessError as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"eDEX-UI clone failed after {RETRY_ATTEMPTS} attempts: {e.stderr}")
                log_message(f"Retrying eDEX-UI clone (attempt {attempt+2}/{RETRY_ATTEMPTS})", logger)
                time.sleep(2)
        fix_permissions(EDEX_DIR, logger)
        if not (EDEX_DIR / "package.json").exists():
            raise Exception("eDEX-UI package.json not found. Clone may have failed.")
        sub_status = "eDEX-UI downloaded"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI downloaded successfully")
    except Exception as e:
        log_message(f"eDEX-UI download failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)

# Install eDEX-UI
def install_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    """Install eDEX-UI dependencies and configure."""
    log_message("Installing eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Installing eDEX-UI...")
    sub_status = ""

    try:
        clean_temp(logger)
        sub_status = "Installing npm dependencies..."
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        npm_cmd = shutil.which("npm")
        if not npm_cmd:
            raise Exception("npm command not found. Ensure Node.js is installed: 'node -v'")
        env = os.environ.copy()
        env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
        for attempt in range(RETRY_ATTEMPTS):
            try:
                result = subprocess.run([npm_cmd, "install"], cwd=str(EDEX_DIR), check=True, timeout=600, capture_output=True, text=True, env=env)
                log_message(f"eDEX-UI npm dependencies installed: {result.stdout}", logger)
                break
            except subprocess.CalledProcessError as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"npm install failed after {RETRY_ATTEMPTS} attempts: {e.stderr}")
                log_message(f"Retrying npm install (attempt {attempt+2}/{RETRY_ATTEMPTS})", logger)
                time.sleep(2)
        fix_permissions(EDEX_DIR / "node_modules", logger)
        sub_status = "Configuring eDEX-UI..."
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        settings_path = EDEX_DIR / "settings.json"
        settings = {
            "shell": "/bin/sh",
            "theme": "tron",
            "window": {
                "title": f"{SYSTEM_NAME} eDEX-UI",
                "size": "fullscreen"
            },
            "autoStart": True,
            "fontSize": 14,
            "keyboardLayout": "us",
            "autoUpdate": False
        }
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        fix_permissions(settings_path, logger)
        sub_status = "eDEX-UI installed"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI installed successfully")
    except Exception as e:
        log_message(f"eDEX-UI installation failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)

# Start eDEX-UI
def start_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> bool:
    """Launch eDEX-UI with Xorg."""
    log_message("Starting eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Starting eDEX-UI...")
    sub_status = ""
    process = None
    xorg_process = None

    def cleanup():
        if process and process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except Exception:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        if xorg_process and xorg_process.poll() is None:
            try:
                os.killpg(os.getpgid(xorg_process.pid), signal.SIGTERM)
                xorg_process.wait(timeout=5)
            except Exception:
                os.killpg(os.getpgid(xorg_process.pid), signal.SIGKILL)
        clean_temp(logger)

    try:
        clean_temp(logger)
        sub_status = "Starting Xorg..."
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        os.environ["DISPLAY"] = ":0"
        xorg_cmd = shutil.which("Xorg")
        if not xorg_cmd:
            raise Exception("Xorg command not found. Install Xorg: 'sudo tce-load -wi Xorg-7.7'")
        xorg_process = subprocess.Popen(
            [xorg_cmd, ":0", "-quiet"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        time.sleep(3)
        if xorg_process.poll() is not None:
            stdout, stderr = xorg_process.communicate(timeout=5)
            raise Exception(f"Xorg failed to start: {stderr or 'Unknown error'}")
        sub_status = "Launching eDEX-UI..."
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        env = os.environ.copy()
        env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
        env["DISPLAY"] = ":0"
        npm_cmd = shutil.which("npm")
        if not npm_cmd:
            raise Exception("npm command not found. Ensure Node.js is installed: 'node -v'")
        process = subprocess.Popen(
            [npm_cmd, "start"],
            cwd=str(EDEX_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,
            env=env
        )
        time.sleep(15)
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=5)
            raise Exception(f"eDEX-UI failed to start: {stderr or 'Unknown error'}")
        log_message("eDEX-UI started successfully", logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI started successfully")
        return True
    except Exception as e:
        log_message(f"eDEX-UI startup failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)
        return False
    finally:
        if not process or process.poll() is not None:
            cleanup()

# Quick check for eDEX-UI
def quick_check_edex_ui(logger: Optional[logging.Logger]) -> bool:
    """Verify eDEX-UI installation."""
    log_message("Checking eDEX-UI installation", logger)
    print(f"[{SYSTEM_NAME}] Checking eDEX-UI...")
    try:
        if not EDEX_DIR.exists() or not (EDEX_DIR / "package.json").exists():
            log_message("eDEX-UI directory or package.json missing", logger, "warning")
            return False
        node_cmd = shutil.which("node")
        npm_cmd = shutil.which("npm")
        if not node_cmd or not npm_cmd:
            log_message("Node.js or npm not found", logger, "warning")
            return False
        env = os.environ.copy()
        env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
        env["DISPLAY"] = ":0"
        xorg_cmd = shutil.which("Xorg")
        if not xorg_cmd:
            log_message("Xorg not found, skipping eDEX-UI test", logger, "warning")
            return False
        xorg_process = subprocess.Popen(
            [xorg_cmd, ":0", "-quiet"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        time.sleep(3)
        if xorg_process.poll() is not None:
            stdout, stderr = xorg_process.communicate(timeout=5)
            log_message(f"Xorg test failed: {stderr or 'Unknown error'}", logger, "warning")
            os.killpg(os.getpgid(xorg_process.pid), signal.SIGTERM)
            return False
        process = subprocess.Popen(
            [npm_cmd, "start"],
            cwd=str(EDEX_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,
            env=env
        )
        time.sleep(5)
        if process.poll() is None:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            os.killpg(os.getpgid(xorg_process.pid), signal.SIGTERM)
            xorg_process.wait(timeout=5)
            log_message("eDEX-UI quick check passed", logger)
            print(f"[{SYSTEM_NAME}] eDEX-UI check passed")
            return True
        stdout, stderr = process.communicate(timeout=5)
        log_message(f"eDEX-UI quick check failed: {stderr or 'Unknown error'}", logger, "warning")
        os.killpg(os.getpgid(xorg_process.pid), signal.SIGTERM)
        return False
    except Exception as e:
        log_message(f"eDEX-UI quick check failed: {e}", logger, "error")
        return False

# Generate setup report
def generate_setup_report(start_time: float, errors: List[str], logger: Optional[logging.Logger]) -> None:
    """Generate detailed setup report."""
    try:
        duration = time.time() - start_time
        disk_usage = shutil.disk_usage(BASE_DIR)
        used_space_gb = (disk_usage.total - disk_usage.free) / (1024 ** 3)
        free_space_gb = disk_usage.free / (1024 ** 3)
        system_info = []
        try:
            with open("/proc/partitions", "r") as f:
                system_info.append("Disk Partitions:\n" + f.read())
        except Exception:
            system_info.append("Disk Partitions: Unable to read /proc/partitions")
        try:
            with open("/proc/mounts", "r") as f:
                system_info.append("Mounts:\n" + f.read())
        except Exception:
            system_info.append("Mounts: Unable to read /proc/mounts")
        try:
            result = subprocess.run(["uname", "-a"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
            system_info.append(f"System Info: {result.stdout.strip()}")
        except Exception:
            system_info.append("System Info: Unable to retrieve")
        try:
            result = subprocess.run(["df", "-h"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
            system_info.append(f"Disk Usage:\n{result.stdout.strip()}")
        except Exception:
            system_info.append("Disk Usage: Unable to retrieve")
        installed_packages = []
        tce_status_cmd = shutil.which("tce-status")
        if tce_status_cmd:
            try:
                result = subprocess.run([tce_status_cmd, "-i"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
                installed_packages.append("Installed Packages:\n" + result.stdout.strip())
            except Exception:
                installed_packages.append("Installed Packages: Unable to retrieve")
        report = [
            f"BERKE OS Setup Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {duration:.2f} seconds",
            f"Disk Usage: {used_space_gb:.2f} GB used, {free_space_gb:.2f} GB free",
            f"Errors Encountered: {len(errors)}",
            "\nSystem Information:"
        ]
        report.extend(system_info)
        report.extend(installed_packages)
        report.append("\nErrors:")
        report.extend(errors if errors else ["None"])
        with open(REPORT_FILE, "w") as f:
            f.write("\n".join(report))
        fix_permissions(REPORT_FILE, logger)
        log_message(f"Setup report generated at {REPORT_FILE}", logger)
        print(f"[{SYSTEM_NAME}] Report generated at {REPORT_FILE}")
    except Exception as e:
        log_message(f"Report generation failed: {e}", logger, "error")

# Main function
def main(stdscr=None) -> bool:
    """Main installation function."""
    global BASE_DIR, TCE_DIR, APP_DIR, EDEX_DIR
    logger = setup_logger()
    start_time = time.time()
    errors = []
    log_message(f"{SYSTEM_NAME} setup started", logger)
    print(f"[{SYSTEM_NAME}] Starting setup at {time.strftime('%H:%M:%S')}...")

    try:
        BASE_DIR, disk_device = detect_disk(logger, stdscr)
        TCE_DIR = BASE_DIR / "tce"
        APP_DIR = BASE_DIR / "apps"
        EDEX_DIR = APP_DIR / "edex-ui"
        fix_permissions(BASE_DIR, logger)
    except Exception as e:
        errors.append(f"Disk setup: {e}")
        log_message(f"Disk setup failed: {e}", logger, "error")
        display_error(stdscr, "DISK SETUP", str(e), logger)

    if stdscr:
        try:
            curses.curs_set(0)
            stdscr.timeout(100)
            rows, cols = stdscr.getmaxyx()
            if rows < MIN_TERM_SIZE[0] or cols < MIN_TERM_SIZE[1]:
                raise Exception(f"Terminal too small: need {MIN_TERM_SIZE[1]}x{MIN_TERM_SIZE[0]}")
            curses.start_color()
            curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        except Exception as e:
            log_message(f"Curses setup failed: {e}", logger, "warning")
            stdscr = None

    if quick_check_edex_ui(logger):
        log_message("eDEX-UI already installed, attempting to start", logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI already installed, starting...")
        if start_edex_ui(stdscr, [("eDEX-UI START", "/")], 0, logger):
            generate_setup_report(start_time, errors, logger)
            print(f"[{SYSTEM_NAME}] Setup completed successfully, eDEX-UI running")
            return True

    stages = [
        ("DEPENDENCIES", "/"),
        ("DISK SETUP", "-"),
        ("eDEX-UI DOWNLOAD", "-"),
        ("eDEX-UI INSTALL", "-"),
        ("eDEX-UI START", "-")
    ]
    functions = [
        install_dependencies,
        lambda stdscr, stages, i, logger: verify_disk(stdscr, stages, i, logger, disk_device),
        download_edex_ui,
        install_edex_ui,
        start_edex_ui
    ]

    for i, func in enumerate(functions):
        try:
            stages[i] = (stages[i][0], "/")
            if stdscr:
                update_display(stdscr, stages, i, "Starting stage...", logger)
            func(stdscr, stages, i, logger)
            stages[i] = (stages[i][0], "DONE")
            if i + 1 < len(stages):
                stages[i + 1] = (stages[i + 1][0], "/")
            if stdscr:
                update_display(stdscr, stages, i, "Stage completed successfully", logger)
            print(f"[{SYSTEM_NAME}] Stage {stages[i][0]} completed successfully")
        except Exception as e:
            errors.append(f"{stages[i][0]}: {e}")
            log_message(f"Stage failed: {stages[i][0]}: {e}", logger, "error")
            display_error(stdscr, stages[i][0], str(e), logger)

    generate_setup_report(start_time, errors, logger)
    if errors:
        print(f"[{SYSTEM_NAME}] Setup completed with {len(errors)} errors. Check {REPORT_FILE} for details")
        return False
    print(f"[{SYSTEM_NAME}] Setup completed successfully, eDEX-UI running")
    return True

if __name__ == "__main__":
    def signal_handler(sig: int, frame) -> None:
        logger = setup_logger()
        log_message(f"Signal received: {sig}", logger, "info")
        clean_temp(logger)
        print(f"[{SYSTEM_NAME}] Terminated by signal: {sig}", file=sys.stderr)
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger = setup_logger()
    log_message("Initializing script...", logger)
    print(f"[{SYSTEM_NAME}] Initializing at {time.strftime('%H:%M:%S')}...")
    try:
        if len(sys.argv) > 1 and sys.argv[1].upper() == "BERKE_KONROL":
            log_message("Running in UI mode with BERKE_KONROL", logger)
            curses.wrapper(main)
        else:
            log_message("Running in standard mode", logger)
            main(None)
    except Exception as e:
        log_message(f"Setup failed: {str(e)}", logger, "error")
        print(f"[{SYSTEM_NAME}] ERROR: Setup failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

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
import stat
from typing import List, Tuple, Optional
from pathlib import Path
import socket
import urllib.request
import urllib.error
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Configuration
SYSTEM_NAME = "BERKE OS"
BASE_DIR = None
TCE_DIR = None
APP_DIR = None
LOG_DIR = Path("/var/log/berke")
LOG_FILE = LOG_DIR / "install.log"
REPORT_FILE = LOG_DIR / "setup_report.txt"
EDEX_DIR = None
NODE_VERSION = "16.20.2"
NODE_URL = "https://nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz"
NODE_MIRRORS = [
    "https://nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz",
    "https://mirror.nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz"
]
NODE_CHECKSUM = "4f34f7f2e66ca676b9c831f6fb3b6c5b0c1f687a6e5f2f51dceda28e6b0a1ca8"
EDEX_URL = "https://github.com/GitSquared/edex-ui.git"
GITHUB_SCRIPT_URL = "https://raw.githubusercontent.com/BreDEVs/kontrol/main/kontrol.py"
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "libX11", "libXScrnSaver", "libXext", "fontconfig", "git", "wget", "curl", "tar"]
REQUIRED_COMMANDS = ["python3.9", "wget", "curl", "git", "tar", "tce-load", "tce-status"]
MIN_TERM_SIZE = (20, 50)
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 10
USER = "tc"
GROUP = "staff"
ANIM_CHARS = "/-\\|"
MIN_DISK_SPACE_GB = 2
MAX_LOG_AGE_DAYS = 7

# Environment setup
os.environ["PATH"] = f"{os.environ.get('PATH', '')}:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin"
os.environ["HOME"] = f"/home/{USER}"
os.environ["LD_LIBRARY_PATH"] = f"{os.environ.get('LD_LIBRARY_PATH', '')}:/usr/local/lib:/usr/lib"

# Logger setup
def setup_logger() -> Optional[logging.Logger]:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fix_permissions(LOG_DIR, logger=None)
        for log in LOG_DIR.glob("install.log.*"):
            try:
                if log.stat().st_mtime < time.time() - MAX_LOG_AGE_DAYS * 86400:
                    log.unlink(missing_ok=True)
            except Exception:
                pass
        logger = logging.getLogger('BerkeOS')
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(str(LOG_FILE), maxBytes=1048576, backupCount=3)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        fix_permissions(LOG_FILE, logger=None)
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
    try:
        temp_dir = Path("/tmp")
        if temp_dir.exists():
            cutoff = time.time() - 86400
            for item in temp_dir.iterdir():
                try:
                    st = item.stat()
                    if st.st_mtime < cutoff:
                        if item.is_file():
                            item.unlink(missing_ok=True)
                        elif item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                except (PermissionError, FileNotFoundError):
                    log_message(f"Failed to clean {item}: Access denied or file not found", logger, "warning")
                except Exception as e:
                    log_message(f"Failed to clean {item}: {e}", logger, "warning")
        log_message("Temporary files cleaned", logger)
    except Exception as e:
        log_message(f"Temporary files cleanup failed: {e}", logger, "error")

# Log message with fallback
def log_message(message: str, logger: Optional[logging.Logger] = None, level: str = "info") -> None:
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

# Center text
def center_text(text: str, width: int) -> Tuple[str, int]:
    text = text[:width-4]
    padding = (width - len(text)) // 2
    return text, padding

# Error display (with fallback to terminal)
def display_error(stdscr, stage: str, error_msg: str, logger: Optional[logging.Logger], suggestion: str = "") -> None:
    specific_suggestions = {
        "DEPENDENCIES": "Check internet connection and ensure tce-load is installed.",
        "DISK SETUP": "Verify disk is connected, formatted (ext4/vfat), and has at least 2 GB free.",
        "eDEX-UI DOWNLOAD": "Ensure GitHub is accessible and git is installed.",
        "eDEX-UI INSTALL": "Verify Node.js and npm are installed correctly.",
        "eDEX-UI START": "Check Xorg installation and display settings."
    }
    suggestion = suggestion or specific_suggestions.get(stage, "Check logs for details.")
    error_summary = f"""
[{SYSTEM_NAME}] ERROR!
Stage: {stage}
Error: {error_msg}
Logs: {LOG_FILE}
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
                (f"Stage: {stage}", curses.color_pair(4), 4),
                (f"Error: {error_msg}", curses.color_pair(4), 6),
                (f"Logs: {LOG_FILE}", curses.color_pair(4), 8),
                (f"Suggestion: {suggestion}", curses.color_pair(4), 10),
                ("View logs: cat /var/log/berke/install.log", curses.color_pair(4), 12),
                ("Report: github.com/BreDEVs/kontrol/issues", curses.color_pair(4), 14),
                ("Press any key to exit", curses.color_pair(4), 16)
            ]
            for line in lines:
                text, attr, row = line
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

# Main display
def update_display(stdscr, stages: List[Tuple[str, str]], current_stage: int, sub_status: str, logger: Optional[logging.Logger]) -> None:
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        title, title_x = center_text("BERKE OS - Setup", cols)
        stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))
        total_stages = len(stages)
        for i, (stage_name, status) in enumerate(stages):
            row = 5 + i * 3
            if row >= rows - 2:
                break
            progress = "█" * int((i + 1 if status == "DONE" else i) * 10 / total_stages) + " " * (10 - int((i + 1 if status == "DONE" else i) * 10 / total_stages))
            stage_text = f"{i+1}. {stage_name[:16]}: [{ANIM_CHARS[int(time.time() * 4) % 4] if i == current_stage and status == '/' else 'DONE' if status == 'DONE' else '-'}] {progress} {int((i + 1 if status == "DONE" else i) * 100 / total_stages)}%"
            text, x = center_text(stage_text, cols)
            attr = curses.color_pair(2) | curses.A_BOLD if i == current_stage and status == "/" else curses.color_pair(3) if status == "DONE" else curses.color_pair(4)
            stdscr.addstr(row, x, text, attr)
            if i == current_stage and status == "/":
                sub_text, sub_x = center_text(f"{sub_status[:26]}", cols)
                stdscr.addstr(row + 1, sub_x, sub_text, curses.color_pair(2))
        stdscr.refresh()
    except Exception as e:
        log_message(f"Display update failed: {e}", logger, "error")

# Fix permissions
def fix_permissions(path: Path, logger: Optional[logging.Logger] = None) -> None:
    for attempt in range(RETRY_ATTEMPTS):
        try:
            parent = path.parent
            while parent != parent.parent:
                if parent.exists() and not os.access(parent, os.W_OK):
                    subprocess.run(["chmod", "775", str(parent)], check=True, timeout=TIMEOUT_SECONDS)
                    try:
                        subprocess.run(["chown", f"{USER}:{GROUP}", str(parent)], check=True, timeout=TIMEOUT_SECONDS)
                    except subprocess.CalledProcessError:
                        log_message(f"chown failed for {parent}: Root access may be required", logger, "warning")
                parent = parent.parent
            if path.exists():
                if not os.access(path, os.W_OK):
                    subprocess.run(["chmod", "-R", "u+w", str(path)], check=True, timeout=TIMEOUT_SECONDS)
                    try:
                        subprocess.run(["chown", "-R", f"{USER}:{GROUP}", str(path)], check=True, timeout=TIMEOUT_SECONDS)
                    except subprocess.CalledProcessError:
                        log_message(f"chown failed for {path}: Root access may be required", logger, "warning")
                if path.is_dir():
                    subprocess.run(["chmod", "775", str(path)], check=True, timeout=TIMEOUT_SECONDS)
                elif os.stat(path).st_mode & stat.S_IXUSR:
                    subprocess.run(["chmod", "755", str(path)], check=True, timeout=TIMEOUT_SECONDS)
                else:
                    subprocess.run(["chmod", "664", str(path)], check=True, timeout=TIMEOUT_SECONDS)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                fix_permissions(path.parent, logger)
            log_message(f"Permissions fixed for {path}", logger)
            break
        except Exception as e:
            if attempt == RETRY_ATTEMPTS - 1:
                log_message(f"Permission fix failed for {path}: {e}", logger, "error")
                raise Exception(f"Permission fix failed for {path}: {e}")
            time.sleep(1)

# Check system resources
def check_resources(logger: Optional[logging.Logger]) -> None:
    try:
        if PSUTIL_AVAILABLE:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            if cpu_usage > 90:
                log_message(f"High CPU usage: {cpu_usage}%", logger, "warning")
            if memory.available < 512 * 1024 * 1024:
                log_message(f"Low memory: {memory.available / 1024 / 1024:.2f} MB available", logger, "warning")
        else:
            try:
                with open("/proc/loadavg", "r") as f:
                    load = float(f.read().split()[0])
                    if load > 4.0:
                        log_message(f"High system load: {load}", logger, "warning")
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if "MemAvailable" in line:
                            mem_kb = int(line.split()[1])
                            if mem_kb < 512 * 1024:
                                log_message(f"Low memory: {mem_kb / 1024:.2f} MB available", logger, "warning")
                            break
            except Exception:
                log_message("Basic resource check failed", logger, "warning")
    except Exception as e:
        log_message(f"Resource check failed: {e}", logger, "warning")

# Detect disk
def detect_disk(logger: Optional[logging.Logger]) -> Tuple[Path, str]:
    try:
        disks = ["/dev/sda1", "/dev/sdb1", "/dev/nvme0n1p1"]
        mount_point = Path("/mnt/disk")
        mkdir_cmd = shutil.which("mkdir")
        subprocess.run([mkdir_cmd, "-p", str(mount_point)], check=True, timeout=TIMEOUT_SECONDS)
        fix_permissions(mount_point, logger)
        lsblk_cmd = shutil.which("lsblk")
        if not lsblk_cmd:
            raise Exception("lsblk command not found")
        result = subprocess.run([lsblk_cmd, "-o", "NAME,MOUNTPOINT,FSTYPE,PARTTYPE"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        for disk in disks:
            if disk in result.stdout:
                lines = result.stdout.splitlines()
                for line in lines:
                    if disk in line:
                        parts = line.split()
                        fstype = parts[2] if len(parts) > 2 else ""
                        if fstype not in ["ext4", "vfat", "ext3"]:
                            log_message(f"Unsupported filesystem {fstype} on {disk}", logger, "warning")
                            continue
                        if mount_point in parts:
                            log_message(f"Mount point {mount_point} already in use", logger, "warning")
                            return mount_point, disk
                        try:
                            mount_cmd = shutil.which("mount")
                            subprocess.run([mount_cmd, disk, str(mount_point)], check=True, timeout=TIMEOUT_SECONDS)
                            subprocess.run([mount_cmd, "-o", "remount,rw", str(mount_point)], check=True, timeout=TIMEOUT_SECONDS)
                            fix_permissions(mount_point, logger)
                            log_message(f"Disk {disk} mounted at {mount_point}", logger)
                            return mount_point, disk
                        except Exception:
                            continue
        raise Exception("No suitable disk found. Please ensure a disk is connected and formatted (ext4/vfat).")
    except Exception as e:
        log_message(f"Disk detection failed: {e}", logger, "error")
        raise

# Check internet connection
def check_internet(stdscr, logger: Optional[logging.Logger]) -> bool:
    dns_servers = [("8.8.8.8", 53), ("1.1.1.1", 53), ("9.9.9.9", 53)]
    http_test = "https://www.google.com"
    ping_cmd = shutil.which("ping")
    for server, port in dns_servers:
        try:
            socket.create_connection((server, port), timeout=5)
            try:
                urllib.request.urlopen(http_test, timeout=5)
                log_message(f"Internet connection established via {server} and HTTP", logger)
                return True
            except urllib.error.URLError as e:
                log_message(f"HTTP test failed: {e}", logger, "warning")
                if ping_cmd:
                    try:
                        subprocess.run([ping_cmd, "-c", "1", server], check=True, timeout=5)
                        log_message(f"Ping test succeeded for {server}", logger)
                        return True
                    except Exception:
                        pass
                return False
        except Exception:
            continue
    log_message("Internet connection failed", logger, "error")
    if stdscr:
        try:
            stdscr.clear()
            rows, cols = stdscr.getmaxyx()
            title, title_x = center_text("BERKE OS - Network Error", cols)
            stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))
            msg, msg_x = center_text("No internet connection. Trying Wi-Fi...", cols)
            stdscr.addstr(4, msg_x, msg, curses.color_pair(4))
            stdscr.refresh()
            nmcli_cmd = shutil.which("nmcli")
            if nmcli_cmd:
                try:
                    result = subprocess.run([nmcli_cmd, "--version"], capture_output=True, text=True, check=True, timeout=5)
                    log_message(f"nmcli found: {result.stdout.strip()}", logger)
                    subprocess.run([nmcli_cmd, "device", "wifi", "list"], check=True, timeout=10)
                    subprocess.run([nmcli_cmd, "device", "wifi", "connect"], check=False, timeout=30)
                    time.sleep(5)
                    for server, port in dns_servers:
                        try:
                            socket.create_connection((server, port), timeout=5)
                            urllib.request.urlopen(http_test, timeout=5)
                            log_message("Wi-Fi connection established", logger)
                            return True
                        except Exception:
                            continue
                except Exception as e:
                    log_message(f"Wi-Fi connection attempt failed: {e}", logger, "warning")
            display_error(stdscr, "Network Check", "Internet connection failed", logger)
        except Exception as e:
            log_message(f"Network error display failed: {e}", logger, "error")
    return False

# Update kontrol.py from GitHub
def update_script(stdscr, logger: Optional[logging.Logger]) -> None:
    log_message("Updating kontrol.py from GitHub", logger)
    print(f"[{SYSTEM_NAME}] Starting script update...")
    stages = [("SCRIPT UPDATE", "/")]
    sub_status = ""

    try:
        clean_temp(logger)
        if not check_internet(stdscr, logger):
            raise Exception("No internet connection")

        sub_status = "Downloading script"
        update_display(stdscr, stages, 0, sub_status, logger)
        script_path = BASE_DIR / "kontrol.py"
        temp_script = Path("/tmp/kontrol.py.new")
        
        for attempt in range(RETRY_ATTEMPTS):
            try:
                with urllib.request.urlopen(GITHUB_SCRIPT_URL, timeout=10) as response:
                    content = response.read()
                    if len(content) > 1024 * 1024:
                        raise Exception("Downloaded file too large")
                    with open(temp_script, "wb") as f:
                        f.write(content)
                fix_permissions(temp_script, logger)
                with open(temp_script, "r") as f:
                    content = f.read()
                    if not ("#!/usr/bin/env python" in content or "import " in content):
                        raise Exception("Downloaded file is not a valid Python script")
                if not temp_script.exists():
                    raise Exception("Script download failed")
                break
            except urllib.error.URLError as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Script download failed: {e}")
                time.sleep(2)

        sub_status = "Replacing script"
        update_display(stdscr, stages, 0, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                fix_permissions(BASE_DIR, logger)
                if script_path.exists():
                    subprocess.run(["mv", str(script_path), f"{script_path}.bak"], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["mv", str(temp_script), str(script_path)], check=True, timeout=TIMEOUT_SECONDS)
                fix_permissions(script_path, logger)
                subprocess.run(["chmod", "+x", str(script_path)], check=True, timeout=TIMEOUT_SECONDS)
                log_message("Script updated successfully", logger)
                print(f"[{SYSTEM_NAME}] Script updated successfully")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Script replacement failed: {e}")
                time.sleep(1)

        sub_status = "Update completed"
        update_display(stdscr, stages, 0, sub_status, logger)
        stages[0] = ("SCRIPT UPDATE", "DONE")
        update_display(stdscr, stages, 0, "Update completed", logger)
        
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        title, title_x = center_text("BERKE OS - Update Done", cols)
        stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))
        prompt, prompt_x = center_text("Press any key to exit...", cols)
        stdscr.addstr(4, prompt_x, prompt, curses.color_pair(4))
        stdscr.refresh()
        stdscr.getch()
        sys.exit(0)
    except Exception as e:
        log_message(f"Script update failed: {e}", logger, "error")
        display_error(stdscr, "SCRIPT UPDATE", str(e), logger)
    finally:
        clean_temp(logger)

# Install dependencies
def install_dependencies(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Checking dependencies", logger)
    print(f"[{SYSTEM_NAME}] Installing dependencies...")
    sub_status = ""

    try:
        clean_temp(logger)
        if not check_internet(stdscr, logger):
            raise Exception("No internet connection")

        for cmd in REQUIRED_COMMANDS:
            sub_status = f"Checking {cmd}"
            update_display(stdscr, stages, current_stage, sub_status, logger)
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    cmd_path = shutil.which(cmd)
                    if not cmd_path:
                        raise Exception(f"{cmd} not found in PATH")
                    if cmd == "python3.9":
                        result = subprocess.run([cmd_path, "--version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                        if "3.9" not in result.stdout:
                            raise Exception("Python 3.9 version mismatch")
                    log_message(f"{cmd} found: {cmd_path}", logger)
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"Required command {cmd} not found: {e}")
                    time.sleep(1)

        fix_permissions(TCE_DIR, logger)

        for pkg in REQUIRED_TCE_PACKAGES:
            sub_status = f"Checking {pkg}"
            update_display(stdscr, stages, current_stage, sub_status, logger)
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    result = subprocess.run(["tce-status", "-i"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    if pkg in result.stdout:
                        log_message(f"{pkg} found", logger)
                        break
                    sub_status = f"Installing {pkg}"
                    update_display(stdscr, stages, current_stage, sub_status, logger)
                    result = subprocess.run(["tce-load", "-w", "-i", "-f", pkg], capture_output=True, text=True, check=True, timeout=600)
                    log_message(f"{pkg} installed: {result.stdout.strip()}", logger)
                    if pkg == "Xorg-7.7":
                        try:
                            x11_dir = Path("/usr/local/lib/X11")
                            fix_permissions(x11_dir, logger)
                            if not x11_dir.exists():
                                raise Exception("X11 directory not found")
                            result = subprocess.run(["Xorg", "-version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                            if "7.7" not in result.stdout:
                                raise Exception("Xorg-7.7 version mismatch")
                        except Exception:
                            sub_status = "Configuring VESA driver"
                            update_display(stdscr, stages, current_stage, sub_status, logger)
                            xorg_conf_dir = Path("/etc/X11/xorg.conf.d")
                            xorg_conf = xorg_conf_dir / "20-xorg-vesa.conf"
                            fix_permissions(xorg_conf_dir, logger)
                            with open(xorg_conf, "w") as f:
                                f.write(
                                    'Section "Device"\n'
                                    '    Identifier "Card0"\n'
                                    '    Driver "vesa"\n'
                                    '    Option "Fallback" "fbdev"\n'
                                    'EndSection\n'
                                    'Section "Screen"\n'
                                    '    Identifier "Screen0"\n'
                                    '    Device "Card0"\n'
                                    '    DefaultDepth 24\n'
                                    '    SubSection "Display"\n'
                                    '        Modes "1024x768" "800x600" "640x480"\n'
                                    '    EndSubSection\n'
                                    'EndSection\n'
                                )
                            fix_permissions(xorg_conf, logger)
                            log_message("VESA driver configured", logger)
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"{pkg} installation failed: {e}")
                    time.sleep(2)

            try:
                onboot_file = TCE_DIR / "onboot.lst"
                fix_permissions(onboot_file, logger)
                if not onboot_file.exists():
                    with open(onboot_file, "w") as f:
                        f.write("")
                with open(onboot_file, "r") as f:
                    content = f.read().strip()
                if pkg not in content:
                    with open(onboot_file, "a") as f:
                        f.write(f"{pkg}\n")
                    fix_permissions(onboot_file, logger)
                    log_message(f"Added {pkg} to onboot.lst", logger)
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"onboot.lst update failed for {pkg}: {e}")
                time.sleep(1)

        sub_status = "Checking Node.js"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                node_cmd = shutil.which("node")
                npm_cmd = shutil.which("npm")
                if not node_cmd or not npm_cmd:
                    raise Exception("Node.js or npm not found")
                result = subprocess.run([node_cmd, "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                npm_result = subprocess.run([npm_cmd, "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                if f"v{NODE_VERSION}" not in result.stdout:
                    raise Exception(f"Node.js version mismatch: expected {NODE_VERSION}, found {result.stdout.strip()}")
                log_message(f"Node.js {result.stdout.strip()} and npm {npm_result.stdout.strip()} found", logger)
                break
            except Exception:
                sub_status = "Installing Node.js"
                update_display(stdscr, stages, current_stage, sub_status, logger)
                try:
                    node_tar = Path("/tmp/node.tar.xz")
                    node_extract_dir = Path("/tmp/node_extract")
                    target_dir = Path("/usr/local/node")
                    fix_permissions(node_extract_dir.parent, logger)
                    if node_tar.exists():
                        node_tar.unlink(missing_ok=True)
                    if node_extract_dir.exists():
                        shutil.rmtree(node_extract_dir, ignore_errors=True)
                    if target_dir.exists():
                        shutil.rmtree(target_dir, ignore_errors=True)
                    for url in NODE_MIRRORS:
                        try:
                            wget_cmd = shutil.which("wget")
                            subprocess.run([wget_cmd, "-O", str(node_tar), url], check=True, timeout=300)
                            with open(node_tar, "rb") as f:
                                checksum = hashlib.sha256(f.read()).hexdigest()
                            if checksum != NODE_CHECKSUM:
                                raise Exception(f"Node.js checksum mismatch: expected {NODE_CHECKSUM}, got {checksum}")
                            break
                        except Exception:
                            continue
                    else:
                        raise Exception("All Node.js mirrors failed")
                    node_extract_dir.mkdir(parents=True, exist_ok=True)
                    fix_permissions(node_extract_dir, logger)
                    tar_cmd = shutil.which("tar")
                    subprocess.run([tar_cmd, "-xJf", str(node_tar), "-C", str(node_extract_dir)], check=True, timeout=300)
                    extracted_dir = next(node_extract_dir.iterdir())
                    subprocess.run(["mv", str(extracted_dir), str(target_dir)], check=True, timeout=10)
                    for binary in ["node", "npm"]:
                        binary_path = target_dir / "bin" / binary
                        link_path = Path(f"/usr/local/bin/{binary}")
                        if link_path.exists():
                            link_path.unlink(missing_ok=True)
                        subprocess.run(["ln", "-s", str(binary_path), str(link_path)], check=True, timeout=TIMEOUT_SECONDS)
                    fix_permissions(target_dir, logger)
                    result = subprocess.run([shutil.which("node"), "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    npm_result = subprocess.run([shutil.which("npm"), "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    if f"v{NODE_VERSION}" not in result.stdout:
                        raise Exception(f"Node.js version verification failed: {result.stdout.strip()}")
                    log_message(f"Node.js {result.stdout.strip()} and npm {npm_result.stdout.strip()} installed", logger)
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"Node.js installation failed: {e}")
                    time.sleep(2)
                finally:
                    if node_tar.exists():
                        node_tar.unlink(missing_ok=True)
                    if node_extract_dir.exists():
                        shutil.rmtree(node_extract_dir, ignore_errors=True)

        sub_status = "Dependencies done"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] Dependencies installed successfully")
    except Exception as e:
        log_message(f"Dependency stage failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp(logger)

# Verify disk
def verify_disk(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger], disk_device: str) -> None:
    log_message("Verifying disk", logger)
    print(f"[{SYSTEM_NAME}] Verifying disk...")
    sub_status = ""

    try:
        clean_temp(logger)
        sub_status = "Checking disk space"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                disk_usage = shutil.disk_usage(BASE_DIR)
                free_space_gb = disk_usage.free / (1024 ** 3)
                if free_space_gb < MIN_DISK_SPACE_GB:
                    raise Exception(f"Insufficient disk space: {free_space_gb:.2f} GB available, {MIN_DISK_SPACE_GB} GB required")
                test_file = BASE_DIR / "test_write"
                start_time = time.time()
                with open(test_file, "wb") as f:
                    f.write(os.urandom(10 * 1024 * 1024))
                elapsed = time.time() - start_time
                test_file.unlink(missing_ok=True)
                if elapsed > 5:
                    log_message(f"Slow disk write speed: {10 / elapsed:.2f} MB/s", logger, "warning")
                log_message(f"Disk space: {free_space_gb:.2f} GB free", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Disk space check failed: {e}")
                time.sleep(1)

        sub_status = "Creating disk dir"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                fix_permissions(BASE_DIR, logger)
                if not BASE_DIR.exists():
                    raise Exception("Disk directory creation failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Disk directory creation failed: {e}")
                time.sleep(1)

        sub_status = "Mounting disk"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                mountpoint_cmd = shutil.which("mountpoint")
                if mountpoint_cmd:
                    result = subprocess.run([mountpoint_cmd, "-q", str(BASE_DIR)], check=False, timeout=TIMEOUT_SECONDS)
                    if result.returncode != 0:
                        subprocess.run(["mkdir", "-p", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                        fix_permissions(BASE_DIR, logger)
                        mount_cmd = shutil.which("mount")
                        subprocess.run([mount_cmd, disk_device, str(BASE_DIR)], check=True, timeout=10)
                        subprocess.run([mount_cmd, "-o", "remount,rw", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                else:
                    mount_cmd = shutil.which("mount")
                    subprocess.run([mount_cmd, disk_device, str(BASE_DIR)], check=True, timeout=10)
                    subprocess.run([mount_cmd, "-o", "remount,rw", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                df_cmd = shutil.which("df")
                result = subprocess.run([df_cmd, "-h", str(BASE_DIR)], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                if str(BASE_DIR) not in result.stdout:
                    raise Exception("Disk mount verification failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Disk mount failed: {e}")
                time.sleep(1)

        sub_status = "Creating app dir"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                fix_permissions(APP_DIR, logger)
                if not APP_DIR.exists():
                    raise Exception("App directory creation failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"App directory creation failed: {e}")
                time.sleep(1)

        sub_status = "Disk setup done"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] Disk setup completed")
    except Exception as e:
        log_message(f"Disk stage failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp(logger)

# Download eDEX-UI
def download_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Downloading eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Downloading eDEX-UI...")
    sub_status = ""

    try:
        clean_temp(logger)
        if not check_internet(stdscr, logger):
            raise Exception("No internet connection")

        sub_status = "Checking eDEX-UI"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if EDEX_DIR.exists() and (EDEX_DIR / "package.json").exists():
                    log_message("eDEX-UI already present", logger)
                    break
                sub_status = "Cloning eDEX-UI"
                update_display(stdscr, stages, current_stage, sub_status, logger)
                if EDEX_DIR.exists():
                    shutil.rmtree(EDEX_DIR, ignore_errors=True)
                fix_permissions(EDEX_DIR.parent, logger)
                git_cmd = shutil.which("git")
                subprocess.run([git_cmd, "clone", "--depth", "1", EDEX_URL, str(EDEX_DIR)], check=True, timeout=600)
                fix_permissions(EDEX_DIR, logger)
                if not (EDEX_DIR / "package.json").exists():
                    raise Exception("eDEX-UI package.json not found")
                log_message("eDEX-UI cloned", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"eDEX-UI clone failed: {e}")
                time.sleep(2)

        sub_status = "eDEX-UI downloaded"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI downloaded successfully")
    except Exception as e:
        log_message(f"eDEX-UI download stage failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp(logger)

# Install eDEX-UI
def install_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Installing eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Installing eDEX-UI...")
    sub_status = ""

    try:
        clean_temp(logger)
        sub_status = "Cleaning npm cache"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                npm_cmd = shutil.which("npm")
                env = os.environ.copy()
                env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
                subprocess.run([npm_cmd, "cache", "clean", "--force"], check=True, timeout=60, env=env)
                log_message("npm cache cleaned", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    log_message(f"npm cache clean failed: {e}", logger, "warning")
                time.sleep(1)

        sub_status = "Installing npm deps"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if (EDEX_DIR / "node_modules").exists():
                    shutil.rmtree(EDEX_DIR / "node_modules", ignore_errors=True)
                fix_permissions(EDEX_DIR, logger)
                env = os.environ.copy()
                env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
                env["NODE_PATH"] = str(EDEX_DIR / "node_modules")
                subprocess.run(
                    [npm_cmd, "install", "--no-audit", "--no-fund", "--legacy-peer-deps"],
                    cwd=str(EDEX_DIR), check=True, timeout=600, env=env
                )
                fix_permissions(EDEX_DIR / "node_modules", logger)
                if not (EDEX_DIR / "node_modules").exists():
                    raise Exception("npm dependencies verification failed")
                log_message("npm dependencies installed", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"npm dependencies installation failed: {e}")
                time.sleep(2)

        sub_status = "Customizing settings"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                settings_path = EDEX_DIR / "settings.json"
                settings = {
                    "shell": "/bin/sh",
                    "shellArgs": ["-c", f"export PATH=$PATH:/usr/local/bin:/usr/bin:/bin; exec sh"],
                    "theme": "tron",
                    "window": {"title": f"{SYSTEM_NAME} eDEX-UI"},
                    "performance": {"lowPowerMode": False, "gpuAcceleration": True}
                }
                with open(settings_path, "w") as f:
                    json.dump(settings, f, indent=2)
                fix_permissions(settings_path, logger)
                with open(settings_path, "r") as f:
                    if SYSTEM_NAME not in f.read():
                        raise Exception("Settings content verification failed")
                log_message("eDEX-UI settings customized", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"eDEX-UI settings customization failed: {e}")
                time.sleep(1)

        sub_status = "Optimizing Xorg"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                xorg_conf_dir = Path("/etc/X11/xorg.conf.d")
                xorg_conf = xorg_conf_dir / "10-optimizations.conf"
                fix_permissions(xorg_conf_dir, logger)
                with open(xorg_conf, "w") as f:
                    f.write(
                        'Section "Device"\n'
                        '    Identifier "Card0"\n'
                        '    Driver "vesa"\n'
                        '    Option "AccelMethod" "exa"\n'
                        '    Option "Fallback" "fbdev"\n'
                        'EndSection\n'
                        'Section "Screen"\n'
                        '    Identifier "Screen0"\n'
                        '    Device "Card0"\n'
                        '    DefaultDepth 24\n'
                        '    SubSection "Display"\n'
                        '        Modes "1024x768" "800x600" "640x480"\n'
                        '    EndSubSection\n'
                        'EndSection\n'
                    )
                fix_permissions(xorg_conf, logger)
                if not xorg_conf.exists():
                    raise Exception("Xorg configuration file creation failed")
                log_message("Xorg optimized", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Xorg optimization failed: {e}")
                time.sleep(1)

        sub_status = "eDEX-UI installed"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI installed successfully")
    except Exception as e:
        log_message(f"eDEX-UI installation stage failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp(logger)

# Post-installation test for eDEX-UI
def post_install_test(logger: Optional[logging.Logger]) -> bool:
    log_message("Running post-installation test for eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Running eDEX-UI test...")
    process = None
    try:
        os.environ["DISPLAY"] = ":0"
        env = os.environ.copy()
        env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
        env["LD_LIBRARY_PATH"] = f"/usr/local/lib:/usr/lib:{env.get('LD_LIBRARY_PATH', '')}"
        env["NODE_PATH"] = str(EDEX_DIR / "node_modules")
        npm_cmd = shutil.which("npm")
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
            log_message("eDEX-UI test run successful", logger)
            print(f"[{SYSTEM_NAME}] eDEX-UI test passed")
            return True
        else:
            stdout, stderr = process.communicate(timeout=TIMEOUT_SECONDS)
            log_message(f"eDEX-UI test run failed: {stderr}", logger, "error")
            print(f"[{SYSTEM_NAME}] eDEX-UI test failed: {stderr}", file=sys.stderr)
            return False
    except Exception as e:
        log_message(f"Post-installation test failed: {e}", logger, "error")
        print(f"[{SYSTEM_NAME}] eDEX-UI test failed: {e}", file=sys.stderr)
        return False
    finally:
        if process and process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=TIMEOUT_SECONDS)
            except Exception:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except Exception:
                    pass
        clean_temp(logger)

# Start eDEX-UI
def start_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> bool:
    log_message("Starting eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Starting eDEX-UI...")
    sub_status = ""
    process = None

    def cleanup():
        try:
            if process and process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=TIMEOUT_SECONDS)
        except Exception:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except Exception:
                pass
        try:
            killall_cmd = shutil.which("killall")
            if killall_cmd:
                subprocess.run([killall_cmd, "-q", "node"], timeout=TIMEOUT_SECONDS)
                subprocess.run([killall_cmd, "-q", "Xorg"], timeout=TIMEOUT_SECONDS)
        except Exception:
            pass
        clean_temp(logger)

    try:
        clean_temp(logger)
        sub_status = "Preparing X11"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                os.environ["DISPLAY"] = ":0"
                pgrep_cmd = shutil.which("pgrep")
                if pgrep_cmd:
                    result = subprocess.run([pgrep_cmd, "-x", "Xorg"], check=False, timeout=TIMEOUT_SECONDS)
                    if result.returncode != 0:
                        xorg_process = subprocess.Popen(
                            ["Xorg", ":0", "-quiet", "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            preexec_fn=os.setsid
                        )
                        for _ in range(10):
                            time.sleep(1)
                            try:
                                xset_cmd = shutil.which("xset")
                                if xset_cmd:
                                    subprocess.run([xset_cmd, "-q"], check=True, timeout=2)
                                    break
                                elif Path("/tmp/.X0-lock").exists():
                                    break
                            except Exception:
                                pass
                        else:
                            xorg_process.terminate()
                            raise Exception("Xorg failed to start or screen not ready")
                log_message("X11 environment prepared", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"X11 startup failed: {e}")
                time.sleep(2)

        sub_status = "Launching eDEX-UI"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                fix_permissions(EDEX_DIR, logger)
                env = os.environ.copy()
                env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
                env["LD_LIBRARY_PATH"] = f"/usr/local/lib:/usr/lib:{env.get('LD_LIBRARY_PATH', '')}"
                env["NODE_PATH"] = str(EDEX_DIR / "node_modules")
                npm_cmd = shutil.which("npm")
                process = subprocess.Popen(
                    [npm_cmd, "start"],
                    cwd=str(EDEX_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,
                    env=env
                )
                time.sleep(20)
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=TIMEOUT_SECONDS)
                    raise Exception(f"eDEX-UI startup failed: {stderr}")
                ps_cmd = shutil.which("ps")
                result = subprocess.run([ps_cmd, "aux"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                if "node" not in result.stdout or "edex-ui" not in result.stdout:
                    raise Exception("eDEX-UI process verification failed")
                log_message("eDEX-UI started", logger)
                print(f"[{SYSTEM_NAME}] eDEX-UI started successfully")
                try:
                    rc_local = Path("/etc/rc.local")
                    if rc_local.exists():
                        with open(rc_local, "a") as f:
                            f.write(f"\n{BASE_DIR / 'kontrol.py'} &\n")
                        fix_permissions(rc_local, logger)
                        log_message("eDEX-UI added to startup", logger)
                except Exception as e:
                    log_message(f"Failed to add to startup: {e}", logger, "warning")
                return True
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"eDEX-UI startup failed: {e}")
                time.sleep(5)
    except Exception as e:
        log_message(f"eDEX-UI startup stage failed: {e}", logger, "error")
        if stdscr:
            display_error(stdscr, stages[current_stage][0], str(e), logger)
        return False
    finally:
        if not process or process.poll() is not None:
            cleanup()

# Quick check for eDEX-UI
def quick_check_edex_ui(logger: Optional[logging.Logger]) -> bool:
    log_message("Running quick check for eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Checking eDEX-UI installation...")
    try:
        if not EDEX_DIR.exists() or not (EDEX_DIR / "package.json").exists():
            log_message("eDEX-UI directory or package.json missing", logger, "warning")
            return False
        if not (EDEX_DIR / "node_modules").exists():
            log_message("eDEX-UI node_modules missing", logger, "warning")
            return False
        node_cmd = shutil.which("node")
        npm_cmd = shutil.which("npm")
        if not node_cmd or not npm_cmd:
            log_message("Node.js or npm not found", logger, "warning")
            return False
        result = subprocess.run([node_cmd, "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
        if f"v{NODE_VERSION}" not in result.stdout:
            log_message(f"Node.js version mismatch: {result.stdout.strip()}", logger, "warning")
            return False
        result = subprocess.run([npm_cmd, "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
        main_js = EDEX_DIR / "main.js"
        if not main_js.exists():
            log_message("eDEX-UI main.js missing", logger, "warning")
            return False
        result = subprocess.run(["tce-status", "-i"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
        for pkg in REQUIRED_TCE_PACKAGES:
            if pkg not in result.stdout:
                log_message(f"Missing TCE package: {pkg}", logger, "warning")
                return False
        x11_dir = Path("/usr/local/lib/X11")
        if not x11_dir.exists():
            log_message("X11 directory missing", logger, "warning")
            return False
        settings_path = EDEX_DIR / "settings.json"
        if not settings_path.exists():
            log_message("eDEX-UI settings.json missing", logger, "warning")
            return False
        try:
            env = os.environ.copy()
            env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
            env["NODE_PATH"] = str(EDEX_DIR / "node_modules")
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
                log_message("eDEX-UI quick test passed", logger)
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=TIMEOUT_SECONDS)
            else:
                stdout, stderr = process.communicate(timeout=TIMEOUT_SECONDS)
                log_message(f"eDEX-UI quick test failed: {stderr}", logger, "warning")
                return False
        except Exception as e:
            log_message(f"eDEX-UI quick test failed: {e}", logger, "warning")
            return False
        log_message("Quick check passed", logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI quick check passed")
        return True
    except Exception as e:
        log_message(f"Quick check failed: {e}", logger, "error")
        print(f"[{SYSTEM_NAME}] eDEX-UI quick check failed: {e}", file=sys.stderr)
        return False

# Generate setup report
def generate_setup_report(start_time: float, errors: List[str], logger: Optional[logging.Logger]) -> None:
    try:
        duration = time.time() - start_time
        disk_usage = shutil.disk_usage(BASE_DIR)
        used_space_gb = (disk_usage.total - disk_usage.free) / (1024 ** 3)
        report = [
            f"BERKE OS Setup Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {duration:.2f} seconds",
            f"Disk Usage: {used_space_gb:.2f} GB",
            f"Errors Encountered: {len(errors)}",
            "\nErrors:"
        ]
        report.extend(errors if errors else ["None"])
        with open(REPORT_FILE, "w") as f:
            f.write("\n".join(report))
        fix_permissions(REPORT_FILE, logger)
        log_message(f"Setup report generated at {REPORT_FILE}", logger)
        print(f"[{SYSTEM_NAME}] Setup report generated at {REPORT_FILE}")
    except Exception as e:
        log_message(f"Setup report generation failed: {e}", logger, "error")
        print(f"[{SYSTEM_NAME}] Setup report generation failed: {e}", file=sys.stderr)

# Main function
def main(stdscr=None):
    global BASE_DIR, TCE_DIR, APP_DIR, EDEX_DIR
    logger = setup_logger()
    start_time = time.time()
    errors = []
    log_message(f"{SYSTEM_NAME} started", logger)
    print(f"[{SYSTEM_NAME}] Starting setup process...")

    try:
        BASE_DIR, disk_device = detect_disk(logger)
        TCE_DIR = BASE_DIR / "tce"
        APP_DIR = BASE_DIR / "apps"
        EDEX_DIR = APP_DIR / "edex-ui"
        fix_permissions(BASE_DIR, logger)
        log_message("Disk initialized", logger)
    except Exception as e:
        errors.append(f"Disk initialization: {e}")
        log_message(f"Disk initialization failed: {e}", logger, "error")
        if stdscr:
            display_error(stdscr, "Initialization", str(e), logger)
        else:
            print(f"[{SYSTEM_NAME}] ERROR: Disk initialization failed: {e}", file=sys.stderr)
        return

    if stdscr:
        try:
            resize_cmd = shutil.which("resize")
            if resize_cmd:
                subprocess.run([resize_cmd], timeout=TIMEOUT_SECONDS)
            curses.curs_set(0)
            stdscr.timeout(100)
            rows, cols = stdscr.getmaxyx()
            if rows < MIN_TERM_SIZE[0] or cols < MIN_TERM_SIZE[1]:
                raise Exception(f"Terminal size too small: {MIN_TERM_SIZE[1]}x{MIN_TERM_SIZE[0]}")
            curses.start_color()
            curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
            title, title_x = center_text("BERKE OS - Initializing", cols)
            stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))
            stdscr.refresh()
            time.sleep(1)
        except Exception as e:
            errors.append(f"Curses initialization: {e}")
            log_message(f"Curses initialization failed: {e}", logger, "error")
            print(f"[{SYSTEM_NAME}] WARNING: Curses initialization failed, switching to terminal mode: {e}", file=sys.stderr)
            stdscr = None

    if quick_check_edex_ui(logger):
        if start_edex_ui(stdscr, [("eDEX-UI START", "/")], 0, logger):
            generate_setup_report(start_time, errors, logger)
            print(f"[{SYSTEM_NAME}] Setup completed successfully")
            return

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
            check_resources(logger)
            stages[i] = (stages[i][0], "/")
            func(stdscr, stages, i, logger)
            stages[i] = (stages[i][0], "DONE")
            if i + 1 < len(stages):
                stages[i + 1] = (stages[i + 1][0], "/")
            if stdscr:
                update_display(stdscr, stages, i, "Stage completed", logger)
            if stages[i][0] == "eDEX-UI INSTALL" and not post_install_test(logger):
                errors.append("eDEX-UI post-installation test failed")
        except Exception as e:
            errors.append(f"{stages[i][0]}: {e}")
            log_message(f"Stage failed: {stages[i][0]}: {e}", logger, "error")
            if stdscr:
                display_error(stdscr, stages[i][0], str(e), logger)
            else:
                print(f"[{SYSTEM_NAME}] ERROR: Stage {stages[i][0]} failed: {e}", file=sys.stderr)
            break

    generate_setup_report(start_time, errors, logger)

    if stdscr:
        try:
            stdscr.clear()
            rows, cols = stdscr.getmaxyx()
            title, title_x = center_text("BERKE OS - Setup Done", cols)
            stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))
            prompt, prompt_x = center_text("Reboot recommended. Press 'r' to reboot, any other key to exit...", cols)
            stdscr.addstr(4, prompt_x, prompt, curses.color_pair(4))
            report, report_x = center_text(f"Report: {REPORT_FILE}", cols)
            stdscr.addstr(6, report_x, report, curses.color_pair(4))
            stdscr.refresh()
            key = stdscr.getch()
            if key == ord('r'):
                log_message("User initiated reboot", logger)
                sync_cmd = shutil.which("sync")
                if sync_cmd:
                    subprocess.run([sync_cmd], timeout=5)
                reboot_cmd = shutil.which("reboot")
                if reboot_cmd:
                    subprocess.run([reboot_cmd], timeout=10)
        except Exception as e:
            log_message(f"Completion screen failed: {e}", logger, "error")
            print(f"[{SYSTEM_NAME}] Setup completed with errors. Check {REPORT_FILE} for details.", file=sys.stderr)
    else:
        print(f"[{SYSTEM_NAME}] Setup completed. Check {REPORT_FILE} for details.", file=sys.stderr)
        print("Reboot recommended. Run 'sudo reboot' to restart.", file=sys.stderr)

if __name__ == "__main__":
    def signal_handler(sig, frame):
        logger = setup_logger()
        log_message(f"Signal received: {sig}", logger, "info")
        try:
            killall_cmd = shutil.which("killall")
            if killall_cmd:
                subprocess.run([killall_cmd, "-q", "node"], timeout=TIMEOUT_SECONDS)
                subprocess.run([killall_cmd, "-q", "Xorg"], timeout=TIMEOUT_SECONDS)
        except Exception:
            pass
        clean_temp(logger)
        print(f"[{SYSTEM_NAME}] Terminated by signal {sig}", file=sys.stderr)
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"[{SYSTEM_NAME}] Initializing...")
    if len(sys.argv) > 1:
        if sys.argv[1] == "Berke:Kontrol":
            try:
                curses.wrapper(main)
            except Exception as e:
                logger = setup_logger()
                log_message(f"{SYSTEM_NAME} failed: {e}", logger, "error")
                print(f"[{SYSTEM_NAME}] ERROR: Setup failed: {e}", file=sys.stderr)
                sys.exit(1)
        elif sys.argv[1] == "Berke:GuncelK":
            try:
                curses.wrapper(update_script)
            except Exception as e:
                logger = setup_logger()
                log_message(f"Script update failed: {e}", logger, "error")
                print(f"[{SYSTEM_NAME}] ERROR: Script update failed: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"[{SYSTEM_NAME}] ERROR: Invalid argument: {sys.argv[1]}", file=sys.stderr)
            print("Usage: python kontrol.py [Berke:Kontrol | Berke:GuncelK]", file=sys.stderr)
            sys.exit(1)
    else:
        main(None)

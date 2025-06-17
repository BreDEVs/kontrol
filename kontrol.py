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
BASE_DIR = None
TCE_DIR = None
APP_DIR = None
LOG_DIR = Path("/var/log/berke")
LOG_FILE = LOG_DIR / "install.log"
REPORT_FILE = LOG_DIR / "setup_report.txt"
EDEX_DIR = None
NODE_VERSION = "16.20.2"
NODE_URL = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
NODE_CHECKSUM = "4f34f7f2e66ca676b9c831f6fb3b6c5b0c1f687a6e5f2f51dceda28e6b0a1ca8"
EDEX_URL = "https://github.com/GitSquared/edex-ui.git"
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "git", "wget", "curl", "tar"]
REQUIRED_COMMANDS = ["python3.9", "wget", "curl", "git", "tar", "tce-load"]
MIN_TERM_SIZE = (20, 50)
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 10
USER = "tc"
GROUP = "staff"
MIN_DISK_SPACE_GB = 2
MAX_LOG_AGE_DAYS = 7

# Environment setup
os.environ["PATH"] = f"{os.environ.get('PATH', '')}:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin"
os.environ["HOME"] = f"/home/{USER}"

# Logger setup
def setup_logger() -> Optional[logging.Logger]:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fix_permissions(LOG_DIR)
        for log in LOG_DIR.glob("install.log.*"):
            if log.stat().st_mtime < time.time() - MAX_LOG_AGE_DAYS * 86400:
                log.unlink(missing_ok=True)
        logger = logging.getLogger('BerkeOS')
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(str(LOG_FILE), maxBytes=1048576, backupCount=3)
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

# Error display
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
            row = 5 + i * 2
            if row >= rows - 2:
                break
            progress = "█" * int((i + 1 if status == "DONE" else i) * 10 / total_stages)
            stage_text = f"{i+1}. {stage_name[:16]}: [{'*' if i == current_stage and status == '/' else 'DONE' if status == 'DONE' else '-'}] {progress}"
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
    try:
        parent = path.parent
        while parent != parent.parent:
            if parent.exists() and not os.access(parent, os.W_OK):
                os.chmod(parent, 0o775)
            parent = parent.parent
        if path.exists():
            if not os.access(path, os.W_OK):
                os.chmod(path, 0o775 if path.is_dir() else 0o664)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            fix_permissions(path.parent, logger)
        log_message(f"Permissions fixed for {path}", logger)
    except Exception as e:
        log_message(f"Permission fix failed for {path}: {e}", logger, "error")
        raise Exception(f"Permission fix failed: {e}")

# Detect disk
def detect_disk(logger: Optional[logging.Logger]) -> Tuple[Path, str]:
    try:
        mount_point = Path("/mnt/disk")
        mount_point.mkdir(parents=True, exist_ok=True)
        fix_permissions(mount_point, logger)
        disks = ["/dev/sda1", "/dev/sdb1", "/dev/nvme0n1p1"]
        lsblk_cmd = shutil.which("lsblk")
        if not lsblk_cmd:
            raise Exception("lsblk command not found")
        result = subprocess.run([lsblk_cmd, "-o", "NAME,FSTYPE,MOUNTPOINT"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        for disk in disks:
            if disk in result.stdout:
                lines = result.stdout.splitlines()
                for line in lines:
                    if disk in line:
                        parts = line.split()
                        fstype = parts[1] if len(parts) > 1 else ""
                        if fstype not in ["ext4", "vfat"]:
                            continue
                        mount_cmd = shutil.which("mount")
                        if not mount_cmd:
                            raise Exception("mount command not found")
                        subprocess.run([mount_cmd, disk, str(mount_point)], check=True, timeout=TIMEOUT_SECONDS)
                        fix_permissions(mount_point, logger)
                        log_message(f"Disk {disk} mounted at {mount_point}", logger)
                        return mount_point, disk
        raise Exception("No suitable disk found. Ensure a disk is connected and formatted (ext4/vfat).")
    except Exception as e:
        log_message(f"Disk detection failed: {e}", logger, "error")
        raise

# Check internet connection
def check_internet(logger: Optional[logging.Logger]) -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        urllib.request.urlopen("https://www.google.com", timeout=5)
        log_message("Internet connection established", logger)
        return True
    except Exception as e:
        log_message(f"Internet connection failed: {e}", logger, "error")
        return False

# Install dependencies
def install_dependencies(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Installing dependencies", logger)
    print(f"[{SYSTEM_NAME}] Installing dependencies...")
    sub_status = ""

    try:
        clean_temp(logger)
        if not check_internet(logger):
            raise Exception("No internet connection")
        for cmd in REQUIRED_COMMANDS:
            sub_status = f"Checking {cmd}"
            if stdscr:
                update_display(stdscr, stages, current_stage, sub_status, logger)
            cmd_path = shutil.which(cmd)
            if not cmd_path:
                raise Exception(f"Required command {cmd} not found")
            log_message(f"{cmd} found: {cmd_path}", logger)
        for pkg in REQUIRED_TCE_PACKAGES:
            sub_status = f"Installing {pkg}"
            if stdscr:
                update_display(stdscr, stages, current_stage, sub_status, logger)
            result = subprocess.run(["tce-status", "-i"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
            if pkg not in result.stdout:
                subprocess.run(["tce-load", "-w", "-i", pkg], check=True, timeout=300)
                log_message(f"{pkg} installed", logger)
            fix_permissions(TCE_DIR, logger)
        sub_status = "Installing Node.js"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        node_cmd = shutil.which("node")
        if not node_cmd or f"v{NODE_VERSION}" not in subprocess.run([node_cmd, "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS).stdout:
            node_tar = Path("/tmp/node.tar.xz")
            target_dir = Path("/usr/local/node")
            wget_cmd = shutil.which("wget")
            if not wget_cmd:
                raise Exception("wget command not found")
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    subprocess.run([wget_cmd, "-O", str(node_tar), NODE_URL], check=True, timeout=300)
                    with open(node_tar, "rb") as f:
                        if hashlib.sha256(f.read()).hexdigest() != NODE_CHECKSUM:
                            raise Exception("Node.js checksum mismatch")
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"Node.js download failed: {e}")
                    time.sleep(2)
            target_dir.mkdir(parents=True, exist_ok=True)
            tar_cmd = shutil.which("tar")
            if not tar_cmd:
                raise Exception("tar command not found")
            subprocess.run([tar_cmd, "-xJf", str(node_tar), "-C", str(target_dir), "--strip-components=1"], check=True, timeout=300)
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
        sub_status = "Dependencies done"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] Dependencies installed")
    except Exception as e:
        log_message(f"Dependency installation failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)

# Verify disk
def verify_disk(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger], disk_device: str) -> None:
    log_message("Verifying disk", logger)
    print(f"[{SYSTEM_NAME}] Verifying disk...")
    sub_status = ""

    try:
        clean_temp(logger)
        sub_status = "Checking disk space"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        disk_usage = shutil.disk_usage(BASE_DIR)
        free_space_gb = disk_usage.free / (1024 ** 3)
        if free_space_gb < MIN_DISK_SPACE_GB:
            raise Exception(f"Insufficient disk space: {free_space_gb:.2f} GB available")
        sub_status = "Creating directories"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        APP_DIR.mkdir(parents=True, exist_ok=True)
        fix_permissions(APP_DIR, logger)
        sub_status = "Disk setup done"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] Disk verified")
    except Exception as e:
        log_message(f"Disk verification failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)

# Download eDEX-UI
def download_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Downloading eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Downloading eDEX-UI...")
    sub_status = ""

    try:
        clean_temp(logger)
        if not check_internet(logger):
            raise Exception("No internet connection")
        sub_status = "Cloning eDEX-UI"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        if EDEX_DIR.exists():
            shutil.rmtree(EDEX_DIR, ignore_errors=True)
        git_cmd = shutil.which("git")
        if not git_cmd:
            raise Exception("git command not found")
        subprocess.run([git_cmd, "clone", "--depth", "1", EDEX_URL, str(EDEX_DIR)], check=True, timeout=600)
        fix_permissions(EDEX_DIR, logger)
        if not (EDEX_DIR / "package.json").exists():
            raise Exception("eDEX-UI package.json not found")
        sub_status = "eDEX-UI downloaded"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI downloaded")
    except Exception as e:
        log_message(f"eDEX-UI download failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)

# Install eDEX-UI
def install_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Installing eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Installing eDEX-UI...")
    sub_status = ""

    try:
        clean_temp(logger)
        sub_status = "Installing npm dependencies"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        npm_cmd = shutil.which("npm")
        if not npm_cmd:
            raise Exception("npm command not found")
        env = os.environ.copy()
        env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
        subprocess.run([npm_cmd, "install"], cwd=str(EDEX_DIR), check=True, timeout=600, env=env)
        fix_permissions(EDEX_DIR / "node_modules", logger)
        sub_status = "Configuring eDEX-UI"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        settings_path = EDEX_DIR / "settings.json"
        settings = {
            "shell": "/bin/sh",
            "theme": "tron",
            "window": {"title": f"{SYSTEM_NAME} eDEX-UI"}
        }
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        fix_permissions(settings_path, logger)
        sub_status = "eDEX-UI installed"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI installed")
    except Exception as e:
        log_message(f"eDEX-UI installation failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)

# Start eDEX-UI
def start_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> bool:
    log_message("Starting eDEX-UI", logger)
    print(f"[{SYSTEM_NAME}] Starting eDEX-UI...")
    sub_status = ""
    process = None

    def cleanup():
        if process and process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except Exception:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        clean_temp(logger)

    try:
        clean_temp(logger)
        sub_status = "Starting Xorg"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        os.environ["DISPLAY"] = ":0"
        xorg_cmd = shutil.which("Xorg")
        if not xorg_cmd:
            raise Exception("Xorg command not found")
        xorg_process = subprocess.Popen(
            [xorg_cmd, ":0", "-quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )
        time.sleep(5)
        if xorg_process.poll() is not None:
            raise Exception("Xorg failed to start")
        sub_status = "Launching eDEX-UI"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        env = os.environ.copy()
        env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
        npm_cmd = shutil.which("npm")
        if not npm_cmd:
            raise Exception("npm command not found")
        process = subprocess.Popen(
            [npm_cmd, "start"],
            cwd=str(EDEX_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,
            env=env
        )
        time.sleep(10)
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=5)
            raise Exception(f"eDEX-UI failed to start: {stderr}")
        log_message("eDEX-UI started", logger)
        print(f"[{SYSTEM_NAME}] eDEX-UI started")
        return True
    except Exception as e:
        log_message(f"eDEX-UI startup failed: {e}", logger, "error")
        display_error(stdscr, stages[current_stage][0], str(e), logger)
        return False
    finally:
        cleanup()

# Quick check for eDEX-UI
def quick_check_edex_ui(logger: Optional[logging.Logger]) -> bool:
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
            log_message("eDEX-UI quick check passed", logger)
            print(f"[{SYSTEM_NAME}] eDEX-UI check passed")
            return True
        stdout, stderr = process.communicate(timeout=5)
        log_message(f"eDEX-UI quick check failed: {stderr}", logger, "warning")
        return False
    except Exception as e:
        log_message(f"eDEX-UI quick check failed: {e}", logger, "error")
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
        print(f"[{SYSTEM_NAME}] Report generated at {REPORT_FILE}")
    except Exception as e:
        log_message(f"Report generation failed: {e}", logger, "error")

# Main function
def main(stdscr=None):
    global BASE_DIR, TCE_DIR, APP_DIR, EDEX_DIR
    logger = setup_logger()
    start_time = time.time()
    errors = []
    log_message(f"{SYSTEM_NAME} setup started", logger)
    print(f"[{SYSTEM_NAME}] Starting setup...")

    try:
        BASE_DIR, disk_device = detect_disk(logger)
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
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
        except Exception as e:
            log_message(f"Curses setup failed: {e}", logger, "warning")
            stdscr = None

    if quick_check_edex_ui(logger):
        if start_edex_ui(stdscr, [("eDEX-UI START", "/")], 0, logger):
            generate_setup_report(start_time, errors, logger)
            print(f"[{SYSTEM_NAME}] Setup complete")
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
            stages[i] = (stages[i][0], "/")
            func(stdscr, stages, i, logger)
            stages[i] = (stages[i][0], "DONE")
            if i + 1 < len(stages):
                stages[i + 1] = (stages[i + 1][0], "/")
            if stdscr:
                update_display(stdscr, stages, i, "Stage completed", logger)
        except Exception as e:
            errors.append(f"{stages[i][0]}: {e}")
            log_message(f"Stage failed: {stages[i][0]}: {e}", logger, "error")
            display_error(stdscr, stages[i][0], str(e), logger)

    generate_setup_report(start_time, errors, logger)
    print(f"[{SYSTEM_NAME}] Setup complete with {len(errors)} errors. Check {REPORT_FILE}")

if __name__ == "__main__":
    def signal_handler(sig, frame):
        logger = setup_logger()
        log_message(f"Signal received: {sig}", logger, "info")
        clean_temp(logger)
        print(f"[{SYSTEM_NAME}] Terminated by signal {sig}", file=sys.stderr)
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"[{SYSTEM_NAME}] Initializing...")
    if len(sys.argv) > 1 and sys.argv[1] == "Berke:Kontrol":
        try:
            curses.wrapper(main)
        except Exception as e:
            logger = setup_logger()
            log_message(f"Setup failed: {e}", logger, "error")
            print(f"[{SYSTEM_NAME}] ERROR: Setup failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        main(None)

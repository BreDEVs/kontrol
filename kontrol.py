import os
import sys
import time
import subprocess
import curses
import hashlib
import shutil
import signal
import json
import logging
import logging.handlers
from typing import List, Tuple, Optional
from pathlib import Path

# Configuration
SYSTEM_NAME = "BERKE OS"
BASE_DIR = Path("/mnt/sda1")
TCE_DIR = BASE_DIR / "tce"
SYS_DIR = BASE_DIR / "system"
APP_DIR = BASE_DIR / "apps"
BACKUP_DIR = BASE_DIR / "backups"
LOG_DIR = Path("/var/log/berke")
LOG_FILE = LOG_DIR / "install.log"
EDEX_DIR = APP_DIR / "edex-ui"
NODE_VERSION = "16.20.2"
NODE_URL = f"https://nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz"
EDEX_URL = "https://github.com/GitSquared/edex-ui.git"
BOOT_SCRIPT = Path("/opt/bootlocal.sh")
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "libX11", "libxss", "libXext", "fontconfig", "git", "wget", "curl", "tar"]
REQUIRED_COMMANDS = ["python3.9", "wget", "curl", "git", "tar"]
MIN_TERM_SIZE = (20, 50)
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 5
USER = "tc"
GROUP = "staff"

# Environment setup
os.environ["PATH"] = f"{os.environ.get('PATH', '')}:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin"
os.environ["HOME"] = f"/home/{USER}"
os.environ["LD_LIBRARY_PATH"] = f"{os.environ.get('LD_LIBRARY_PATH', '')}:/usr/local/lib"

# Logger setup
def setup_logger() -> Optional[logging.Logger]:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(LOG_DIR)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
        subprocess.run(["sudo", "chmod", "775", str(LOG_DIR)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
        
        logger = logging.getLogger('BerkeOS')
        logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(str(LOG_FILE), maxBytes=1048576, backupCount=3)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(LOG_FILE)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
        subprocess.run(["sudo", "chmod", "664", str(LOG_FILE)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
        
        return logger
    except Exception as e:
        with open("/tmp/install_fallback.log", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: Logger setup failed: {e}\n")
        return None

# File hash calculation
def calculate_file_hash(filepath: Path) -> Optional[str]:
    try:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        log_message(f"File hash calculation failed: {filepath}: {e}")
        return None

# Clean temporary files
def clean_temp() -> None:
    try:
        temp_dir = Path("/tmp")
        if temp_dir.exists():
            for item in temp_dir.iterdir():
                try:
                    if item.is_file():
                        subprocess.run(["sudo", "rm", "-f", str(item)], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                except Exception:
                    pass
    except Exception as e:
        log_message(f"Temporary files cleanup failed: {e}")

# Log message with fallback
def log_message(message: str, logger: Optional[logging.Logger] = None) -> None:
    try:
        if logger:
            logger.info(message)
        else:
            with open("/tmp/install_fallback.log", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
    except Exception:
        pass

# Draw border
def draw_border(stdscr, y: int, x: int, height: int, width: int) -> None:
    try:
        stdscr.addstr(y, x, "┌" + "─" * (width - 2) + "┐")
        for i in range(1, height - 1):
            stdscr.addstr(y + i, x, "│" + " " * (width - 2) + "│")
        stdscr.addstr(y + height - 1, x, "└" + "─" * (width - 2) + "┘")
    except Exception as e:
        log_message(f"Border drawing failed: {e}")

# Error display
def display_error(stdscr, stage: str, error_msg: str, logger: Optional[logging.Logger]) -> None:
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        box_width = min(cols - 4, 60)
        box_height = min(rows - 4, 15)
        box_y = (rows - box_height) // 2
        box_x = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        draw_border(stdscr, box_y, box_x, box_height, box_width)

        title = "B E R K E  O S"
        title_x = box_x + (box_width - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_y + 1, title_x, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        error_title = "ERROR OCCURRED!"
        error_title_x = box_x + (box_width - len(error_title)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_y + 3, error_title_x, error_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(2))

        stage_info = f"Stage: {stage}"
        stage_x = box_x + (box_width - len(stage_info)) // 2
        stdscr.addstr(box_y + 5, stage_x, stage_info)

        error_info = f"Error: {error_msg[:box_width-4]}"
        error_x = box_x + (box_width - len(error_info)) // 2
        stdscr.addstr(box_y + 6, error_x, error_info)

        solution = f"Check logs: {LOG_FILE}"
        solution_x = box_x + (box_width - len(solution)) // 2
        stdscr.addstr(box_y + 8, solution_x, solution)

        exit_prompt = "Press any key to exit"
        exit_x = box_x + (box_width - len(exit_prompt)) // 2
        stdscr.addstr(box_y + box_height - 2, exit_x, exit_prompt)
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        log_message(f"Error display failed: {e}", logger)
    sys.exit(1)

# Main display
def update_display(stdscr, stages: List[Tuple[str, str]], current_stage: int, sub_status: str, logger: Optional[logging.Logger]) -> None:
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        box_width = min(cols - 4, 60)
        box_height = min(rows - 4, 20)
        box_y = (rows - box_height) // 2
        box_x = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        draw_border(stdscr, box_y, box_x, box_height, box_width)

        title = "B E R K E  O S"
        title_x = box_x + (box_width - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_y + 1, title_x, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        sys_title = "System initializing"
        sys_x = box_x + (box_width - len(sys_title)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_y + 3, sys_x, sys_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(2))

        for i, (stage_name, status) in enumerate(stages):
            stage_text = f"{i+1}. {stage_name} [{status}]"
            stage_x = box_x + 2
            row = box_y + 5 + i
            if row >= box_y + box_height - 3:
                break
            if i == current_stage and status == "/":
                stdscr.attron(curses.color_pair(4))
                stage_text = f"{i+1}. {stage_name} [{'/-\\|'[int(time.time() * 4) % 4]}]"
                stdscr.addstr(row, stage_x, stage_text[:box_width-4], curses.A_BOLD)
                sub_status_text = f"Status: {sub_status[:box_width-10]}"
                sub_status_x = box_x + 2
                stdscr.addstr(row + 1, sub_status_x, sub_status_text[:box_width-4], curses.A_BOLD)
                stdscr.attroff(curses.color_pair(4))
            elif status == "DONE":
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(row, stage_x, stage_text[:box_width-4])
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(row, stage_x, stage_text[:box_width-4])
                stdscr.attroff(curses.color_pair(5))

        if sub_status and stages[current_stage][1] == "DONE":
            sub_status_text = f"Status: {sub_status[:box_width-10]}"
            sub_status_x = box_x + 2
            stdscr.attron(curses.color_pair(4))
            stdscr.addstr(box_y + 5 + current_stage + 1, sub_status_x, sub_status_text[:box_width-4], curses.A_BOLD)
            stdscr.attroff(curses.color_pair(4))

        stdscr.refresh()
    except Exception as e:
        log_message(f"Display update failed: {e}", logger)

# Install dependencies
def install_dependencies(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Checking dependencies", logger)
    sub_status = ""

    try:
        clean_temp()
        
        for cmd in REQUIRED_COMMANDS:
            sub_status = f"Checking {cmd}"
            update_display(stdscr, stages, current_stage, sub_status, logger)
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    result = subprocess.run(["which", cmd], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    if cmd == "python3.9":
                        result = subprocess.run([cmd, "--version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                        if "3.9" not in result.stdout:
                            raise Exception("Python 3.9 version mismatch")
                    log_message(f"{cmd} found: {result.stdout.strip()}", logger)
                    break
                except Exception:
                    sub_status = f"Installing {cmd}"
                    update_display(stdscr, stages, current_stage, sub_status, logger)
                    try:
                        subprocess.run(["sudo", "tce-load", "-w", "-i", cmd], check=True, timeout=300, capture_output=True)
                        result = subprocess.run(["which", cmd], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                        if cmd == "python3.9":
                            result = subprocess.run([cmd, "--version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                            if "3.9" not in result.stdout:
                                raise Exception("Python 3.9 installation failed")
                        log_message(f"{cmd} installed: {result.stdout.strip()}", logger)
                        break
                    except Exception as e:
                        if attempt == RETRY_ATTEMPTS - 1:
                            raise Exception(f"{cmd} installation failed: {e}")
                        time.sleep(2)

        for pkg in REQUIRED_TCE_PACKAGES:
            if pkg in REQUIRED_COMMANDS:
                continue
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
                    subprocess.run(["sudo", "tce-load", "-w", "-i", pkg], check=True, timeout=300, capture_output=True)
                    log_message(f"{pkg} installed", logger)
                    if pkg == "Xorg-7.7":
                        try:
                            x11_dir = Path("/usr/local/lib/X11")
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
                            xorg_conf_dir.mkdir(parents=True, exist_ok=True)
                            with open("/tmp/20-xorg-vesa.conf", "w") as f:
                                f.write(
                                    'Section "Device"\n'
                                    '    Identifier "Card0"\n'
                                    '    Driver "vesa"\n'
                                    'EndSection\n'
                                )
                            subprocess.run(["sudo", "mv", "/tmp/20-xorg-vesa.conf", str(xorg_conf)], check=True, timeout=TIMEOUT_SECONDS)
                            subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(xorg_conf)], check=True, timeout=TIMEOUT_SECONDS)
                            subprocess.run(["sudo", "chmod", "664", str(xorg_conf)], check=True, timeout=TIMEOUT_SECONDS)
                            log_message("VESA driver configured", logger)
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"{pkg} installation failed: {e}")
                    time.sleep(2)
                try:
                    onboot_file = TCE_DIR / "onboot.lst"
                    subprocess.run(["sudo", "touch", str(onboot_file)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(onboot_file)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chmod", "664", str(onboot_file)], check=True, timeout=TIMEOUT_SECONDS)
                    with open(onboot_file, "r") as f:
                        content = f.read()
                    if pkg not in content:
                        with open("/tmp/onboot.lst", "w") as f:
                            f.write(content.rstrip() + f"\n{pkg}\n")
                        subprocess.run(["sudo", "mv", "/tmp/onboot.lst", str(onboot_file)], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(onboot_file)], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "chmod", "664", str(onboot_file)], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                except Exception as e:
                    raise Exception(f"onboot.lst update failed: {e}")

        sub_status = "Checking Node.js"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
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
                    if node_tar.exists():
                        node_tar.unlink()
                    if node_extract_dir.exists():
                        shutil.rmtree(node_extract_dir)
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    subprocess.run(["sudo", "wget", "-O", str(node_tar), NODE_URL], check=True, timeout=300, capture_output=True)
                    node_extract_dir.mkdir(parents=True, exist_ok=True)
                    subprocess.run(["sudo", "tar", "-xJf", str(node_tar), "-C", str(node_extract_dir)], check=True, timeout=300)
                    extracted_dir = next(node_extract_dir.iterdir())
                    subprocess.run(["sudo", "mv", str(extracted_dir), str(target_dir)], check=True, timeout=10)
                    for binary in ["node", "npm"]:
                        binary_path = target_dir / "bin" / binary
                        link_path = Path(f"/usr/local/bin/{binary}")
                        if link_path.exists():
                            link_path.unlink()
                        subprocess.run(["sudo", "ln", "-s", str(binary_path), str(link_path)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chown", "-R", f"{USER}:{GROUP}", str(target_dir)], check=True, timeout=10)
                    subprocess.run(["sudo", "chmod", "-R", "755", str(target_dir)], check=True, timeout=10)
                    result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
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
                        node_tar.unlink()
                    if node_extract_dir.exists():
                        shutil.rmtree(node_extract_dir)

        sub_status = "Dependencies completed"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"Dependency stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Verify disk
def verify_disk(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Verifying disk", logger)
    sub_status = ""

    try:
        clean_temp()
        sub_status = "Creating disk directory"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                BASE_DIR.mkdir(parents=True, exist_ok=True)
                subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "775", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                if not BASE_DIR.exists():
                    raise Exception("Disk directory creation failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Disk directory creation failed: {e}")
                time.sleep(2)

        sub_status = "Mounting disk"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                result = subprocess.run(["mountpoint", "-q", str(BASE_DIR)], capture_output=True, check=False, timeout=TIMEOUT_SECONDS)
                if result.returncode != 0:
                    subprocess.run(["sudo", "mkdir", "-p", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                    try:
                        subprocess.run(["sudo", "mount", "/dev/sda1", str(BASE_DIR)], check=True, timeout=10, capture_output=True)
                    except Exception:
                        sub_status = "Formatting disk"
                        update_display(stdscr, stages, current_stage, sub_status, logger)
                        subprocess.run(["sudo", "mkfs.ext4", "-F", "/dev/sda1"], check=True, timeout=600, capture_output=True)
                        subprocess.run(["sudo", "mount", "/dev/sda1", str(BASE_DIR)], check=True, timeout=10)
                subprocess.run(["sudo", "mount", "-o", "remount,rw", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                result = subprocess.run(["df", "-h", str(BASE_DIR)], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                if str(BASE_DIR) not in result.stdout:
                    raise Exception("Disk mount verification failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Disk mount failed: {e}")
                time.sleep(2)

        sub_status = "Creating directories"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        directories = [TCE_DIR, SYS_DIR, APP_DIR, BACKUP_DIR]
        for directory in directories:
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(directory)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chmod", "775", str(directory)], check=True, timeout=TIMEOUT_SECONDS)
                    if not directory.exists():
                        raise Exception(f"Directory creation failed: {directory}")
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"Directory creation failed: {directory}: {e}")
                    time.sleep(2)

        sub_status = "Disk setup completed"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"Disk stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Verify backup
def verify_backup(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Creating backup", logger)
    sub_status = ""

    try:
        clean_temp()
        sub_status = "Creating backup directory"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(BACKUP_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "775", str(BACKUP_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                if not BACKUP_DIR.exists():
                    raise Exception("Backup directory creation failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Backup directory creation failed: {e}")
                time.sleep(2)

        sub_status = "Backing up files"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_file = BACKUP_DIR / f"backup_{timestamp}.tar.gz"
                dirs_to_backup = [SYS_DIR, APP_DIR, TCE_DIR]
                for d in dirs_to_backup:
                    d.mkdir(parents=True, exist_ok=True)
                    subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(d)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chmod", "775", str(d)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(
                    ["sudo", "tar", "-czf", str(backup_file)] + [str(d) for d in dirs_to_backup],
                    check=True, timeout=600, capture_output=True
                )
                subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(backup_file)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "664", str(backup_file)], check=True, timeout=TIMEOUT_SECONDS)
                if not backup_file.exists():
                    raise Exception("Backup file creation failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Backup creation failed: {e}")
                time.sleep(2)

        sub_status = "Verifying backup"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                backup_hash = calculate_file_hash(backup_file)
                if not backup_hash:
                    raise Exception("Backup hash calculation failed")
                backup_log = BACKUP_DIR / "backup_log.txt"
                with open("/tmp/backup_log.txt", "a") as f:
                    f.write(f"{timestamp}: {backup_file}, SHA256: {backup_hash}\n")
                subprocess.run(["sudo", "mv", "/tmp/backup_log.txt", str(backup_log)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(backup_log)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "664", str(backup_log)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                if not backup_log.exists():
                    raise Exception("Backup log creation failed")
                log_message(f"Backup created: {backup_file}, SHA256: {backup_hash}", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Backup verification failed: {e}")
                time.sleep(2)

        sub_status = "Backup completed"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"Backup stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Download EDEX-UI
def download_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Downloading EDEX-UI", logger)
    sub_status = ""

    try:
        clean_temp()
        sub_status = "Checking EDEX-UI presence"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if EDEX_DIR.exists() and (EDEX_DIR / "package.json").exists():
                    log_message("EDEX-UI already present", logger)
                    break
                sub_status = "Cloning EDEX-UI"
                update_display(stdscr, stages, current_stage, sub_status, logger)
                if EDEX_DIR.exists():
                    shutil.rmtree(EDEX_DIR)
                subprocess.run(["sudo", "git", "clone", EDEX_URL, str(EDEX_DIR)], check=True, timeout=600, capture_output=True)
                subprocess.run(["sudo", "chown", "-R", f"{USER}:{GROUP}", str(EDEX_DIR)], check=True, timeout=10)
                subprocess.run(["sudo", "chmod", "-R", "775", str(EDEX_DIR)], check=True, timeout=10)
                if not (EDEX_DIR / "package.json").exists():
                    raise Exception("EDEX-UI package.json not found")
                log_message("EDEX-UI cloned", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"EDEX-UI clone failed: {e}")
                time.sleep(2)

        sub_status = "EDEX-UI downloaded"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"EDEX-UI download stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Install EDEX-UI
def install_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Installing EDEX-UI", logger)
    sub_status = ""

    try:
        clean_temp()
        sub_status = "Installing npm dependencies"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if (EDEX_DIR / "node_modules").exists():
                    shutil.rmtree(EDEX_DIR / "node_modules")
                subprocess.run(
                    ["sudo", "npm", "install", "--unsafe-perm", "--no-audit", "--no-fund"],
                    cwd=str(EDEX_DIR), check=True, timeout=600, capture_output=True
                )
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
                    "shell": "/bin/bash",
                    "shellArgs": ["-c", f"export PATH=$PATH:/usr/local/bin; exec bash"],
                    "theme": "tron",
                    "window": {"title": f"{SYSTEM_NAME} EDEX-UI"},
                    "performance": {"lowPowerMode": False, "gpuAcceleration": True}
                }
                with open("/tmp/settings.json", "w") as f:
                    json.dump(settings, f, indent=2)
                subprocess.run(["sudo", "mv", "/tmp/settings.json", str(settings_path)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(settings_path)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "664", str(settings_path)], check=True, timeout=TIMEOUT_SECONDS)
                with open(settings_path, "r") as f:
                    if SYSTEM_NAME not in f.read():
                        raise Exception("Settings content verification failed")
                log_message("EDEX-UI settings customized", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"EDEX-UI settings customization failed: {e}")
                time.sleep(2)

        sub_status = "Optimizing Xorg"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                xorg_conf_dir = Path("/etc/X11/xorg.conf.d")
                xorg_conf = xorg_conf_dir / "10-optimizations.conf"
                xorg_conf_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(xorg_conf_dir)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "775", str(xorg_conf_dir)], check=True, timeout=TIMEOUT_SECONDS)
                with open("/tmp/xorg.conf", "w") as f:
                    f.write(
                        'Section "Device"\n'
                        '    Identifier "Card0"\n'
                        '    Driver "vesa"\n'
                        '    Option "AccelMethod" "exa"\n'
                        'EndSection\n'
                    )
                subprocess.run(["sudo", "mv", "/tmp/xorg.conf", str(xorg_conf)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(xorg_conf)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "664", str(xorg_conf)], check=True, timeout=TIMEOUT_SECONDS)
                if not xorg_conf.exists():
                    raise Exception("Xorg configuration file creation failed")
                log_message("Xorg optimized", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Xorg optimization failed: {e}")
                time.sleep(2)

        sub_status = "EDEX-UI installation completed"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"EDEX-UI installation stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Start EDEX-UI
def start_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Starting EDEX-UI", logger)
    sub_status = ""
    process = None

    def cleanup():
        if process and process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=TIMEOUT_SECONDS)
            except Exception:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        subprocess.run(["sudo", "killall", "-q", "node"], capture_output=True, timeout=TIMEOUT_SECONDS)
        subprocess.run(["sudo", "killall", "-q", "Xorg"], capture_output=True, timeout=TIMEOUT_SECONDS)
        clean_temp()

    try:
        clean_temp()
        sub_status = "Preparing X11 environment"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                os.environ["DISPLAY"] = ":0"
                result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, check=False, timeout=TIMEOUT_SECONDS)
                if result.returncode != 0:
                    xorg_process = subprocess.Popen(
                        ["sudo", "Xorg", ":0", "-quiet"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid
                    )
                    time.sleep(3)
                    if xorg_process.poll() is not None:
                        raise Exception("Xorg failed to start")
                log_message("X11 environment prepared", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"X11 startup failed: {e}")
                time.sleep(2)

        sub_status = "Launching EDEX-UI"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                env = os.environ.copy()
                env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
                env["LD_LIBRARY_PATH"] = f"/usr/local/lib:{env.get('LD_LIBRARY_PATH', '')}"
                process = subprocess.Popen(
                    ["sudo", "npm", "start", "--unsafe-perm"],
                    cwd=str(EDEX_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,
                    env=env
                )
                time.sleep(15)
                if process.poll() is not None:
                    stdout, stderr = process.communicate(timeout=TIMEOUT_SECONDS)
                    raise Exception(f"EDEX-UI startup failed: {stderr}")
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                if "node" not in result.stdout or "edex-ui" not in result.stdout:
                    raise Exception("EDEX-UI process verification failed")
                log_message("EDEX-UI started", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"EDEX-UI startup failed: {e}")
                time.sleep(2)

        sub_status = "EDEX-UI started"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"EDEX-UI startup stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        cleanup()

# Configure autostart
def configure_autostart(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Configuring autostart", logger)
    sub_status = ""

    try:
        clean_temp()
        sub_status = "Updating boot script"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                script_path = BASE_DIR / "kontrol.py"
                if not script_path.exists():
                    raise Exception("kontrol.py not found")
                subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(script_path)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "775", str(script_path)], check=True, timeout=TIMEOUT_SECONDS)
                BOOT_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
                if BOOT_SCRIPT.exists():
                    with open(BOOT_SCRIPT, "r") as f:
                        content = f.read()
                    if str(script_path) in content:
                        log_message("Autostart already configured", logger)
                    else:
                        subprocess.run(["sudo", "cp", str(BOOT_SCRIPT), f"{BOOT_SCRIPT}.bak"], check=True, timeout=TIMEOUT_SECONDS)
                        with open("/tmp/bootlocal.sh", "w") as f:
                            f.write(content.rstrip() + f"\npython3.9 {script_path} --skip-ui &\n")
                        subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", str(BOOT_SCRIPT)], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(BOOT_SCRIPT)], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "chmod", "775", str(BOOT_SCRIPT)], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                        log_message("Autostart configured", logger)
                else:
                    with open("/tmp/bootlocal.sh", "w") as f:
                        f.write(f"#!/bin/sh\npython3.9 {script_path} --skip-ui &\n")
                    subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", str(BOOT_SCRIPT)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chown", f"{USER}:{GROUP}", str(BOOT_SCRIPT)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chmod", "775", str(BOOT_SCRIPT)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                    log_message("Boot script created", logger)
                with open(BOOT_SCRIPT, "r") as f:
                    if str(script_path) not in f.read():
                        raise Exception("Boot script content verification failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Autostart configuration failed: {e}")
                time.sleep(2)

        sub_status = "Autostart configuration completed"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"Autostart stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Main function
def main(stdscr):
    logger = setup_logger()
    log_message(f"{SYSTEM_NAME} started", logger)

    try:
        subprocess.run(["resize"], capture_output=True, timeout=TIMEOUT_SECONDS)
        curses.curs_set(0)
        stdscr.timeout(100)
        rows, cols = stdscr.getmaxyx()
        if rows < MIN_TERM_SIZE[0] or cols < MIN_TERM_SIZE[1]:
            raise Exception(f"Terminal size too small: {MIN_TERM_SIZE[1]}x{MIN_TERM_SIZE[0]}")
        box_width = min(cols - 4, 60)
        box_height = min(rows - 4, 15)
        box_y = (rows - box_height) // 2
        box_x = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        draw_border(stdscr, box_y, box_x, box_height, box_width)

        title = "B E R K E  O S"
        title_x = box_x + (box_width - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_y + 1, title_x, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        status = "Waiting"
        status_x = box_x + (box_width - len(status)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_y + box_height // 2, status_x, status)
        stdscr.attroff(curses.color_pair(2))
        stdscr.refresh()
        time.sleep(2)
    except Exception as e:
        log_message(f"Curses initialization failed: {e}", logger)
        display_error(stdscr, "Initialization", str(e), logger)

    skip_ui = "--skip-ui" in sys.argv
    if skip_ui:
        if EDEX_DIR.exists() and (EDEX_DIR / "package.json").exists():
            start_edex_ui(None, [("EDEX-UI START", "/")], 0, logger)
        else:
            log_message("EDEX-UI not found, full installation required", logger)
            sys.exit(1)

    stages = [
        ("DEPENDENCY INSTALLATION", "/"),
        ("DISK CONFIGURATION", "-"),
        ("BACKUP CREATION", "-"),
        ("EDEX-UI DOWNLOAD", "-"),
        ("EDEX-UI INSTALLATION", "-"),
        ("EDEX-UI START", "-"),
        ("AUTOSTART CONFIGURATION", "-")
    ]
    functions = [
        install_dependencies,
        verify_disk,
        verify_backup,
        download_edex_ui,
        install_edex_ui,
        start_edex_ui,
        configure_autostart
    ]

    for i, func in enumerate(functions):
        try:
            stages[i] = (stages[i][0], "/")
            func(stdscr, stages, i, logger)
            stages[i] = (stages[i][0], "DONE")
            if i + 1 < len(stages):
                stages[i + 1] = (stages[i + 1][0], "/")
            update_display(stdscr, stages, i, "Stage completed", logger)
        except Exception as e:
            log_message(f"Stage failed: {stages[i][0]}: {e}", logger)
            display_error(stdscr, stages[i][0], str(e), logger)

    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        box_width = min(cols - 4, 60)
        box_height = min(rows - 4, 15)
        box_y = (rows - box_height) // 2
        box_x = (cols - box_width) // 2
        draw_border(stdscr, box_y, box_x, box_height, box_width)

        title = "B E R K E  O S"
        title_x = box_x + (box_width - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_y + 1, title_x, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        complete_msg = "Installation Completed Successfully!"
        complete_x = box_x + (box_width - len(complete_msg)) // 2
        stdscr.addstr(box_y + 5, complete_x, complete_msg, curses.A_BOLD)

        prompt = "Press any key to continue..."
        prompt_x = box_x + (box_width - len(prompt)) // 2
        stdscr.addstr(box_y + 7, prompt_x, prompt)
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        log_message(f"Completion screen failed: {e}", logger)

if __name__ == "__main__":
    def signal_handler(sig, frame):
        logger = setup_logger()
        log_message(f"Signal received: {sig}", logger)
        subprocess.run(["sudo", "killall", "-q", "node"], capture_output=True, timeout=TIMEOUT_SECONDS)
        subprocess.run(["sudo", "killall", "-q", "Xorg"], capture_output=True, timeout=TIMEOUT_SECONDS)
        clean_temp()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        curses.wrapper(main)
    except Exception as e:
        logger = setup_logger()
        log_message(f"{SYSTEM_NAME} crashed: {e}", logger)
        sys.exit(1)

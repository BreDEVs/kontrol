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
from typing import List, Tuple, Optional
from pathlib import Path
import socket
import urllib.request

# Configuration
SYSTEM_NAME = "BERKE OS"
BASE_DIR = Path("/mnt/sda1")
TCE_DIR = BASE_DIR / "tce"
APP_DIR = BASE_DIR / "apps"
LOG_DIR = Path("/var/log/berke")
LOG_FILE = LOG_DIR / "install.log"
EDEX_DIR = APP_DIR / "edex-ui"
NODE_VERSION = "16.20.2"
NODE_URL = "https://nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz"
EDEX_URL = "https://github.com/GitSquared/edex-ui.git"
GITHUB_SCRIPT_URL = "https://raw.githubusercontent.com/yourusername/berke-os/main/kontrol.py"  # Replace with your repo
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "libX11", "libXScrnSaver", "libXext", "fontconfig", "git", "wget", "curl", "tar"]
REQUIRED_COMMANDS = ["python3.9", "wget", "curl", "git", "tar", "tce-load", "tce-status"]
MIN_TERM_SIZE = (20, 50)
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 10
USER = "tc"
GROUP = "staff"

# Environment setup
os.environ["PATH"] = f"{os.environ.get('PATH', '')}:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin"
os.environ["HOME"] = f"/home/{USER}"
os.environ["LD_LIBRARY_PATH"] = f"{os.environ.get('LD_LIBRARY_PATH', '')}:/usr/local/lib:/usr/lib"

# Logger setup
def setup_logger() -> Optional[logging.Logger]:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["chown", f"{USER}:{GROUP}", str(LOG_DIR)], check=True, timeout=TIMEOUT_SECONDS)
        subprocess.run(["chmod", "775", str(LOG_DIR)], check=True, timeout=TIMEOUT_SECONDS)
        
        logger = logging.getLogger('BerkeOS')
        logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(str(LOG_FILE), maxBytes=1048576, backupCount=3)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        subprocess.run(["chown", f"{USER}:{GROUP}", str(LOG_FILE)], check=True, timeout=TIMEOUT_SECONDS)
        subprocess.run(["chmod", "664", str(LOG_FILE)], check=True, timeout=TIMEOUT_SECONDS)
        
        return logger
    except Exception as e:
        with open("/tmp/install_fallback.log", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: Logger setup failed: {e}\n")
        return None

# Clean temporary files
def clean_temp() -> None:
    try:
        temp_dir = Path("/tmp")
        if temp_dir.exists():
            for item in temp_dir.iterdir():
                try:
                    if item.is_file():
                        subprocess.run(["rm", "-f", str(item)], check=True, timeout=TIMEOUT_SECONDS)
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

# Center text
def center_text(text: str, width: int) -> Tuple[str, int]:
    text = text[:width-4]
    padding = (width - len(text)) // 2
    return text, padding

# Error display
def display_error(stdscr, stage: str, error_msg: str, logger: Optional[logging.Logger]) -> None:
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        
        lines = [
            ("BERKE OS - ERROR!", curses.A_BOLD | curses.color_pair(1), 2),
            (f"Stage: {stage}", curses.color_pair(4), 4),
            (f"Error: {error_msg}", curses.color_pair(4), 6),
            (f"Logs: {LOG_FILE}", curses.color_pair(4), 8),
            ("Press any key to exit", curses.color_pair(4), 10)
        ]
        
        for text, attr, row in lines:
            formatted_text, x = center_text(text, cols)
            stdscr.addstr(row, x, formatted_text, attr)
        
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
        
        title, title_x = center_text("BERKE OS - Setup", cols)
        stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))

        for i, (stage_name, status) in enumerate(stages):
            row = 5 + i * 3
            if row >= rows - 2:
                break
            stage_text = f"{i+1}. {stage_name[:20]}: [{'DONE' if status == 'DONE' else anim_chars[int(time.time() * 4) % 4] if i == current_stage and status == '/' else '-'}]"
            text, x = center_text(stage_text, cols)
            attr = curses.color_pair(2) | curses.A_BOLD if i == current_stage and status == "/" else curses.color_pair(3) if status == "DONE" else curses.color_pair(4)
            stdscr.addstr(row, x, text, attr)
            if i == current_stage and status == "/":
                sub_text, sub_x = center_text(f"{sub_status[:30]}", cols)
                stdscr.addstr(row + 1, sub_x, sub_text, curses.color_pair(2))

        stdscr.refresh()
    except Exception as e:
        log_message(f"Display update failed: {e}", logger)

# Ensure permissions
def ensure_permissions(path: Path, user: str, group: str, mode: str) -> None:
    for attempt in range(RETRY_ATTEMPTS):
        try:
            if path.exists():
                subprocess.run(["chown", "-R", f"{user}:{group}", str(path)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["chmod", "-R", mode, str(path)], check=True, timeout=TIMEOUT_SECONDS)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["chown", f"{user}:{group}", str(path.parent)], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["chmod", "775", str(path.parent)], check=True, timeout=TIMEOUT_SECONDS)
            break
        except Exception as e:
            if attempt == RETRY_ATTEMPTS - 1:
                log_message(f"Permission setting failed for {path}: {e}")
                raise Exception(f"Permission setting failed for {path}: {e}")
            time.sleep(1)

# Check internet connection
def check_internet(logger: Optional[logging.Logger]) -> bool:
    dns_servers = [("8.8.8.8", 53), ("1.1.1.1", 53)]
    for server, port in dns_servers:
        try:
            socket.create_connection((server, port), timeout=5)
            log_message(f"Internet connection established via {server}", logger)
            return True
        except Exception:
            continue
    log_message("Internet connection failed", logger)
    return False

# Update kontrol.py from GitHub
def update_script(stdscr, logger: Optional[logging.Logger]) -> None:
    log_message("Updating kontrol.py from GitHub", logger)
    stages = [("SCRIPT UPDATE", "/")]
    sub_status = ""
    anim_chars = "/-\\|"

    try:
        clean_temp()
        if not check_internet(logger):
            raise Exception("No internet connection")

        sub_status = "Downloading new script"
        update_display(stdscr, stages, 0, sub_status, logger)
        script_path = BASE_DIR / "kontrol.py"
        temp_script = Path("/tmp/kontrol.py.new")
        
        for attempt in range(RETRY_ATTEMPTS):
            try:
                with urllib.request.urlopen(GITHUB_SCRIPT_URL) as response:
                    with open(temp_script, "wb") as f:
                        f.write(response.read())
                if not temp_script.exists():
                    raise Exception("Script download failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"Script download failed: {e}")
                time.sleep(1)

        sub_status = "Replacing script"
        update_display(stdscr, stages, 0, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if script_path.exists():
                    subprocess.run(["mv", str(script_path), f"{script_path}.bak"], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["mv", str(temp_script), str(script_path)], check=True, timeout=TIMEOUT_SECONDS)
                ensure_permissions(script_path, USER, GROUP, "755")
                log_message("Script updated successfully", logger)
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
        title, title_x = center_text("BERKE OS - Update Completed", cols)
        stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))
        prompt, prompt_x = center_text("Press any key to exit...", cols)
        stdscr.addstr(4, prompt_x, prompt, curses.color_pair(4))
        stdscr.refresh()
        stdscr.getch()
        sys.exit(0)
    except Exception as e:
        log_message(f"Script update failed: {e}", logger)
        display_error(stdscr, "SCRIPT UPDATE", str(e), logger)
    finally:
        clean_temp()

# Install dependencies
def install_dependencies(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Checking dependencies", logger)
    sub_status = ""
    anim_chars = "/-\\|"

    try:
        clean_temp()
        if not check_internet(logger):
            raise Exception("No internet connection")

        # Verify essential commands
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
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"Required command {cmd} not found: {e}")
                    time.sleep(1)

        # Ensure TCE directory permissions
        ensure_permissions(TCE_DIR, USER, GROUP, "775")

        # Install TCE packages
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
                    subprocess.run(["tce-load", "-w", "-i", pkg], check=True, timeout=300)
                    log_message(f"{pkg} installed", logger)
                    if pkg == "Xorg-7.7":
                        try:
                            x11_dir = Path("/usr/local/lib/X11")
                            ensure_permissions(x11_dir, USER, GROUP, "775")
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
                            ensure_permissions(xorg_conf_dir, USER, GROUP, "775")
                            with open(xorg_conf, "w") as f:
                                f.write(
                                    'Section "Device"\n'
                                    '    Identifier "Card0"\n'
                                    '    Driver "vesa"\n'
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
                            ensure_permissions(xorg_conf, USER, GROUP, "664")
                            log_message("VESA driver configured", logger)
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"{pkg} installation failed: {e}")
                    time.sleep(1)

            # Update onboot.lst
            try:
                onboot_file = TCE_DIR / "onboot.lst"
                ensure_permissions(onboot_file, USER, GROUP, "664")
                if not onboot_file.exists():
                    with open(onboot_file, "w") as f:
                        f.write("")
                
                with open(onboot_file, "r") as f:
                    content = f.read().strip()
                if pkg not in content:
                    with open(onboot_file, "a") as f:
                        f.write(f"{pkg}\n")
                    ensure_permissions(onboot_file, USER, GROUP, "664")
                    log_message(f"Added {pkg} to onboot.lst", logger)
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"onboot.lst update failed for {pkg}: {e}")
                time.sleep(1)

        # Install Node.js
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
                        shutil.rmtree(node_extract_dir, ignore_errors=True)
                    if target_dir.exists():
                        shutil.rmtree(target_dir, ignore_errors=True)
                    subprocess.run(["wget", "-O", str(node_tar), NODE_URL], check=True, timeout=300)
                    node_extract_dir.mkdir(parents=True, exist_ok=True)
                    ensure_permissions(node_extract_dir, USER, GROUP, "775")
                    subprocess.run(["tar", "-xJf", str(node_tar), "-C", str(node_extract_dir)], check=True, timeout=300)
                    extracted_dir = next(node_extract_dir.iterdir())
                    subprocess.run(["mv", str(extracted_dir), str(target_dir)], check=True, timeout=10)
                    for binary in ["node", "npm"]:
                        binary_path = target_dir / "bin" / binary
                        link_path = Path(f"/usr/local/bin/{binary}")
                        if link_path.exists():
                            link_path.unlink()
                        subprocess.run(["ln", "-s", str(binary_path), str(link_path)], check=True, timeout=TIMEOUT_SECONDS)
                    ensure_permissions(target_dir, USER, GROUP, "755")
                    result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    if f"v{NODE_VERSION}" not in result.stdout:
                        raise Exception(f"Node.js version verification failed: {result.stdout.strip()}")
                    log_message(f"Node.js {result.stdout.strip()} and npm {npm_result.stdout.strip()} installed", logger)
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        raise Exception(f"Node.js installation failed: {e}")
                    time.sleep(1)
                finally:
                    if node_tar.exists():
                        node_tar.unlink()
                    if node_extract_dir.exists():
                        shutil.rmtree(node_extract_dir, ignore_errors=True)

        sub_status = "Dependencies done"
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
    anim_chars = "/-\\|"

    try:
        clean_temp()
        sub_status = "Creating disk dir"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                ensure_permissions(BASE_DIR, USER, GROUP, "775")
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
                result = subprocess.run(["mountpoint", "-q", str(BASE_DIR)], capture_output=True, check=False, timeout=TIMEOUT_SECONDS)
                if result.returncode != 0:
                    subprocess.run(["mkdir", "-p", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["mount", "/dev/sda1", str(BASE_DIR)], check=True, timeout=10)
                subprocess.run(["mount", "-o", "remount,rw", str(BASE_DIR)], check=True, timeout=TIMEOUT_SECONDS)
                result = subprocess.run(["df", "-h", str(BASE_DIR)], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
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
                ensure_permissions(APP_DIR, USER, GROUP, "775")
                if not APP_DIR.exists():
                    raise Exception("App directory creation failed")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"App directory creation failed: {e}")
                time.sleep(1)

        sub_status = "Disk setup done"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"Disk stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Download eDEX-UI
def download_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Downloading eDEX-UI", logger)
    sub_status = ""
    anim_chars = "/-\\|"

    try:
        clean_temp()
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
                ensure_permissions(EDEX_DIR.parent, USER, GROUP, "775")
                subprocess.run(["git", "clone", EDEX_URL, str(EDEX_DIR)], check=True, timeout=600)
                ensure_permissions(EDEX_DIR, USER, GROUP, "775")
                if not (EDEX_DIR / "package.json").exists():
                    raise Exception("eDEX-UI package.json not found")
                log_message("eDEX-UI cloned", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"eDEX-UI clone failed: {e}")
                time.sleep(1)

        sub_status = "eDEX-UI downloaded"
        update_display(stdscr, stages, current_stage, sub_status, logger)
    except Exception as e:
        log_message(f"eDEX-UI download stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Install eDEX-UI
def install_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> None:
    log_message("Installing eDEX-UI", logger)
    sub_status = ""
    anim_chars = "/-\\|"

    try:
        clean_temp()
        sub_status = "Installing npm deps"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                if (EDEX_DIR / "node_modules").exists():
                    shutil.rmtree(EDEX_DIR / "node_modules", ignore_errors=True)
                env = os.environ.copy()
                env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
                env["NODE_PATH"] = str(EDEX_DIR / "node_modules")
                subprocess.run(
                    ["npm", "install", "--no-audit", "--no-fund"],
                    cwd=str(EDEX_DIR), check=True, timeout=600, env=env
                )
                ensure_permissions(EDEX_DIR / "node_modules", USER, GROUP, "775")
                if not (EDEX_DIR / "node_modules").exists():
                    raise Exception("npm dependencies verification failed")
                log_message("npm dependencies installed", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"npm dependencies installation failed: {e}")
                time.sleep(1)

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
                ensure_permissions(settings_path, USER, GROUP, "664")
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
                ensure_permissions(xorg_conf_dir, USER, GROUP, "775")
                with open(xorg_conf, "w") as f:
                    f.write(
                        'Section "Device"\n'
                        '    Identifier "Card0"\n'
                        '    Driver "vesa"\n'
                        '    Option "AccelMethod" "exa"\n'
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
                ensure_permissions(xorg_conf, USER, GROUP, "664")
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
    except Exception as e:
        log_message(f"eDEX-UI installation stage failed: {e}", logger)
        display_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        clean_temp()

# Start eDEX-UI
def start_edex_ui(stdscr, stages: List[Tuple[str, str]], current_stage: int, logger: Optional[logging.Logger]) -> bool:
    log_message("Starting eDEX-UI", logger)
    sub_status = ""
    process = None
    anim_chars = "/-\\|"

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
            subprocess.run(["killall", "-q", "node"], timeout=TIMEOUT_SECONDS)
            subprocess.run(["killall", "-q", "Xorg"], timeout=TIMEOUT_SECONDS)
        except Exception:
            pass
        clean_temp()

    try:
        clean_temp()
        sub_status = "Preparing X11"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                os.environ["DISPLAY"] = ":0"
                result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, check=False, timeout=TIMEOUT_SECONDS)
                if result.returncode != 0:
                    xorg_process = subprocess.Popen(
                        ["Xorg", ":0", "-quiet", "-nolisten", "tcp"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setsid
                    )
                    time.sleep(3)
                    if xorg_process.poll() is not None:
                        raise Exception("Xorg failed to start")
                log_message("X11 environment prepared", logger)
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"X11 startup failed: {e}")
                time.sleep(1)

        sub_status = "Launching eDEX-UI"
        if stdscr:
            update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_ATTEMPTS):
            try:
                env = os.environ.copy()
                env["PATH"] = f"/usr/local/node/bin:{env['PATH']}"
                env["LD_LIBRARY_PATH"] = f"/usr/local/lib:/usr/lib:{env.get('LD_LIBRARY_PATH', '')}"
                env["NODE_PATH"] = str(EDEX_DIR / "node_modules")
                process = subprocess.Popen(
                    ["npm", "start"],
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
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                if "node" not in result.stdout or "edex-ui" not in result.stdout:
                    raise Exception("eDEX-UI process verification failed")
                log_message("eDEX-UI started", logger)
                return True
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise Exception(f"eDEX-UI startup failed: {e}")
                time.sleep(5)
    except Exception as e:
        log_message(f"eDEX-UI startup stage failed: {e}", logger)
        if stdscr:
            display_error(stdscr, stages[current_stage][0], str(e), logger)
        return False
    finally:
        if not process or process.poll() is not None:
            cleanup()

# Quick check for eDEX-UI
def quick_check_edex_ui(logger: Optional[logging.Logger]) -> bool:
    try:
        if not EDEX_DIR.exists() or not (EDEX_DIR / "package.json").exists():
            log_message("eDEX-UI directory or package.json missing", logger)
            return False
        if not (EDEX_DIR / "node_modules").exists():
            log_message("eDEX-UI node_modules missing", logger)
            return False
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
        if f"v{NODE_VERSION}" not in result.stdout:
            log_message(f"Node.js version mismatch: {result.stdout.strip()}", logger)
            return False
        result = subprocess.run(["npm", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
        result = subprocess.run(["tce-status", "-i"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
        for pkg in REQUIRED_TCE_PACKAGES:
            if pkg not in result.stdout:
                log_message(f"Missing TCE package: {pkg}", logger)
                return False
        x11_dir = Path("/usr/local/lib/X11")
        if not x11_dir.exists():
            log_message("X11 directory missing", logger)
            return False
        log_message("Quick check passed", logger)
        return True
    except Exception as e:
        log_message(f"Quick check failed: {e}", logger)
        return False

# Main function
def main(stdscr=None):
    logger = setup_logger()
    log_message(f"{SYSTEM_NAME} started", logger)

    if stdscr:
        try:
            subprocess.run(["resize"], capture_output=True, timeout=TIMEOUT_SECONDS)
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
            log_message(f"Curses initialization failed: {e}", logger)
            display_error(stdscr, "Initialization", str(e), logger)

    # Quick check and start eDEX-UI if possible
    if quick_check_edex_ui(logger):
        if start_edex_ui(None, [("eDEX-UI START", "/")], 0, logger):
            return

    # Full setup if quick check fails
    stages = [
        ("DEPENDENCIES", "/"),
        ("DISK SETUP", "-"),
        ("eDEX-UI DOWNLOAD", "-"),
        ("eDEX-UI INSTALL", "-"),
        ("eDEX-UI START", "-")
    ]
    functions = [
        install_dependencies,
        verify_disk,
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
            log_message(f"Stage failed: {stages[i][0]}: {e}", logger)
            if stdscr:
                display_error(stdscr, stages[i][0], str(e), logger)

    if stdscr:
        try:
            stdscr.clear()
            rows, cols = stdscr.getmaxyx()
            title, title_x = center_text("BERKE OS - Setup Done", cols)
            stdscr.addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(1))
            prompt, prompt_x = center_text("Press any key to exit...", cols)
            stdscr.addstr(4, prompt_x, prompt, curses.color_pair(4))
            stdscr.refresh()
            stdscr.getch()
        except Exception as e:
            log_message(f"Completion screen failed: {e}", logger)

if __name__ == "__main__":
    anim_chars = "/-\\|"
    def signal_handler(sig, frame):
        logger = setup_logger()
        log_message(f"Signal received: {sig}", logger)
        try:
            subprocess.run(["killall", "-q", "node"], timeout=TIMEOUT_SECONDS)
            subprocess.run(["killall", "-q", "Xorg"], timeout=TIMEOUT_SECONDS)
        except Exception:
            pass
        clean_temp()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Command handling
    if len(sys.argv) > 1:
        if sys.argv[1] == "Berke:Kontrol":
            try:
                curses.wrapper(main)
            except Exception as e:
                logger = setup_logger()
                log_message(f"{SYSTEM_NAME} failed: {e}", logger)
                sys.exit(1)
        elif sys.argv[1] == "Berke:GuncelK":
            try:
                curses.wrapper(update_script)
            except Exception as e:
                logger = setup_logger()
                log_message(f"Script update failed: {e}", logger)
                sys.exit(1)
    else:
        # Run without curses if not manual
        main(None)

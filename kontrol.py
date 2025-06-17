import os
import sys
import time
import subprocess
import curses
import hashlib
import shutil
import signal
import json
import pwd
import logging
import logging.handlers

# Configuration
SYSTEM_NAME = "BERKE OS"
BASE_DIR = "/mnt/sda1"
TCE_DIRECTORY = os.path.join(BASE_DIR, "tce")
SYS_DIRECTORY = os.path.join(BASE_DIR, "system")
APP_DIRECTORY = os.path.join(BASE_DIR, "apps")
BACKUP_DIRECTORY = os.path.join(BASE_DIR, "backups")
LOG_DIRECTORY = "/var/log/berke"
LOG_FILEPATH = os.path.join(LOG_DIRECTORY, "install.log")
EDEX_DIRECTORY = os.path.join(APP_DIRECTORY, "edex-ui")
NODE_VER = "16.20.2"
EDEX_SOURCE = "https://github.com/GitSquared/edex-ui.git"
BOOT_SCRIPT_PATH = "/opt/bootlocal.sh"
REQUIRED_TCE = ["python3.9", "Xorg-7.7", "libX11", "libxss", "libX", "fontconfig", "X11", "git", "wget", "xml", "curl", "tar"]
REQUIRED_COMMS = ["python3.9", "wget", "curl", "git", "tar"]
MINIMUM_TERM = (20, 50)
RETRY_COUNT = 3
TIMEOUT_SECS = 5
USER_NAME = "tc"
GROUP_NAME = "staff"

# Set PATH
os.environ["PATH"] = f"{os.environ.get('PATH', '')}:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin"

# Setup logging with proper permissions
def setup_logging():
    try:
        os.makedirs(LOG_DIRECTORY, exist_ok=True)
        subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", LOG_DIRECTORY], check=True, timeout=TIMEOUT_SECS, capture_output=True)
        subprocess.run(["sudo", "chmod", "775", LOG_DIRECTORY], check=True, timeout=TIMEOUT_SECS, capture_output=True)
        
        logger = logging.getLogger('BerkeOS')
        logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(
            LOG_FILEPATH, 
            maxBytes=1048576, 
            backupCount=3
        )
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", LOG_FILEPATH], check=True, timeout=TIMEOUT_SECS, capture_output=True)
        subprocess.run(["sudo", "chmod", "664", LOG_FILEPATH], check=True, timeout=TIMEOUT_SECS, capture_output=True)
        
        return logger
    except Exception as e:
        print(f"Logging kurulum hatasi: {e}", file=sys.stderr)
        with open("/tmp/install_fallback.log", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: Logging kurulum hatasi: {e}\n")
        return None

# File hash calculation
def calc_file_hash(filepath):
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        log_message(f"Dosya hash hesaplama hatasi: {filepath}: {e}")
        return None

# Clean temporary files
def cleanup_temp():
    try:
        if os.path.exists("/tmp"):
            for item in os.listdir("/tmp"):
                path = os.path.join("/tmp", item)
                try:
                    if os.path.isfile(path):
                        subprocess.run(["sudo", "rm", "-f", path], check=True, timeout=TIMEOUT_SECS, capture_output=True)
                    elif os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
    except Exception as e:
        log_message(f"Geçici dosya temizleme hatasi: {e}")

# Log message with fallback
def log_message(message, logger=None):
    try:
        if logger:
            logger.info(message)
        else:
            with open("/tmp/install_fallback.log", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
    except Exception as e:
        print(f"Log yazma hatasi: {e}", file=sys.stderr)

# Draw box
def draw_border(stdscr, start_y, start_x, height, width):
    try:
        stdscr.addstr(start_y, start_x, "┌" + "─" * (width - 2) + "┐")
        for i in range(1, height - 1):
            stdscr.addstr(start_y + i, start_x, "│" + " " * (width - 2) + "│")
        stdscr.addstr(start_y + height - 1, start_x, "└" + "─" * (width - 2) + "┘")
    except Exception as e:
        log_message(f"Border cizme hatasi: {e}")

# Error screen
def show_error(stdscr, stage, error_msg, logger):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        box_width = min(cols - 4, max(50, int(cols * 0.8)))
        box_height = min(rows - 4, max(15, int(rows * 0.6)))
        box_y = (rows - box_height) // 2
        box_x = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        draw_border(stdscr, box_y, box_x, box_height, box_width)

        title = "B E R K E  O S"
        title_x = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_y + 1, title_x, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        error_title = "HATA ALINDI!"
        error_title_x = (cols - len(error_title)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_y + 3, error_title_x, error_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(2))

        stage_info = f"Asama: {stage}"
        stage_x = (cols - len(stage_info)) // 2
        stdscr.addstr(box_y + 5, stage_x, stage_info)

        error_info = f"Hata: {error_msg[:box_width-4]}"
        error_x = (cols - len(error_info)) // 2
        stdscr.addstr(box_y + 6, error_x, error_info)

        solution = f"Loglari kontrol edin: {LOG_FILEPATH} veya /tmp/install_fallback.log"
        solution_x = (cols - len(solution)) // 2
        stdscr.addstr(box_y + 8, solution_x, solution)

        exit_prompt = "Cikmak icin bir tusa basin"
        exit_x = (cols - len(exit_prompt)) // 2
        stdscr.addstr(box_y + box_height - 3, exit_x, exit_prompt)
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        log_message(f"Hata ekrani gosterme hatasi: {e}", logger)
        print(f"HATA ALINDI!\nAsama: {stage}\nHata: {error_msg}", file=sys.stderr)
    sys.exit(1)

# Main screen
def update_display(stdscr, stages, current_stage, sub_status, logger):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        box_width = min(cols - 4, max(50, int(cols * 0.8)))
        box_height = min(rows - 4, max(20, int(rows * 0.6)))
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
        title_x = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_y + 1, title_x, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        sys_title = "Sistem baslatiliyor"
        sys_x = (cols - len(sys_title)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_y + 3, sys_x, sys_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(2))

        for i, (stage_name, status) in enumerate(stages):
            stage_text = f"{i+1}. {stage_name} [{status}]"
            stage_x = (cols - len(stage_text)) // 2
            row = box_y + 5 + i
            if row >= box_y + box_height - 3:
                break
            if i == current_stage and status == "/":
                stdscr.attron(curses.color_pair(4))
                anim_chars = ["/", "-", "\\", "|"]
                for j in range(10):
                    stage_text = f"{i+1}. {stage_name} [{anim_chars[j % 4]}]"
                    stage_x = (cols - len(stage_text)) // 2
                    stdscr.addstr(row, stage_x, stage_text, curses.A_BOLD)
                    sub_status_text = f"Durum: {sub_status[:box_width-10]}" if sub_status else ""
                    sub_status_x = (cols - len(sub_status_text)) // 2
                    stdscr.addstr(row + 1, sub_status_x, sub_status_text, curses.A_BOLD)
                    stdscr.refresh()
                    time.sleep(0.2)
                stdscr.attroff(curses.color_pair(4))
            elif status == "TAMAM":
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(row, stage_x, stage_text)
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(row, stage_x, stage_text)
                stdscr.attroff(curses.color_pair(5))

        if sub_status and stages[current_stage][1] == "TAMAM":
            sub_status_text = f"Durum: {sub_status[:box_width-10]}"
            sub_status_x = (cols - len(sub_status_text)) // 2
            stdscr.attron(curses.color_pair(4))
            stdscr.addstr(box_y + 5 + current_stage + 1, sub_status_x, sub_status_text, curses.A_BOLD)
            stdscr.attroff(curses.color_pair(4))

        stdscr.refresh()
    except Exception as e:
        log_message(f"Ekran guncelleme hatasi: {e}", logger)
        print(f"{title}\nSistem baslatiliyor\n" + "\n".join(f"{i+1}. {s[0]} [{s[1]}]" for i, s in enumerate(stages)), file=sys.stderr)

# Install dependencies
def install_deps(stdscr, stages, current_stage, logger):
    log_message("Bağımlılıklar kontrol ediliyor", logger)
    sub_status = ""

    try:
        cleanup_temp()
        
        # Check and install commands
        for cmd in REQUIRED_COMMS:
            try:
                result = subprocess.run(["which", cmd], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
                if cmd == "python3.9":
                    result = subprocess.run([cmd, "--version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
                    if "3.9" not in result.stdout:
                        raise Exception("Python 3.9 sürümü uygun değil")
                log_message(f"{cmd} bulundu: {result.stdout.strip()}", logger)
                continue
            except Exception:
                sub_status = f"{cmd} yükleniyor"
                update_display(stdscr, stages, current_stage, sub_status, logger)
                for attempt in range(RETRY_COUNT):
                    try:
                        subprocess.run(["sudo", "tce-load", "-w", "-i", cmd], check=True, timeout=300, capture_output=True)
                        result = subprocess.run(["which", cmd], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
                        if cmd == "python3.9":
                            result = subprocess.run([cmd, "--version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
                            if "3.9" not in result.stdout:
                                raise Exception("Python 3.9 sürümü yüklenemedi")
                        log_message(f"{cmd} yüklendi: {result.stdout.strip()}", logger)
                        break
                    except Exception as e:
                        if attempt == RETRY_COUNT - 1:
                            log_message(f"{cmd} yüklenemedi: {e}", logger)
                            raise Exception(f"{cmd} yüklenemedi: {e}")
                        time.sleep(2)

        # Check and install TCE packages
        for pkg in REQUIRED_TCE:
            if pkg in REQUIRED_COMMS:
                continue
            try:
                result = subprocess.run(["tce-status", "-i"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
                if pkg in result.stdout:
                    log_message(f"{pkg} bulundu", logger)
                    continue
                else:
                    raise Exception(f"{pkg} yüklü değil")
            except Exception:
                sub_status = f"{pkg} yükleniyor"
                update_display(stdscr, stages, current_stage, sub_status, logger)
                for attempt in range(RETRY_COUNT):
                    try:
                        subprocess.run(["sudo", "tce-load", "-w", "-i", pkg], check=True, timeout=300, capture_output=True)
                        log_message(f"{pkg} yüklendi", logger)
                        if pkg == "Xorg-7.7":
                            if not os.path.exists("/usr/local/lib/X11"):
                                raise Exception("Xorg-7.7 yüklendi ama X11 dizini bulunamadı")
                            try:
                                result = subprocess.run(["Xorg", "-version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
                                if "7.7" not in result.stdout:
                                    raise Exception("Xorg-7.7 sürümü doğrulanamadı")
                            except Exception as e:
                                log_message(f"Xorg sürüm kontrolü başarısız, vesa sürücüsü deneniyor: {e}", logger)
                                with open("/tmp/20-xorg-vesa.conf", "w") as f:
                                    f.write(
                                        'Section "Device"\n'
                                        '    Identifier "Card0"\n'
                                        '    Driver "vesa"\n'
                                        'EndSection\n'
                                    )
                                subprocess.run(["sudo", "mkdir", "-p", "/etc/X11/xorg.conf.d"], check=True, timeout=TIMEOUT_SECS)
                                subprocess.run(["sudo", "mv", "/tmp/20-xorg-vesa.conf", "/etc/X11/xorg.conf.d/20-xorg-vesa.conf"], check=True, timeout=TIMEOUT_SECS)
                                subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", "/etc/X11/xorg.conf.d/20-xorg-vesa.conf"], check=True, timeout=TIMEOUT_SECS)
                                subprocess.run(["sudo", "chmod", "664", "/etc/X11/xorg.conf.d/20-xorg-vesa.conf"], check=True, timeout=TIMEOUT_SECS)
                        break
                    except Exception as e:
                        if attempt == RETRY_COUNT - 1:
                            log_message(f"{pkg} yüklenemedi: {e}", logger)
                            raise Exception(f"{pkg} yüklenemedi: {e}")
                        time.sleep(2)
                try:
                    onboot_path = os.path.join(TCE_DIRECTORY, "onboot.lst")
                    subprocess.run(["sudo", "touch", onboot_path], check=True, timeout=TIMEOUT_SECS)
                    subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", onboot_path], check=True, timeout=TIMEOUT_SECS)
                    subprocess.run(["sudo", "chmod", "664", onboot_path], check=True, timeout=TIMEOUT_SECS)
                    with open(onboot_path, "r") as f:
                        content = f.read()
                    if pkg not in content:
                        with open("/tmp/onboot.lst", "w") as f:
                            f.write(content.rstrip() + f"\n{pkg}\n")
                        subprocess.run(["sudo", "mv", "/tmp/onboot.lst", onboot_path], check=True, timeout=TIMEOUT_SECS)
                        subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", onboot_path], check=True, timeout=TIMEOUT_SECS)
                        subprocess.run(["sudo", "chmod", "664", onboot_path], check=True, timeout=TIMEOUT_SECS)
                        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                except Exception as e:
                    log_message(f"onboot.lst güncelleme hatası: {e}", logger)
                    raise Exception(f"onboot.lst güncelleme hatası: {e}")

        # Check and install Node.js
        try:
            result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
            npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
            if f"v{NODE_VER}" not in result.stdout:
                raise Exception(f"Node.js sürümü {NODE_VER} değil")
            log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} bulundu", logger)
        except Exception:
            sub_status = "Node.js yükleniyor"
            update_display(stdscr, stages, current_stage, sub_status, logger)
            for attempt in range(RETRY_COUNT):
                try:
                    node_url = f"https://nodejs.org/dist/v{NODE_VER}/node-v{NODE_VER}-linux-x64.tar.xz"
                    node_tar = "/tmp/node.tar.xz"
                    subprocess.run(["sudo", "wget", "-O", node_tar, node_url], check=True, timeout=300, capture_output=True)
                    if not os.path.exists(node_tar):
                        raise Exception("Node.js arşivi indirilemedi")
                    subprocess.run(["sudo", "tar", "-xJf", node_tar, "-C", "/usr/local"], check=True, timeout=300)
                    subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VER}-linux-x64/bin/node", "/usr/local/bin/node"], check=True, timeout=TIMEOUT_SECS)
                    subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VER}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True, timeout=TIMEOUT_SECS)
                    result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
                    if f"v{NODE_VER}" not in result.stdout:
                        raise Exception("Node.js sürümü doğrulanamadı")
                    log_message("Node.js ve npm yüklendi", logger)
                    break
                except Exception as e:
                    if attempt == RETRY_COUNT - 1:
                        log_message(f"Node.js yüklenemedi: {e}", logger)
                        raise Exception(f"Node.js yüklenemedi: {e}")
                    time.sleep(2)
                finally:
                    if os.path.exists(node_tar):
                        subprocess.run(["sudo", "rm", "-f", node_tar], check=True, timeout=TIMEOUT_SECS, capture_output=True)

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_status = "Bağımlılıklar tamamlandı"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        time.sleep(5)
    except Exception as e:
        log_message(f"Bağımlılık aşaması başarısız: {e}", logger)
        show_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        cleanup_temp()

# Verify disk
def check_disk(stdscr, stages, current_stage, logger):
    log_message("Disk doğrulanıyor", logger)
    sub_status = ""

    try:
        cleanup_temp()
        sub_status = "Disk dizini oluşturuluyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_COUNT):
            try:
                subprocess.run(["sudo", "mkdir", "-p", BASE_DIR], check=True, timeout=TIMEOUT_SECS, capture_output=True)
                subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", BASE_DIR], check=True, timeout=TIMEOUT_SECS)
                subprocess.run(["sudo", "chmod", "775", BASE_DIR], check=True, timeout=TIMEOUT_SECS)
                if not os.path.exists(BASE_DIR):
                    raise Exception("Disk dizini oluşturulamadı")
                break
            except Exception as e:
                if attempt == RETRY_COUNT - 1:
                    log_message(f"Disk dizini oluşturulamadı: {e}", logger)
                    raise Exception(f"Disk dizini oluşturulamadı: {e}")
                time.sleep(2)

        sub_status = "Disk bağlanıyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_COUNT):
            try:
                result = subprocess.run(["mountpoint", "-q", BASE_DIR], capture_output=True, check=False, timeout=TIMEOUT_SECS)
                if result.returncode != 0:
                    try:
                        subprocess.run(["sudo", "mount", "/dev/sda1", BASE_DIR], check=True, timeout=10, capture_output=True)
                    except Exception:
                        log_message("Disk bağlama başarısız, biçimlendirme deneniyor", logger)
                        sub_status = "Disk biçimlendiriliyor"
                        update_display(stdscr, stages, current_stage, sub_status, logger)
                        try:
                            subprocess.run(["sudo", "mkfs.ext4", "-F", "/dev/sda1"], check=True, timeout=600, capture_output=True)
                            subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", "/dev/sda1"], check=True, timeout=TIMEOUT_SECS)
                            subprocess.run(["sudo", "mount", "/dev/sda1", BASE_DIR], check=True, timeout=10)
                        except Exception as e:
                            log_message(f"Disk biçimlendirme başarısız: {e}", logger)
                            raise Exception(f"Disk biçimlendirme başarısız: {e}")
                subprocess.run(["sudo", "mount", "-o", "remount,rw", BASE_DIR], check=True, timeout=TIMEOUT_SECS)
                result = subprocess.run(["df", "-h", BASE_DIR], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
                if BASE_DIR not in result.stdout:
                    raise Exception("Disk bağlama doğrulanamadı")
                break
            except Exception as e:
                if attempt == RETRY_COUNT - 1:
                    log_message(f"Disk bağlama başarısız: {e}", logger)
                    raise Exception(f"Disk bağlama başarısız: {e}")
                time.sleep(2)

        sub_status = "Dizinler oluşturuluyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        dirs = [TCE_DIRECTORY, SYS_DIRECTORY, APP_DIRECTORY, BACKUP_DIRECTORY]
        for d in dirs:
            for attempt in range(RETRY_COUNT):
                try:
                    subprocess.run(["sudo", "mkdir", "-p", d], check=True, timeout=TIMEOUT_SECS, capture_output=True)
                    subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", d], check=True, timeout=TIMEOUT_SECS)
                    subprocess.run(["sudo", "chmod", "775", d], check=True, timeout=TIMEOUT_SECS)
                    if not os.path.exists(d):
                        raise Exception(f"Dizin oluşturulamadı: {d}")
                    break
                except Exception as e:
                    if attempt == RETRY_COUNT - 1:
                        log_message(f"Dizin oluşturma başarısız: {d}: {e}", logger)
                        raise Exception(f"Dizin oluşturma başarısız: {d}: {e}")
                    time.sleep(2)

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_status = "Disk tamamlandı"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        time.sleep(5)
    except Exception as e:
        log_message(f"Disk aşaması başarısız: {e}", logger)
        show_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        cleanup_temp()

# Verify backup
def create_backup(stdscr, stages, current_stage, logger):
    log_message("Sistem yedekleniyor", logger)
    sub_status = ""

    try:
        cleanup_temp()
        sub_status = "Yedek dizini oluşturuluyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_COUNT):
            try:
                subprocess.run(["sudo", "mkdir", "-p", BACKUP_DIRECTORY], check=True, timeout=TIMEOUT_SECS, capture_output=True)
                subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", BACKUP_DIRECTORY], check=True, timeout=TIMEOUT_SECS)
                subprocess.run(["sudo", "chmod", "775", BACKUP_DIRECTORY], check=True, timeout=TIMEOUT_SECS)
                if not os.path.exists(BACKUP_DIRECTORY):
                    raise Exception("Yedek dizini oluşturulamadı")
                break
            except Exception as e:
                if attempt == RETRY_COUNT - 1:
                    log_message(f"Yedek dizini oluşturulamadı: {e}", logger)
                    raise Exception(f"Yedek dizini oluşturulamadı: {e}")
                time.sleep(2)

        sub_status = "Dosyalar yedekleniyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(BACKUP_DIRECTORY, f"backup_{timestamp}.tar.gz")
            dirs_to_backup = [SYS_DIRECTORY, APP_DIRECTORY, TCE_DIRECTORY]
            for d in dirs_to_backup:
                if not os.path.exists(d):
                    subprocess.run(["sudo", "mkdir", "-p", d], check=True, timeout=TIMEOUT_SECS, capture_output=True)
                    subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", d], check=True, timeout=TIMEOUT_SECS)
                    subprocess.run(["sudo", "chmod", "775", d], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "tar", "-czf", backup_file] + dirs_to_backup, check=True, timeout=600, capture_output=True)
            subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", backup_file], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "chmod", "664", backup_file], check=True, timeout=TIMEOUT_SECS)
            if not os.path.exists(backup_file):
                raise Exception("Yedek dosyası oluşturulamadı")
        except Exception as e:
            log_message(f"Yedekleme başarısız: {e}", logger)
            raise Exception(f"Yedekleme başarısız: {e}")

        sub_status = "Yedek doğrulanıyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        try:
            backup_hash = calc_file_hash(backup_file)
            if not backup_hash:
                raise Exception("Yedek doğrulama başarısız")
            log_message(f"Yedek oluşturuldu: {backup_file}, SHA256: {backup_hash}", logger)
            backup_log = os.path.join(BACKUP_DIRECTORY, "backup_log.txt")
            with open("/tmp/backup_log.txt", "a") as f:
                f.write(f"{timestamp}: {backup_file}, SHA256: {backup_hash}\n")
            subprocess.run(["sudo", "mv", "/tmp/backup_log.txt", backup_log], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", backup_log], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "chmod", "664", backup_log], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
            if not os.path.exists(backup_log):
                raise Exception("Yedek log dosyası oluşturulamadı")
        except Exception as e:
            log_message(f"Yedek doğrulama başarısız: {e}", logger)
            raise Exception(f"Yedek doğrulama başarısız: {e}")

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_status = "Yedekleme tamamlandı"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        time.sleep(5)
    except Exception as e:
        log_message(f"Yedekleme aşaması başarısız: {e}", logger)
        show_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        cleanup_temp()

# Download EDEX-UI
def fetch_edex_ui(stdscr, stages, current_stage, logger):
    log_message("EDEX-UI indiriliyor", logger)
    sub_status = ""

    try:
        cleanup_temp()
        sub_status = "EDEX-UI varlığı kontrol ediliyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        if os.path.exists(EDEX_DIRECTORY) and os.path.isfile(os.path.join(EDEX_DIRECTORY, "package.json")):
            log_message("EDEX-UI zaten mevcut", logger)
        else:
            sub_status = "EDEX-UI klonlanıyor"
            update_display(stdscr, stages, current_stage, sub_status, logger)
            for attempt in range(RETRY_COUNT):
                try:
                    if os.path.exists(EDEX_DIRECTORY):
                        shutil.rmtree(EDEX_DIRECTORY, ignore_errors=True)
                    subprocess.run(["sudo", "git", "clone", EDEX_SOURCE, EDEX_DIRECTORY], check=True, timeout=600, capture_output=True)
                    subprocess.run(["sudo", "chown", "-R", f"{USER_NAME}:{GROUP_NAME}", EDEX_DIRECTORY], check=True, timeout=10)
                    subprocess.run(["sudo", "chmod", "-R", "775", EDEX_DIRECTORY], check=True, timeout=10)
                    if not os.path.exists(os.path.join(EDEX_DIRECTORY, "package.json")):
                        raise Exception("EDEX-UI package.json bulunamadı")
                    log_message("EDEX-UI klonlandı", logger)
                    break
                except Exception as e:
                    if attempt == RETRY_COUNT - 1:
                        log_message(f"EDEX-UI klonlama başarısız: {e}", logger)
                        raise Exception(f"EDEX-UI klonlama başarısız: {e}")
                    time.sleep(2)

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_status = "EDEX-UI indirildi"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        time.sleep(5)
    except Exception as e:
        log_message(f"EDEX-UI indirme aşaması başarısız: {e}", logger)
        show_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        cleanup_temp()

# Install EDEX-UI
def setup_edex_ui(stdscr, stages, current_stage, logger):
    log_message("EDEX-UI kuruluyor", logger)
    sub_status = ""

    try:
        cleanup_temp()
        sub_status = "npm bağımlılıkları yükleniyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_COUNT):
            try:
                subprocess.run(["sudo", "npm", "install", "--unsafe-perm"], cwd=EDEX_DIRECTORY, check=True, timeout=600, capture_output=True)
                if not os.path.exists(os.path.join(EDEX_DIRECTORY, "node_modules")):
                    raise Exception("npm bağımlılıkları doğrulanamadı")
                log_message("npm bağımlılıkları yüklendi", logger)
                break
            except Exception as e:
                if attempt == RETRY_COUNT - 1:
                    log_message(f"npm bağımlılıkları yüklenemedi: {e}", logger)
                    raise Exception(f"npm bağımlılıkları yüklenemedi: {e}")
                time.sleep(2)

        sub_status = "Ayarlar özelleştiriliyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        try:
            settings_path = os.path.join(EDEX_DIRECTORY, "settings.json")
            settings = {
                "shell": "/bin/bash",
                "shellArgs": ["-c", f"export PATH=$PATH:/usr/local/bin; exec bash"],
                "theme": "tron",
                "window": {"title": f"{SYSTEM_NAME} EDEX-UI"},
                "performance": {"lowPowerMode": False, "gpuAcceleration": True}
            }
            with open("/tmp/settings.json", "w") as f:
                json.dump(settings, f, indent=2)
            subprocess.run(["sudo", "mv", "/tmp/settings.json", settings_path], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", settings_path], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "chmod", "664", settings_path], check=True, timeout=TIMEOUT_SECS)
            if not os.path.exists(settings_path):
                raise Exception("Ayarlar dosyası taşınamadı")
            with open(settings_path, "r") as f:
                if f"{SYSTEM_NAME}" not in f.read():
                    raise Exception("Ayarlar içeriği doğrulanamadı")
            log_message("EDEX-UI ayarlar özelleştirildi", logger)
        except Exception as e:
            log_message(f"EDEX-UI ayarlar özelleştirilemedi: {e}", logger)
            raise Exception(f"EDEX-UI ayarlar özelleştirilemedi: {e}")

        sub_status = "Xorg optimize ediliyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        try:
            xorg_conf_dir = "/etc/X11/xorg.conf.d"
            xorg_conf = os.path.join(xorg_conf_dir, "10-optimizations.conf")
            subprocess.run(["sudo", "mkdir", "-p", xorg_conf_dir], check=True, timeout=TIMEOUT_SECS, capture_output=True)
            subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", xorg_conf_dir], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "chmod", "775", xorg_conf_dir], check=True, timeout=TIMEOUT_SECS)
            with open("/tmp/xorg.conf", "w") as f:
                f.write(
                    'Section "Device"\n'
                    '    Identifier "Card0"\n'
                    '    Driver "vesa"\n'
                    '    Option "AccelMethod" "exa"\n'
                    'EndSection\n'
                )
            subprocess.run(["sudo", "mv", "/tmp/xorg.conf", xorg_conf], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", xorg_conf], check=True, timeout=TIMEOUT_SECS)
            subprocess.run(["sudo", "chmod", "664", xorg_conf], check=True, timeout=TIMEOUT_SECS)
            if not os.path.exists(xorg_conf):
                raise Exception("Xorg yapılandırma dosyası taşınamadı")
            log_message("Xorg optimize edildi", logger)
        except Exception as e:
            log_message(f"Xorg optimizasyonu başarısız: {e}", logger)
            raise Exception(f"Xorg optimizasyonu başarısız: {e}")

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_status = "EDEX-UI kurulumu tamamlandı"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        time.sleep(5)
    except Exception as e:
        log_message(f"EDEX-UI kurulum aşaması başarısız: {e}", logger)
        show_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        cleanup_temp()

# Start EDEX-UI
def launch_edex_ui(stdscr, stages, current_stage, logger):
    log_message("EDEX-UI başlatılıyor", logger)
    sub_status = ""
    process = None

    def cleanup():
        if process and process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=TIMEOUT_SECS)
            except Exception:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        subprocess.run(["sudo", "killall", "-q", "node"], capture_output=True, timeout=TIMEOUT_SECS)
        subprocess.run(["sudo", "killall", "-q", "Xorg"], capture_output=True, timeout=TIMEOUT_SECS)
        cleanup_temp()

    try:
        cleanup_temp()
        sub_status = "X11 ortamı hazırlanıyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_COUNT):
            try:
                os.environ["DISPLAY"] = ":0"
                result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, check=False, timeout=TIMEOUT_SECS)
                if result.returncode != 0:
                    subprocess.run(["sudo", "Xorg", "-quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
                    time.sleep(3)
                    result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, check=True, timeout=TIMEOUT_SECS)
                log_message("X11 ortamı hazırlandı", logger)
                break
            except Exception as e:
                if attempt == RETRY_COUNT - 1:
                    log_message(f"X11 başlatma başarısız: {e}", logger)
                    raise Exception(f"X11 başlatma başarısız: {e}")
                time.sleep(2)

        sub_status = "EDEX-UI çalıştırılıyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        try:
            process = subprocess.Popen(
                ["sudo", "npm", "start", "--unsafe-perm"],
                cwd=EDEX_DIRECTORY,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            time.sleep(15)
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=TIMEOUT_SECS)
                log_message(f"EDEX-UI başlatma başarısız: {stderr}", logger)
                raise Exception(f"EDEX-UI başlatılamadı: {stderr}")
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECS)
            if "node" not in result.stdout or "edex-ui" not in result.stdout:
                raise Exception("EDEX-UI süreci doğrulanamadı")
            log_message("EDEX-UI başlatıldı", logger)
        except Exception as e:
            log_message(f"EDEX-UI başlatma başarısız: {e}", logger)
            raise Exception(f"EDEX-UI başlatma başarısız: {e}")

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_status = "EDEX-UI başlatıldı"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        time.sleep(5)
    except Exception as e:
        log_message(f"EDEX-UI başlatma aşaması başarısız: {e}", logger)
        show_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        cleanup()

# Configure autostart
def setup_autostart(stdscr, stages, current_stage, logger):
    log_message("Otomatik başlatma ayarlanıyor", logger)
    sub_status = ""

    try:
        cleanup_temp()
        sub_status = "Boot scripti güncelleniyor"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        for attempt in range(RETRY_COUNT):
            try:
                script_path = "/mnt/sda1/kontrol.py"
                if not os.path.exists(script_path):
                    raise Exception("kontrol.py bulunamadı")
                subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", script_path], check=True, timeout=TIMEOUT_SECS)
                subprocess.run(["sudo", "chmod", "775", script_path], check=True, timeout=TIMEOUT_SECS)
                if os.path.exists(BOOT_SCRIPT_PATH):
                    with open(BOOT_SCRIPT_PATH, "r") as f:
                        content = f.read()
                    if script_path in content:
                        log_message("Otomatik başlatma zaten ayarlanmış", logger)
                    else:
                        subprocess.run(["sudo", "cp", BOOT_SCRIPT_PATH, f"{BOOT_SCRIPT_PATH}.bak"], capture_output=True, timeout=TIMEOUT_SECS)
                        with open("/tmp/bootlocal.sh", "w") as f:
                            f.write(content.rstrip() + f"\npython3.9 {script_path} --skip-ui &\n")
                        subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", BOOT_SCRIPT_PATH], check=True, timeout=TIMEOUT_SECS)
                        subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", BOOT_SCRIPT_PATH], check=True, timeout=TIMEOUT_SECS)
                        subprocess.run(["sudo", "chmod", "775", BOOT_SCRIPT_PATH], check=True, timeout=TIMEOUT_SECS)
                        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                        log_message("Otomatik başlatma eklendi", logger)
                else:
                    with open("/tmp/bootlocal.sh", "w") as f:
                        f.write(f"#!/bin/sh\npython3.9 {script_path} --skip-ui &\n")
                    subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", BOOT_SCRIPT_PATH], check=True, timeout=TIMEOUT_SECS)
                    subprocess.run(["sudo", "chown", f"{USER_NAME}:{GROUP_NAME}", BOOT_SCRIPT_PATH], check=True, timeout=TIMEOUT_SECS)
                    subprocess.run(["sudo", "chmod", "775", BOOT_SCRIPT_PATH], check=True, timeout=TIMEOUT_SECS)
                    subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                    log_message("Yeni boot scripti oluşturuldu", logger)
                with open(BOOT_SCRIPT_PATH, "r") as f:
                    if script_path not in f.read():
                        raise Exception("Boot scripti içeriği doğrulanamadı")
                break
            except Exception as e:
                if attempt == RETRY_COUNT - 1:
                    log_message(f"Otomatik başlatma ayarlama başarısız: {e}", logger)
                    raise Exception(f"Otomatik başlatma ayarlama başarısız: {e}")
                time.sleep(2)

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_status = "Otomatik başlatma tamamlandı"
        update_display(stdscr, stages, current_stage, sub_status, logger)
        time.sleep(5)
    except Exception as e:
        log_message(f"Otomatik başlatma aşaması başarısız: {e}", logger)
        show_error(stdscr, stages[current_stage][0], str(e), logger)
    finally:
        cleanup_temp()

# Main function
def main(stdscr):
    logger = setup_logging()
    log_message(f"{SYSTEM_NAME} başlatıldı", logger)

    try:
        subprocess.run(["resize"], capture_output=True, timeout=TIMEOUT_SECS)
        curses.curs_set(0)
        stdscr.timeout(-1)
        rows, cols = stdscr.getmaxyx()
        if rows < MINIMUM_TERM[0] or cols < MINIMUM_TERM[1]:
            raise Exception(f"Terminal boyutu yetersiz (min {MINIMUM_TERM[1]}x{MINIMUM_TERM[0]})")
        box_width = min(cols - 4, max(50, int(cols * 0.8)))
        box_height = min(rows - 4, max(15, int(rows * 0.6)))
        box_y = (rows - box_height) // 2
        box_x = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        draw_border(stdscr, box_y, box_x, box_height, box_width)

        title = "B E R K E  O S"
        title_x = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_y + 1, title_x, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        status = "Beklemede"
        status_x = (cols - len(status)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_y + box_height // 2, status_x, status)
        stdscr.attroff(curses.color_pair(2))
        stdscr.refresh()
        time.sleep(2)
    except Exception as e:
        log_message(f"Curses başlatılamadı: {e}", logger)
        print(f"Curses başlatılamadı: {e}", file=sys.stderr)
        sys.exit(1)

    skip_ui = "--skip-ui" in sys.argv
    if skip_ui:
        if os.path.exists(EDEX_DIRECTORY) and os.path.isfile(os.path.join(EDEX_DIRECTORY, "package.json")):
            launch_edex_ui(None, [("EDEX-UI BAŞLATMA", "/")], 0, logger)
        else:
            log_message("EDEX-UI bulunamadı, kurulum gerekiyor", logger)
            print("EDEX-UI bulunamadı, tam kurulum yapın", file=sys.stderr)
        sys.exit(0)

    stages = [
        ("BAĞIMLILIK YÜKLEME", "/"),
        ("DİSK YAPILANDIRMA", "-"),
        ("YEDEKLEME", "-"),
        ("EDEX-UI İNDİRME", "-"),
        ("EDEX-UI KURULUM", "-"),
        ("EDEX-UI BAŞLATMA", "-"),
        ("OTOMATİK BAŞLAMA", "-")
    ]
    functions = [
        install_deps,
        check_disk,
        create_backup,
        fetch_edex_ui,
        setup_edex_ui,
        launch_edex_ui,
        setup_autostart
    ]

    for i, func in enumerate(functions):
        try:
            func(stdscr, stages, i, logger)
        except Exception as e:
            log_message(f"Aşama başarısız: {stages[i][0]}: {e}", logger)
            show_error(stdscr, stages[i][0], str(e), logger)

if __name__ == "__main__":
    def signal_handler(sig, frame):
        logger = setup_logging()
        log_message(f"Sinyal alındı: {sig}", logger)
        subprocess.run(["sudo", "killall", "-q", "node"], capture_output=True, timeout=TIMEOUT_SECS)
        subprocess.run(["sudo", "killall", "-q", "Xorg"], capture_output=True, timeout=TIMEOUT_SECS)
        cleanup_temp()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        curses.wrapper(main)
    except Exception as e:
        logger = setup_logging()
        log_message(f"{SYSTEM_NAME} çöktü: {e}", logger)
        print(f"Hata: {e}\n{SYSTEM_NAME}", file=sys.stderr)
        sys.exit(1)

import os
import sys
import time
import subprocess
import curses
import hashlib
import shutil
import signal
import json

# Configuration
SYSTEM_NAME = "BERKE OS"
ROOT_DIR = "/mnt/sda1"
TCE_DIR = os.path.join(ROOT_DIR, "tce")
SYSTEM_DIR = os.path.join(ROOT_DIR, "system")
APPS_DIR = os.path.join(ROOT_DIR, "apps")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups")
LOG_DIR = os.path.join(SYSTEM_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "install_log.txt")
EDEX_DIR = os.path.join(APPS_DIR, "edex-ui")
NODE_VERSION = "16.20.2"
EDEX_URL = "https://github.com/GitSquared/edex-ui.git"
BOOT_SCRIPT = "/opt/bootlocal.sh"
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "libX11", "libxss", "fontconfig", "git", "wget", "curl", "tar"]
REQUIRED_COMMANDS = ["python3.9", "wget", "curl", "git", "tar"]
MIN_TERM_SIZE = (20, 50)
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 5

# Set PATH
os.environ["PATH"] = f"{os.environ.get('PATH', '')}:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin"

# Logging with fallback
def log_message(message):
    try:
        if os.path.exists(ROOT_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)
            subprocess.run(["sudo", "chown", "tc:staff", LOG_DIR], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
            subprocess.run(["sudo", "chmod", "775", LOG_DIR], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
            with open(LOG_FILE, "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
            subprocess.run(["sudo", "chown", "tc:staff", LOG_FILE], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
            subprocess.run(["sudo", "chmod", "664", LOG_FILE], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
        else:
            with open("/tmp/install_log.txt", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
    except Exception as e:
        print(f"Log yazma hatasi: {e}", file=sys.stderr)

# File hash calculation
def calculate_file_hash(file_path):
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        log_message(f"Dosya hash hesaplanamadi: {file_path}: {e}")
        return None

# Clean temporary files
def clean_temp():
    try:
        if os.path.exists("/tmp"):
            for item in os.listdir("/tmp"):
                path = os.path.join("/tmp", item)
                try:
                    if os.path.isfile(path):
                        subprocess.run(["sudo", "rm", "-f", path], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
                    elif os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
    except Exception as e:
        log_message(f"Gecici dosyalar temizlenemedi: {e}")

# Draw box
def draw_box(stdscr, start_row, start_col, height, width):
    try:
        stdscr.addstr(start_row, start_col, "┌" + "─" * (width - 2) + "┐")
        for i in range(1, height - 1):
            stdscr.addstr(start_row + i, start_col, "│" + " " * (width - 2) + "│")
        stdscr.addstr(start_row + height - 1, start_col, "└" + "─" * (width - 2) + "┘")
    except Exception as e:
        log_message(f"Kutu cizme hatasi: {e}")

# Error screen
def display_error(stdscr, stage, error_msg):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        box_width = min(cols - 4, max(50, int(cols * 0.8)))
        box_height = min(rows - 4, max(15, int(rows * 0.6)))
        box_start_row = (rows - box_height) // 2
        box_start_col = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)

        title = "B E R K E  O S"
        title_col = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        error_title = "HATA ALINDI!"
        error_title_col = (cols - len(error_title)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_start_row + 3, error_title_col, error_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(2))

        stage_info = f"Asama: {stage}"
        stage_col = (cols - len(stage_info)) // 2
        stdscr.addstr(box_start_row + 5, stage_col, stage_info)

        error_info = f"Hata: {error_msg[:box_width-4]}"
        error_col = (cols - len(error_info)) // 2
        stdscr.addstr(box_start_row + 6, error_col, error_info)

        solution = f"Loglari kontrol edin: {LOG_FILE} veya /tmp/install_log.txt"
        solution_col = (cols - len(solution)) // 2
        stdscr.addstr(box_start_row + 8, solution_col, solution)

        exit_prompt = "Cikmak icin bir tusa basin"
        exit_col = (cols - len(exit_prompt)) // 2
        stdscr.addstr(box_start_row + box_height - 3, exit_col, exit_prompt)
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        log_message(f"Hata ekrani gosterilemedi: {e}")
        print(f"HATA ALINDI!\nAsama: {stage}\nHata: {error_msg}", file=sys.stderr)
    sys.exit(1)

# Main screen
def display_main(stdscr, stages, current_stage, sub_status):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        box_width = min(cols - 4, max(50, int(cols * 0.8)))
        box_height = min(rows - 4, max(20, int(rows * 0.6)))
        box_start_row = (rows - box_height) // 2
        box_start_col = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)

        title = "B E R K E  O S"
        title_col = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        sys_title = "Sistem baslatiliyor"
        sys_col = (cols - len(sys_title)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_start_row + 3, sys_col, sys_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(2))

        for i, (stage_name, status) in enumerate(stages):
            stage_text = f"{i+1}. {stage_name} [{status}]"
            stage_col = (cols - len(stage_text)) // 2
            row = box_start_row + 5 + i
            if row >= box_start_row + box_height - 3:
                break
            if i == current_stage and status == "/":
                stdscr.attron(curses.color_pair(4))
                anim_chars = ["/", "-", "\\", "|"]
                for j in range(10):
                    stage_text = f"{i+1}. {stage_name} [{anim_chars[j % 4]}]"
                    stage_col = (cols - len(stage_text)) // 2
                    stdscr.addstr(row, stage_col, stage_text, curses.A_BOLD)
                    sub_status_text = f"Durum: {sub_status[:box_width-10]}" if sub_status else ""
                    sub_status_col = (cols - len(sub_status_text)) // 2
                    stdscr.addstr(row + 1, sub_status_col, sub_status_text, curses.A_BOLD)
                    stdscr.refresh()
                    time.sleep(0.2)
                stdscr.attroff(curses.color_pair(4))
            elif status == "TAMAM":
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(row, stage_col, stage_text)
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(row, stage_col, stage_text)
                stdscr.attroff(curses.color_pair(5))

        if sub_status and stages[current_stage][1] == "TAMAM":
            sub_status_text = f"Durum: {sub_status[:box_width-10]}"
            sub_status_col = (cols - len(sub_status_text)) // 2
            stdscr.attron(curses.color_pair(4))
            stdscr.addstr(box_start_row + 5 + current_stage + 1, sub_status_col, sub_status_text, curses.A_BOLD)
            stdscr.attroff(curses.color_pair(4))

        stdscr.refresh()
    except Exception as e:
        log_message(f"Ekran guncelleme basarisiz: {e}")
        print(f"{title}\nSistem baslatiliyor\n" + "\n".join(f"{i+1}. {s[0]} [{s[1]}]" for i, s in enumerate(stages)), file=sys.stderr)

# Install dependencies
def install_dependencies(stdscr, stages, current_stage):
    log_message("Bagimliliklar kontrol ediliyor")
    sub_statuses = []

    try:
        clean_temp()
        for cmd in REQUIRED_COMMANDS:
            sub_statuses.append(f"{cmd} kontrol ediliyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    result = subprocess.run(["which", cmd], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    if cmd == "python3.9":
                        result = subprocess.run([cmd, "--version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                        if "3.9" not in result.stdout:
                            raise Exception("Python 3.9 surumu uygun degil")
                    log_message(f"{cmd} bulundu: {result.stdout.strip()}")
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        sub_statuses.append(f"{cmd} yukleniyor")
                        display_main(stdscr, stages, current_stage, sub_statuses[-1])
                        try:
                            subprocess.run(["sudo", "tce-load", "-w", "-i", cmd], check=True, timeout=300, capture_output=True)
                            result = subprocess.run(["which", cmd], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                            if cmd == "python3.9":
                                result = subprocess.run([cmd, "--version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                                if "3.9" not in result.stdout:
                                    raise Exception("Python 3.9 surumu yuklenemedi")
                            log_message(f"{cmd} yuklendi: {result.stdout.strip()}")
                            break
                        except Exception as e2:
                            log_message(f"{cmd} yuklenemedi: {e2}")
                            raise Exception(f"{cmd} yuklenemedi: {e2}")
                    time.sleep(2)

        for package in REQUIRED_TCE_PACKAGES:
            if package in REQUIRED_COMMANDS:
                continue
            sub_statuses.append(f"{package} kontrol ediliyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    result = subprocess.run(["tce-status", "-i"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                    if package in result.stdout:
                        log_message(f"{package} bulundu")
                        break
                    else:
                        sub_statuses.append(f"{package} yukleniyor")
                        display_main(stdscr, stages, current_stage, sub_statuses[-1])
                        subprocess.run(["sudo", "tce-load", "-w", "-i", package], check=True, timeout=300, capture_output=True)
                        log_message(f"{package} yuklendi")
                        if package == "Xorg-7.7":
                            if not os.path.exists("/usr/local/lib/X11"):
                                raise Exception("Xorg-7.7 yuklendi ama X11 dizini bulunamadi")
                            result = subprocess.run(["Xorg", "-version"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                            if "7.7" not in result.stdout:
                                raise Exception("Xorg-7.7 surumu dogrulanamadi")
                        break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        log_message(f"{package} yuklenemedi: {e}")
                        raise Exception(f"{package} yuklenemedi: {e}")
                    time.sleep(2)
            try:
                onboot_file = os.path.join(TCE_DIR, "onboot.lst")
                with open(onboot_file, "r") as f:
                    content = f.read()
                if package not in content:
                    with open("/tmp/onboot.lst", "w") as f:
                        f.write(content.rstrip() + f"\n{package}\n")
                    subprocess.run(["sudo", "mv", "/tmp/onboot.lst", onboot_file], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chown", "tc:staff", onboot_file], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chmod", "664", onboot_file], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
            except Exception as e:
                log_message(f"onboot.lst guncelleme basarisiz: {e}")
                raise Exception(f"onboot.lst guncelleme basarisiz: {e}")

        sub_statuses.append("Node.js kontrol ediliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        for attempt in range(RETRY_ATTEMPTS):
            try:
                result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                if f"v{NODE_VERSION}" not in result.stdout:
                    raise Exception(f"Node.js surumu {NODE_VERSION} degil")
                log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} bulundu")
                break
            except Exception:
                if attempt == RETRY_ATTEMPTS - 1:
                    sub_statuses.append("Node.js yukleniyor")
                    display_main(stdscr, stages, current_stage, sub_statuses[-1])
                    try:
                        node_url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
                        node_tar = "/tmp/node.tar.xz"
                        subprocess.run(["sudo", "wget", "-O", node_tar, node_url], check=True, timeout=300, capture_output=True)
                        if not os.path.exists(node_tar):
                            raise Exception("Node.js arsivi indirilemedi")
                        subprocess.run(["sudo", "tar", "-xJf", node_tar, "-C", "/usr/local"], check=True, timeout=300)
                        subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/node", "/usr/local/bin/node"], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True, timeout=TIMEOUT_SECONDS)
                        result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                        if f"v{NODE_VERSION}" not in result.stdout:
                            raise Exception("Node.js surumu dogrulanamadi")
                        log_message("Node.js ve npm yuklendi")
                        break
                    except Exception as e:
                        log_message(f"Node.js yuklenemedi: {e}")
                        raise Exception(f"Node.js yuklenemedi: {e}")
                    finally:
                        if os.path.exists(node_tar):
                            subprocess.run(["sudo", "rm", "-f", node_tar], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
                time.sleep(2)

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("Bagimliliklar tamamlandi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"Bagimlilik asamasi basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))
    finally:
        clean_temp()

# Verify disk
def verify_disk(stdscr, stages, current_stage):
    log_message("Disk dogrulaniyor")
    sub_statuses = []

    try:
        clean_temp()
        sub_statuses.append("Disk dizini olusturuluyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        for attempt in range(RETRY_ATTEMPTS):
            try:
                subprocess.run(["sudo", "mkdir", "-p", ROOT_DIR], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
                subprocess.run(["sudo", "chown", "tc:staff", ROOT_DIR], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "775", ROOT_DIR], check=True, timeout=TIMEOUT_SECONDS)
                if not os.path.exists(ROOT_DIR):
                    raise Exception("Disk dizini olusturulamadi")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    log_message(f"Disk dizini olusturulamadi: {e}")
                    raise Exception(f"Disk dizini olusturulamadi: {e}")
                time.sleep(2)

        sub_statuses.append("Disk baglaniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        for attempt in range(RETRY_ATTEMPTS):
            try:
                result = subprocess.run(["mountpoint", "-q", ROOT_DIR], capture_output=True, check=False, timeout=TIMEOUT_SECONDS)
                if result.returncode != 0:
                    try:
                        subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True, timeout=10, capture_output=True)
                    except Exception:
                        log_message("Disk baglama basarisiz, bicimlendirme deneniyor")
                        subprocess.run(["sudo", "mkfs.ext4", "-F", "/dev/sda1"], check=True, timeout=600, capture_output=True)
                        subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True, timeout=10)
                subprocess.run(["sudo", "mount", "-o", "remount,rw", ROOT_DIR], check=True, timeout=TIMEOUT_SECONDS)
                result = subprocess.run(["df", "-h", ROOT_DIR], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
                if ROOT_DIR not in result.stdout:
                    raise Exception("Disk baglama dogrulanamadi")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    log_message(f"Disk baglama basarisiz: {e}")
                    raise Exception(f"Disk baglama basarisiz: {e}")
                time.sleep(2)

        sub_statuses.append("Dizinler olusturuluyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        dirs = [TCE_DIR, SYSTEM_DIR, APPS_DIR, BACKUP_DIR, LOG_DIR]
        for d in dirs:
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    subprocess.run(["sudo", "mkdir", "-p", d], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
                    subprocess.run(["sudo", "chown", "tc:staff", d], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chmod", "775", d], check=True, timeout=TIMEOUT_SECONDS)
                    if not os.path.exists(d):
                        raise Exception(f"Dizin olusturulamadi: {d}")
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        log_message(f"Dizin olusturma basarisiz: {d}: {e}")
                        raise Exception(f"Dizin olusturma basarisiz: {d}: {e}")
                    time.sleep(2)

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("Disk tamamlandi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"Disk asamasi basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))
    finally:
        clean_temp()

# Verify backup
def verify_backup(stdscr, stages, current_stage):
    log_message("Sistem yedekleniyor")
    sub_statuses = []

    try:
        clean_temp()
        sub_statuses.append("Yedek dizini olusturuluyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        for attempt in range(RETRY_ATTEMPTS):
            try:
                subprocess.run(["sudo", "mkdir", "-p", BACKUP_DIR], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
                subprocess.run(["sudo", "chown", "tc:staff", BACKUP_DIR], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "775", BACKUP_DIR], check=True, timeout=TIMEOUT_SECONDS)
                if not os.path.exists(BACKUP_DIR):
                    raise Exception("Yedek dizini olusturulamadi")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    log_message(f"Yedek dizini olusturulamadi: {e}")
                    raise Exception(f"Yedek dizini olusturulamadi: {e}")
                time.sleep(2)

        sub_statuses.append("Dosyalar yedekleniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.tar.gz")
            dirs_to_backup = [SYSTEM_DIR, APPS_DIR, TCE_DIR]
            for d in dirs_to_backup:
                if not os.path.exists(d):
                    subprocess.run(["sudo", "mkdir", "-p", d], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
                    subprocess.run(["sudo", "chown", "tc:staff", d], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chmod", "775", d], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "tar", "-czf", backup_file] + dirs_to_backup, check=True, timeout=600, capture_output=True)
            if not os.path.exists(backup_file):
                raise Exception("Yedek dosyasi olusturulamadi")
        except Exception as e:
            log_message(f"Yedekleme basarisiz: {e}")
            raise Exception(f"Yedekleme basarisiz: {e}")

        sub_statuses.append("Yedek dogrulaniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            backup_hash = calculate_file_hash(backup_file)
            if not backup_hash:
                raise Exception("Yedek dogrulama basarisiz")
            log_message(f"Yedek olusturuldu: {backup_file}, SHA256: {backup_hash}")
            backup_log = os.path.join(BACKUP_DIR, "backup_log.txt")
            with open("/tmp/backup_log.txt", "a") as f:
                f.write(f"{timestamp}: {backup_file}, SHA256: {backup_hash}\n")
            subprocess.run(["sudo", "mv", "/tmp/backup_log.txt", backup_log], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "chown", "tc:staff", backup_log], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "chmod", "664", backup_log], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
            if not os.path.exists(backup_log):
                raise Exception("Yedek log dosyasi olusturulamadi")
        except Exception as e:
            log_message(f"Yedek dogrulama basarisiz: {e}")
            raise Exception(f"Yedek dogrulama basarisiz: {e}")

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("Yedekleme tamamlandi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"Yedekleme asamasi basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))
    finally:
        clean_temp()

# Download EDEX-UI
def download_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI indiriliyor")
    sub_statuses = []

    try:
        clean_temp()
        sub_statuses.append("EDEX-UI varligi kontrol ediliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        if os.path.exists(EDEX_DIR) and os.path.isfile(os.path.join(EDEX_DIR, "package.json")):
            log_message("EDEX-UI zaten mevcut")
        else:
            sub_statuses.append("EDEX-UI klonlaniyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    if os.path.exists(EDEX_DIR):
                        shutil.rmtree(EDEX_DIR, ignore_errors=True)
                    subprocess.run(["sudo", "git", "clone", EDEX_URL, EDEX_DIR], check=True, timeout=600, capture_output=True)
                    subprocess.run(["sudo", "chown", "-R", "tc:staff", EDEX_DIR], check=True, timeout=10)
                    subprocess.run(["sudo", "chmod", "-R", "775", EDEX_DIR], check=True, timeout=10)
                    if not os.path.exists(os.path.join(EDEX_DIR, "package.json")):
                        raise Exception("EDEX-UI package.json bulunamadi")
                    log_message("EDEX-UI klonlandi")
                    break
                except Exception as e:
                    if attempt == RETRY_ATTEMPTS - 1:
                        log_message(f"EDEX-UI klonlama basarisiz: {e}")
                        raise Exception(f"EDEX-UI klonlama basarisiz: {e}")
                    time.sleep(2)

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("EDEX-UI indirildi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"EDEX-UI indirme asamasi basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))
    finally:
        clean_temp()

# Install EDEX-UI
def install_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI kuruluyor")
    sub_statuses = []

    try:
        clean_temp()
        sub_statuses.append("npm bagimliliklari yukleniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        for attempt in range(RETRY_ATTEMPTS):
            try:
                subprocess.run(["sudo", "npm", "install", "--unsafe-perm"], cwd=EDEX_DIR, check=True, timeout=600, capture_output=True)
                if not os.path.exists(os.path.join(EDEX_DIR, "node_modules")):
                    raise Exception("npm bagimliliklari dogrulanamadi")
                log_message("npm bagimliliklari yuklendi")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    log_message(f"npm bagimliliklari yuklenemedi: {e}")
                    raise Exception(f"npm bagimliliklari yuklenemedi: {e}")
                time.sleep(2)

        sub_statuses.append("Ayarlar ozellestiriliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            settings_path = os.path.join(EDEX_DIR, "settings.json")
            settings = {
                "shell": "/bin/bash",
                "shellArgs": ["-c", f"export PATH=$PATH:/usr/local/bin; exec bash"],
                "theme": "tron",
                "window": {"title": f"{SYSTEM_NAME} EDEX-UI"},
                "performance": {"lowPowerMode": False, "gpuAcceleration": True}
            }
            with open("/tmp/settings.json", "w") as f:
                json.dump(settings, f, indent=2)
            subprocess.run(["sudo", "mv", "/tmp/settings.json", settings_path], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "chown", "tc:staff", settings_path], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "chmod", "664", settings_path], check=True, timeout=TIMEOUT_SECONDS)
            if not os.path.exists(settings_path):
                raise Exception("Ayarlar dosyasi tasinamadi")
            with open(settings_path, "r") as f:
                if f"{SYSTEM_NAME}" not in f.read():
                    raise Exception("Ayarlar icerigi dogrulanamadi")
            log_message("EDEX-UI ayarlar ozellestirildi")
        except Exception as e:
            log_message(f"EDEX-UI ayarlar ozellestirilemedi: {e}")
            raise Exception(f"EDEX-UI ayarlar ozellestirilemedi: {e}")

        sub_statuses.append("Xorg optimize ediliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            xorg_conf_dir = "/etc/X11/xorg.conf.d"
            xorg_conf = os.path.join(xorg_conf_dir, "10-optimizations.conf")
            subprocess.run(["sudo", "mkdir", "-p", xorg_conf_dir], check=True, timeout=TIMEOUT_SECONDS, capture_output=True)
            subprocess.run(["sudo", "chown", "tc:staff", xorg_conf_dir], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "chmod", "775", xorg_conf_dir], check=True, timeout=TIMEOUT_SECONDS)
            with open("/tmp/xorg.conf", "w") as f:
                f.write(
                    'Section "Device"\n'
                    '    Identifier "Card0"\n'
                    '    Driver "vesa"\n'
                    '    Option "AccelMethod" "exa"\n'
                    'EndSection\n'
                )
            subprocess.run(["sudo", "mv", "/tmp/xorg.conf", xorg_conf], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "chown", "tc:staff", xorg_conf], check=True, timeout=TIMEOUT_SECONDS)
            subprocess.run(["sudo", "chmod", "664", xorg_conf], check=True, timeout=TIMEOUT_SECONDS)
            if not os.path.exists(xorg_conf):
                raise Exception("Xorg yapilandirma dosyasi tasinamadi")
            log_message("Xorg optimize edildi")
        except Exception as e:
            log_message(f"Xorg optimizasyonu basarisiz: {e}")
            raise Exception(f"Xorg optimizasyonu basarisiz: {e}")

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("EDEX-UI kurulumu tamamlandi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"EDEX-UI kurulum asamasi basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))
    finally:
        clean_temp()

# Start EDEX-UI
def start_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI baslatiliyor")
    sub_statuses = []
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
        sub_statuses.append("X11 ortami hazirlaniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        for attempt in range(RETRY_ATTEMPTS):
            try:
                os.environ["DISPLAY"] = ":0"
                result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, check=False, timeout=TIMEOUT_SECONDS)
                if result.returncode != 0:
                    subprocess.run(["sudo", "Xorg", "-quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
                    time.sleep(3)
                    result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, check=True, timeout=TIMEOUT_SECONDS)
                log_message("X11 ortami hazirlandi")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    log_message(f"X11 baslatma basarisiz: {e}")
                    raise Exception(f"X11 baslatma basarisiz: {e}")
                time.sleep(2)

        sub_statuses.append("EDEX-UI calistiriliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            process = subprocess.Popen(
                ["sudo", "npm", "start", "--unsafe-perm"],
                cwd=EDEX_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            time.sleep(15)
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=TIMEOUT_SECONDS)
                log_message(f"EDEX-UI baslatma basarisiz: {stderr}")
                raise Exception(f"EDEX-UI baslatilamadi: {stderr}")
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS)
            if "node" not in result.stdout or "edex-ui" not in result.stdout:
                raise Exception("EDEX-UI process dogrulanamadi")
            log_message("EDEX-UI baslatildi")
        except Exception as e:
            log_message(f"EDEX-UI baslatma basarisiz: {e}")
            raise Exception(f"EDEX-UI baslatma basarisiz: {e}")

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("EDEX-UI baslatildi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"EDEX-UI baslatma asamasi basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))
    finally:
        cleanup()

# Configure autostart
def configure_autostart(stdscr, stages, current_stage):
    log_message("Otomatik baslama ayarlanliyor")
    sub_statuses = []

    try:
        clean_temp()
        sub_statuses.append("Boot scripti guncelleniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        for attempt in range(RETRY_ATTEMPTS):
            try:
                script_path = "/mnt/sda1/kontrol.py"
                if not os.path.exists(script_path):
                    raise Exception("kontrol.py bulunamadi")
                subprocess.run(["sudo", "chown", "tc:staff", script_path], check=True, timeout=TIMEOUT_SECONDS)
                subprocess.run(["sudo", "chmod", "775", script_path], check=True, timeout=TIMEOUT_SECONDS)
                if os.path.exists(BOOT_SCRIPT):
                    with open(BOOT_SCRIPT, "r") as f:
                        content = f.read()
                    if script_path in content:
                        log_message("Otomatik baslama zaten ayarlanmis")
                    else:
                        subprocess.run(["sudo", "cp", BOOT_SCRIPT, f"{BOOT_SCRIPT}.bak"], capture_output=True, timeout=TIMEOUT_SECONDS)
                        with open("/tmp/bootlocal.sh", "w") as f:
                            f.write(content.rstrip() + f"\npython3.9 {script_path} --skip-ui &\n")
                        subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", BOOT_SCRIPT], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "chown", "tc:staff", BOOT_SCRIPT], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "chmod", "775", BOOT_SCRIPT], check=True, timeout=TIMEOUT_SECONDS)
                        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                        log_message("Otomatik baslama eklendi")
                else:
                    with open("/tmp/bootlocal.sh", "w") as f:
                        f.write(f"#!/bin/sh\npython3.9 {script_path} --skip-ui &\n")
                    subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", BOOT_SCRIPT], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chown", "tc:staff", BOOT_SCRIPT], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "chmod", "775", BOOT_SCRIPT], check=True, timeout=TIMEOUT_SECONDS)
                    subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                    log_message("Yeni boot scripti olusturuldu")
                with open(BOOT_SCRIPT, "r") as f:
                    if script_path not in f.read():
                        raise Exception("Boot scripti icerigi dogrulanamadi")
                break
            except Exception as e:
                if attempt == RETRY_ATTEMPTS - 1:
                    log_message(f"Otomatik baslama ayarlama basarisiz: {e}")
                    raise Exception(f"Otomatik baslama ayarlama basarisiz: {e}")
                time.sleep(2)

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("Otomatik baslama tamamlandi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"Otomatik baslama asamasi basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))
    finally:
        clean_temp()

# Main function
def main(stdscr):
    try:
        subprocess.run(["resize"], capture_output=True, timeout=TIMEOUT_SECONDS)
        curses.curs_set(0)
        stdscr.timeout(-1)
        rows, cols = stdscr.getmaxyx()
        if rows < MIN_TERM_SIZE[0] or cols < MIN_TERM_SIZE[1]:
            raise Exception(f"Terminal boyutu yetersiz (min {MIN_TERM_SIZE[1]}x{MIN_TERM_SIZE[0]})")
        box_width = min(cols - 4, max(50, int(cols * 0.8)))
        box_height = min(rows - 4, max(15, int(rows * 0.6)))
        box_start_row = (rows - box_height) // 2
        box_start_col = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)

        title = "B E R K E  O S"
        title_col = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        status = "Beklemede"
        status_col = (cols - len(status)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_start_row + box_height // 2, status_col, status)
        stdscr.attroff(curses.color_pair(2))
        stdscr.refresh()
        time.sleep(2)
    except Exception as e:
        log_message(f"Curses baslatilamadi: {e}")
        print(f"Curses baslatilamadi: {e}", file=sys.stderr)
        sys.exit(1)

    skip_ui = "--skip-ui" in sys.argv
    if skip_ui:
        if os.path.exists(EDEX_DIR) and os.path.isfile(os.path.join(EDEX_DIR, "package.json")):
            start_edex_ui(None, [("EDEX-UI BASLATMA", "/")], 0)
        else:
            log_message("EDEX-UI bulunamadi, kurulum gerekiyor")
            print("EDEX-UI bulunamadi, tam kurulum yapin", file=sys.stderr)
        sys.exit(0)

    stages = [
        ("BAGIMLILIK YUKLEME", "/"),
        ("DISK YAPILANDIRMA", "-"),
        ("YEDEKLEME", "-"),
        ("EDEX-UI INDIRME", "-"),
        ("EDEX-UI KURULUM", "-"),
        ("EDEX-UI BASLATMA", "-"),
        ("OTOMATIK BASLAMA", "-")
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
            func(stdscr, stages, i)
        except Exception as e:
            log_message(f"Asama basarisiz: {stages[i][0]}: {e}")
            display_error(stdscr, stages[i][0], str(e))

if __name__ == "__main__":
    def signal_handler(sig, frame):
        log_message(f"Sinyal alindi: {sig}")
        subprocess.run(["sudo", "killall", "-q", "node"], capture_output=True, timeout=TIMEOUT_SECONDS)
        subprocess.run(["sudo", "killall", "-q", "Xorg"], capture_output=True, timeout=TIMEOUT_SECONDS)
        clean_temp()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        log_message(f"{SYSTEM_NAME} basladi")
        curses.wrapper(main)
    except Exception as e:
        log_message(f"{SYSTEM_NAME} coktu: {e}")
        print(f"Hata: {e}\n{SYSTEM_NAME}", file=sys.stderr)
        sys.exit(1)

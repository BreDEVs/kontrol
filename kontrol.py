import os
import sys
import time
import subprocess
import curses
import hashlib
import requests
import json
import shutil
import signal

# Configuration
SYSTEM_NAME = "BERKE OS"
ROOT_DIR = "/mnt/sda1"
TCE_DIR = os.path.join(ROOT_DIR, "tce")
SYSTEM_DIR = os.path.join(ROOT_DIR, "system")
APPS_DIR = os.path.join(ROOT_DIR, "apps")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups")
LOG_FILE = os.path.join(SYSTEM_DIR, "logs", "install_log.txt")
EDEX_DIR = os.path.join(APPS_DIR, "edex-ui")
NODE_VERSION = "16.20.2"
EDEX_URL = "https://github.com/GitSquared/edex-ui.git"
COMMANDS_SCRIPT = "/usr/local/bin/berke_commands.sh"
BOOT_SCRIPT = "/opt/bootlocal.sh"
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "libX11", "libxss", "fontconfig", "git", "wget", "curl", "tar", "wireless-tools", "wpa_supplicant"]
REQUIRED_COMMANDS = ["python3.9", "wget", "curl", "git", "tar"]
MIN_TERM_SIZE = (20, 50)

# Set PATH
os.environ["PATH"] = f"{os.environ.get('PATH', '')}:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin"

# Logging
def log_message(message):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        subprocess.run(["sudo", "chmod", "755", os.path.dirname(LOG_FILE)], check=True, timeout=5)
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
        subprocess.run(["sudo", "chmod", "644", LOG_FILE], check=True, timeout=5)
    except Exception as e:
        print(f"Log yazma hatasi: {e}")

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

# Check internet connection
def check_internet():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.RequestException:
        return False

# Clean temporary files
def clean_temp():
    try:
        if os.path.exists("/tmp"):
            for item in os.listdir("/tmp"):
                path = os.path.join("/tmp", item)
                if os.path.isfile(path):
                    subprocess.run(["sudo", "rm", "-f", path], check=True, timeout=5)
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
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

# Network setup
def network_setup(stdscr):
    try:
        clean_temp()
        stdscr.clear()
        curses.curs_set(0)
        rows, cols = stdscr.getmaxyx()
        box_width = min(cols - 4, max(50, int(cols * 0.8)))
        box_height = min(rows - 4, max(20, int(rows * 0.6)))
        box_start_row = (rows - box_height) // 2
        box_start_col = (cols - box_width) // 2

        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)

        title = "B E R K E  O S"
        title_col = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        subtitle = "AG BAGLANTI"
        subtitle_col = (cols - len(subtitle)) // 2
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_start_row + 3, subtitle_col, subtitle, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(2))

        log_message("Ag hazirlaniyor")
        subprocess.run(["sudo", "rfkill", "unblock", "wifi"], check=True, capture_output=True, timeout=5)
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"], check=True, capture_output=True, timeout=5)
        log_message("Ag taraniyor")
        result = subprocess.run(["sudo", "iwlist", "wlan0", "scan"], capture_output=True, text=True, timeout=30, check=True)
        networks = []
        current_ssid = ""
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("ESSID:"):
                current_ssid = line.split(":", 1)[1].strip('"')
                if current_ssid:
                    networks.append(current_ssid)

        if not networks:
            raise Exception("Ag bulunamadi")

        selected = 0
        while True:
            stdscr.clear()
            draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
            stdscr.attroff(curses.color_pair(1))
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(box_start_row + 3, subtitle_col, subtitle, curses.A_BOLD)
            stdscr.attroff(curses.color_pair(2))
            for i, net in enumerate(networks[:box_height - 6]):
                net_text = f"> {net}" if i == selected else f"  {net}"
                net_col = (cols - len(net_text)) // 2
                stdscr.addstr(box_start_row + 5 + i, net_col, net_text, curses.A_REVERSE if i == selected else 0)
            prompt = "Yukari/Asagi: Secim, Enter: Baglan, Q: Cikis"
            prompt_col = (cols - len(prompt)) // 2
            stdscr.addstr(box_start_row + box_height - 3, prompt_col, prompt)
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(networks) - 1:
                selected += 1
            elif key == 10:
                break
            elif key == ord('q'):
                raise Exception("Kullanici ag secimi iptal etti")

        ssid = networks[selected]
        stdscr.clear()
        draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_start_row + 3, subtitle_col, subtitle, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(2))
        ssid_text = f"Secilen ag: {ssid}"
        ssid_col = (cols - len(ssid_text)) // 2
        stdscr.addstr(box_start_row + 5, ssid_col, ssid_text)
        pwd_prompt = "Sifre: "
        pwd_prompt_col = (cols - len(pwd_prompt)) // 2
        stdscr.addstr(box_start_row + 6, pwd_prompt_col, pwd_prompt)
        curses.curs_set(1)
        curses.echo()
        password = stdscr.getstr(box_start_row + 6, pwd_prompt_col + len(pwd_prompt), 60).decode()
        curses.noecho()
        curses.curs_set(0)

        log_message(f"Ag baglantisi deneniyor: {ssid}")
        with open("/tmp/wpa.conf", "w") as f:
            f.write(f'network={{\nssid="{ssid}"\npsk="{password}"\n}}\n')
        if not os.path.exists("/tmp/wpa.conf"):
            raise Exception("wpa.conf olusturulamadi")
        subprocess.run(["sudo", "mv", "/tmp/wpa.conf", "/etc/wpa_supplicant.conf"], check=True, timeout=5)
        subprocess.run(["sudo", "chmod", "600", "/etc/wpa_supplicant.conf"], check=True, timeout=5)
        subprocess.run(["sudo", "killall", "-q", "wpa_supplicant"], capture_output=True, timeout=5)
        subprocess.run(["sudo", "wpa_supplicant", "-B", "-i", "wlan0", "-c", "/etc/wpa_supplicant.conf"], check=True, timeout=10)
        subprocess.run(["sudo", "udhcpc", "-i", "wlan0"], check=True, timeout=30)
        if not check_internet():
            raise Exception("Ag baglantisi basarisiz")
        log_message(f"Ag baglantisi basarili: {ssid}")
        success_msg = "Baglanti basarili! Devam icin bir tusa basin"
        success_col = (cols - len(success_msg)) // 2
        stdscr.addstr(box_start_row + 8, success_col, success_msg)
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        log_message(f"Ag baglantisi basarisiz: {e}")
        stdscr.clear()
        draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))
        error_msg = f"Hata: {str(e)[:box_width-4]}"
        error_col = (cols - len(error_msg)) // 2
        stdscr.addstr(box_start_row + 5, error_col, error_msg)
        solution = "Wi-Fi adaptorunu kontrol edin veya kablolu baglanti deneyin"
        solution_col = (cols - len(solution)) // 2
        stdscr.addstr(box_start_row + 6, solution_col, solution)
        exit_prompt = "Cikmak icin bir tusa basin"
        exit_col = (cols - len(exit_prompt)) // 2
        stdscr.addstr(box_start_row + 8, exit_col, exit_prompt)
        stdscr.refresh()
        stdscr.getch()
        raise Exception(f"Ag baglantisi basarisiz: {e}")
    finally:
        clean_temp()

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
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)

        title = "B E R K E  O S"
        title_col = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        error_title = "HATA ALINDI!"
        error_title_col = (cols - len(error_title)) // 2
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(box_start_row + 3, error_title_col, error_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(3))

        stage_info = f"Asama: {stage}"
        stage_col = (cols - len(stage_info)) // 2
        stdscr.addstr(box_start_row + 5, stage_col, stage_info)

        error_info = f"Hata: {error_msg[:box_width-4]}"
        error_col = (cols - len(error_info)) // 2
        stdscr.addstr(box_start_row + 6, error_col, error_info)

        solution = f"Loglari kontrol edin: {LOG_FILE}"
        solution_col = (cols - len(solution)) // 2
        stdscr.addstr(box_start_row + 8, solution_col, solution)

        exit_prompt = "Cikmak icin bir tusa basin"
        exit_col = (cols - len(exit_prompt)) // 2
        stdscr.addstr(box_start_row + box_height - 3, exit_col, exit_prompt)
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        log_message(f"Hata ekrani gosterilemedi: {e}")
        print(f"HATA ALINDI!\nAsama: {stage}\nHata: {error_msg}")
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
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
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
                stdscr.attron(curses.color_pair(5))
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
                stdscr.attroff(curses.color_pair(5))
            elif status == "TAMAM":
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(row, stage_col, stage_text)
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.attron(curses.color_pair(6))
                stdscr.addstr(row, stage_col, stage_text)
                stdscr.attroff(curses.color_pair(6))

        if sub_status and stages[current_stage][1] == "TAMAM":
            sub_status_text = f"Durum: {sub_status[:box_width-10]}"
            sub_status_col = (cols - len(sub_status_text)) // 2
            stdscr.attron(curses.color_pair(5))
            stdscr.addstr(box_start_row + 5 + current_stage + 1, sub_status_col, sub_status_text, curses.A_BOLD)
            stdscr.attroff(curses.color_pair(5))

        stdscr.refresh()
    except Exception as e:
        log_message(f"Ekran guncelleme basarisiz: {e}")
        print(f"{title}\nSistem baslatiliyor\n" + "\n".join(f"{i+1}. {s[0]} [{s[1]}]" for i, s in enumerate(stages)))

# Install dependencies
def install_dependencies(stdscr, stages, current_stage):
    log_message("Bagimliliklar kontrol ediliyor")
    sub_statuses = []
    needs_internet = False

    try:
        clean_temp()
        for cmd in REQUIRED_COMMANDS:
            sub_statuses.append(f"{cmd} kontrol ediliyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            try:
                result = subprocess.run(["which", cmd], capture_output=True, text=True, check=True, timeout=5)
                if cmd == "python3.9":
                    result = subprocess.run([cmd, "--version"], capture_output=True, check=True, timeout=5)
                    if "3.9" not in result.stdout:
                        raise Exception("Python 3.9 surumu uygun degil")
                log_message(f"{cmd} bulundu: {result.stdout.strip()}")
            except Exception as e:
                needs_internet = True
                sub_statuses.append(f"{cmd} yukleniyor")
                display_main(stdscr, stages, current_stage, sub_statuses[-1])
                for attempt in range(2):
                    try:
                        result = subprocess.run(["sudo", "tce-load", "-w", "-i", cmd], capture_output=True, text=True, check=True, timeout=300)
                        log_message(f"{cmd} yuklendi")
                        break
                    except Exception as e2:
                        if attempt == 1:
                            log_message(f"{cmd} yuklenemedi: {e2}")
                            raise Exception(f"{cmd} yuklenemedi: {e2}")

        sub_statuses.append("Python requests kontrol ediliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            import requests
            log_message("requests modulu bulundu")
        except ImportError:
            needs_internet = True
            sub_statuses.append("Python requests yukleniyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            try:
                subprocess.run(["sudo", "pip3", "install", "requests"], check=True, timeout=300, capture_output=True)
                import requests
                log_message("requests modulu yuklendi")
            except Exception as e:
                log_message(f"requests modulu yuklenemedi: {e}")
                raise Exception(f"requests modulu yuklenemedi: {e}")

        for package in REQUIRED_TCE_PACKAGES:
            if package in REQUIRED_COMMANDS:
                continue
            sub_statuses.append(f"{package} kontrol ediliyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            try:
                result = subprocess.run(["tce-status", "-i"], capture_output=True, text=True, check=True, timeout=5)
                if package in result.stdout:
                    log_message(f"{package} bulundu")
                else:
                    needs_internet = True
                    sub_statuses.append(f"{package} yukleniyor")
                    display_main(stdscr, stages, current_stage, sub_statuses[-1])
                    for attempt in range(2):
                        try:
                            result = subprocess.run(["sudo", "tce-load", "-w", "-i", package], capture_output=True, text=True, check=True, timeout=300)
                            log_message(f"{package} yuklendi")
                            break
                        except Exception as e:
                            if attempt == 1:
                                log_message(f"{package} yuklenemedi: {e}")
                                raise Exception(f"{package} yuklenemedi: {e}")
                            time.sleep(2)
                    if package == "Xorg-7.7":
                        if not os.path.exists("/usr/local/lib/X11"):
                            raise Exception("Xorg-7.7 yuklendi ama X11 dizini bulunamadi")
                        result = subprocess.run(["Xorg", "-version"], capture_output=True, text=True, timeout=5)
                        if "7.7" not in result.stdout:
                            raise Exception("Xorg-7.7 surumu dogrulanamadi")
                with open(os.path.join(TCE_DIR, "onboot.lst"), "a") as f:
                    if package not in f.read():
                        f.write(f"{package}\n")
                subprocess.run(["sudo", "chmod", "644", os.path.join(TCE_DIR, "onboot.lst")], check=True, timeout=5)
                subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
            except Exception as e:
                log_message(f"{package} yuklenemedi: {e}")
                raise Exception(f"{package} yuklenemedi: {e}")

        sub_statuses.append("Node.js kontrol ediliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=5)
            npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, check=True, timeout=5)
            if f"v{NODE_VERSION}" not in result.stdout:
                raise Exception(f"Node.js surumu {NODE_VERSION} degil")
            log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} bulundu")
        except Exception:
            needs_internet = True
            sub_statuses.append("Node.js yukleniyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            for attempt in range(2):
                try:
                    node_url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
                    subprocess.run(["sudo", "curl", "-o", "/tmp/node.tar.xz", node_url], check=True, timeout=300, capture_output=True)
                    if not os.path.exists("/tmp/node.tar.xz"):
                        raise Exception("Node.js arsivi indirilemedi")
                    subprocess.run(["sudo", "tar", "-xJf", "/tmp/node.tar.xz", "-C", "/usr/local"], check=True, timeout=300)
                    subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/node", "/usr/local/bin/node"], check=True, timeout=5)
                    subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True, timeout=5)
                    result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=5)
                    if f"v{NODE_VERSION}" not in result.stdout:
                        raise Exception("Node.js surumu dogrulanamadi")
                    log_message("Node.js ve npm yuklendi")
                    break
                except Exception as e:
                    if attempt == 1:
                        log_message(f"Node.js yuklenemedi: {e}")
                        raise Exception(f"Node.js yuklenemedi: {e}")
                    time.sleep(2)
                finally:
                    clean_temp()

        if needs_internet:
            sub_statuses.append("Internet baglantisi kontrol ediliyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            if not check_internet():
                sub_statuses.append("Internet baglantisi kuruluyor")
                display_main(stdscr, stages, current_stage, sub_statuses[-1])
                network_setup(stdscr)

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
        try:
            subprocess.run(["sudo", "mkdir", "-p", ROOT_DIR], check=True, timeout=5, capture_output=True)
            subprocess.run(["sudo", "chmod", "755", ROOT_DIR], check=True, timeout=5)
            if not os.path.exists(ROOT_DIR):
                raise Exception("Disk dizini olusturulamadi")
        except Exception as e:
            log_message(f"Disk dizini olusturulamadi: {e}")
            raise Exception(f"Disk dizini olusturulamadi: {e}")

        sub_statuses.append("Disk baglaniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            result = subprocess.run(["mountpoint", "-q", ROOT_DIR], capture_output=True, check=False, timeout=5)
            if result.returncode != 0:
                try:
                    subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True, timeout=10, capture_output=True)
                except Exception:
                    log_message("Disk baglama basarisiz, bicimlendirme deneniyor")
                    subprocess.run(["sudo", "mkfs.ext4", "-F", "/dev/sda1"], check=True, timeout=600, capture_output=True)
                    subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True, timeout=10)
            subprocess.run(["sudo", "mount", "-o", "remount,rw", ROOT_DIR], check=True, timeout=5)
            result = subprocess.run(["df", "-h", ROOT_DIR], capture_output=True, text=True, check=True, timeout=5)
            if ROOT_DIR not in result.stdout:
                raise Exception("Disk baglama dogrulanamadi")
        except Exception as e:
            log_message(f"Disk baglama basarisiz: {e}")
            raise Exception(f"Disk baglama basarisiz: {e}")

        sub_statuses.append("Dizinler olusturuluyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            dirs = [TCE_DIR, SYSTEM_DIR, APPS_DIR, BACKUP_DIR, os.path.join(SYSTEM_DIR, "logs")]
            for d in dirs:
                subprocess.run(["sudo", "mkdir", "-p", d], check=True, timeout=5, capture_output=True)
                subprocess.run(["sudo", "chmod", "755", d], check=True, timeout=5)
                if not os.path.exists(d):
                    raise Exception(f"Dizin olusturulamadi: {d}")
        except Exception as e:
            log_message(f"Dizin olusturma basarisiz: {e}")
            raise Exception(f"Dizin olusturma basarisiz: {e}")

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
        try:
            subprocess.run(["sudo", "mkdir", "-p", BACKUP_DIR], check=True, timeout=5, capture_output=True)
            subprocess.run(["sudo", "chmod", "750", BACKUP_DIR], check=True, timeout=5)
            if not os.path.exists(BACKUP_DIR):
                raise Exception("Yedek dizini olusturulamadi")
        except Exception as e:
            log_message(f"Yedek dizini olusturulamadi: {e}")
            raise Exception(f"Yedek dizini olusturulamadi: {e}")

        sub_statuses.append("Dosyalar yedekleniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.tar.gz")
            dirs_to_backup = [SYSTEM_DIR, APPS_DIR, TCE_DIR]
            for d in dirs_to_backup:
                if not os.path.exists(d):
                    log_message(f"Yedeklenecek dizin bulunamadi: {d}")
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
            with open(os.path.join(BACKUP_DIR, "backup_log.txt"), "a") as f:
                f.write(f"{timestamp}: {backup_file}, SHA256: {backup_hash}\n")
            subprocess.run(["sudo", "chmod", "644", os.path.join(BACKUP_DIR, "backup_log.txt")], check=True, timeout=5)
            subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
            if not os.path.exists(os.path.join(BACKUP_DIR, "backup_log.txt")):
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
            if not check_internet():
                sub_statuses.append("Internet baglantisi kuruluyor")
                display_main(stdscr, stages, current_stage, sub_statuses[-1])
                network_setup(stdscr)
            sub_statuses.append("EDEX-UI klonlaniyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            for attempt in range(2):
                try:
                    if os.path.exists(EDEX_DIR):
                        shutil.rmtree(EDEX_DIR, ignore_errors=True)
                    subprocess.run(["sudo", "git", "clone", EDEX_URL, EDEX_DIR], check=True, timeout=600, capture_output=True)
                    subprocess.run(["sudo", "chmod", "-R", "755", EDEX_DIR], check=True, timeout=10)
                    log_message("EDEX-UI klonlandi")
                    break
                except Exception as e:
                    if attempt == 1:
                        log_message(f"EDEX-UI klonlama basarisiz: {e}")
                        raise Exception(f"EDEX-UI klonlama basarisiz: {e}")
                    time.sleep(2)
            if not os.path.exists(os.path.join(EDEX_DIR, "package.json")):
                raise Exception("EDEX-UI package.json bulunamadi")

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("EDEX-UI indirildi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"EDEX-UI indirme asamasi basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))
    finally:
        clean_temp()

# Create custom commands
def create_custom_commands(stdscr, stages, current_stage):
    log_message("Ozel komutlar olusturuluyor")
    sub_statuses = []

    try:
        clean_temp()
        sub_statuses.append("Komut betigi olusturuluyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        cmd_script = f"""#!/bin/bash
case "$1" in
    Berk0:Kapat)
        sudo poweroff
        ;;
    Berk0:YenidenBaslat)
        sudo reboot
        ;;
    Berk0:Internet)
        sudo python3.9 /mnt/sda1/kontrol.py --network
        ;;
    Berk0:Durum)
        echo "Sistem Durumu:"
        df -h
        uptime
        iwconfig wlan0
        ;;
    Berk0:Guncelle)
        sudo tce-update
        ;;
    *)
        echo "Bilinmeyen komut: $1"
        echo "Kullanilabilir: Berk0:Kapat, Berk0:YenidenBaslat, Berk0:Internet, Berk0:Durum, Berk0:Guncelle"
        exit 1
        ;;
esac
"""
        try:
            with open("/tmp/berke_commands.sh", "w") as f:
                f.write(cmd_script)
            if not os.path.exists("/tmp/berke_commands.sh"):
                raise Exception("Komut betigi olusturulamadi")
            subprocess.run(["sudo", "mv", "/tmp/berke_commands.sh", COMMANDS_SCRIPT], check=True, timeout=5)
            subprocess.run(["sudo", "chmod", "755", COMMANDS_SCRIPT], check=True, timeout=5)
            if not os.path.exists(COMMANDS_SCRIPT):
                raise Exception("Komut betigi tasinamadi")
            with open(COMMANDS_SCRIPT, "r") as f:
                if "Berk0:Kapat" not in f.read():
                    raise Exception("Komut betigi icerigi dogrulanamadi")
            log_message("Komut betigi olusturuldu")
        except Exception as e:
            log_message(f"Ozel komutlar olusturulamadi: {e}")
            raise Exception(f"Ozel komutlar olusturulamadi: {e}")

        stages[current_stage] = (stages[current_stage][0], "TAMAM")
        sub_statuses.append("Ozel komutlar tamamlandi")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        time.sleep(5)
    except Exception as e:
        log_message(f"Ozel komutlar asamasi basarisiz: {e}")
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
        try:
            for attempt in range(2):
                try:
                    subprocess.run(["sudo", "npm", "install", "--unsafe-perm"], cwd=EDEX_DIR, check=True, timeout=600, capture_output=True)
                    log_message("npm bagimliliklari yuklendi")
                    break
                except Exception as e:
                    if attempt == 1:
                        log_message(f"npm bagimliliklari yuklenemedi: {e}")
                        raise Exception(f"npm bagimliliklari yuklenemedi: {e}")
                    time.sleep(2)
            if not os.path.exists(os.path.join(EDEX_DIR, "node_modules")):
                raise Exception("npm bagimliliklari dogrulanamadi")
        except Exception as e:
            log_message(f"npm bagimliliklari yuklenemedi: {e}")
            raise Exception(f"npm bagimliliklari yuklenemedi: {e}")

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
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    settings.update(existing)
                except Exception as e:
                    log_message(f"Mevcut ayarlar okunamadi: {e}")
            with open("/tmp/settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            if not os.path.exists("/tmp/settings.json"):
                raise Exception("Gecici ayar dosyasi olusturulamadi")
            subprocess.run(["sudo", "mv", "/tmp/settings.json", settings_path], check=True, timeout=5)
            subprocess.run(["sudo", "chmod", "644", settings_path], check=True, timeout=5)
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
            xorg_conf = "/etc/X11/xorg.conf.d/10-optimizations.conf"
            subprocess.run(["sudo", "mkdir", "-p", os.path.dirname(xorg_conf)], check=True, timeout=5, capture_output=True)
            with open("/tmp/xorg.conf", "w") as f:
                f.write(
                    'Section "Device"\n'
                    '    Identifier "Card0"\n'
                    '    Driver "vesa"\n'
                    '    Option "AccelMethod" "exa"\n'
                    'EndSection\n'
                )
            if not os.path.exists("/tmp/xorg.conf"):
                raise Exception("Xorg yapilandirma dosyasi olusturulamadi")
            subprocess.run(["sudo", "mv", "/tmp/xorg.conf", xorg_conf], check=True, timeout=5)
            subprocess.run(["sudo", "chmod", "644", xorg_conf], check=True, timeout=5)
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
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                process.kill()
        subprocess.run(["sudo", "killall", "-q", "node"], capture_output=True, timeout=5)
        subprocess.run(["sudo", "killall", "-q", "Xorg"], capture_output=True, timeout=5)
        clean_temp()

    try:
        clean_temp()
        sub_statuses.append("X11 ortami hazirlaniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            os.environ["DISPLAY"] = ":0"
            result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, check=False, timeout=5)
            if result.returncode != 0:
                for attempt in range(2):
                    try:
                        subprocess.run(["sudo", "Xorg", "-quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
                        time.sleep(3)
                        result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, check=True, timeout=5)
                        break
                    except Exception as e:
                        if attempt == 1:
                            log_message(f"Xorg baslatma basarisiz: {e}")
                            raise Exception(f"Xorg baslatma basarisiz: {e}")
                        time.sleep(2)
            log_message("X11 ortami hazirlandi")
        except Exception as e:
            log_message(f"X11 baslatma basarisiz: {e}")
            raise Exception(f"X11 baslatma basarisiz: {e}")

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
                stdout, stderr = process.communicate(timeout=5)
                log_message(f"EDEX-UI baslatma basarisiz: {stderr}")
                raise Exception(f"EDEX-UI baslatilamadi: {stderr}")
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=True, timeout=5)
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
        try:
            script_path = "/mnt/sda1/kontrol.py"
            if not os.path.exists(script_path):
                raise Exception("kontrol.py bulunamadi")
            subprocess.run(["sudo", "chmod", "755", script_path], check=True, timeout=5)
            if os.path.exists(BOOT_SCRIPT):
                with open(BOOT_SCRIPT, "r") as f:
                    content = f.read()
                if script_path in content:
                    log_message("Otomatik baslama zaten ayarlanmis")
                else:
                    subprocess.run(["sudo", "cp", BOOT_SCRIPT, f"{BOOT_SCRIPT}.bak"], capture_output=True, timeout=5)
                    with open("/tmp/bootlocal.sh", "w") as f:
                        f.write(content.rstrip() + f"\npython3.9 {script_path} --skip-ui &\n")
                    subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", BOOT_SCRIPT], check=True, timeout=5)
                    subprocess.run(["sudo", "chmod", "755", BOOT_SCRIPT], check=True, timeout=5)
                    subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                    log_message("Otomatik baslama eklendi")
            else:
                with open("/tmp/bootlocal.sh", "w") as f:
                    f.write(f"#!/bin/sh\npython3.9 {script_path} --skip-ui &\n")
                subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", BOOT_SCRIPT], check=True, timeout=5)
                subprocess.run(["sudo", "chmod", "755", BOOT_SCRIPT], check=True, timeout=5)
                subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
                log_message("Yeni boot scripti olusturuldu")
            with open(BOOT_SCRIPT, "r") as f:
                if script_path not in f.read():
                    raise Exception("Boot scripti icerigi dogrulanamadi")
        except Exception as e:
            log_message(f"Otomatik baslama ayarlama basarisiz: {e}")
            raise Exception(f"Otomatik baslama ayarlama basarisiz: {e}")

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
        subprocess.run(["resize"], capture_output=True, timeout=5)
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
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
        draw_box(stdscr, box_start_row, box_start_col, box_height, box_width)

        title = "B E R K E  O S"
        title_col = (cols - len(title)) // 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(box_start_row + 1, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        status = "Beklemede"
        status_col = (cols - len(status)) // 2
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(box_start_row + box_height // 2, status_col, status)
        stdscr.attroff(curses.color_pair(6))
        stdscr.refresh()
        time.sleep(2)
    except Exception as e:
        log_message(f"Curses baslatilamadi: {e}")
        print(f"Curses baslatilamadi: {e}")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--network":
        network_setup(stdscr)
        sys.exit(0)

    skip_ui = "--skip-ui" in sys.argv
    if skip_ui:
        if os.path.exists(EDEX_DIR) and os.path.isfile(os.path.join(EDEX_DIR, "package.json")):
            start_edex_ui(None, [("EDEX-UI BASLATMA", "/")], 0)
        sys.exit(0)

    stages = [
        ("BAGIMLILIK YUKLEME", "/"),
        ("DISK YAPILANDIRMA", "-"),
        ("YEDEKLEME", "-"),
        ("EDEX-UI INDIRME", "-"),
        ("OZEL KOMUTLAR", "-"),
        ("EDEX-UI KURULUM", "-"),
        ("EDEX-UI BASLATMA", "-"),
        ("OTOMATIK BASLAMA", "-")
    ]
    functions = [
        install_dependencies,
        verify_disk,
        verify_backup,
        download_edex_ui,
        create_custom_commands,
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
        subprocess.run(["sudo", "killall", "-q", "node"], capture_output=True, timeout=5)
        subprocess.run(["sudo", "killall", "-q", "Xorg"], capture_output=True, timeout=5)
        clean_temp()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        log_message(f"{SYSTEM_NAME} basladi")
        curses.wrapper(main)
    except Exception as e:
        log_message(f"{SYSTEM_NAME} coktu: {e}")
        print(f"Hata: {e}\n{SYSTEM_NAME}")
        sys.exit(1)

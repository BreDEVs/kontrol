import os
import subprocess
import sys
import time
import curses
import json
import hashlib
import requests

# Configuration
SYSTEM_NAME = "Berke OS"
ROOT_DIR = "/mnt/sda1"
TCE_DIR = os.path.join(ROOT_DIR, "tce")
SYSTEM_DIR = os.path.join(ROOT_DIR, "system")
APPS_DIR = os.path.join(ROOT_DIR, "apps")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups")
LOG_FILE = os.path.join(SYSTEM_DIR, "logs", "install_log.txt")
EDEX_DIR = os.path.join(APPS_DIR, "edex-ui")
NODE_VERSION = "16.20.2"
EDEX_REPO = "https://github.com/GitSquared/edex-ui.git"
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "libX11", "libxss", "fontconfig", "git", "wget", "curl", "tar", "wireless_tools", "wpa_supplicant"]
REQUIRED_COMMANDS = ["python3.9", "wget", "curl", "git", "tar"]

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
        print(f"Log yazma hatası: {e}")

# File hash calculation
def calculate_file_hash(file_path):
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        log_message(f"Dosya karması hesaplanamadı: {file_path}: {e}")
        return None

# Check internet connection
def check_internet():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.RequestException:
        return False

# Network scanning and connection
def network_setup(stdscr):
    try:
        stdscr.clear()
        curses.curs_set(0)
        rows, cols = stdscr.getmaxyx()
        curses.start_color()
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        title = "BERKE OS"
        title_col = max(0, (cols - len(title)) // 2)
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(0, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(6))
        subtitle = "AĞ BAĞLANTISI"
        subtitle_col = max(0, (cols - len(subtitle)) // 2)
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(2, subtitle_col, subtitle, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        log_message("Ağ hazırlanıyor...")
        subprocess.run(["sudo", "rfkill", "unblock", "wifi"], capture_output=True, check=True, timeout=5)
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"], capture_output=True, check=True, timeout=5)
        log_message("Ağ taranıyor...")
        result = subprocess.run(["sudo", "iwlist", "wlan0", "scan"], capture_output=True, text=True, check=True, timeout=30)
        networks = []
        current_ssid = ""
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("ESSID:"):
                current_ssid = line.split(":", 1)[1].strip('"')
                if current_ssid:
                    networks.append(current_ssid)

        if not networks:
            raise Exception("Ağ bulunamadı")

        selected = 0
        while True:
            stdscr.clear()
            stdscr.attron(curses.color_pair(6))
            stdscr.addstr(0, title_col, title, curses.A_BOLD)
            stdscr.attroff(curses.color_pair(6))
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(2, subtitle_col, subtitle, curses.A_BOLD)
            stdscr.attroff(curses.color_pair(1))
            for i, net in enumerate(networks[:rows-5]):
                if i == selected:
                    stdscr.addstr(i+4, 2, f"> {net}", curses.A_REVERSE)
                else:
                    stdscr.addstr(i+4, 2, f"  {net}")
            stdscr.addstr(rows-2, 2, "Yukarı/Aşağı: Seçim, Enter: Bağlan, Q: Çıkış")
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(networks)-1:
                selected += 1
            elif key == 10:  # Enter
                break
            elif key == ord('q'):
                raise Exception("Kullanıcı ağ seçimini iptal etti")

        ssid = networks[selected]
        stdscr.clear()
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(0, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(6))
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(2, subtitle_col, subtitle, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))
        stdscr.addstr(4, 2, f"Seçilen ağ: {ssid}")
        stdscr.addstr(5, 2, "Şifre: ")
        curses.curs_set(1)
        curses.echo()
        password = stdscr.getstr(5, 10, 60).decode()
        curses.noecho()
        curses.curs_set(0)

        log_message(f"Ağ bağlantısı deneniyor: {ssid}")
        with open("/tmp/wpa.conf", "w") as f:
            f.write(f'network={{\nssid="{ssid}"\npsk="{password}"\n}}\n')
        subprocess.run(["sudo", "mv", "/tmp/wpa.conf", "/etc/wpa_supplicant.conf"], check=True, timeout=5)
        subprocess.run(["sudo", "chmod", "600", "/etc/wpa_supplicant.conf"], check=True, timeout=5)
        subprocess.run(["sudo", "killall", "-q", "wpa_supplicant"], capture_output=True, timeout=5)
        subprocess.run(["sudo", "wpa_supplicant", "-B", "-i", "wlan0", "-c", "/etc/wpa_supplicant.conf"], check=True, timeout=10)
        subprocess.run(["sudo", "udhcpc", "-i", "wlan0"], check=True, timeout=30)
        if not check_internet():
            raise Exception("Ağ bağlantısı başarısız")
        log_message(f"Ağ bağlantısı başarılı: {ssid}")
        stdscr.addstr(7, 2, "Bağlantı başarılı! Devam için bir tuşa basın...")
        stdscr.getch()
    except Exception as e:
        log_message(f"Ağ bağlantısı başarısız: {e}")
        stdscr.clear()
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(0, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(6))
        stdscr.addstr(4, 2, f"Hata: {str(e)}")
        stdscr.addstr(5, 2, "Çözüm: Wi-Fi adaptörünü kontrol edin veya kablolu bağlantı deneyin.")
        stdscr.addstr(6, 2, "Çıkmak için bir tuşa basın...")
        stdscr.getch()
        raise Exception(f"Ağ bağlantısı başarısız: {e}")

# Display error screen
def display_error(stdscr, stage, error_msg):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        curses.start_color()
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        
        title = "BERKE OS"
        title_col = max(0, (cols - len(title)) // 2)
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(0, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(6))
        
        error_title = "HATA ALINDI! BAŞLATILAMADI!"
        error_col = max(0, (cols - len(error_title)) // 2)
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(rows//2 - 4, error_col, error_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(3))
        
        stage_info = f"Aşama: {stage}"
        stage_col = max(0, (cols - len(stage_info)) // 2)
        stdscr.addstr(rows//2 - 2, stage_col, stage_info)
        
        error_info = f"Hata: {error_msg[:cols-4]}"
        error_col = max(0, (cols - len(error_info)) // 2)
        stdscr.addstr(rows//2, error_col, error_info)
        
        solution = "Çözüm: Logları kontrol edin (/mnt/sda1/system/logs/install_log.txt) veya sistemi yeniden başlatın."
        solution_col = max(0, (cols - len(solution)) // 2)
        stdscr.addstr(rows//2 + 2, solution_col, solution)
        
        stdscr.addstr(rows//2 + 4, 2, "Çıkmak için bir tuşa basın")
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        log_message(f"Hata ekranı gösterilemedi: {e}")
        print(f"HATA ALINDI! BAŞLATILAMADI!\nAşama: {stage}\nHata: {error_msg}")
    sys.exit(1)

# Display main screen
def display_main(stdscr, stages, current_stage, sub_status):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        
        curses.start_color()
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        
        title = "BERKE OS"
        title_col = max(0, (cols - len(title)) // 2)
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(0, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(6))

        sys_title = "Sistem başlatılıyor"
        sys_col = max(0, (cols - len(sys_title)) // 2)
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(4, sys_col, sys_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        for i, (stage_name, status) in enumerate(stages):
            stage_text = f"{i+1}. {stage_name} [{status}]"
            stage_col = max(0, (cols - len(stage_text)) // 2)
            if i == current_stage and status == "/":
                stdscr.attron(curses.color_pair(4))
                anim_chars = ["/", "-", "\\", "|"]
                for j in range(10):
                    stage_text = f"{i+1}. {stage_name} [{anim_chars[j % 4]}]"
                    stage_col = max(0, (cols - len(stage_text)) // 2)
                    stdscr.addstr(6 + i, stage_col, stage_text, curses.A_BOLD)
                    sub_status_text = f"Durum: {sub_status[:cols-10]}" if sub_status else ""
                    sub_status_col = max(0, (cols - len(sub_status_text)) // 2)
                    stdscr.addstr(7 + i, sub_status_col, sub_status_text, curses.A_BOLD)
                    stdscr.refresh()
                    time.sleep(0.2)
                stdscr.attroff(curses.color_pair(4))
            elif status == "HAZIR!":
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(6 + i, stage_col, stage_text)
                stdscr.attroff(curses.color_pair(2))
            else:
                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(6 + i, stage_col, stage_text)
                stdscr.attroff(curses.color_pair(5))
        
        if sub_status and stages[current_stage][1] == "HAZIR!":
            sub_status_text = f"Durum: {sub_status[:cols-10]}"
            sub_status_col = max(0, (cols - len(sub_status_text)) // 2)
            stdscr.attron(curses.color_pair(4))
            stdscr.addstr(7 + current_stage, sub_status_col, sub_status_text, curses.A_BOLD)
            stdscr.attroff(curses.color_pair(4))
        
        stdscr.refresh()
    except Exception as e:
        log_message(f"Ekran güncelleme başarısız: {e}")
        print(f"{title}\nSistem başlatılıyor\n" + "\n".join(f"{i+1}. {s[0]} [{s[1]}]" for i, s in enumerate(stages)))

# Install dependencies
def install_dependencies(stdscr, stages, current_stage):
    log_message("Bağımlılıklar kontrol ediliyor...")
    sub_statuses = []
    needs_internet = False

    for cmd in REQUIRED_COMMANDS:
        sub_statuses.append(f"{cmd} kontrol ediliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            result = subprocess.run(["which", cmd], capture_output=True, text=True, check=True, timeout=5)
            if cmd == "python3.9":
                subprocess.run([cmd, "--version"], capture_output=True, check=True, timeout=5)
            log_message(f"{cmd} bulundu: {result.stdout.strip()}")
        except Exception:
            needs_internet = True
            sub_statuses.append(f"{cmd} yükleniyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            try:
                result = subprocess.run(["sudo", "tce-load", "-w", "-i", cmd], capture_output=True, text=True, check=True, timeout=120)
                log_message(f"{cmd} yüklendi")
            except Exception as e:
                log_message(f"{cmd} yüklenemedi: {e}")
                display_error(stdscr, stages[current_stage][0], f"{cmd} yüklenemedi: {str(e)}")

    sub_statuses.append("Python requests kontrol ediliyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        import requests
        log_message("requests modülü bulundu")
    except ImportError:
        needs_internet = True
        sub_statuses.append("Python requests yükleniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            subprocess.run(["sudo", "pip3", "install", "requests"], check=True, timeout=120)
            log_message("requests modülü yüklendi")
        except Exception as e:
            log_message(f"requests modülü yüklenemedi: {e}")
            display_error(stdscr, stages[current_stage][0], f"requests modülü yüklenemedi: {str(e)}")

    for package in REQUIRED_TCE_PACKAGES:
        if package in REQUIRED_COMMANDS:
            continue
        sub_statuses.append(f"{package} kontrol ediliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            result = subprocess.run(["tce-status", "-i", package], capture_output=True, text=True, check=True, timeout=5)
            if result.returncode == 0 and package in result.stdout:
                log_message(f"{package} bulundu")
            else:
                needs_internet = True
                sub_statuses.append(f"{package} yükleniyor")
                display_main(stdscr, stages, current_stage, sub_statuses[-1])
                result = subprocess.run(["sudo", "tce-load", "-w", "-i", package], capture_output=True, text=True, check=True, timeout=120)
                log_message(f"{package} yüklendi")
            with open(os.path.join(TCE_DIR, "onboot.lst"), "a") as f:
                f.write(f"{package}\n")
            subprocess.run(["sudo", "chmod", "644", os.path.join(TCE_DIR, "onboot.lst")], check=True, timeout=5)
            subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
        except Exception as e:
            log_message(f"{package} yüklenemedi: {e}")
            display_error(stdscr, stages[current_stage][0], f"{package} yüklenemedi: {str(e)}")

    sub_statuses.append("Node.js kontrol ediliyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True, timeout=5)
        npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, check=True, timeout=5)
        log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} bulundu")
    except Exception:
        needs_internet = True
        sub_statuses.append("Node.js yükleniyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        try:
            node_url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
            subprocess.run(["sudo", "curl", "-o", "/tmp/node.tar.xz", node_url], check=True, timeout=120)
            if not os.path.exists("/tmp/node.tar.xz"):
                raise Exception("Node.js arşivi indirilemedi")
            subprocess.run(["sudo", "tar", "-xJf", "/tmp/node.tar.xz", "-C", "/usr/local"], check=True, timeout=120)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/node", "/usr/local/bin/node"], check=True, timeout=5)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True, timeout=5)
            subprocess.run(["sudo", "rm", "-f", "/tmp/node.tar.xz"], check=True, timeout=5)
            if subprocess.run(["npm", "-v"], capture_output=True, timeout=5).returncode != 0:
                raise Exception("npm doğrulaması başarısız")
            log_message("Node.js ve npm yüklendi")
        except Exception as e:
            log_message(f"Node.js yüklenemedi: {e}")
            display_error(stdscr, stages[current_stage][0], f"Node.js yüklenemedi: {str(e)}")

    if needs_internet:
        sub_statuses.append("İnternet bağlantısı kontrol ediliyor")
        display_main(stdscr, stages, current_stage, sub_statuses[-1])
        if not check_internet():
            sub_statuses.append("İnternet bağlantısı kuruluyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            network_setup(stdscr)

    stages[current_stage] = (stages[current_stage][0], "HAZIR!")
    display_main(stdscr, stages, current_stage, "Bağımlılıklar tamamlandı")

# Verify and setup disk
def verify_disk(stdscr, stages, current_stage):
    log_message("Disk doğrulanıyor...")
    sub_statuses = []

    sub_statuses.append("Disk dizini oluşturuluyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        subprocess.run(["sudo", "mkdir", "-p", ROOT_DIR], check=True, timeout=5)
        subprocess.run(["sudo", "chmod", "755", ROOT_DIR], check=True, timeout=5)
    except Exception as e:
        log_message(f"Disk dizini oluşturulamadı: {e}")
        display_error(stdscr, stages[current_stage][0], f"Disk dizini oluşturulamadı: {str(e)}")

    sub_statuses.append("Disk bağlanıyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        result = subprocess.run(["mountpoint", "-q", ROOT_DIR], capture_output=True, check=False, timeout=5)
        if result.returncode != 0:
            try:
                subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True, timeout=10)
            except Exception:
                log_message("Disk bağlama başarısız, biçimlendirme deneniyor...")
                subprocess.run(["sudo", "mkfs.ext4", "-F", "/dev/sda1"], check=True, timeout=60)
                subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True, timeout=10)
        subprocess.run(["sudo", "mount", "-o", "remount,rw", ROOT_DIR], check=True, timeout=5)
    except Exception as e:
        log_message(f"Disk bağlama başarısız: {e}")
        display_error(stdscr, stages[current_stage][0], f"Disk bağlama başarısız: {str(e)}")

    sub_statuses.append("Dizinler oluşturuluyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        dirs = [TCE_DIR, SYSTEM_DIR, APPS_DIR, BACKUP_DIR, os.path.join(SYSTEM_DIR, "logs")]
        for d in dirs:
            subprocess.run(["sudo", "mkdir", "-p", d], check=True, timeout=5)
            subprocess.run(["sudo", "chmod", "755", d], check=True, timeout=5)
    except Exception as e:
        log_message(f"Dizin oluşturma başarısız: {e}")
        display_error(stdscr, stages[current_stage][0], f"Dizin oluşturma başarısız: {str(e)}")

    stages[current_stage] = (stages[current_stage][0], "HAZIR!")
    display_main(stdscr, stages, current_stage, "Disk hazır")

# Verify backup
def verify_backup(stdscr, stages, current_stage):
    log_message("Sistem yedekleniyor...")
    sub_statuses = []

    sub_statuses.append("Yedek dizini oluşturuluyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        subprocess.run(["sudo", "mkdir", "-p", BACKUP_DIR], check=True, timeout=5)
        subprocess.run(["sudo", "chmod", "755", BACKUP_DIR], check=True, timeout=5)
    except Exception as e:
        log_message(f"Yedek dizini oluşturulamadı: {e}")
        display_error(stdscr, stages[current_stage][0], f"Yedek dizini oluşturulamadı: {str(e)}")

    sub_statuses.append("Dosyalar yedekleniyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.tar.gz")
        dirs_to_backup = [SYSTEM_DIR, APPS_DIR, TCE_DIR]
        subprocess.run(["sudo", "tar", "-czf", backup_file] + dirs_to_backup, check=True, timeout=300)
        if not os.path.exists(backup_file):
            raise Exception("Yedek dosyası oluşturulmadı")
    except Exception as e:
        log_message(f"Yedekleme başarısız: {e}")
        display_error(stdscr, stages[current_stage][0], f"Yedekleme başarısız: {str(e)}")

    sub_statuses.append("Yedek doğrulanıyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        backup_hash = calculate_file_hash(backup_file)
        if not backup_hash:
            raise Exception("Yedek doğrulaması başarısız")
        log_message(f"Yedek oluşturuldu: {backup_file}, SHA256: {backup_hash}")
        with open(os.path.join(BACKUP_DIR, "backup_log.txt"), "a") as f:
            f.write(f"{timestamp}: {backup_file}, SHA256: {backup_hash}\n")
        subprocess.run(["sudo", "chmod", "644", os.path.join(BACKUP_DIR, "backup_log.txt")], check=True, timeout=5)
        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
    except Exception as e:
        log_message(f"Yedek doğrulama başarısız: {e}")
        display_error(stdscr, stages[current_stage][0], f"Yedek doğrulama başarısız: {str(e)}")

    stages[current_stage] = (stages[current_stage][0], "HAZIR!")
    display_main(stdscr, stages, current_stage, "Yedekleme tamamlandı")

# Download EDEX-UI
def download_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI indiriliyor...")
    sub_statuses = []

    sub_statuses.append("EDEX-UI varlığı kontrol ediliyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        if os.path.exists(EDEX_DIR) and os.path.isfile(os.path.join(EDEX_DIR, "package.json")):
            log_message("EDEX-UI zaten mevcut")
        else:
            if not check_internet():
                sub_statuses.append("İnternet bağlantısı kuruluyor")
                display_main(stdscr, stages, current_stage, sub_statuses[-1])
                network_setup(stdscr)
            sub_statuses.append("EDEX-UI klonlanıyor")
            display_main(stdscr, stages, current_stage, sub_statuses[-1])
            subprocess.run(["sudo", "git", "clone", EDEX_REPO, EDEX_DIR], check=True, timeout=360)
            subprocess.run(["sudo", "chmod", "-R", "755", EDEX_DIR], check=True, timeout=5)
            log_message("EDEX-UI klonlandı")
        if not os.path.exists(os.path.join(EDEX_DIR, "package.json")):
            raise Exception("package.json bulunamadı")
    except Exception as e:
        log_message(f"EDEX-UI indirme başarısız: {e}")
        display_error(stdscr, stages[current_stage][0], f"EDEX-UI indirme başarısız: {str(e)}")

    stages[current_stage] = (stages[current_stage][0], "HAZIR!")
    display_main(stdscr, stages, current_stage, "EDEX-UI indirildi")

# Install EDEX-UI
def install_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI kuruluyor...")
    sub_statuses = []

    sub_statuses.append("npm bağımlılıkları yükleniyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        subprocess.run(["sudo", "npm", "install", "--unsafe-perm"], cwd=EDEX_DIR, check=True, timeout=600, text=True, capture_output=True)
        log_message("npm bağımlılıkları yüklendi")
    except Exception as e:
        log_message(f"npm bağımlılıkları yüklenemedi: {e}")
        display_error(stdscr, stages[current_stage][0], f"npm bağımlılıkları yüklenemedi: {str(e)}")

    sub_statuses.append("Ayarlar özelleştiriliyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        settings_path = os.path.join(EDEX_DIR, "settings.json")
        settings = {
            "shell": f"{SYSTEM_NAME} Terminal",
            "theme": "tron",
            "window": {"title": f"{SYSTEM_NAME}"},
            "performance": {"lowPowerMode": False, "gpuAcceleration": True}
        }
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                settings.update(existing)
            except Exception:
                log_message("Mevcut ayarlar okunamadı, yeni oluşturuluyor")
        with open("/tmp/settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        if not os.path.exists("/tmp/settings.json"):
            raise Exception("Geçici ayar dosyası oluşturulmadı")
        subprocess.run(["sudo", "mv", "/tmp/settings.json", settings_path], check=True, timeout=5)
        subprocess.run(["sudo", "chmod", "644", settings_path], check=True, timeout=5)
        subprocess.run(["sudo", "rm", "-f", "/tmp/settings.json"], check=True, timeout=5)
        log_message("EDEX-UI ayarları özelleştirildi")
    except Exception as e:
        log_message(f"EDEX-UI ayarları özelleştirilemedi: {str(e)}")
        display_error(stdscr, stages[current_stage][0], f"EDEX-UI ayarları özelleştirilemedi: {str(e)}")

    sub_statuses.append("Xorg ayarları optimize ediliyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        xorg_conf = "/etc/X11/xorg.conf.d/10-optimizations.conf"
        subprocess.run(["sudo", "mkdir", "-p", os.path.dirname(xorg_conf)], check=True, timeout=5)
        with open("/tmp/xorg.conf", "w") as f:
            f.write(
                'Section "Device"\n'
                '    Identifier "Card0"\n'
                '    Driver "vesa"\n'
                '    Option "AccelMethod" "exa"\n'
                'EndSection\n'
            )
        if not os.path.exists("/tmp/xorg.conf"):
            raise Exception("Xorg yapılandırma dosyası oluşturulmadı")
        subprocess.run(["sudo", "mv", "/tmp/xorg.conf", xorg_conf], check=True, timeout=5)
        subprocess.run(["sudo", "644", xorg_conf], check=True, timeout=5)
        subprocess.run(["sudo", "rm", "-f", "/tmp/xorg.conf"], check=True, timeout=5)
        log_message("Xorg optimize edildi")
    except Exception as e:
        log_message(f"Xorg optimizasyonu başarısız: {e}")
        display_error(stdscr, stages[current_stage][0], f"Xorg optimizasyonu başarısız: {str(e)}")

    stages[current_stage] = (stages[current_stage][0], "HAZIR!")
    display_main(stdscr, stages, current_stage, "EDEX-UI kuruldu")

# Start EDEX-UI
def start_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI başlatılıyor...")
    sub_statuses = []

    sub_statuses.append("X11 ortamı hazırlanıyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        os.environ["DISPLAY"] = ":0"
        result = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, timeout=5)
        if result.returncode != 0:
            subprocess.run(["sudo", "Xorg", "-quiet", "&"], check=True, timeout=10)
            time.sleep(2)
        log_message("X11 ortamı hazırlandı")
    except Exception as e:
        log_message(f"X11 başlatma başarısız: {e}")
        display_error(stdscr, stages[current_stage][0], f"X11 başlatma başarısız: {str(e)}")

    sub_statuses.append("EDEX-UI çalıştırılıyor")
    display_main(stdscr, stages, current_stage, sub_statuses[-1])
    try:
        process = subprocess.Popen(["sudo", "npm", "start", "--unsafe-perm"], cwd=EDEX_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(5)
        if process.poll() is None:
            stdout, stderr = process.communicate()
            raise Exception(f"EDEX-UI başlatılamadı: {stderr}")
        log_message("EDEX-UI başlatıldı")
    except Exception as e:
        log_message(f"EDEX-UI başlatma başarısız: {str(e)}")
        display_error(stdscr, stages[current_stage][0], f"EDEX-UI başlatma başarısız: {str(e)}")

    stages[current_stage] = (stages[current_stage][0], "HAZIR!")
    display_main(stdscr, stages, current_stage, "EDEX-UI başlatıldı")

# Main function
def main(stdscr):
    try:
        curses.curs_set(0)
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        curses.start_color()
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        title = "BERKE OS"
        title_col = max(0, (cols - len(title)) // 2)
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(rows//2 - 2, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(6))
        status = "Beklemede"
        status_col = max(0, (cols - len(status)) // 2)
        stdscr.attron(curses.color_pair(5))
        stdscr.addstr(rows//2, status_col, status)
        stdscr.attroff(curses.color_pair(5))
        stdscr.refresh()
        time.sleep(2)
    except Exception as e:
        log_message(f"Curses başlatılamadı: {e}")
        print(f"Curses başlatılamadı: {e}")
        sys.exit(1)

    stages = [
        ("BAĞIMLILIK YÜKLEME", "/"),
        ("DISK YAPILANDIRMA", "-"),
        ("YEDEKLEME", "-"),
        ("EDEX-UI INDIRME", "-"),
        ("EDEX-UI KURULUM", "-"),
        ("EDEX-UI BAŞLATMA", "-")
    ]
    functions = [
        install_dependencies,
        verify_disk,
        verify_backup,
        download_edex_ui,
        install_edex_ui,
        start_edex_ui
    ]

    for i, func in enumerate(functions):
        try:
            func(stdscr, stages, i)
        except Exception as e:
            log_message(f"Aşama başarısız: {stages[i][0]}: {e}")
            display_error(stdscr, stages[i][0], str(e))

if __name__ == "__main__":
    try:
        log_message(f"{SYSTEM_NAME} başladı")
        curses.wrapper(main)
    except Exception as e:
        log_message(f"{SYSTEM_NAME} çöktü: {e}")
        print(f"Hata: {e}\n{SYSTEM_NAME}")
        sys.exit(1)

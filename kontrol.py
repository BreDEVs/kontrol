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
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "libX11", "libxss", "fontconfig", "git", "wireless_tools", "wpa_supplicant"]

# Logging
def log_message(message):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        subprocess.run(["sudo", "chmod", "755", os.path.dirname(LOG_FILE)], check=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
        subprocess.run(["sudo", "chmod", "644", LOG_FILE], check=True)
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
        log_message(f"Dosya karmasi hesaplanamadi: {file_path}: {e}")
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
        title = "AG BAGLANTISI"
        title_col = max(0, (cols - len(title)) // 2)
        stdscr.addstr(0, title_col, title, curses.A_BOLD)

        log_message("Ag taraniyor...")
        result = subprocess.run(["sudo", "iwlist", "wlan0", "scan"], capture_output=True, text=True, timeout=30)
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
            stdscr.addstr(0, title_col, title, curses.A_BOLD)
            for i, net in enumerate(networks[:rows-5]):
                if i == selected:
                    stdscr.addstr(i+2, 2, f"> {net}", curses.A_REVERSE)
                else:
                    stdscr.addstr(i+2, 2, f"  {net}")
            stdscr.addstr(rows-2, 2, "Yukari/Asagi: Secim, Enter: Baglan, Q: Cikis")
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(networks)-1:
                selected += 1
            elif key == 10:  # Enter
                break
            elif key == ord('q'):
                raise Exception("Kullanici ag secimini iptal etti")

        ssid = networks[selected]
        stdscr.clear()
        stdscr.addstr(0, title_col, title, curses.A_BOLD)
        stdscr.addstr(2, 2, f"Secilen ag: {ssid}")
        stdscr.addstr(3, 2, "Sifre: ")
        curses.curs_set(1)
        curses.echo()
        password = stdscr.getstr(3, 10, 60).decode()
        curses.noecho()
        curses.curs_set(0)

        log_message(f"Ag baglantisi deneniyor: {ssid}")
        with open("/tmp/wpa.conf", "w") as f:
            f.write(f'network={{\nssid="{ssid}"\npsk="{password}"\n}}\n')
        subprocess.run(["sudo", "mv", "/tmp/wpa.conf", "/etc/wpa_supplicant.conf"], check=True)
        subprocess.run(["sudo", "chmod", "600", "/etc/wpa_supplicant.conf"], check=True)
        subprocess.run(["sudo", "killall", "wpa_supplicant"], capture_output=True)
        subprocess.run(["sudo", "wpa_supplicant", "-B", "-i", "wlan0", "-c", "/etc/wpa_supplicant.conf"], check=True)
        subprocess.run(["sudo", "udhcpc", "-i", "wlan0"], check=True, timeout=30)
        if not check_internet():
            raise Exception("Ag baglantisi basarisiz")
        log_message(f"Ag baglantisi basarili: {ssid}")
        stdscr.addstr(5, 2, "Baglanti basarili! Devam etmek icin bir tusa basin...")
        stdscr.getch()
    except Exception as e:
        log_message(f"Ag baglantisi basarisiz: {e}")
        stdscr.clear()
        stdscr.addstr(0, title_col, title, curses.A_BOLD)
        stdscr.addstr(2, 2, f"Hata: {str(e)}")
        stdscr.addstr(4, 2, "Cikmak icin bir tusa basin...")
        stdscr.getch()
        raise Exception(f"Ag baglantisi basarisiz: {e}")

# Display error screen
def display_error(stdscr, stage, error_msg):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        curses.start_color()
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        
        error_title = "HATA ALINDI! BASLATILAMADI!"
        error_col = max(0, (cols - len(error_title)) // 2)
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(rows//2 - 2, error_col, error_title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(3))
        
        stage_info = f"Asama: {stage}"
        stage_col = max(0, (cols - len(stage_info)) // 2)
        stdscr.addstr(rows//2, stage_col, stage_info)
        
        error_info = f"Hata: {error_msg}"
        error_col = max(0, (cols - len(error_info)) // 2)
        stdscr.addstr(rows//2 + 2, error_col, error_info)
        
        stdscr.addstr(rows//2 + 4, max(0, (cols - 25) // 2), "Cikmak icin bir tusa basin...")
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        log_message(f"Hata ekrani gosterilemedi: {e}")
        print(f"HATA ALINDI! BASLATILAMADI!\nAsama: {stage}\nHata: {error_msg}")
    sys.exit(1)

# Display main screen
def display_main(stdscr, stages, current_stage):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        compact_ascii = (
            " ____          _          ___ ____  \n"
            "| __ )  ___ __| | ___    / _ \\___ \\ \n"
            "|  _ \\ / __/ _` |/ _ \\  | | | |__) |\n"
            "| |_) | (_| (_| |  __/  | |_| / __/ \n"
            "|____/ \\___\\__,_|\\___|   \\___/____|\n"
        )
        lines = compact_ascii.splitlines()
        max_line_len = max(len(line.rstrip()) for line in lines)
        start_row = max(0, (rows - len(lines) - len(stages) - 5) // 2)
        start_col = max(0, (cols - max_line_len) // 2)
        
        curses.start_color()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Turuncu yerine sarı
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        
        # Ana başlık
        title = "YUKLEME ARACI"
        title_col = max(0, (cols - len(title)) // 2)
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(start_row, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))

        # ASCII
        if rows >= len(lines) + len(stages) + 5 and cols >= max_line_len:
            for i, line in enumerate(lines):
                stdscr.addstr(start_row + i + 2, start_col, line.rstrip())
        else:
            for i, line in enumerate(lines):
                stdscr.addstr(i + 2, 0, line.rstrip()[:cols])

        # Sistem başlatılıyor
        sys_title = "Sistem baslatiliyor"
        sys_col = max(0, (cols - len(sys_title)) // 2)
        stdscr.addstr(start_row + len(lines) + 3, sys_col, sys_title, curses.A_BOLD)

        # Aşamalar
        for i, (stage_name, status) in enumerate(stages):
            stage_text = f"{i+1}. {stage_name} [{status}]"
            stage_col = max(0, (cols - len(stage_text)) // 2)
            if i == current_stage and status == "/":
                anim_chars = ["/", "-", "\\", "|"]
                for j in range(10):  # 2 saniye animasyon
                    stage_text = f"{i+1}. {stage_name} [{anim_chars[j % 4]}]"
                    stage_col = max(0, (cols - len(stage_text)) // 2)
                    stdscr.addstr(start_row + len(lines) + 5 + i, stage_col, stage_text)
                    stdscr.refresh()
                    time.sleep(0.2)
            elif status == "HAZIR!":
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(start_row + len(lines) + 5 + i, stage_col, stage_text, curses.A_BOLD)
                stdscr.attroff(curses.color_pair(2))
            else:
                stdscr.addstr(start_row + len(lines) + 5 + i, stage_col, stage_text)
        stdscr.refresh()
    except Exception as e:
        log_message(f"Ekran guncelleme basarisiz: {e}")
        print(f"YUKLEME ARACI\n{compact_ascii.rstrip()}\nSistem baslatiliyor\n" + "\n".join(f"{i+1}. {s[0]} [{s[1]}]" for i, s in enumerate(stages)))

# Install dependencies
def install_dependencies(stdscr, stages, current_stage):
    log_message("Bagimliliklar yukleniyor...")
    try:
        if not check_internet():
            network_setup(stdscr)
        
        # Install TCZ packages
        for package in REQUIRED_TCE_PACKAGES:
            result = subprocess.run(["sudo", "tce-load", "-w", "-i", package], capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise Exception(f"{package} yuklenemedi: {result.stderr}")
            log_message(f"{package} yuklendi")
            with open(os.path.join(TCE_DIR, "onboot.lst"), "a") as f:
                f.write(f"{package}\n")
            subprocess.run(["sudo", "chmod", "644", os.path.join(TCE_DIR, "onboot.lst")], check=True)
            subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)

        # Install requests
        import requests
        log_message("requests modulu yuklu")
    except ImportError:
        try:
            subprocess.run(["sudo", "pip3", "install", "requests"], check=True, timeout=120)
            log_message("requests modulu yuklendi")
        except Exception as e:
            log_message(f"requests modulu yuklenemedi: {e}")
            raise Exception(f"requests modulu yuklenemedi: {e}")

    # Install Node.js
    try:
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, timeout=5)
        npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and npm_result.returncode == 0:
            log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} yuklu")
        else:
            raise Exception("Node.js veya npm eksik")
    except Exception:
        log_message("Node.js veya npm yuklu degil, kuruluyor...")
        node_url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
        subprocess.run(["sudo", "wget", node_url, "-O", "/tmp/node.tar.xz"], check=True, timeout=120)
        subprocess.run(["sudo", "tar", "-xJf", "/tmp/node.tar.xz", "-C", "/usr/local"], check=True, timeout=120)
        subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/node", "/usr/local/bin/node"], check=True)
        subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True)
        subprocess.run(["sudo", "rm", "-f", "/tmp/node.tar.xz"], check=True)
        if subprocess.run(["npm", "-v"], capture_output=True, timeout=5).returncode != 0:
            raise Exception("npm dogrulama basarisiz")
        log_message("Node.js ve npm manuel yuklendi")

    stages[current_stage] = (stages[current_stage][0], "HAZIR!")
    display_main(stdscr, stages, current_stage)

# Verify and setup disk
def verify_disk(stdscr, stages, current_stage):
    log_message("Disk dogrulaniyor...")
    try:
        subprocess.run(["sudo", "mkdir", "-p", ROOT_DIR], check=True)
        subprocess.run(["sudo", "chmod", "755", ROOT_DIR], check=True)
        try:
            subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True)
        except subprocess.CalledProcessError:
            log_message("Disk baglama basarisiz, bicimlendirme deneniyor...")
            subprocess.run(["sudo", "mkfs.ext4", "/dev/sda1"], check=True)
            subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True)
        subprocess.run(["sudo", "mount", "-o", "remount,rw", ROOT_DIR], check=True)
        dirs = [TCE_DIR, SYSTEM_DIR, APPS_DIR, BACKUP_DIR, os.path.join(SYSTEM_DIR, "logs")]
        for d in dirs:
            subprocess.run(["sudo", "mkdir", "-p", d], check=True)
            subprocess.run(["sudo", "chmod", "755", d], check=True)
        log_message("Disk dogrulama tamamlandi")
        stages[current_stage] = (stages[current_stage][0], "HAZIR!")
        display_main(stdscr, stages, current_stage)
    except Exception as e:
        log_message(f"Disk dogrulama basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))

# Verify backup
def verify_backup(stdscr, stages, current_stage):
    log_message("Sistem yedekleniyor...")
    try:
        subprocess.run(["sudo", "mkdir", "-p", BACKUP_DIR], check=True)
        subprocess.run(["sudo", "chmod", "755", BACKUP_DIR], check=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"berkeos_backup_{timestamp}.tar.gz")
        dirs_to_backup = [SYSTEM_DIR, APPS_DIR, TCE_DIR]
        subprocess.run(["sudo", "tar", "-czf", backup_file] + dirs_to_backup, check=True, timeout=300)
        backup_hash = calculate_file_hash(backup_file)
        if not backup_hash:
            raise Exception("Yedek dogrulama basarisiz")
        log_message(f"Yedek olusturuldu: {backup_file}, SHA256: {backup_hash}")
        with open(os.path.join(BACKUP_DIR, "backup_log.txt"), "a") as f:
            f.write(f"{timestamp}: {backup_file}, SHA256: {backup_hash}\n")
        subprocess.run(["sudo", "chmod", "644", os.path.join(BACKUP_DIR, "backup_log.txt")], check=True)
        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
        stages[current_stage] = (stages[current_stage][0], "HAZIR!")
        display_main(stdscr, stages, current_stage)
    except Exception as e:
        log_message(f"Yedekleme basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))

# Download EDEX-UI
def download_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI indiriliyor...")
    try:
        if not os.path.exists(EDEX_DIR):
            subprocess.run(["sudo", "git", "clone", EDEX_REPO, EDEX_DIR], check=True, timeout=300)
            subprocess.run(["sudo", "chmod", "-R", "755", EDEX_DIR], check=True)
            log_message("EDEX-UI klonlandi")
        else:
            log_message("EDEX-UI zaten mevcut")
        if not os.path.exists(os.path.join(EDEX_DIR, "package.json")):
            raise Exception("package.json bulunamadi")
        stages[current_stage] = (stages[current_stage][0], "HAZIR!")
        display_main(stdscr, stages, current_stage)
    except Exception as e:
        log_message(f"EDEX-UI indirme basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))

# Install EDEX-UI
def install_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI kuruluyor...")
    try:
        subprocess.run(["sudo", "npm", "install"], cwd=EDEX_DIR, check=True, timeout=600)
        log_message("npm bagimliliklari yuklendi")

        settings_path = os.path.join(EDEX_DIR, "settings.json")
        settings = {
            "shell": f"{SYSTEM_NAME} Terminal",
            "theme": "tron",
            "window": {"title": f"{SYSTEM_NAME} EDEX-UI"},
            "performance": {"lowPowerMode": False, "gpuAcceleration": True}
        }
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                existing = json.load(f)
            settings.update(existing)
        with open("/tmp/settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        subprocess.run(["sudo", "mv", "/tmp/settings.json", settings_path], check=True)
        subprocess.run(["sudo", "chmod", "644", settings_path], check=True)
        subprocess.run(["sudo", "rm", "-f", "/tmp/settings.json"], check=True)
        log_message("EDEX-UI ayarlari ozellestirildi")

        xorg_conf = "/etc/X11/xorg.conf.d/10-optimizations.conf"
        subprocess.run(["sudo", "mkdir", "-p", os.path.dirname(xorg_conf)], check=True)
        with open("/tmp/xorg.conf", "w") as f:
            f.write(
                'Section "Device"\n'
                '    Identifier "Card0"\n'
                '    Driver "vesa"\n'
                '    Option "AccelMethod" "exa"\n'
                'EndSection\n'
            )
        subprocess.run(["sudo", "mv", "/tmp/xorg.conf", xorg_conf], check=True)
        subprocess.run(["sudo", "chmod", "644", xorg_conf], check=True)
        subprocess.run(["sudo", "rm", "-f", "/tmp/xorg.conf"], check=True)
        log_message("Xorg optimize edildi")

        stages[current_stage] = (stages[current_stage][0], "HAZIR!")
        display_main(stdscr, stages, current_stage)
    except Exception as e:
        log_message(f"EDEX-UI kurulumu basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))

# Start EDEX-UI
def start_edex_ui(stdscr, stages, current_stage):
    log_message("EDEX-UI baslatiliyor...")
    try:
        process = subprocess.Popen(["sudo", "npm", "start"], cwd=EDEX_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)
        if process.poll() is None:
            log_message("EDEX-UI baslatildi")
            stages[current_stage] = (stages[current_stage][0], "HAZIR!")
            display_main(stdscr, stages, current_stage)
        else:
            stdout, stderr = process.communicate()
            raise Exception(f"EDEX-UI baslatilamadi: {stderr.decode()}")
    except Exception as e:
        log_message(f"EDEX-UI baslatma basarisiz: {e}")
        display_error(stdscr, stages[current_stage][0], str(e))

# Main function
def main(stdscr):
    try:
        curses.curs_set(0)
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        title = "YUKLEME ARACI"
        title_col = max(0, (cols - len(title)) // 2)
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(rows//2 - 2, title_col, title, curses.A_BOLD)
        stdscr.attroff(curses.color_pair(1))
        status = "Beklemede"
        status_col = max(0, (cols - len(status)) // 2)
        stdscr.addstr(rows//2, status_col, status)
        stdscr.refresh()
        time.sleep(2)
    except Exception as e:
        log_message(f"Curses baslatilamadi: {e}")
        print(f"Curses baslatilamadi: {e}")
        sys.exit(1)

    stages = [
        ("BAGIMLILIK YUKLEME", "/"),
        ("DISK YAPILANDIRMA", "-"),
        ("YEDEKLEME", "-"),
        ("EDEX-UI INDIRME", "-"),
        ("EDEX-UI KURULUM", "-"),
        ("EDEX-UI BASLATMA", "-")
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
        display_main(stdscr, stages, i)
        try:
            func(stdscr, stages, i)
        except Exception as e:
            log_message(f"Asama basarisiz: {stages[i][0]}: {e}")
            display_error(stdscr, stages[i][0], str(e))

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        log_message(f"{SYSTEM_NAME} coktu: {e}")
        print(f"Hata: {e}\nBerke OS")
        sys.exit(1)

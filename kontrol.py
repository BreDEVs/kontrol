import os
import subprocess
import sys
import time
import curses
import json
import hashlib

# Configuration
SYSTEM_NAME = "Berke OS"
ROOT_DIR = "/mnt/sda1"
TCE_DIR = os.path.join(ROOT_DIR, "tce")
SYSTEM_DIR = os.path.join(ROOT_DIR, "system")
APPS_DIR = os.path.join(ROOT_DIR, "apps")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups")
LOG_FILE = os.path.join(SYSTEM_DIR, "logs", "install_log.txt")
EDEX_DIR = os.path.join(APPS_DIR, "edex-ui")
CONFIG_FILE = os.path.join(SYSTEM_DIR, "berkeos_config.json")
TCE_REPO = "http://repo.tinycorelinux.net"
NODE_VERSION = "16.20.2"
EDEX_REPO = "https://github.com/GitSquared/edex-ui.git"
BOOTLOCAL_FILE = "/opt/bootlocal.sh"
BOOTLOCAL_BACKUP = os.path.join(BACKUP_DIR, "bootlocal.sh.bak")
REQUIRED_TCE_PACKAGES = ["python3.9", "Xorg-7.7", "libX11", "libxss", "fontconfig", "git", "wireless_tools", "wpa_supplicant"]

# Install requests if missing
try:
    import requests
except ImportError:
    subprocess.run(["sudo", "pip3", "install", "requests"], check=True)
    import requests

# Logging
def log_message(message):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        subprocess.run(["sudo", "chmod", "755", os.path.dirname(LOG_FILE)], check=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
        subprocess.run(["sudo", "chmod", "644", LOG_FILE], check=True)
    except Exception as e:
        log_message(f"Log yazma hatasi: {e}")

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

# Verify and setup disk
def verify_disk(stdscr):
    log_message("Disk dogrulaniyor...")
    try:
        subprocess.run(["sudo", "mkdir", "-p", ROOT_DIR], check=True)
        subprocess.run(["sudo", "chmod", "755", ROOT_DIR], check=True)
        try:
            subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True)
        except subprocess.CalledProcessError:
            log_message("Disk baglama basarisiz, bicimlendirme deneniyor...")
            try:
                subprocess.run(["sudo", "mkfs.ext4", "/dev/sda1"], check=True)
                subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True)
            except Exception as e:
                log_message(f"Disk bicimlendirme basarisiz: {e}")
                display_status(stdscr, "DISK YAPILANDIRMA", "disk baglaniyor", False, "Hata")
                return False
        subprocess.run(["sudo", "mount", "-o", "remount,rw", ROOT_DIR], check=True)
        dirs = [TCE_DIR, SYSTEM_DIR, APPS_DIR, BACKUP_DIR, os.path.join(SYSTEM_DIR, "logs")]
        for d in dirs:
            subprocess.run(["sudo", "mkdir", "-p", d], check=True)
            subprocess.run(["sudo", "chmod", "755", d], check=True)
        log_message("Disk dogrulama tamamlandi")
        display_status(stdscr, "DISK YAPILANDIRMA", "disk baglaniyor", True, "Yuklendi")
        return True
    except Exception as e:
        log_message(f"Disk dogrulama basarisiz: {e}")
        display_status(stdscr, "DISK YAPILANDIRMA", "disk baglaniyor", False, "Hata")
        return False

# Verify dependencies
def verify_dependencies(stdscr):
    log_message("Bagimliliklar dogrulaniyor...")
    try:
        import requests
        log_message("requests modulu yuklu")
    except ImportError:
        try:
            install_tce_package("python3.9-pip")
            subprocess.run(["sudo", "pip3", "install", "requests"], check=True, timeout=120)
            log_message("requests modulu yuklendi")
        except Exception as e:
            log_message(f"requests modulu yuklenemedi: {e}")
            display_status(stdscr, "BAGIMLILIK YUKLEME", "python modulleri yukleniyor", False, "Hata")
            return False

    try:
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, timeout=5)
        npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and npm_result.returncode == 0:
            log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} yuklu")
        else:
            raise Exception("Node.js veya npm eksik")
    except Exception:
        log_message("Node.js veya npm yuklu degil, kuruluyor...")
        try:
            node_url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
            subprocess.run(["sudo", "wget", node_url, "-O", "/tmp/node.tar.xz"], check=True, timeout=120)
            subprocess.run(["sudo", "tar", "-xJf", "/tmp/node.tar.xz", "-C", "/usr/local"], check=True, timeout=120)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/node", "/usr/local/bin/node"], check=True)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True)
            subprocess.run(["sudo", "rm", "-f", "/tmp/node.tar.xz"], check=True)
            log_message("Node.js ve npm manuel yuklendi")
        except Exception as e:
            log_message(f"Node.js ve npm kurulumu basarisiz: {e}")
            display_status(stdscr, "BAGIMLILIK YUKLEME", "nodejs yukleniyor", False, "Hata")
            return False
    display_status(stdscr, "BAGIMLILIK YUKLEME", "nodejs ve python modulleri yukleniyor", True, "Yuklendi")
    return True

# Install Tiny Core package
def install_tce_package(package_name):
    try:
        log_message(f"Yukleniyor: {package_name}")
        result = subprocess.run(["sudo", "tce-load", "-w", "-i", package_name], capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            log_message(f"{package_name} yuklendi")
            with open(os.path.join(TCE_DIR, "onboot.lst"), "a") as f:
                f.write(f"{package_name}\n")
            subprocess.run(["sudo", "chmod", "644", os.path.join(TCE_DIR, "onboot.lst")], check=True)
            subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
        else:
            log_message(f"{package_name} yuklenemedi: {result.stderr}")
    except Exception as e:
        log_message(f"Yukleme hatasi: {package_name}: {e}")

# Verify and install EDEX-UI
def verify_edex_ui(stdscr):
    log_message("EDEX-UI dogrulaniyor...")
    if not os.path.exists(EDEX_DIR):
        log_message("EDEX-UI klonlaniyor...")
        try:
            subprocess.run(["sudo", "git", "clone", EDEX_REPO, EDEX_DIR], check=True, timeout=300)
            subprocess.run(["sudo", "chmod", "-R", "755", EDEX_DIR], check=True)
            log_message("EDEX-UI klonlandi")
        except Exception as e:
            log_message(f"EDEX-UI klonlama basarisiz: {e}")
            display_status(stdscr, "EDEX-UI YUKLEME", "edex-ui indiriliyor", False, "Hata")
            return False

    package_json_path = os.path.join(EDEX_DIR, "package.json")
    if not os.path.exists(package_json_path):
        log_message("package.json bulunamadi")
        display_status(stdscr, "EDEX-UI YUKLEME", "edex-ui dosyalari dogrulaniyor", False, "Hata")
        return False

    try:
        subprocess.run(["sudo", "npm", "install"], cwd=EDEX_DIR, check=True, timeout=600)
        log_message("npm bagimliliklari yuklendi")
    except Exception as e:
        log_message(f"npm bagimliliklari yuklenemedi: {e}")
        display_status(stdscr, "EDEX-UI YUKLEME", "edex-ui kuruluyor", False, "Hata")
        return False

    settings_path = os.path.join(EDEX_DIR, "settings.json")
    try:
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
    except Exception as e:
        log_message(f"EDEX-UI ayarlari ozellestirilemedi: {e}")

    try:
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
    except Exception as e:
        log_message(f"Xorg optimizasyonu basarisiz: {e}")

    display_status(stdscr, "EDEX-UI YUKLEME", "edex-ui kuruluyor", True, "Yuklendi")
    return True

# Start EDEX-UI
def start_edex_ui(stdscr):
    log_message("EDEX-UI baslatiliyor...")
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            process = subprocess.Popen(["sudo", "npm", "start"], cwd=EDEX_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)
            if process.poll() is None:
                log_message("EDEX-UI baslatildi")
                display_status(stdscr, "EDEX-UI BASLATMA", "edex-ui calistiriliyor", True, "Yuklendi")
                return True
            else:
                stdout, stderr = process.communicate()
                log_message(f"EDEX-UI baslatilamadi (deneme {attempt + 1}/{max_attempts}): {stderr.decode()}")
        except Exception as e:
            log_message(f"EDEX-UI baslatilamadi (deneme {attempt + 1}/{max_attempts}): {e}")
        time.sleep(3)
    log_message("EDEX-UI baslatma basarisiz")
    display_status(stdscr, "EDEX-UI BASLATMA", "edex-ui calistiriliyor", False, "Hata")
    return False

# Verify backup
def verify_backup(stdscr):
    log_message("Sistem yedekleniyor...")
    try:
        subprocess.run(["sudo", "mkdir", "-p", BACKUP_DIR], check=True)
        subprocess.run(["sudo", "chmod", "755", BACKUP_DIR], check=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"berkeos_backup_{timestamp}.tar.gz")
        dirs_to_backup = [SYSTEM_DIR, APPS_DIR, TCE_DIR]
        subprocess.run(["sudo", "tar", "-czf", backup_file] + dirs_to_backup, check=True, timeout=300)
        backup_hash = calculate_file_hash(backup_file)
        if backup_hash:
            log_message(f"Yedek olusturuldu: {backup_file}, SHA256: {backup_hash}")
            with open(os.path.join(BACKUP_DIR, "backup_log.txt"), "a") as f:
                f.write(f"{timestamp}: {backup_file}, SHA256: {backup_hash}\n")
            subprocess.run(["sudo", "chmod", "644", os.path.join(BACKUP_DIR, "backup_log.txt")], check=True)
        else:
            log_message("Yedek dogrulama basarisiz")
            display_status(stdscr, "YEDEKLEME", "sistem yedekleniyor", False, "Hata")
            return False
        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
        display_status(stdscr, "YEDEKLEME", "sistem yedekleniyor", True, "Yuklendi")
        return True
    except Exception as e:
        log_message(f"Yedekleme basarisiz: {e}")
        display_status(stdscr, "YEDEKLEME", "sistem yedekleniyor", False, "Hata")
        return False

# Configure bootlocal.sh
def configure_bootlocal(stdscr):
    log_message("bootlocal.sh yapilandiriliyor...")
    try:
        if os.path.exists(BOOTLOCAL_FILE):
            subprocess.run(["sudo", "cp", BOOTLOCAL_FILE, BOOTLOCAL_BACKUP], check=True)
            subprocess.run(["sudo", "chmod", "644", BOOTLOCAL_BACKUP], check=True)
            log_message(f"bootlocal.sh yedegi alindi: {BOOTLOCAL_BACKUP}")

        bootlocal_content = (
            "#!/bin/sh\n"
            "# Berke OS Bootlocal Configuration\n"
            f"sudo tce-load -i python3.9\n"
            f"sudo python3 {os.path.join(ROOT_DIR, 'kontrol.py')}\n"
        )
        with open("/tmp/bootlocal.sh", "w") as f:
            f.write(bootlocal_content)
        subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", BOOTLOCAL_FILE], check=True)
        subprocess.run(["sudo", "chmod", "+x", BOOTLOCAL_FILE], check=True)
        subprocess.run(["sudo", "rm", "-f", "/tmp/bootlocal.sh"], check=True)

        current_hash = calculate_file_hash(BOOTLOCAL_FILE)
        if current_hash:
            log_message(f"bootlocal.sh guncellendi, SHA256: {current_hash}")
        else:
            log_message("bootlocal.sh dogrulama basarisiz")
        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
        display_status(stdscr, "ONYUKLEME YAPILANDIRMA", "sistem onyuklemesi ayarlanıyor", True, "Yuklendi")
        return True
    except Exception as e:
        log_message(f"bootlocal.sh yapilandirmasi basarisiz: {e}")
        display_status(stdscr, "ONYUKLEME YAPILANDIRMA", "sistem onyuklemesi ayarlanıyor", False, "Hata")
        return False

# Configuration file handling
def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {"default_edex": False}
    except Exception as e:
        log_message(f"Konfigurasyon yuklenemedi: {e}")
        return {"default_edex": False}

def save_config(config):
    try:
        subprocess.run(["sudo", "mkdir", "-p", os.path.dirname(CONFIG_FILE)], check=True)
        subprocess.run(["sudo", "chmod", "755", os.path.dirname(CONFIG_FILE)], check=True)
        with open("/tmp/config.json", "w") as f:
            json.dump(config, f, indent=2)
        subprocess.run(["sudo", "mv", "/tmp/config.json", CONFIG_FILE], check=True)
        subprocess.run(["sudo", "chmod", "644", CONFIG_FILE], check=True)
        subprocess.run(["sudo", "rm", "-f", "/tmp/config.json"], check=True)
        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
    except Exception as e:
        log_message(f"Konfigurasyon kaydedilemedi: {e}")

# Display status
def display_status(stdscr, stage, description, success, status_text):
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
        start_row = max(0, (rows - len(lines) - 5) // 2)
        start_col = max(0, (cols - max_line_len) // 2)
        
        curses.start_color()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Turuncu yerine sarı
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        
        # Ana başlık
        title = "YUKLEME ARACI"
        title_col = max(0, (cols - len(title)) // 2)
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(start_row, title_col, title)
        stdscr.attroff(curses.color_pair(1))

        # ASCII
        if rows >= len(lines) + 5 and cols >= max_line_len:
            for i, line in enumerate(lines):
                stdscr.addstr(start_row + i + 2, start_col, line.rstrip())
        else:
            for i, line in enumerate(lines):
                stdscr.addstr(i + 2, 0, line.rstrip()[:cols])

        # Aşama başlığı
        stage_col = max(0, (cols - len(stage)) // 2)
        stdscr.addstr(start_row + len(lines) + 3, stage_col, stage)

        # Açıklama ve animasyon
        desc = f"{description} [/]"
        desc_col = max(0, (cols - len(desc)) // 2)
        stdscr.addstr(start_row + len(lines) + 4, desc_col, desc)

        # Animasyon
        anim_chars = ["/", "-", "\\", "|"]
        for i in range(10):  # 2 saniye animasyon
            stdscr.addstr(start_row + len(lines) + 4, desc_col + len(description) + 2, anim_chars[i % 4])
            stdscr.refresh()
            time.sleep(0.2)

        # Durum
        status_col = max(0, (cols - len(status_text)) // 2)
        stdscr.addstr(start_row + len(lines) + 4, status_col, status_text)
        if success:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(start_row + len(lines) + 4, status_col, status_text)
            stdscr.attroff(curses.color_pair(2))
        else:
            stdscr.attron(curses.color_pair(3))
            stdscr.addstr(start_row + len(lines) + 4, status_col, status_text)
            stdscr.attroff(curses.color_pair(3))
        stdscr.refresh()
        if success:
            time.sleep(1)
        else:
            stdscr.getch()
    except Exception as e:
        log_message(f"Ekran guncelleme basarisiz: {e}")
        print(f"YUKLEME ARACI\n{compact_ascii.rstrip()}\n{stage}\n{description} [/]\n{status_text}")

def main(stdscr):
    try:
        curses.curs_set(0)
        display_status(stdscr, "BASLATMA", "sistem baslatiliyor", True, "Yuklendi")
    except Exception as e:
        log_message(f"Curses baslatilamadi: {e}")

    config = load_config()
    if config.get("default_edex", False):
        display_status(stdscr, "EDEX-UI BASLATMA", "edex-ui varsayilan olarak calistiriliyor", True, "Yuklendi")
        if verify_edex_ui(stdscr):
            start_edex_ui(stdscr)
        return

    if not verify_disk(stdscr):
        return

    display_status(stdscr, "PAKET YUKLEME", "gerekli paketler yukleniyor", True, "Yuklendi")
    for package in REQUIRED_TCE_PACKAGES:
        install_tce_package(package)

    if not verify_dependencies(stdscr):
        return

    if not verify_edex_ui(stdscr):
        return

    if not configure_bootlocal(stdscr):
        pass  # Kritik değil, devam et

    verify_backup(stdscr)  # Kritik değil, hata olsa da devam

    try:
        stdscr.clear()
        stdscr.addstr(0, 0, "EDEX-UI her baslangicta varsayilan olarak baslatilsin mi? (e/h)")
        stdscr.refresh()
        choice = stdscr.getch()
        config["default_edex"] = choice == ord("e")
        save_config(config)
    except Exception as e:
        log_message(f"Varsayilan secim alinamadi: {e}")

    if not start_edex_ui(stdscr):
        return

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        log_message(f"{SYSTEM_NAME} coktu: {e}")
        print(f"Hata: {e}\nBerke OS")

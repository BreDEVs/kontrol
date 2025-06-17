import os
import re
import subprocess
import sys
import time
import curses
import shutil
import json
import hashlib

# Configuration
SYSTEM_NAME = "BerkeOS"
ROOT_DIR = "/mnt/sda1"
TCE_DIR = os.path.join(ROOT_DIR, "tce")
HOME_DIR = os.path.join(ROOT_DIR, "home")
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
REQUIRED_TCE_PACKAGES = ["python3.9", "nodejs", "Xorg-7.7", "libX11", "libxss", "fontconfig", "git", "wireless_tools", "wpa_supplicant", "parted"]

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

# System checks
def check_system():
    log_message(f"{SYSTEM_NAME} sistem kontrol ediliyor...")
    status = True
    errors = []

    # CPU check
    try:
        with open("/proc/cpuinfo") as f:
            if "processor" not in f.read():
                errors.append("CPU bilgileri alınamadı")
                status = False
    except Exception as e:
        errors.append(f"CPU kontrolü başarısız: {e}")
        status = False

    # RAM check
    try:
        result = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
        mem = int(result.stdout.splitlines()[1].split()[1])
        if mem < 100:
            errors.append(f"RAM yetersiz ({mem} MB)")
            status = False
    except Exception as e:
        errors.append(f"RAM kontrolü başarısız: {e}")
        status = False

    # Storage check
    try:
        if not os.path.exists("/dev/sda"):
            errors.append("Disk /dev/sda mevcut değil")
            status = False
        else:
            subprocess.run(["sudo", "mkdir", "-p", ROOT_DIR], check=True)
            subprocess.run(["sudo", "chmod", "755", ROOT_DIR], check=True)
            try:
                subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True)
            except subprocess.CalledProcessError:
                log_message("Disk bağlama başarısız, biçimlendirme deneniyor...")
                try:
                    subprocess.run(["sudo", "fsck", "/dev/sda1", "-y"], check=True)
                    subprocess.run(["sudo", "parted", "/dev/sda", "mklabel", "msdos"], check=True, stderr=subprocess.DEVNULL)
                    subprocess.run(["sudo", "parted", "/dev/sda", "mkpart", "primary", "ext4", "1MiB", "100%"], check=True)
                    subprocess.run(["sudo", "mkfs.ext4", "/dev/sda1"], check=True)
                    subprocess.run(["sudo", "mount", "/dev/sda1", ROOT_DIR], check=True)
                except Exception as e:
                    errors.append(f"Disk biçimlendirme başarısız: {e}")
                    status = False
            subprocess.run(["sudo", "mount", "-o", "remount,rw", ROOT_DIR], check=True)
            subprocess.run(["sudo", "mkdir", "-p", SYSTEM_DIR], check=True)
            subprocess.run(["sudo", "chmod", "755", SYSTEM_DIR], check=True)
    except Exception as e:
        errors.append(f"Depolama yapılandırması başarısız: {e}")
        status = False

    # Boot check
    try:
        with open("/etc/issue") as f:
            if "Tiny Core" not in f.read():
                errors.append("Tiny Core boot doğrulanamadı")
                status = False
    except Exception as e:
        errors.append(f"Boot kontrolü başarısız: {e}")
        status = False

    if errors:
        log_message("Sistem kontrol hataları: " + "; ".join(errors))
    return status, errors

# Disk optimization
def optimize_disk():
    log_message("Disk bölümleri optimize ediliyor...")
    try:
        subprocess.run(["sudo", "fsck", "/dev/sda1", "-f", "-y"], check=True)
        subprocess.run(["sudo", "mount", "-o", "remount,rw", ROOT_DIR], check=True)
        dirs = [TCE_DIR, HOME_DIR, SYSTEM_DIR, APPS_DIR, BACKUP_DIR, os.path.join(SYSTEM_DIR, "logs")]
        for d in dirs:
            subprocess.run(["sudo", "mkdir", "-p", d], check=True)
            subprocess.run(["sudo", "chmod", "755", d], check=True)
        log_message("BerkeOS dosya sistemi oluşturuldu")
        return True
    except Exception as e:
        log_message(f"Disk optimizasyonu başarısız: {e}")
        return False

# Network connection (Wi-Fi and Ethernet)
def check_and_connect_network(stdscr):
    log_message("Ağ bağlantısı kontrol ediliyor...")
    try:
        result = subprocess.run(["ping", "-c", "1", "google.com"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log_message("Ağ bağlantısı mevcut")
            return True
    except Exception as e:
        log_message(f"Ağ bağlantısı yok: {e}")

    # Try Ethernet
    try:
        subprocess.run(["sudo", "udhcpc", "-i", "eth0"], check=True, timeout=10)
        result = subprocess.run(["ping", "-c", "1", "google.com"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log_message("Ethernet bağlantısı kuruldu")
            return True
    except Exception as e:
        log_message(f"Ethernet bağlantısı başarısız, Wi-Fi deneniyor: {e}")

    # Wi-Fi
    display_status(stdscr, "Wi-Fi ağları taranıyor...")
    try:
        result = subprocess.run(["sudo", "iwlist", "wlan0", "scan"], capture_output=True, text=True, timeout=10)
        networks = re.findall(r'ESSID:"(.*?)"', result.stdout)
        if not networks:
            log_message("Wi-Fi ağları bulunamadı")
            display_status(stdscr, "Hata: Wi-Fi ağları bulunamadı!")
            time.sleep(3)
            return False
    except Exception as e:
        log_message(f"iwlist komutu başarısız: {e}")
        display_status(stdscr, "Hata: Wi-Fi tarama başarısız!")
        time.sleep(3)
        return False

    stdscr.clear()
    stdscr.addstr(0, 0, f"{SYSTEM_NAME} Wi-Fi Ağı Seçin:")
    for i, network in enumerate(networks):
        stdscr.addstr(i + 1, 0, f"{i + 1}. {network}")
    stdscr.addstr(len(networks) + 2, 0, f"Seçim (1-{len(networks)}): ")
    stdscr.refresh()

    while True:
        try:
            choice = int(stdscr.getstr().decode()) - 1
            if 0 <= choice < len(networks):
                selected_network = networks[choice]
                break
        except ValueError:
            pass

    stdscr.clear()
    stdscr.addstr(0, 0, f"{selected_network} için şifre girin:")
    stdscr.addstr(1, 0, "Şifre: ")
    stdscr.refresh()
    password = stdscr.getstr().decode()

    display_status(stdscr, f"{selected_network} bağlanıyor...")
    try:
        subprocess.run(["sudo", "chmod", "600", "/tmp/wpa.conf"], check=True, ignore_errors=True)
        with open("/tmp/wpa.conf", "w") as f:
            f.write(f'network={{\nssid="{selected_network}"\npsk="{password}"\n}}\n')
        subprocess.run(["sudo", "wpa_supplicant", "-B", "-i", "wlan0", "-c", "/tmp/wpa.conf"], check=True, timeout=10)
        subprocess.run(["sudo", "udhcpc", "-i", "wlan0"], check=True, timeout=10)
        subprocess.run(["sudo", "rm", "-f", "/tmp/wpa.conf"], check=True)
        log_message(f"{selected_network} bağlandı")
        return True
    except Exception as e:
        log_message(f"Wi-Fi bağlantısı başarısız: {e}")
        display_status(stdscr, "Hata: Wi-Fi bağlantısı başarısız!")
        time.sleep(3)
        return False

# Install Tiny Core package
def install_tce_package(package_name):
    try:
        log_message(f"Yükleniyor: {package_name}")
        result = subprocess.run(["sudo", "tce-load", "-w", "-i", package_name], capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            log_message(f"{package_name} yüklendi")
            with open(os.path.join(TCE_DIR, "onboot.lst"), "a") as f:
                f.write(f"{package_name}\n")
            subprocess.run(["sudo", "chmod", "644", os.path.join(TCE_DIR, "onboot.lst")], check=True)
            subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
        else:
            log_message(f"{package_name} yüklenemedi: {result.stderr}")
    except Exception as e:
        log_message(f"Yükleme hatası: {package_name}: {e}")

# Install Python modules
def install_python_modules():
    log_message("Python modülleri kontrol ediliyor...")
    try:
        import requests
        log_message("requests modülü yüklü")
    except ImportError:
        try:
            install_tce_package("python3.9-pip")
            subprocess.run(["sudo", "pip3", "install", "requests"], check=True, timeout=120)
            log_message("requests modülü yüklendi")
        except Exception as e:
            log_message(f"Python modülleri yüklenemedi: {e}")

# Install Node.js and npm
def install_node_npm():
    log_message("Node.js ve npm kontrol ediliyor...")
    try:
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, timeout=5)
        npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and npm_result.returncode == 0:
            log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} yüklü")
            return True
    except Exception:
        log_message("Node.js veya npm yüklü değil, kuruluyor...")

    try:
        install_tce_package("nodejs")
        if subprocess.run(["npm", "-v"], capture_output=True, timeout=5).returncode != 0:
            log_message("npm eksik, manuel kurulum yapılıyor...")
            node_url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
            subprocess.run(["sudo", "wget", node_url, "-O", "/tmp/node.tar.xz"], check=True, timeout=120)
            subprocess.run(["sudo", "tar", "-xJf", "/tmp/node.tar.xz", "-C", "/usr/local"], check=True, timeout=120)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/node", "/usr/local/bin/node"], check=True)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True)
            subprocess.run(["sudo", "rm", "-f", "/tmp/node.tar.xz"], check=True)
            log_message("Node.js ve npm manuel yüklendi")
        return True
    except Exception as e:
        log_message(f"Node.js ve npm kurulumu başarısız: {e}")
        return False

# Install and customize EDEX-UI
def install_and_customize_edex_ui():
    log_message("EDEX-UI kontrol ediliyor...")
    if not os.path.exists(EDEX_DIR):
        log_message("EDEX-UI klonlanıyor...")
        try:
            subprocess.run(["sudo", "git", "clone", EDEX_REPO, EDEX_DIR], check=True, timeout=300)
            subprocess.run(["sudo", "chmod", "-R", "755", EDEX_DIR], check=True)
            log_message("EDEX-UI klonlandı")
        except Exception as e:
            log_message(f"EDEX-UI klonlama başarısız: {e}")
            return False

    package_json_path = os.path.join(EDEX_DIR, "package.json")
    if not os.path.exists(package_json_path):
        log_message("package.json bulunamadı")
        return False

    try:
        subprocess.run(["sudo", "npm", "install"], cwd=EDEX_DIR, check=True, timeout=600)
        log_message("npm bağımlılıkları yüklendi")
    except Exception as e:
        log_message(f"npm bağımlılıkları yüklenemedi: {e}")
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
        log_message("EDEX-UI ayarları özelleştirildi")
    except Exception as e:
        log_message(f"EDEX-UI ayarları özelleştirilemedi: {e}")

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
        log_message(f"Xorg optimizasyonu başarısız: {e}")

    return True

# Start EDEX-UI
def start_edex_ui():
    log_message("EDEX-UI başlatılıyor...")
    try:
        process = subprocess.Popen(["sudo", "npm", "start"], cwd=EDEX_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)
        if process.poll() is None:
            log_message("EDEX-UI başlatıldı")
            return True
        else:
            stdout, stderr = process.communicate()
            log_message(f"EDEX-UI başlatılamadı: {stderr.decode()}")
            return False
    except Exception as e:
        log_message(f"EDEX-UI başlatılamadı: {e}")
        return False

# System backup
def backup_system():
    log_message("Sistem yedekleniyor...")
    try:
        subprocess.run(["sudo", "mkdir", "-p", BACKUP_DIR], check=True)
        subprocess.run(["sudo", "chmod", "755", BACKUP_DIR], check=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"berkeos_backup_{timestamp}.tar.gz")
        dirs_to_backup = [HOME_DIR, SYSTEM_DIR, APPS_DIR, TCE_DIR]
        subprocess.run(["sudo", "tar", "-czf", backup_file] + dirs_to_backup, check=True, timeout=300)
        backup_hash = calculate_file_hash(backup_file)
        if backup_hash:
            log_message(f"Yedek oluşturuldu: {backup_file}, SHA256: {backup_hash}")
            with open(os.path.join(BACKUP_DIR, "backup_log.txt"), "a") as f:
                f.write(f"{timestamp}: {backup_file}, SHA256: {backup_hash}\n")
            subprocess.run(["sudo", "chmod", "644", os.path.join(BACKUP_DIR, "backup_log.txt")], check=True)
        else:
            log_message("Yedek doğrulama başarısız")
        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
        return True
    except Exception as e:
        log_message(f"Yedekleme başarısız: {e}")
        return False

# Configure bootlocal.sh
def configure_bootlocal():
    log_message("bootlocal.sh yapılandırılıyor...")
    try:
        if os.path.exists(BOOTLOCAL_FILE):
            subprocess.run(["sudo", "cp", BOOTLOCAL_FILE, BOOTLOCAL_BACKUP], check=True)
            subprocess.run(["sudo", "chmod", "644", BOOTLOCAL_BACKUP], check=True)
            log_message(f"bootlocal.sh yedeği alındı: {BOOTLOCAL_BACKUP}")

        bootlocal_content = (
            "#!/bin/sh\n"
            "# BerkeOS Bootlocal Configuration\n"
            f"sudo tce-load -i python3.9\n"
            f"sudo tce-load -i nodejs\n"
            f"sudo python3 {os.path.join(ROOT_DIR, 'kontrol.py')}\n"
        )
        with open("/tmp/bootlocal.sh", "w") as f:
            f.write(bootlocal_content)
        subprocess.run(["sudo", "mv", "/tmp/bootlocal.sh", BOOTLOCAL_FILE], check=True)
        subprocess.run(["sudo", "chmod", "+x", BOOTLOCAL_FILE], check=True)
        subprocess.run(["sudo", "rm", "-f", "/tmp/bootlocal.sh"], check=True)

        current_hash = calculate_file_hash(BOOTLOCAL_FILE)
        if current_hash:
            log_message(f"bootlocal.sh güncellendi, SHA256: {current_hash}")
        else:
            log_message("bootlocal.sh doğrulama başarısız")
        subprocess.run(["sudo", "filetool.sh", "-b"], check=True, timeout=10)
        return True
    except Exception as e:
        log_message(f"bootlocal.sh yapılandırması başarısız: {e}")
        return False

# Configuration file handling
def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {"default_edex": False}
    except Exception as e:
        log_message(f"Konfigürasyon yüklenemedi: {e}")
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
        log_message(f"Konfigürasyon kaydedilemedi: {e}")

# Display status
def display_status(stdscr, status, error=False):
    try:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        compact_ascii = (
            "██████╗ ██████╗ ██████╗ ██╗  ██╗███████╗\n"
            "██╔══██╗██╔═══╝ ██╔══██╗██║ ██╔╝██╔════╝\n"
            "██████╦╝█████╗  ██████╔╝█████═╝ █████╗  \n"
            "██╔══██╗██╔══╝  ██╔══██╗██╔═██╗ ██╔══╝  \n"
            "██████╦╝███████╗██║  ██║██║ ╚██╗███████╗\n"
            "╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝\n"
            "Berke Oruç tarafından yapılmıştır\n"
        )
        lines = compact_ascii.splitlines()
        start_row = max(0, (rows - len(lines) - 2) // 2)
        start_col = max(0, (cols - max(len(line) for line in lines)) // 2)
        if rows >= len(lines) + 2 and cols >= max(len(line) for line in lines):
            for i, line in enumerate(lines):
                stdscr.addstr(start_row + i, start_col, line.rstrip())
            stdscr.addstr(start_row + len(lines) + 1, start_col, f"Durum: {status}")
            if not error:
                stdscr.addstr(start_row + len(lines) + 2, start_col, "Devam etmek için bir tuşa basın...")
        else:
            stdscr.addstr(0, 0, f"Durum: {status}")
            if not error:
                stdscr.addstr(1, 0, "Devam etmek için bir tuşa basın...")
        stdscr.refresh()
        if not error:
            stdscr.getch()
    except Exception as e:
        log_message(f"Ekran güncelleme başarısız: {e}")
        print(f"Durum: {status}\nBerke Oruç tarafından yapılmıştır")
        if not error:
            print("Devam etmek için bir tuşa basın...")
            input()

def main(stdscr):
    try:
        curses.curs_set(0)
        display_status(stdscr, f"{SYSTEM_NAME} Başlatılıyor...")
    except Exception as e:
        log_message(f"Curses başlatılamadı: {e}")
        print(f"Curses başlatılamadı: {e}")
        time.sleep(3)
        return

    config = load_config()
    if config.get("default_edex", False):
        display_status(stdscr, "EDEX-UI varsayılan olarak başlatılıyor...")
        if install_and_customize_edex_ui():
            start_edex_ui()
        return

    display_status(stdscr, "Sistem kontrol ediliyor...")
    system_status, errors = check_system()
    if not system_status:
        error_msg = "Hata: Sistem uygun değil! Hatalar: " + "; ".join(errors)
        display_status(stdscr, error_msg, error=True)
        log_message(error_msg)
        time.sleep(5)
        return

    display_status(stdscr, "Disk bölümleri optimize ediliyor...")
    if not optimize_disk():
        display_status(stdscr, "Hata: Disk optimizasyonu başarısız!", error=True)
        log_message("Disk optimizasyonu başarısız")
        time.sleep(5)
        return

    display_status(stdscr, "Ağ bağlantısı kontrol ediliyor...")
    if not check_and_connect_network(stdscr):
        display_status(stdscr, "Hata: Ağ bağlantısı sağlanamadı!", error=True)
        log_message("Ağ bağlantısı sağlanamadı")
        time.sleep(5)
        return

    display_status(stdscr, "Gerekli paketler yükleniyor...")
    for package in REQUIRED_TCE_PACKAGES:
        install_tce_package(package)

    display_status(stdscr, "Python modülleri yükleniyor...")
    install_python_modules()

    display_status(stdscr, "Node.js ve npm yükleniyor...")
    if not install_node_npm():
        display_status(stdscr, "Hata: Node.js veya npm yüklenemedi!", error=True)
        log_message("Node.js veya npm yüklenemedi")
        time.sleep(5)
        return

    display_status(stdscr, "EDEX-UI yükleniyor...")
    if not install_and_customize_edex_ui():
        display_status(stdscr, "Hata: EDEX-UI yüklenemedi!", error=True)
        log_message("EDEX-UI yüklenemedi")
        time.sleep(5)
        return

    display_status(stdscr, "bootlocal.sh yapılandırılıyor...")
    if not configure_bootlocal():
        display_status(stdscr, "Hata: Önyükleme yapılandırması başarısız!", error=True)
        log_message("Önyükleme yapılandırması başarısız")
        time.sleep(5)
        return

    display_status(stdscr, "Sistem yedekleniyor...")
    if not backup_system():
        display_status(stdscr, "Hata: Yedekleme başarısız!", error=True)
        log_message("Yedekleme başarısız")
        time.sleep(5)
        return

    try:
        stdscr.clear()
        stdscr.addstr(0, 0, "EDEX-UI her başlangıçta varsayılan olarak başlatılsın mı? (e/h)")
        stdscr.refresh()
        choice = stdscr.getch()
        config["default_edex"] = choice == ord("e")
        save_config(config)
    except Exception as e:
        log_message(f"Varsayılan seçim alınamadı: {e}")

    display_status(stdscr, f"{SYSTEM_NAME} Kurulum Tamamlandı!")
    if start_edex_ui():
        display_status(stdscr, f"{SYSTEM_NAME} EDEX-UI HAZIR!", error=True)
    else:
        display_status(stdscr, "Hata: EDEX-UI başlatılamadı!", error=True)
        log_message("EDEX-UI başlatılamadı")
        time.sleep(5)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        log_message(f"{SYSTEM_NAME} çöktü: {e}")
        print(f"Hata: {e}\nBerke Oruç tarafından yapılmıştır")

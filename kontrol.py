import os
import re
import subprocess
import sys
import time
import curses
import shutil
import json
import requests
from urllib.parse import quote

# Yapılandırma
ROOT_DIR = "/mnt/sda1"
TCE_DIR = "/mnt/sda1/tce"
BACKUP_DIR = "/mnt/sda1/backup"
LOG_FILE = "/mnt/sda1/install_log.txt"
EDEX_DIR = "/mnt/sda1/edex-ui"
CONFIG_FILE = "/mnt/sda1/berke_os_config.json"
TCE_REPO = "http://repo.tinycorelinux.net"
NODE_VERSION = "16.20.2"
EDEX_REPO = "https://github.com/GitSquared/edex-ui.git"

# Gerekli Tiny Core paketleri
REQUIRED_TCE_PACKAGES = ["python3.9", "nodejs", "Xorg-7.7", "libX11", "libxss", "fontconfig", "git", "w3m", "wireless_tools", "wpa_supplicant", "virtualbox-guest"]

# Log dosyasına yaz
def log_message(message):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
    except Exception as e:
        print(f"Log yazma hatası: {e}")

# Sistem kontrolleri
def check_system():
    log_message("Sistem kontrol ediliyor...")
    status = True

    # CPU kontrolü
    try:
        result = subprocess.run(["lscpu"], capture_output=True, text=True, timeout=10)
        if "CPU(s):" not in result.stdout:
            log_message("Hata: CPU bilgileri alınamadı!")
            status = False
    except Exception as e:
        log_message(f"Hata: lscpu komutu çalışmadı: {e}")
        status = False

    # RAM kontrolü
    try:
        result = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=10)
        mem = int(result.stdout.splitlines()[1].split()[1])
        if mem < 512:
            log_message(f"Uyarı: RAM yetersiz ({mem} MB)!")
            status = False
    except Exception as e:
        log_message(f"Hata: free komutu çalışmadı: {e}")
        status = False

    # Depolama kontrolü
    try:
        if not os.path.exists(ROOT_DIR):
            log_message(f"Hata: {ROOT_DIR} mevcut değil!")
            status = False
        else:
            # Yazılabilirlik kontrolü
            subprocess.run(["sudo", "mount", "-o", "remount,rw", ROOT_DIR], check=True)
            subprocess.run(["sudo", "chmod", "-R", "u+w", ROOT_DIR], check=True)
            if not os.path.exists(TCE_DIR):
                log_message(f"{TCE_DIR} oluşturuluyor...")
                os.makedirs(TCE_DIR, exist_ok=True)
                os.makedirs(os.path.join(TCE_DIR, "optional"), exist_ok=True)
                with open("/opt/.tce_dir", "w") as f:
                    f.write(TCE_DIR)
                log_message(f"{TCE_DIR} yapılandırıldı.")
    except Exception as e:
        log_message(f"Hata: Depolama yapılandırması başarısız: {e}")
        status = False

    # Boot kontrolü
    try:
        result = subprocess.run(["dmesg"], capture_output=True, text=True, timeout=10)
        if "Tiny Core" not in result.stdout:
            log_message("Uyarı: Tiny Core boot doğrulanamadı!")
            status = False
    except Exception as e:
        log_message(f"Hata: dmesg komutu çalışmadı: {e}")
        status = False

    return status

# Ağ bağlantısını kontrol et ve Wi-Fi bağlan
def check_and_connect_network(stdscr):
    log_message("Ağ bağlantısı kontrol ediliyor...")
    try:
        result = subprocess.run(["ping", "-c", "1", "google.com"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_message("Ağ bağlantısı mevcut.")
            return True
    except Exception as e:
        log_message(f"Ağ bağlantısı yok, Wi-Fi taranıyor: {e}")

    # Wi-Fi tarama
    display_status(stdscr, "Wi-Fi ağları taranıyor...")
    try:
        result = subprocess.run(["iwlist", "wlan0", "scan"], capture_output=True, text=True, timeout=30)
        networks = re.findall(r"ESSID:\"(.*?)\"", result.stdout)
        if not networks:
            log_message("Hata: Wi-Fi ağları bulunamadı!")
            display_status(stdscr, "Hata: Wi-Fi ağları bulunamadı!")
            time.sleep(5)
            return False
    except Exception as e:
        log_message(f"Hata: iwlist komutu çalışmadı: {e}")
        display_status(stdscr, "Hata: Wi-Fi tarama başarısız!")
        time.sleep(5)
        return False

    # Wi-Fi seçimi
    stdscr.clear()
    stdscr.addstr(0, 0, "Wi-Fi Ağı Seçin:")
    for i, network in enumerate(networks):
        stdscr.addstr(i + 1, 0, f"{i + 1}. {network}")
    stdscr.addstr(len(networks) + 2, 0, "Seçim (1-{}): ".format(len(networks)))
    stdscr.refresh()

    while True:
        try:
            choice = int(stdscr.getstr().decode()) - 1
            if 0 <= choice < len(networks):
                selected_network = networks[choice]
                break
        except:
            pass

    # Şifre girişi
    stdscr.clear()
    stdscr.addstr(0, 0, f"{selected_network} için şifre girin:")
    stdscr.addstr(1, 0, "Şifre: ")
    stdscr.refresh()
    password = stdscr.getstr().decode()

    # Wi-Fi bağlantısı
    display_status(stdscr, f"{selected_network} bağlanıyor...")
    try:
        with open("/tmp/wpa.conf", "w") as f:
            f.write(f'network={{\nssid="{selected_network}"\npsk="{password}"\n}}\n')
        subprocess.run(["sudo", "wpa_supplicant", "-B", "-i", "wlan0", "-c", "/tmp/wpa.conf"], check=True, timeout=30)
        subprocess.run(["sudo", "udhcpc", "-i", "wlan0"], check=True, timeout=30)
        log_message(f"{selected_network} bağlandı.")
        return True
    except Exception as e:
        log_message(f"Hata: Wi-Fi bağlantısı başarısız: {e}")
        display_status(stdscr, "Hata: Wi-Fi bağlantısı başarısız!")
        time.sleep(5)
        return False

# Tiny Core paketini yükle
def install_tce_package(package_name):
    try:
        log_message(f"Yükleniyor: {package_name}")
        result = subprocess.run(["tce-load", "-w", "-i", package_name], capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            log_message(f"{package_name} başarıyla yüklendi.")
            with open(os.path.join(TCE_DIR, "onboot.lst"), "a") as f:
                f.write(f"{package_name}\n")
            subprocess.run(["filetool.sh", "-b"], check=True, timeout=30)
        else:
            log_message(f"Hata: {package_name} yüklenemedi: {result.stderr}")
    except Exception as e:
        log_message(f"Yükleme hatası: {package_name}: {e}")

# Python modüllerini kur
def install_python_modules():
    log_message("Python modülleri kontrol ediliyor...")
    try:
        subprocess.run(["pip3", "install", "requests"], check=True, timeout=300)
        log_message("requests modülü yüklendi.")
    except Exception as e:
        log_message(f"Hata: Python modülleri yüklenemedi: {e}")
        try:
            subprocess.run(["tce-load", "-w", "-i", "python3.9-pip"], check=True, timeout=300)
            subprocess.run(["pip3", "install", "requests"], check=True, timeout=300)
            log_message("pip ve requests modülü yüklendi.")
        except Exception as e2:
            log_message(f"Hata: pip yüklenemedi: {e2}")

# Node.js ve npm kur
def install_node_npm():
    log_message("Node.js ve npm kontrol ediliyor...")
    try:
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, timeout=10)
        npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and npm_result.returncode == 0:
            log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} yüklü.")
            return True
    except Exception:
        log_message("Node.js veya npm yüklü değil, kuruluyor...")

    try:
        install_tce_package("nodejs")
        if subprocess.run(["npm", "-v"], capture_output=True, timeout=10).returncode != 0:
            log_message("npm eksik, manuel kurulum yapılıyor...")
            node_url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
            subprocess.run(["wget", node_url, "-O", "/tmp/node.tar.xz"], check=True, timeout=300)
            subprocess.run(["sudo", "tar", "-xJf", "/tmp/node.tar.xz", "-C", "/usr/local"], check=True, timeout=300)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/node", "/usr/local/bin/node"], check=True)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True)
            log_message("Node.js ve npm manuel olarak yüklendi.")
        return True
    except Exception as e:
        log_message(f"Hata: Node.js ve npm kurulumu başarısız: {e}")
        return False

# EDEX-UI’yi klonla ve özelleştir
def install_and_customize_edex_ui():
    log_message("EDEX-UI kontrol ediliyor...")
    if not os.path.exists(EDEX_DIR):
        log_message("EDEX-UI klonlanıyor...")
        try:
            subprocess.run(["git", "clone", EDEX_REPO, EDEX_DIR], check=True, timeout=600)
            log_message("EDEX-UI başarıyla klonlandı.")
        except Exception as e:
            log_message(f"Hata: EDEX-UI klonlama başarısız: {e}")
            return False

    # package.json kontrolü ve bağımlılık yükleme
    package_json_path = os.path.join(EDEX_DIR, "package.json")
    if not os.path.exists(package_json_path):
        log_message("Hata: package.json bulunamadı!")
        return False

    try:
        subprocess.run(["npm", "install"], cwd=EDEX_DIR, check=True, timeout=900)
        log_message("npm bağımlılıkları yüklendi.")
    except Exception as e:
        log_message(f"Hata: npm bağımlılıkları yüklenemedi: {e}")
        return False

    # EDEX-UI özelleştirme
    settings_path = os.path.join(EDEX_DIR, "settings.json")
    try:
        settings = {"shell": "BERKE OS Terminal", "theme": "tron"}
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                existing = json.load(f)
                settings.update(existing)
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        log_message("EDEX-UI ayarları özelleştirildi.")
    except Exception as e:
        log_message(f"Hata: EDEX-UI ayarları özelleştirilemedi: {e}")

    return True

# JavaScript dosyasını kontrol et
def check_js_file(file_path):
    log_message(f"JavaScript dosyası kontrol ediliyor: {file_path}")
    try:
        result = subprocess.run(["node", "-c", file_path], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_message(f"{file_path} sözdizimi doğru.")
            return True
        else:
            log_message(f"Sözdizimi hatası: {file_path}, {result.stderr}")
            backup_path = os.path.join(BACKUP_DIR, os.path.relpath(file_path, ROOT_DIR))
            if os.path.exists(backup_path):
                shutil.copy(backup_path, file_path)
                log_message(f"{file_path} yedekten geri yüklendi.")
                return True
            else:
                log_message(f"{file_path} için yedek bulunamadı!")
                return False
    except Exception as e:
        log_message(f"Hata: {file_path} işlenemedi: {e}")
        return False

# Yedek oluştur
def create_backup(file_path):
    try:
        backup_path = os.path.join(BACKUP_DIR, os.path.relpath(file_path, ROOT_DIR))
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy(file_path, backup_path)
        log_message(f"Yedek oluşturuldu: {backup_path}")
    except Exception as e:
        log_message(f"Hata: Yedek oluşturulamadı: {e}")

# Terminal tabanlı web tarayıcı
def web_search(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Web Arama (Çıkmak için 'q' girin)")
    stdscr.addstr(1, 0, "Sorgu: ")
    stdscr.refresh()
    query = stdscr.getstr().decode()
    if query.lower() == "q":
        return

    page = 1
    while True:
        display_status(stdscr, f"Arama yapılıyor: {query} (Sayfa {page})...")
        try:
            url = f"https://www.google.com/search?q={quote(query)}&start={(page-1)*10}"
            result = subprocess.run(["w3m", "-dump", url], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                log_message(f"Hata: w3m arama başarısız: {result.stderr}")
                display_status(stdscr, "Hata: Arama başarısız!")
                time.sleep(5)
                break
            lines = result.stdout.splitlines()
            results = []
            for line in lines:
                if line.startswith("  ") and "http" in line:
                    results.append(line.strip())
            results = results[:7]

            stdscr.clear()
            stdscr.addstr(0, 0, f"Sonuçlar: {query} (Sayfa {page})")
            for i, res in enumerate(results, 1):
                stdscr.addstr(i, 0, f"{i}. {res[:70]}...")
            stdscr.addstr(8, 0, "Komut (sayfa> veya git:<sıra>): ")
            stdscr.refresh()

            cmd = stdscr.getstr().decode()
            if cmd == "sayfa>":
                page += 1
            elif cmd.startswith("git:"):
                try:
                    idx = int(cmd.split(":")[1]) - 1
                    if 0 <= idx < len(results):
                        url = results[idx].split()[-1]
                        subprocess.run(["w3m", url], timeout=60)
                    else:
                        stdscr.addstr(9, 0, "Geçersiz sıra numarası!")
                        stdscr.refresh()
                        time.sleep(2)
                except Exception as e:
                    stdscr.addstr(9, 0, f"Hata: Geçersiz komut: {e}")
                    stdscr.refresh()
                    time.sleep(2)
            elif cmd.lower() == "q":
                break
        except Exception as e:
            log_message(f"Hata: Arama başarısız: {e}")
            display_status(stdscr, "Hata: Arama başarısız!")
            time.sleep(5)
            break

# EDEX-UI’yi başlat
def start_edex_ui():
    log_message("EDEX-UI başlatılıyor...")
    try:
        subprocess.Popen(["npm", "start"], cwd=EDEX_DIR)
        log_message("EDEX-UI başarıyla başlatıldı.")
        return True
    except Exception as e:
        log_message(f"Hata: EDEX-UI başlatılamadı: {e}")
        return False

# Konfigürasyon dosyasını oku/yaz
def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        log_message(f"Hata: Konfigürasyon yüklenemedi: {e}")
    return {"default_edex": False}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        subprocess.run(["filetool.sh", "-b"], check=True, timeout=30)
    except Exception as e:
        log_message(f"Hata: Konfigürasyon kaydedilemedi: {e}")

# Ana arayüz
def main_menu(stdscr):
    options = ["EDEX-UI Başlat", "Klasik Terminal", "Web Tarayıcı", "Çıkış"]
    selected = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "BERKE OS Ana Menü")
        for i, option in enumerate(options):
            if i == selected:
                stdscr.addstr(i + 2, 0, f"> {option}", curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 0, f"  {option}")
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(options) - 1:
            selected += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return selected

# Curses ile ekran çıktısı
def display_status(stdscr, status):
    stdscr.clear()
    ascii_art = """
██████╗░███████╗██████╗░██╗░░██╗███████╗  ░█████╗░░██████╗
██╔══██╗██╔════╝██╔══██╗██║░██╔╝██╔════╝  ██╔══██╗██╔════╝
██████╦╝█████╗░░██████╔╝█████═╝░█████╗░░  ██║░░██║╚█████╗░
██╔══██╗██╔══╝░░██╔══██╗██╔═██╗░██╔══╝░░  ██║░░██║░╚═══██╗
██████╦╝███████╗██║░░██║██║░╚██╗███████╗  ╚█████╔╝██████╔╝
╚═════╝░╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝╚══════╝  ░╚════╝░╚═════╝░

██╗░░██╗░█████╗░███╗░░██╗████████╗██████╗░░█████╗░██╗░░░░░
██║░██╔╝██╔══██╗████╗░██║╚══██╔══╝██╔══██╗██╔══██╗██║░░░░░
█████═╝░██║░░██║██╔██╗██║░░░██║░░░██████╔╝██║░░██║██║░░░░░
██╔═██╗░██║░░██║██║╚████║░░░██║░░░██╔══██╗██║░░██║██║░░░░░
██║░╚██╗╚█████╔╝██║░╚███║░░░██║░░░██║░░██║╚█████╔╝███████╗
╚═╝░░╚═╝░╚════╝░╚═╝░░╚══╝░░░╚═╝░░░╚═╝░░╚═╝░╚════╝░╚══════╝
    """
    try:
        for i, line in enumerate(ascii_art.split("\n")):
            stdscr.addstr(i, 0, line)
        stdscr.addstr(len(ascii_art.split("\n")) + 1, 0, f"Durum: {status}")
        stdscr.refresh()
    except Exception as e:
        log_message(f"Hata: Ekran güncelleme başarısız: {e}")

def main(stdscr):
    # Curses ayarları
    try:
        curses.curs_set(0)
        display_status(stdscr, "Başlatılıyor...")
    except Exception as e:
        log_message(f"Hata: Curses başlatılamadı: {e}")
        return

    # Konfigürasyon kontrolü
    config = load_config()
    if config.get("default_edex", False):
        display_status(stdscr, "EDEX-UI varsayılan olarak başlatılıyor...")
        if install_and_customize_edex_ui():
            start_edex_ui()
        return

    # Sistem kontrolü
    display_status(stdscr, "Sistem kontrol ediliyor...")
    if not check_system():
        display_status(stdscr, "Hata: Sistem uygun değil!")
        time.sleep(5)
        return

    # Ağ kontrolü
    display_status(stdscr, "Ağ bağlantısı kontrol ediliyor...")
    if not check_and_connect_network(stdscr):
        display_status(stdscr, "Hata: Ağ bağlantısı sağlanamadı!")
        time.sleep(5)
        return

    # Tiny Core paketlerini yükle
    display_status(stdscr, "Gerekli paketler yükleniyor...")
    for package in REQUIRED_TCE_PACKAGES:
        install_tce_package(package)

    # Python modüllerini yükle
    display_status(stdscr, "Python modülleri yükleniyor...")
    install_python_modules()

    # Node.js ve npm kur
    display_status(stdscr, "Node.js ve npm yükleniyor...")
    if not install_node_npm():
        display_status(stdscr, "Hata: Node.js veya npm yüklenemedi!")
        time.sleep(5)
        return

    # EDEX-UI kur ve özelleştir
    display_status(stdscr, "EDEX-UI yükleniyor...")
    if not install_and_customize_edex_ui():
        display_status(stdscr, "Hata: EDEX-UI yüklenemedi!")
        time.sleep(5)
        return

    # JavaScript dosyalarını tara ve kontrol et
    display_status(stdscr, "JavaScript dosyaları kontrol ediliyor...")
    js_files = []
    try:
        for dirpath, _, filenames in os.walk(EDEX_DIR):
            for filename in filenames:
                if filename.endswith(".js"):
                    js_files.append(os.path.join(dirpath, filename))
        for js_file in js_files:
            create_backup(js_file)
            if not check_js_file(js_file):
                log_message(f"Uyarı: {js_file} hatalı!")
                display_status(stdscr, f"Uyarı: {os.path.basename(js_file)} hatalı!")
                time.sleep(2)
    except Exception as e:
        log_message(f"Hata: JavaScript dosyaları kontrol edilemedi: {e}")

    # Varsayılan EDEX-UI sorusu
    stdscr.clear()
    stdscr.addstr(0, 0, "EDEX-UI her başlangıçta varsayılan olarak başlatılsın mı? (e/h)")
    stdscr.refresh()
    try:
        choice = stdscr.getch()
        config["default_edex"] = choice == ord("e")
        save_config(config)
    except Exception as e:
        log_message(f"Hata: Varsayılan seçim alınamadı: {e}")

    # Ana menü
    while True:
        choice = main_menu(stdscr)
        if choice == 0:  # EDEX-UI
            display_status(stdscr, "EDEX-UI başlatılıyor...")
            if start_edex_ui():
                display_status(stdscr, "BERKE OS EDEX-UI HAZIR!")
            else:
                display_status(stdscr, "Hata: EDEX-UI başlatılamadı!")
            time.sleep(5)
        elif choice == 1:  # Klasik Terminal
            stdscr.clear()
            stdscr.refresh()
            curses.endwin()
            subprocess.run(["bash"])
            break
        elif choice == 2:  # Web Tarayıcı
            web_search(stdscr)
        elif choice == 3:  # Çıkış
            break

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        log_message(f"Hata: Ana program çöktü: {e}")
        print(f"Hata: {e}")

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
REQUIRED_TCE_PACKAGES = ["nodejs", "Xorg-7.7", "libX11", "libxss", "fontconfig", "git", "w3m"]

# Log dosyasına yaz
def log_message(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")

# Sistem kontrolleri
def check_system():
    log_message("Sistem kontrol ediliyor...")
    status = True

    # CPU kontrolü
    try:
        result = subprocess.run(["lscpu"], capture_output=True, text=True)
        if "CPU(s):" not in result.stdout:
            log_message("Hata: CPU bilgileri alınamadı!")
            status = False
    except:
        log_message("Hata: lscpu komutu çalışmadı!")
        status = False

    # RAM kontrolü
    try:
        result = subprocess.run(["free", "-m"], capture_output=True, text=True)
        mem = int(result.stdout.splitlines()[1].split()[1])
        if mem < 512:
            log_message(f"Uyarı: RAM yetersiz ({mem} MB)!")
            status = False
    except:
        log_message("Hata: free komutu çalışmadı!")
        status = False

    # Depolama kontrolü
    if not os.path.exists(ROOT_DIR):
        log_message(f"Hata: {ROOT_DIR} mevcut değil!")
        status = False
    elif not os.path.exists(TCE_DIR):
        log_message(f"{TCE_DIR} oluşturuluyor...")
        subprocess.run(["sudo", "mkdir", "-p", TCE_DIR], check=True)
        subprocess.run(["sudo", "mkdir", "-p", os.path.join(TCE_DIR, "optional")], check=True)
        with open("/opt/.tce_dir", "w") as f:
            f.write(TCE_DIR)
        log_message(f"{TCE_DIR} yapılandırıldı.")

    # Boot kontrolü
    try:
        result = subprocess.run(["dmesg"], capture_output=True, text=True)
        if "Tiny Core" not in result.stdout:
            log_message("Uyarı: Tiny Core boot doğrulanamadı!")
            status = False
    except:
        log_message("Hata: dmesg komutu çalışmadı!")
        status = False

    # X Window Sistemi kontrolü
    try:
        result = subprocess.run(["tce-audit", "check", "Xorg-7.7"], capture_output=True)
        if result.returncode != 0:
            log_message("Hata: Xorg-7.7 yüklü değil!")
            install_tce_package("Xorg-7.7")
    except:
        log_message("Hata: Xorg-7.7 kontrolü başarısız!")
        status = False

    return status

# Ağ bağlantısını kontrol et ve Wi-Fi bağlan
def check_and_connect_network(stdscr):
    log_message("Ağ bağlantısı kontrol ediliyor...")
    try:
        result = subprocess.run(["ping", "-c", "1", "google.com"], capture_output=True, text=True)
        if result.returncode == 0:
            log_message("Ağ bağlantısı mevcut.")
            return True
    except:
        log_message("Ağ bağlantısı yok, Wi-Fi taranıyor...")

    # Wi-Fi tarama
    display_status(stdscr, "Wi-Fi ağları taranıyor...")
    try:
        result = subprocess.run(["iwlist", "wlan0", "scan"], capture_output=True, text=True)
        networks = re.findall(r"ESSID:\"(.*?)\"", result.stdout)
        if not networks:
            log_message("Hata: Wi-Fi ağları bulunamadı!")
            display_status(stdscr, "Hata: Wi-Fi ağları bulunamadı!")
            time.sleep(5)
            return False
    except:
        log_message("Hata: iwlist komutu çalışmadı!")
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
        subprocess.run(["sudo", "wpa_supplicant", "-B", "-i", "wlan0", "-c", "/tmp/wpa.conf"], check=True)
        subprocess.run(["sudo", "udhcpc", "-i", "wlan0"], check=True)
        log_message(f"{selected_network} bağlandı.")
        return True
    except:
        log_message("Hata: Wi-Fi bağlantısı başarısız!")
        display_status(stdscr, "Hata: Wi-Fi bağlantısı başarısız!")
        time.sleep(5)
        return False

# Tiny Core paketini yükle
def install_tce_package(package_name):
    try:
        log_message(f"Yükleniyor: {package_name}")
        result = subprocess.run(["tce-load", "-w", "-i", package_name], capture_output=True, text=True)
        if result.returncode == 0:
            log_message(f"{package_name} başarıyla yüklendi.")
            with open(os.path.join(TCE_DIR, "onboot.lst"), "a") as f:
                f.write(f"{package_name}\n")
            subprocess.run(["filetool.sh", "-b"], check=True)
        else:
            log_message(f"Hata: {package_name} yüklenemedi: {result.stderr}")
    except subprocess.CalledProcessError as e:
        log_message(f"Yükleme hatası: {e}")

# Node.js ve npm kur
def install_node_npm():
    log_message("Node.js ve npm kontrol ediliyor...")
    try:
        result = subprocess.run(["node", "-v"], capture_output=True, text=True)
        npm_result = subprocess.run(["npm", "-v"], capture_output=True, text=True)
        if result.returncode == 0 and npm_result.returncode == 0:
            log_message(f"Node.js {result.stdout.strip()} ve npm {npm_result.stdout.strip()} yüklü.")
            return True
    except:
        log_message("Node.js veya npm yüklü değil, kuruluyor...")

    try:
        install_tce_package("nodejs")
        if subprocess.run(["npm", "-v"], capture_output=True).returncode != 0:
            log_message("npm eksik, manuel kurulum yapılıyor...")
            node_url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz"
            subprocess.run(["wget", node_url, "-O", "/tmp/node.tar.xz"], check=True)
            subprocess.run(["sudo", "tar", "-xJf", "/tmp/node.tar.xz", "-C", "/usr/local"], check=True)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/node", "/usr/local/bin/node"], check=True)
            subprocess.run(["sudo", "ln", "-sf", f"/usr/local/node-v{NODE_VERSION}-linux-x64/bin/npm", "/usr/local/bin/npm"], check=True)
            log_message("Node.js ve npm manuel olarak yüklendi.")
        return True
    except:
        log_message("Hata: Node.js ve npm kurulumu başarısız!")
        return False

# EDEX-UI’yi klonla ve özelleştir
def install_and_customize_edex_ui():
    log_message("EDEX-UI kontrol ediliyor...")
    if not os.path.exists(EDEX_DIR):
        log_message("EDEX-UI klonlanıyor...")
        try:
            subprocess.run(["git", "clone", EDEX_REPO, EDEX_DIR], check=True)
            log_message("EDEX-UI başarıyla klonlandı.")
        except:
            log_message("Hata: EDEX-UI klonlama başarısız!")
            return False

    # package.json kontrolü ve bağımlılık yükleme
    package_json_path = os.path.join(EDEX_DIR, "package.json")
    if not os.path.exists(package_json_path):
        log_message("Hata: package.json bulunamadı!")
        return False

    try:
        subprocess.run(["npm", "install"], cwd=EDEX_DIR, check=True)
        log_message("npm bağımlılıkları yüklendi.")
    except:
        log_message("Hata: npm bağımlılıkları yüklenemedi!")
        return False

    # EDEX-UI özelleştirme (örneğin, isim değişikliği)
    settings_path = os.path.join(EDEX_DIR, "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
            settings["shell"] = "BERKE OS Terminal"  # İsim özelleştirme
            settings["theme"] = "tron"  # Örnek tema değişikliği
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)
            log_message("EDEX-UI ayarları özelleştirildi.")
        except:
            log_message("Hata: EDEX-UI ayarları özelleştirilemedi!")

    # Dosya yönetim modülü için yapılandırma
    try:
        fs_module_path = os.path.join(EDEX_DIR, "src", "components", "filesystem")
        if os.path.exists(fs_module_path):
            log_message("Dosya yönetim modülü tespit edildi.")
        else:
            log_message("Uyarı: Dosya yönetim modülü eksik, EDEX-UI yeniden klonlanabilir.")
    except:
        log_message("Hata: Dosya yönetim modülü kontrolü başarısız!")
        return False

    return True

# JavaScript dosyasını kontrol et
def check_js_file(file_path):
    log_message(f"JavaScript dosyası kontrol ediliyor: {file_path}")
    try:
        result = subprocess.run(["node", "-c", file_path], capture_output=True, text=True)
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
    backup_path = os.path.join(BACKUP_DIR, os.path.relpath(file_path, ROOT_DIR))
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy(file_path, backup_path)
    log_message(f"Yedek oluşturuldu: {backup_path}")

# Terminal tabanlı web tarayıcı
def web_search(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Web Arama (Çıkmak için 'q' girin)")
    stdscr.addstr(1, 0, "Sorgu: ")
    stdscr.refresh()
    query = stdscr.getstr().decode()
    if query.lower() == "q":
        return

    # Google araması (basit bir API yerine doğrudan w3m ile)
    page = 1
    while True:
        display_status(stdscr, f"Arama yapılıyor: {query} (Sayfa {page})...")
        try:
            # Google arama URL’si (basit scraping)
            url = f"https://www.google.com/search?q={quote(query)}&start={(page-1)*10}"
            result = subprocess.run(["w3m", "-dump", url], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            results = []
            for line in lines:
                if line.startswith("  ") and "http" in line:
                    results.append(line.strip())
            results = results[:7]  # İlk 7 sonuç

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
                        subprocess.run(["w3m", url])
                    else:
                        stdscr.addstr(9, 0, "Geçersiz sıra numarası!")
                        stdscr.refresh()
                        time.sleep(2)
                except:
                    stdscr.addstr(9, 0, "Hata: Geçersiz komut!")
                    stdscr.refresh()
                    time.sleep(2)
            elif cmd.lower() == "q":
                break
        except:
            log_message("Hata: Arama başarısız!")
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
    except:
        log_message("Hata: EDEX-UI başlatılamadı!")
        return False

# Konfigürasyon dosyasını oku/yaz
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"default_edex": False}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    subprocess.run(["filetool.sh", "-b"], check=True)

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
    for i, line in enumerate(ascii_art.split("\n")):
        stdscr.addstr(i, 0, line)
    stdscr.addstr(len(ascii_art.split("\n")) + 1, 0, f"Durum: {status}")
    stdscr.refresh()

def main(stdscr):
    # Curses ayarları
    curses.curs_set(0)
    display_status(stdscr, "Başlatılıyor...")

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
    for dirpath, _, filenames in os.walk(EDEX_DIR):
        for filename in filenames:
            if filename.endswith(".js"):
                js_files.append(os.path.join(dirpath, filename))
    for js_file in js_files:
        create_backup(js_file)
        if not check_js_file(js_file):
            log_message(f"Uyarı: {js_file} hatalı, yedekten geri yüklendi veya düzeltilemedi!")
            display_status(stdscr, f"Uyarı: {os.path.basename(js_file)} hatalı!")

    # Varsayılan EDEX-UI sorusu
    stdscr.clear()
    stdscr.addstr(0, 0, "EDEX-UI her başlangıçta varsayılan olarak başlatılsın mı? (e/h)")
    stdscr.refresh()
    choice = stdscr.getch()
    config["default_edex"] = choice == ord("e")
    save_config(config)

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
    curses.wrapper(main)
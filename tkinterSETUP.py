import subprocess
import logging
import sys
import os

# Loglama ayarları
LOG_FILE = "/home/tc/setup_tkinter.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Gerekli TinyCore paketleri
TCE_PACKAGES = ["tcl", "tk", "libX11", "libfontconfig", "libXft"]

def run_command(command, error_msg):
    """Komutu çalıştırır ve hata kontrolü yapar."""
    try:
        result = subprocess.run(command, check=True, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"Komut başarılı: {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"{error_msg}: {e.stderr}")
        print(f"Hata: {error_msg} - Detaylar: {LOG_FILE}")
        return False

def install_tce_packages():
    """TinyCore paketlerini yükler."""
    print("Tkinter için TinyCore paketleri yükleniyor...")
    for pkg in TCE_PACKAGES:
        if not run_command(["tce-load", "-wi", pkg], f"Paket yüklenemedi: {pkg}"):
            return False
    return True

def set_library_path():
    """Kütüphane yolunu günceller."""
    print("Kütüphane yolu ayarlanıyor...")
    os.environ["LD_LIBRARY_PATH"] = "/usr/local/lib:/usr/lib:" + os.environ.get("LD_LIBRARY_PATH", "")
    with open("/home/tc/.ashrc", "a") as f:
        f.write('export LD_LIBRARY_PATH=/usr/local/lib:/usr/lib:$LD_LIBRARY_PATH\n')
    logging.info("LD_LIBRARY_PATH güncellendi")
    return True

def test_tkinter():
    """Tkinter'ın çalıştığını test eder."""
    print("Tkinter test ediliyor...")
    try:
        result = subprocess.run(["python3.9", "-c", "import tkinter; print(tkinter.TkVersion)"],
                               check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"Tkinter testi başarılı: {result.stdout}")
        print(f"Tkinter çalışıyor! Sürüm: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Tkinter testi başarısız: {e.stderr}")
        print(f"Hata: Tkinter çalışmıyor - Detaylar: {LOG_FILE}")
        return False

def main():
    """Ana fonksiyon."""
    print("Tkinter Kurulum Betiği")
    print("Log dosyası: ", LOG_FILE)

    if not install_tce_packages():
        sys.exit(1)
    if not set_library_path():
        sys.exit(1)
    if not test_tkinter():
        sys.exit(1)
    print("Tkinter başarıyla kuruldu ve çalışıyor!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Kullanıcı tarafından iptal edildi")
        print("\nKurulum iptal edildi")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Beklenmeyen hata: {str(e)}")
        print(f"Beklenmeyen hata oluştu - Detaylar: {LOG_FILE}")
        sys.exit(1)

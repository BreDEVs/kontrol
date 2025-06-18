#!/usr/bin/env python3
import os, subprocess, urllib.request, re
import tkinter as tk
from tkinter import ttk, messagebox

BERKE_URL = "https://raw.githubusercontent.com/BreDEVs/kontrol/main/BERKE0S.py"
APPNAME = "berke0s"
PKGDIR = f"{APPNAME}"
TCE_DIR = "/mnt/sda1/tce/optional"

def log(msg):
    progress.insert(tk.END, msg + "\n")
    progress.see(tk.END)
    root.update()

def download():
    log("→ BERKE0S.py indiriliyor...")
    os.makedirs(f"{PKGDIR}/usr/local/bin", exist_ok=True)
    urllib.request.urlretrieve(BERKE_URL, f"{PKGDIR}/usr/local/bin/{APPNAME}.py")
    os.chmod(f"{PKGDIR}/usr/local/bin/{APPNAME}.py", 0o755)

def find_deps():
    log("→ Bağımlılıklar belirleniyor...")
    content = open(f"{PKGDIR}/usr/local/bin/{APPNAME}.py").read()
    deps = set(re.findall(r"import\s+(\w+)", content)) | set(re.findall(r"from\s+(\w+)", content))
    deps = {d for d in deps if d not in ("os","sys","subprocess","re","urllib","tkinter")}
    log(f"   Bulunan: {', '.join(deps)}")
    return deps

def install_deps(deps):
    log("→ Pip ile bağımlılıklar yükleniyor...")
    for d in deps:
        log(f"   pip3 install {d} …")
        subprocess.run(["pip3", "install", "--target=" + f"{PKGDIR}/usr/local/lib/python3.8/site-packages", d])

def make_tcz():
    log("→ .tcz paketi oluşturuluyor...")
    subprocess.run(["mksquashfs", PKGDIR, f"{APPNAME}.tcz", "-noappend"])

def write_meta():
    log("→ .dep ve .info dosyaları yazılıyor...")
    with open(f"{APPNAME}.tcz.dep","w") as f:
        f.write("python3.8.tcz\n")
    size_kb = os.path.getsize(f"{APPNAME}.tcz")//1024
    with open(f"{APPNAME}.tcz.info","w") as f:
        f.write(f"Title: {APPNAME}\nDescription: BERKE0S\nVersion:1.0\nAuthor:Berke\nSize:{size_kb}K\n")

def install_tcz():
    log("→ Paket Tiny Core sistemine kuruluyor…")
    os.makedirs(TCE_DIR, exist_ok=True)
    for ext in (".tcz", ".tcz.dep", ".tcz.info"):
        subprocess.run(["cp", f"{APPNAME}{ext}", TCE_DIR])
    with open("/mnt/sda1/tce/onboot.lst","a") as f:
        f.write(f"{APPNAME}.tcz\n")

def setup_autostart():
    log("→ bootlocal.sh içine çalıştırma komutu ekleniyor…")
    bl = "/opt/bootlocal.sh"
    cmd = f"python3 /usr/local/bin/{APPNAME}.py &\n"
    if os.path.exists(bl):
        with open(bl,"r+") as f:
            data = f.read()
            if cmd not in data:
                f.write(cmd)
    else:
        with open(bl,"w") as f:
            f.write(cmd)
    subprocess.run(["filetool.sh","-b"])

def run_install():
    try:
        download()
        deps = find_deps()
        install_deps(deps)
        make_tcz()
        write_meta()
        install_tcz()
        setup_autostart()
        messagebox.showinfo("Bitti", "BERKE0S başarıyla kuruldu!\nSistemi yeniden başlatabilirsiniz.")
    except Exception as e:
        messagebox.showerror("Hata", str(e))

root = tk.Tk()
root.title("BERKE0S Kurulum Aracı")
root.geometry("500x400")

frm = ttk.Frame(root, padding=10)
frm.pack(expand=True, fill=tk.BOTH)
ttk.Label(frm, text="BERKE0S Kurulum Aracı", font=("Arial",14)).pack(pady=5)
ttk.Button(frm, text="Kurulumu Başlat", command=run_install).pack(pady=10)
progress = tk.Text(frm, state=tk.NORMAL)
progress.pack(expand=True, fill=tk.BOTH)

root.mainloop()

import os
import sys
import time
import json
import subprocess
import threading
import signal
import psutil
import socket
import bcrypt
import re
import shutil
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatter import Formatter
from pygments.lex import lex
import getpass
import datetime
import hashlib
import logging
import queue
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import pty
import fcntl
import termios
import uuid
import base64
from io import BytesIO
from urllib.parse import quote
import zipfile
import tarfile
import glob
import pwd
import grp
import stat
import imaplib
import email
import smtplib
from email.message import EmailMessage
from flask import Flask, request, jsonify

### --- CONFIGURATION AND INITIALIZATION ---
CONFIG_DIR = "/home/tc/.berke0s"
CONFIG_FILE = f"{CONFIG_DIR}/config.json"
SESSION_FILE = f"{CONFIG_DIR}/session.json"
EULA_FILE = f"{CONFIG_DIR}/eula.txt"
LOG_FILE = f"{CONFIG_DIR}/berke0s.log"
THEME_DIR = f"{CONFIG_DIR}/themes"
PLUGIN_DIR = f"{CONFIG_DIR}/plugins"

# Setup logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Default configuration
DEFAULT_CONFIG = {
    "first_boot": True,
    "language": "en_US",
    "timezone": "UTC",
    "theme": "monochrome",
    "users": [],
    "wifi": {"ssid": "", "password": ""},
    "eula_accepted": False,
    "desktop": {
        "wallpaper": "",
        "icon_size": 48,
        "grid_snap": True
    },
    "notifications": {
        "enabled": True,
        "timeout": 5000
    },
    "power": {
        "sleep_timeout": 600,
        "screen_off_timeout": 300
    },
    "accessibility": {
        "high_contrast": False,
        "screen_reader": False,
        "font_scale": 1.0
    }
}

# Ensure directories exist
for d in [CONFIG_DIR, THEME_DIR, PLUGIN_DIR]:
    os.makedirs(d, exist_ok=True)

# Load or create config
def load_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Config load error: {e}")
        return DEFAULT_CONFIG

# Save config
def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logging.error(f"Config save error: {e}")

# Load or create session
def load_session():
    try:
        if not os.path.exists(SESSION_FILE):
            return {"open_windows": [], "desktop_icons": []}
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Session load error: {e}")
        return {"open_windows": [], "desktop_icons": []}

# Save session
def save_session(session):
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session, f, indent=4)
    except Exception as e:
        logging.error(f"Session save error: {e}")

# Install required packages for TinyCore
def install_packages():
    packages = [
        "python3.9", "tk", "tcl", "python3.9-pip", "alsa", "bluez",
        "e2fsprogs", "nano", "htop", "bash", "tar", "zip", "wireless-tools",
        "scrot", "libnotify", "espeak", "mpv"
    ]
    for pkg in packages:
        try:
            subprocess.run(["tce-load", "-wi", pkg], check=True, capture_output=True)
            logging.info(f"Installed package: {pkg}")
        except subprocess.CalledProcessError as e:
            logging.warning(f"Package install failed: {pkg} - {e}")
    try:
        subprocess.run(["pip3", "install", "psutil", "Pillow", "flask"], check=True)
        logging.info("Installed Python dependencies")
    except subprocess.CalledProcessError as e:
        logging.warning(f"Python dependencies install failed: {e}")

# Setup autostart
def setup_autostart():
    try:
        bootlocal = "/opt/bootlocal.sh"
        cmd = f"python3 /usr/local/bin/BERKE0S.py &\n"
        if not os.path.exists(bootlocal):
            with open(bootlocal, 'w') as f:
                f.write(cmd)
        else:
            with open(bootlocal, 'r') as f:
                content = f.read()
            if cmd not in content:
                with open(bootlocal, 'a') as f:
                    f.write(cmd)
        subprocess.run(["filetool.sh", "-b"], check=True)
        logging.info("Autostart configured")
    except Exception as e:
        logging.error(f"Autostart setup error: {e}")

### --- UI THEME AND ICONS ---
CSS_STYLE = """
:root {
    --bg: rgba(0, 0, 0, 0.4);
    --fg: #ffffff;
    --accent: rgba(255, 255, 255, 0.2);
    --border: #ffffff;
}
body {
    background: var(--bg);
    color: var(--fg);
    font-family: system-ui, sans-serif;
    font-size: 12px;
    margin: 0;
    backdrop-filter: blur(5px);
    user-select: none;
}
.window {
    border: 1px solid var(--border);
    background: var(--bg);
    transition: all 0.2s ease;
    position: absolute;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}
.titlebar {
    background: var(--accent);
    padding: 5px;
    cursor: move;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.taskbar {
    position: fixed;
    bottom: 0;
    width: 100%;
    background: rgba(0, 0, 0, 0.6);
    height: 32px;
    display: flex;
    align-items: center;
    padding: 0 10px;
    z-index: 1000;
}
.taskbar .start {
    cursor: pointer;
    padding: 5px;
}
.taskbar .clock {
    font-weight: bold;
    flex-grow: 1;
    text-align: center;
}
.taskbar .widgets img {
    width: 20px;
    height: 20px;
    margin-left: 8px;
}
button {
    background: var(--accent);
    border: 1px solid var(--border);
    color: var(--fg);
    padding: 5px 10px;
    cursor: pointer;
    transition: all 0.2s ease;
    border-radius: 3px;
}
button:hover {
    background: rgba(255, 255, 255, 0.3);
}
input, select, textarea {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid var(--border);
    color: var(--fg);
    padding: 5px;
    border-radius: 3px;
}
.listbox {
    background: rgba(0, 0, 0, 0.6);
    color: var(--fg);
    border: 1px solid var(--border);
}
.context-menu {
    background: var(--bg);
    border: 1px solid var(--border);
    padding: 5px;
}
.desktop-icon {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 80px;
    margin: 10px;
    cursor: pointer;
}
.desktop-icon img {
    width: 48px;
    height: 48px;
}
.desktop-icon span {
    color: var(--fg);
    text-align: center;
    margin-top: 5px;
    font-size: 11px;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
"""

BATTERY_ICON = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
    <rect x="2" y="7" width="16" height="10" rx="2"/>
    <path d="M20 10v4"/>
    <rect x="4" y="9" width="{fill_width}" height="6" fill="#fff"/>
</svg>
"""
WIFI_ICON = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
    <path d="M12 20h.01"/>
    <path d="M2 8.82a15 15 0 0 1 20 0"/>
    <path d="M5 12.82a10 10 0 0 1 14 0"/>
    <path d="M8 16.82a5 5 0 0 1 8 0"/>
</svg>
"""
VOLUME_ICON = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
</svg>
"""
BLUETOOTH_ICON = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
    <path d="M7 7l10 10-5 5V2l5 5L7 17"/>
</svg>
"""
FILE_ICON = """
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
</svg>
"""
FOLDER_ICON = """
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
</svg>
"""
CALCULATOR_ICON = """
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
    <rect x="4" y="2" width="16" height="20" rx="2"/>
    <line x1="8" y1="6" x2="16" y2="6"/>
    <line x1="8" y1="10" x2="16" y2="10"/>
    <line x1="8" y1="14" x2="16" y2="14"/>
    <line x1="8" y1="18" x2="16" y2="18"/>
</svg>
"""
SYSINFO_ICON = """
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="16" x2="12" y2="12"/>
    <line x1="12" y1="8" x2="12" y2="8"/>
</svg>
"""

### --- PLUGINS SYSTEM ---
class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.load_plugins()

    def load_plugins(self):
        for plugin_file in glob.glob(f"{PLUGIN_DIR}/*.py"):
            try:
                module_name = os.path.basename(plugin_file).replace('.py', '')
                spec = __import__('importlib.util').spec_from_file_location(module_name, plugin_file)
                module = __import__('importlib.util').module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'register_plugin'):
                    plugin = module.register_plugin()
                    self.plugins[module_name] = plugin
                    logging.info(f"Loaded plugin: {module_name}")
                else:
                    logging.warning(f"Plugin {module_name} has no register_plugin function")
            except Exception as e:
                logging.error(f"Plugin load error: {module_name} - {e}")

    def execute_plugin(self, plugin_name, *args, **kwargs):
        if plugin_name in self.plugins:
            try:
                return self.plugins[plugin_name](*args, **kwargs)
            except Exception as e:
                logging.error(f"Plugin execution error: {plugin_name} - {e}")

### --- NOTIFICATION SYSTEM ---
class NotificationSystem:
    def __init__(self):
        self.config = load_config()

    def send(self, title, message, timeout=5000):
        if not self.config["notifications"]["enabled"]:
            return
        try:
            subprocess.run(["notify-send", "-t", str(timeout), title, message], check=True)
            logging.info(f"Notification sent: {title} - {message}")
        except Exception as e:
            logging.warning(f"Notification error: {e}")
            # Fallback to logging if notify-send is unavailable
            logging.info(f"Notification fallback: {title} - {message}")

### --- DESKTOP AND WINDOW MANAGER ---
class WindowManager:
    def __init__(self):
        self.windows = []
        self.z_index = 100
        try:
            self.root = tk.Tk()
            self.root.attributes('-fullscreen', True)
            self.root.configure(bg='black')
        except Exception as e:
            logging.error(f"Tkinter initialization error: {e}")
            raise RuntimeError("Failed to initialize Tkinter")
        self.config = load_config()
        self.notifications = NotificationSystem()
        self.plugins = PluginManager()
        
        # Desktop canvas
        self.desktop = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.desktop.pack(fill=tk.BOTH, expand=True)
        self.desktop_icons = {}
        self.load_desktop_icons()
        
        # Taskbar
        self.taskbar = tk.Frame(self.root, bg='rgba(0,0,0,0.6)', height=32)
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Taskbar elements
        self.start_btn = tk.Label(self.taskbar, text="☰", fg="white", bg="rgba(0,0,0,0.6)", 
                                font=("Arial", 14), cursor="hand2")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.taskbar_windows = tk.Frame(self.taskbar, bg="rgba(0,0,0,0.6)")
        self.taskbar_windows.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.clock = tk.Label(self.taskbar, fg="white", bg="rgba(0,0,0,0.6)", font=("Arial", 12))
        self.clock.pack(side=tk.LEFT, padx=10)
        self.update_clock()
        
        # Widgets
        self.widgets = tk.Frame(self.taskbar, bg="rgba(0,0,0,0.6)")
        self.widgets.pack(side=tk.RIGHT)
        self.battery_label = tk.Label(self.widgets, bg="rgba(0,0,0,0.6)")
        self.battery_label.pack(side=tk.RIGHT, padx=2)
        self.wifi_label = tk.Label(self.widgets, bg="rgba(0,0,0,0.6)")
        self.wifi_label.pack(side=tk.RIGHT, padx=2)
        self.volume_label = tk.Label(self.widgets, bg="rgba(0,0,0,0.6)")
        self.volume_label.pack(side=tk.RIGHT, padx=2)
        self.bluetooth_label = tk.Label(self.widgets, bg="rgba(0,0,0,0.6)")
        self.bluetooth_label.pack(side=tk.RIGHT, padx=2)
        
        # Bindings
        self.desktop.bind("<Button-3>", self.show_desktop_menu)
        
        # Power management
        self.last_activity = time.time()
        self.root.bind("<Any-KeyPress>", self.reset_activity)
        self.root.bind("<Any-Motion>", self.reset_activity)
        self.check_power_state()
        
        # Update widgets
        self.update_widgets()

    def reset_activity(self, event):
        self.last_activity = time.time()

    def check_power_state(self):
        current_time = time.time()
        if current_time - self.last_activity > self.config["power"]["screen_off_timeout"]:
            self.screen_off()
        elif current_time - self.last_activity > self.config["power"]["sleep_timeout"]:
            self.suspend()
        self.root.after(60000, self.check_power_state)

    def screen_off(self):
        try:
            subprocess.run(["xset", "dpms", "force", "off"], check=True)
        except Exception as e:
            logging.warning(f"Screen off error: {e}")

    def suspend(self):
        try:
            subprocess.run(["sudo", "pm-suspend"], check=True)
        except Exception as e:
            logging.warning(f"Suspend error: {e}")

    def update_clock(self):
        try:
            self.clock.config(text=datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y"))
            self.root.after(1000, self.update_clock)
        except Exception as e:
            logging.warning(f"Clock update error: {e}")

    def update_widgets(self):
        # Battery
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = int(battery.percent)
                fill_width = (percent / 100) * 12
                svg = BATTERY_ICON.format(fill_width=fill_width)
                self.battery_label.config(image=self.svg_to_photo(svg))
        except Exception as e:
            logging.warning(f"Battery widget error: {e}")

        # WiFi
        try:
            output = subprocess.check_output(["iwconfig"], text=True, stderr=subprocess.DEVNULL)
            strength = re.search(r"Signal level=(-?\d+)", output)
            if strength:
                level = int(strength.group(1))
                color = "#fff" if level > -70 else "#888"
                self.wifi_label.config(image=self.svg_to_photo(WIFI_ICON.replace("#fff", color)))
        except Exception as e:
            logging.warning(f"WiFi widget error: {e}")

        # Volume
        try:
            output = subprocess.check_output(["amixer", "get", "Master"], text=True)
            volume = re.search(r"\[(\d+)%\]", output)
            if volume:
                vol = int(volume.group(1))
                color = "#fff" if vol > 0 else "#888"
                self.volume_label.config(image=self.svg_to_photo(VOLUME_ICON.replace("#fff", color)))
        except Exception as e:
            logging.warning(f"Volume widget error: {e}")

        # Bluetooth
        try:
            output = subprocess.check_output(["bluetoothctl", "show"], text=True)
            powered = "Powered: yes" in output
            color = "#fff" if powered else "#888"
            self.bluetooth_label.config(image=self.svg_to_photo(BLUETOOTH_ICON.replace("#fff", color)))
        except Exception as e:
            logging.warning(f"Bluetooth widget error: {e}")

        self.root.after(5000, self.update_widgets)

    def svg_to_photo(self, svg):
        try:
            img = Image.open(BytesIO(svg.encode())).convert("RGBA")
            img = img.resize((20, 20), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logging.error(f"SVG render error: {e}")
            img = Image.new("RGBA", (20, 20), (255, 255, 255, 0))
            return ImageTk.PhotoImage(img)

    def load_desktop_icons(self):
        session = load_session()
        for icon in session["desktop_icons"]:
            self.add_desktop_icon(icon["path"], icon["x"], icon["y"])

    def add_desktop_icon(self, path, x, y):
        icon_id = str(uuid.uuid4())
        icon_type = FOLDER_ICON if os.path.isdir(path) else FILE_ICON
        icon_img = self.svg_to_photo(icon_type)
        
        name = os.path.basename(path)
        icon = self.desktop.create_image(x, y, image=icon_img, anchor=tk.NW)
        text = self.desktop.create_text(x + 24, y + 56, text=name, fill="white", 
                                      font=("Arial", 11), anchor=tk.N)
        
        self.desktop_icons[icon_id] = {
            "path": path,
            "icon": icon,
            "text": text,
            "image": icon_img
        }
        
        self.desktop.tag_bind(icon, "<Button-1>", lambda e: self.handle_icon_click(icon_id))
        self.desktop.tag_bind(icon, "<Button-3>", lambda e: self.show_icon_menu(e, icon_id))
        self.desktop.tag_bind(icon, "<B1-Motion>", lambda e: self.drag_icon(e, icon_id))
        
        session = load_session()
        session["desktop_icons"].append({"path": path, "x": x, "y": y})
        save_session(session)

    def handle_icon_click(self, icon_id):
        path = self.desktop_icons[icon_id]["path"]
        if os.path.isdir(path):
            FileManager(self).open(path)
        else:
            FileManager(self).navigate_file(path)

    def drag_icon(self, event, icon_id):
        icon = self.desktop_icons[icon_id]
        x, y = event.x, event.y
        if self.config["desktop"]["grid_snap"]:
            grid_size = self.config["desktop"]["icon_size"]
            x = round(x / grid_size) * grid_size
            y = round(y / grid_size) * grid_size
        self.desktop.coords(icon["icon"], x, y)
        self.desktop.coords(icon["text"], x + 24, y + 56)
        
        session = load_session()
        for s_icon in session["desktop_icons"]:
            if s_icon["path"] == icon["path"]:
                s_icon["x"], s_icon["y"] = x, y
        save_session(session)

    def show_icon_menu(self, event, icon_id):
        menu = tk.Menu(self.root, tearoff=0, bg="rgba(0,0,0,0.4)", fg="white")
        path = self.desktop_icons[icon_id]["path"]
        menu.add_command(label="Open", command=lambda: self.handle_icon_click(icon_id))
        menu.add_command(label="Delete", command=lambda: self.delete_icon(icon_id))
        menu.add_separator()
        menu.add_command(label="Properties", command=lambda: self.show_properties(path))
        menu.post(event.x_root, event.y_root)

    def delete_icon(self, icon_id):
        icon = self.desktop_icons[icon_id]
        self.desktop.delete(icon["icon"])
        self.desktop.delete(icon["text"])
        session = load_session()
        session["desktop_icons"] = [i for i in session["desktop_icons"] if i["path"] != icon["path"]]
        save_session(session)
        del self.desktop_icons[icon_id]

    def show_properties(self, path):
        try:
            stats = os.stat(path)
            content = f"""
            Path: {path}
            Type: {'Directory' if os.path.isdir(path) else 'File'}
            Size: {stats.st_size} bytes
            Modified: {datetime.datetime.fromtimestamp(stats.st_mtime)}
            Permissions: {oct(stats.st_mode)[-3:]}
            """
            self.create_window("Properties", lambda f: tk.Label(f, text=content, fg="white", 
                                                            bg="rgba(0,0,0,0.4)", justify=tk.LEFT).pack(padx=10, pady=10))
        except Exception as e:
            logging.error(f"Properties error: {path} - {e}")

    def create_window(self, title, content, x=100, y=100, width=600, height=400):
        window = tk.Toplevel(self.root)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.overrideredirect(True)
        window.configure(bg='rgba(0,0,0,0.4)')
        window.attributes('-alpha', 0.95)
        
        # Titlebar
        titlebar = tk.Frame(window, bg='rgba(255,255,255,0.2)')
        titlebar.pack(fill=tk.X)
        tk.Label(titlebar, text=title, fg="white", bg='rgba(255,255,255,0.2)', 
                font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        btn_frame = tk.Frame(titlebar, bg='rgba(255,255,255,0.2)')
        btn_frame.pack(side=tk.RIGHT)
        tk.Button(btn_frame, text="_", command=lambda: window.iconify(), fg="white", 
                 bg='rgba(255,255,255,0.2)', bd=0).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="□", command=lambda: self.toggle_maximize(window), 
                 fg="white", bg='rgba(255,255,255,0.2)', bd=0).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="✕", command=lambda: self.close_window(window), 
                 fg="white", bg='rgba(255,255,255,0.2)', bd=0).pack(side=tk.LEFT)
        
        # Content
        content_frame = tk.Frame(window, bg='rgba(0,0,0,0.4)')
        content_frame.pack(fill=tk.BOTH, expand=True)
        content(content_frame)
        
        # Window management
        self.make_draggable(window, titlebar)
        self.make_resizable(window)
        window.bind("<Button-1>", lambda e: self.focus_window(window))
        window.bind("<Button-3>", lambda e: self.show_context_menu(e, window))
        self.windows.append(window)
        
        # Taskbar button
        btn = tk.Button(self.taskbar_windows, text=title, fg="white", bg="rgba(0,0,0,0.6)", 
                       bd=0, command=lambda: self.toggle_window(window))
        btn.pack(side=tk.LEFT, padx=2)
        window.taskbar_btn = btn
        
        # Save session
        session = load_session()
        session["open_windows"].append({
            "title": title,
            "x": x, "y": y, "width": width, "height": height
        })
        save_session(session)
        
        return window

    def toggle_window(self, window):
        if window.state() == "withdrawn":
            window.deiconify()
        else:
            window.withdraw()

    def toggle_maximize(self, window):
        if not hasattr(window, '_is_maximized') or not window._is_maximized:
            window._geometry = window.geometry()
            window.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()-32}+0+0")
            window._is_maximized = True
        else:
            window.geometry(window._geometry)
            window._is_maximized = False

    def close_window(self, window):
        try:
            self.windows.remove(window)
            window.taskbar_btn.destroy()
            session = load_session()
            session["open_windows"] = [w for w in session["open_windows"] if w["title"] != window.title()]
            save_session(session)
            window.destroy()
        except Exception as e:
            logging.error(f"Close window error: {e}")

    def focus_window(self, window):
        try:
            window.lift()
            self.z_index += 1
            window.configure(takefocus=True)
            window.focus_force()
        except Exception as e:
            logging.warning(f"Focus window error: {e}")

    def make_draggable(self, window, titlebar):
        titlebar.bind("<Button-1>", lambda e: self.start_drag(e, window))
        titlebar.bind("<B1-Motion>", lambda e: self.do_drag(e, window))

    def start_drag(self, event, window):
        window._drag_start_x = event.x_root
        window._drag_start_y = event.y_root
        window._window_x = window.winfo_x()
        window._window_y = window.winfo_y()

    def do_drag(self, event, window):
        if hasattr(window, '_is_maximized') and window._is_maximized:
            return
        dx = event.x_root - window._drag_start_x
        dy = event.y_root - window._drag_start_y
        window.geometry(f"+{window._window_x + dx}+{window._window_y + dy}")

    def make_resizable(self, window):
        resize_handle = tk.Frame(window, bg="white", width=10, height=10, cursor="se-resize")
        resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        resize_handle.bind("<Button-1>", lambda e: self.start_resize(e, window))
        resize_handle.bind("<B1-Motion>", lambda e: self.do_resize(e, window))

    def start_resize(self, event, window):
        window._resize_start_x = event.x_root
        window._resize_start_y = event.y_root
        window._resize_width = window.winfo_width()
        window._resize_height = window.winfo_height()

    def do_resize(self, event, window):
        dx = event.x_root - window._resize_start_x
        dy = event.y_root - window._resize_start_y
        new_width = max(200, window._resize_width + dx)
        new_height = max(150, window._resize_height + dy)
        window.geometry(f"{new_width}x{new_height}")

    def show_context_menu(self, event, window):
        menu = tk.Menu(self.root, tearoff=0, bg="rgba(0,0,0,0.4)", fg="white")
        menu.add_command(label="Close", command=lambda: self.close_window(window))
        menu.add_command(label="Maximize/Restore", command=lambda: self.toggle_maximize(window))
        menu.add_command(label="Minimize", command=window.iconify)
        menu.post(event.x_root, event.y_root)

    def show_desktop_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg="rgba(0,0,0,0.4)", fg="white")
        menu.add_command(label="New File", command=self.create_new_file)
        menu.add_command(label="New Folder", command=self.create_new_folder)
        menu.add_separator()
        menu.add_command(label="Change Wallpaper", command=self.change_wallpaper)
        menu.add_command(label="Desktop Settings", command=self.open_desktop_settings)
        menu.post(event.x_root, event.y_root)

    def create_new_file(self):
        path = os.path.join(os.environ["HOME"], f"new_file_{int(time.time())}.txt")
        open(path, 'a').close()
        self.add_desktop_icon(path, 100, 100)

    def create_new_folder(self):
        path = os.path.join(os.environ["HOME"], f"new_folder_{int(time.time())}")
        os.makedirs(path, exist_ok=True)
        self.add_desktop_icon(path, 100, 100)

    def change_wallpaper(self):
        file = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file:
            config = load_config()
            config["desktop"]["wallpaper"] = file
            save_config(config)
            self.apply_wallpaper()

    def apply_wallpaper(self):
        wallpaper = self.config["desktop"]["wallpaper"]
        if wallpaper and os.path.exists(wallpaper):
            try:
                img = Image.open(wallpaper)
                img = img.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.LANCZOS)
                self.desktop_bg = ImageTk.PhotoImage(img)
                self.desktop.create_image(0, 0, image=self.desktop_bg, anchor=tk.NW)
            except Exception as e:
                logging.warning(f"Wallpaper apply error: {e}")

    def open_desktop_settings(self):
        def build_ui(frame):
            tk.Label(frame, text="Icon Size", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
            size_var = tk.IntVar(value=self.config["desktop"]["icon_size"])
            tk.Scale(frame, from_=32, to=96, orient=tk.HORIZONTAL, variable=size_var, 
                    bg="rgba(0,0,0,0.4)", fg="white").pack()
            snap_var = tk.BooleanVar(value=self.config["desktop"]["grid_snap"])
            tk.Checkbutton(frame, text="Grid Snap", variable=snap_var, fg="white", 
                          bg="rgba(0,0,0,0.4)").pack(pady=5)
            tk.Button(frame, text="Apply", command=lambda: self.save_desktop_settings(size_var.get(), snap_var.get())).pack(pady=10)
        self.create_window("Desktop Settings", build_ui)

    def save_desktop_settings(self, icon_size, grid_snap):
        config = load_config()
        config["desktop"].update({"icon_size": icon_size, "grid_snap": grid_snap})
        save_config(config)
        self.config = config
        # Refresh icons
        session = load_session()
        for icon_id in list(self.desktop_icons.keys()):
            self.delete_icon(icon_id)
        self.load_desktop_icons()

    def shutdown(self):
        try:
            subprocess.run(["sudo", "poweroff"], check=True)
        except Exception as e:
            logging.error(f"Shutdown error: {e}")

    def reboot(self):
        try:
            subprocess.run(["sudo", "reboot"], check=True)
        except Exception as e:
            logging.error(f"Reboot error: {e}")

    def logout(self):
        try:
            session = load_session()
            session["open_windows"] = []
            save_session(session)
            self.cleanup()
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            logging.error(f"Logout error: {e}")

    def cleanup(self):
        try:
            for window in self.windows[:]:
                self.close_window(window)
            if self.root:
                self.root.destroy()
            logging.info("WindowManager cleanup completed")
        except Exception as e:
            logging.error(f"Cleanup error: {e}")

### --- RESOURCE MONITOR ---
class ResourceMonitor:
    def __init__(self, wm):
        self.wm = wm
        self.running = True
        self.cpu_history = queue.Queue(maxsize=60)
        self.ram_history = queue.Queue(maxsize=60)
        threading.Thread(target=self.monitor, daemon=True).start()

    def monitor(self):
        while self.running:
            try:
                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory().percent
                self.cpu_history.put(cpu)
                self.ram_history.put(mem)
                
                if cpu > 80 or mem > 80:
                    self.wm.notifications.send(
                        "High Resource Usage",
                        f"CPU: {cpu:.1f}% Memory: {mem:.1f}%"
                    )
                
                for proc in psutil.process_iter(['pid', 'status']):
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        try:
                            proc.terminate()
                            logging.info(f"Terminated zombie process: {proc.pid}")
                        except:
                            pass
                
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Resource monitor error: {e}")

    def get_usage_history(self):
        return {
            "cpu": list(self.cpu_history.queue),
            "ram": list(self.ram_history.queue)
        }

### --- ONBOARDING WIZARD ---
class OnboardingWizard:
    def __init__(self, wm, config):
        self.wm = wm
        self.config = config
        self.window = None
        self.locales = {
            "en_US": "English (US)",
            "es_ES": "Español",
            "fr_FR": "Français",
            "de_DE": "Deutsch"
        }
        self.timezones = [
            "UTC", "America/New_York", "Europe/London", "Asia/Tokyo",
            "Australia/Sydney", "America/Los_Angeles", "Europe/Berlin"
        ]

    def open(self):
        if not self.config["first_boot"]:
            return
        self.window = self.wm.create_window("Berke0S Setup", self.build_ui, width=500, height=500)

    def build_ui(self, frame):
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Welcome
        welcome = ttk.Frame(notebook)
        notebook.add(welcome, text="Welcome")
        tk.Label(welcome, text="Welcome to Berke0S!\nLet's get started.", 
                fg="white", bg="rgba(0,0,0,0.4)", font=("Arial", 14)).pack(pady=20)

        # Language
        lang_frame = ttk.Frame(notebook)
        notebook.add(lang_frame, text="Language")
        tk.Label(lang_frame, text="Select Language", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=10)
        lang_var = tk.StringVar(value=self.config["language"])
        ttk.Combobox(lang_frame, textvariable=lang_var, values=list(self.locales.keys()), 
                    state="readonly").pack(pady=5)

        # Timezone
        tz_frame = ttk.Frame(notebook)
        notebook.add(tz_frame, text="Timezone")
        tk.Label(tz_frame, text="Select Timezone", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=10)
        tz_var = tk.StringVar(value=self.config["timezone"])
        ttk.Combobox(tz_frame, textvariable=tz_var, values=self.timezones, 
                    state="readonly").pack(pady=5)

        # WiFi
        wifi_frame = ttk.Frame(notebook)
        notebook.add(wifi_frame, text="Wi-Fi")
        tk.Label(wifi_frame, text="Wi-Fi Network", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        ssid_var = tk.StringVar()
        ssids = self.scan_wifi()
        ssid_menu = ttk.Combobox(wifi_frame, textvariable=ssid_var, values=ssids, 
                                state="readonly")
        ssid_menu.pack(pady=5)
        tk.Button(wifi_frame, text="Refresh", command=lambda: self.refresh_wifi(ssid_menu)).pack()
        tk.Label(wifi_frame, text="Password", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        passwd_var = tk.StringVar()
        tk.Entry(wifi_frame, textvariable=passwd_var, show="*", bg="rgba(0,0,0,0.6)", 
                fg="white").pack(pady=5)

        # User
        user_frame = ttk.Frame(notebook)
        notebook.add(user_frame, text="User")
        tk.Label(user_frame, text="Username", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        user_var = tk.StringVar()
        tk.Entry(user_frame, textvariable=user_var, bg="rgba(0,0,0,0.6)", 
                fg="white").pack(pady=5)
        tk.Label(user_frame, text="Password", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        user_passwd_var = tk.StringVar()
        tk.Entry(user_frame, textvariable=user_passwd_var, show="*", 
                bg="rgba(0,0,0,0.6)", fg="white").pack(pady=5)
        tk.Label(user_frame, text="Confirm Password", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        confirm_passwd_var = tk.StringVar()
        tk.Entry(user_frame, textvariable=confirm_passwd_var, show="*", 
                bg="rgba(0,0,0,0.6)", fg="white").pack(pady=5)

        # EULA
        eula_frame = ttk.Frame(notebook)
        notebook.add(eula_frame, text="EULA")
        eula_text = tk.Text(eula_frame, height=10, bg="rgba(0,0,0,0.6)", fg="white", 
                           wrap=tk.WORD)
        eula_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        eula_text.insert(tk.END, self.get_eula_text())
        eula_text.config(state="disabled")
        accept_var = tk.BooleanVar()
        tk.Checkbutton(eula_frame, text="I accept the terms", 
                      variable=accept_var, fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)

        # Accessibility
        access_frame = ttk.Frame(notebook)
        notebook.add(access_frame, text="Accessibility")
        high_contrast_var = tk.BooleanVar(value=self.config["accessibility"]["high_contrast"])
        tk.Checkbutton(access_frame, text="High Contrast Mode", variable=high_contrast_var, 
                      fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        screen_reader_var = tk.BooleanVar(value=self.config["accessibility"]["screen_reader"])
        tk.Checkbutton(access_frame, text="Enable Screen Reader", variable=screen_reader_var, 
                      fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        font_scale_var = tk.DoubleVar(value=self.config["accessibility"]["font_scale"])
        tk.Label(access_frame, text="Font Scale", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        tk.Scale(access_frame, from_=0.8, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, 
                variable=font_scale_var, bg="rgba(0,0,0,0.6)", fg="white").pack(pady=5)

        # Finish
        tk.Button(frame, text="Finish", command=lambda: self.finish(
            lang_var.get(), tz_var.get(), ssid_var.get(), passwd_var.get(),
            user_var.get(), user_passwd_var.get(), confirm_passwd_var.get(),
            accept_var.get(), high_contrast_var.get(), screen_reader_var.get(),
            font_scale_var.get()
        )).pack(pady=10)

    def get_eula_text(self):
        default_eula = """
        Berke0S End User License Agreement
        This software is provided "as is", without warranty of any kind.
        By using Berke0S, you agree to the terms of this agreement.
        """
        try:
            if not os.path.exists(EULA_FILE):
                with open(EULA_FILE, 'w') as f:
                    f.write(default_eula)
            with open(EULA_FILE, 'r') as f:
                return f.read()
        except Exception as e:
            logging.warning(f"EULA load error: {e}")
            return default_eula

    def scan_wifi(self):
        try:
            output = subprocess.check_output(["iwconfig"], text=True, stderr=subprocess.DEVNULL)
            ssids = re.findall(r'ESSID:"(.*?)"', output)
            return list(set(ssids))
        except Exception as e:
            logging.warning(f"WiFi scan error: {e}")
            return []

    def refresh_wifi(self, combobox):
        ssids = self.scan_wifi()
        combobox["values"] = ssids

    def finish(self, lang, tz, ssid, passwd, username, passwd1, passwd2, eula_accepted, 
               high_contrast, screen_reader, font_scale):
        if not eula_accepted:
            messagebox.showerror("Error", "You must accept the EULA")
            return
        if not username or not passwd1 or passwd1 != passwd2:
            messagebox.showerror("Error", "Invalid username or passwords do not match")
            return
        if not lang or not tz:
            messagebox.showerror("Error", "Please select language and timezone")
            return

        try:
            # Update config
            self.config.update({
                "first_boot": False,
                "language": lang,
                "timezone": tz,
                "wifi": {"ssid": ssid, "password": passwd},
                "users": [{"username": username, 
                          "password": hashlib.sha256(passwd1.encode()).hexdigest()}],
                "eula_accepted": True,
                "accessibility": {
                    "high_contrast": high_contrast,
                    "screen_reader": screen_reader,
                    "font_scale": font_scale
                }
            })
            save_config(self.config)

            # Setup user
            home_dir = f"/home/{username}"
            os.makedirs(home_dir, exist_ok=True)
            subprocess.run(["sudo", "chown", f"{username}:{username}", home_dir], check=True)
            subprocess.run(["sudo", "chmod", "700", home_dir], check=True)

            # Setup timezone
            subprocess.run(["sudo", "ln", "-sf", f"/usr/share/zoneinfo/{tz}", 
                           "/etc/localtime"], check=True)

            # Setup WiFi
            if ssid and passwd:
                subprocess.run(["sudo", "iwconfig", "wlan0", "essid", ssid, "key", passwd], check=True)
                subprocess.run(["sudo", "udhcpc", "-i", "wlan0"], check=True)
                self.wm.notifications.send("Network", "Connected to Wi-Fi")

            # Setup accessibility
            if screen_reader:
                try:
                    subprocess.run(["espeak", "Welcome to Berke0S"], check=True)
                except:
                    pass

            self.window.destroy()
            self.wm.notifications.send("Setup Complete", "Berke0S is ready to use!")
            logging.info("Onboarding completed successfully")
        except Exception as e:
            logging.error(f"Onboarding finish error: {e}")
            messagebox.showerror("Error", f"Setup failed: {str(e)}")

### --- LOGIN MANAGER ---
class LoginManager:
    def __init__(self, wm, config):
        self.wm = wm
        self.config = config
        self.window = None
        self.attempts = 0
        self.lockout_time = 0

    def show_login(self):
        if time.time() < self.lockout_time:
            messagebox.showerror("Locked", 
                                f"Too many attempts. Try again in {int(self.lockout_time - time.time())} seconds")
            return
        self.window = self.wm.create_window("Login to Berke0S", self.build_ui, 
                                          width=350, height=250)

    def build_ui(self, frame):
        tk.Label(frame, text="Welcome to Berke0S", fg="white", bg="rgba(0,0,0,0.4)", 
                font=("Arial", 16)).pack(pady=10)
        tk.Label(frame, text="Username", fg="white", bg="rgba(0,0,0,0.4)").pack()
        user_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=user_var, 
                    values=[u["username"] for u in self.config["users"]], 
                    state="readonly").pack(pady=5)
        tk.Label(frame, text="Password", fg="white", bg="rgba(0,0,0,0.4)").pack()
        passwd_var = tk.StringVar()
        tk.Entry(frame, textvariable=passwd_var, show="*", bg="rgba(0,0,0,0.6)", 
                fg="white").pack(pady=5)
        tk.Button(frame, text="Login", command=lambda: self.login(user_var.get(), 
                                                                passwd_var.get())).pack(pady=10)
        tk.Button(frame, text="Guest Login", 
                 command=lambda: self.guest_login()).pack(pady=5)

    def login(self, username, password):
        hashed_pass = hashlib.sha256(password.encode()).hexdigest()
        for user in self.config["users"]:
            if user["username"] == username and user["password"] == hashed_pass:
                os.environ["USER"] = username
                os.environ["HOME"] = f"/home/{username}"
                self.window.destroy()
                self.wm.notifications.send("Welcome", f"Logged in as {username}")
                logging.info(f"User logged in: {username}")
                return
        self.attempts += 1
        if self.attempts >= 3:
            self.lockout_time = time.time() + 60
            self.window.destroy()
            messagebox.showerror("Error", "Too many attempts. Locked for 60 seconds")
            logging.warning(f"Login lockout for user: {username}")
        else:
            messagebox.showerror("Error", "Invalid credentials")
            logging.warning(f"Failed login attempt for user: {username}")

    def guest_login(self):
        os.environ["USER"] = "guest"
        os.environ["HOME"] = "/tmp/guest"
        os.makedirs("/tmp/guest", exist_ok=True)
        self.window.destroy()
        self.wm.notifications.send("Welcome", "Logged in as Guest")
        logging.info("Guest login")

### --- FILE MANAGER ---
class FileManager:
    def __init__(self, wm):
        self.wm = wm
        self.file_types = {
            ".txt": lambda path: TextEditor(self.wm).open(path),
            ".py": lambda path: TextEditor(self.wm).open(path),
            ".jpg": lambda path: self.wm.create_window("Image Viewer", 
                                                     lambda f: tk.Label(f, 
                                                                       image=tk.PhotoImage(file=path)).pack()),
            ".png": lambda path: self.wm.create_window("Image Viewer", 
                                                     lambda f: tk.Label(f, 
                                                                       image=tk.PhotoImage(file=path)).pack()),
            ".mp3": lambda path: MediaPlayer(self.wm).play(path),
            ".mp4": lambda path: MediaPlayer(self.wm).play(path),
            ".zip": lambda path: self.extract_archive(path, "zip"),
            ".tar.gz": lambda path: self.extract_archive(path, "tar.gz")
        }

    def open(self, path=None):
        self.current_path = path or os.environ["HOME"]
        self.wm.create_window("File Manager", self.build_ui, width=800, height=500)

    def build_ui(self, frame):
        # Toolbar
        toolbar = tk.Frame(frame, bg="rgba(0,0,0,0.4)")
        toolbar.pack(fill=tk.X)
        tk.Button(toolbar, text="New File", command=self.create_file).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="New Folder", command=self.create_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Copy", command=self.copy).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Paste", command=self.paste).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=2)
        
        # Path bar
        path_frame = tk.Frame(frame, bg="rgba(0,0,0,0.4)")
        path_frame.pack(fill=tk.X)
        self.path_var = tk.StringVar(value=self.current_path)
        tk.Entry(path_frame, textvariable=self.path_var, bg="rgba(0,0,0,0.6)", 
                fg="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(path_frame, text="Go", command=self.navigate_path).pack(side=tk.LEFT)

        # Main view
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left_panel = tk.Frame(paned, bg="rgba(0,0,0,0.4)")
        paned.add(left_panel, weight=1)
        right_panel = tk.Frame(paned, bg="rgba(0,0,0,0.4)")
        paned.add(right_panel, weight=1)

        self.left_list = tk.Listbox(left_panel, bg="rgba(0,0,0,0.6)", fg="white", 
                                   selectmode=tk.EXTENDED)
        self.left_list.pack(fill=tk.BOTH, expand=True)
        self.right_list = tk.Listbox(right_panel, bg="rgba(0,0,0,0.6)", fg="white", 
                                    selectmode=tk.EXTENDED)
        self.right_list.pack(fill=tk.BOTH, expand=True)

        self.left_list.bind("<Double-1>", lambda e: self.navigate(self.left_list, self.current_path))
        self.right_list.bind("<Double-1>", lambda e: self.navigate(self.right_list, self.current_path))
        self.left_list.bind("<Button-3>", lambda e: self.show_file_menu(e, self.left_list))
        self.right_list.bind("<Button-3>", lambda e: self.show_file_menu(e, self.right_list))

        self.clipboard = []
        self.update_lists()

    def update_lists(self):
        for lb in [self.left_list, self.right_list]:
            lb.delete(0, tk.END)
            try:
                items = sorted(os.listdir(self.current_path), 
                              key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x))
                for item in items:
                    prefix = "📁 " if os.path.isdir(os.path.join(self.current_path, item)) else "📄 "
                    lb.insert(tk.END, prefix + item)
            except Exception as e:
                lb.insert(tk.END, f"Error: {str(e)}")
                logging.warning(f"File list update error: {e}")

    def navigate_path(self):
        self.current_path = self.path_var.get()
        self.update_lists()

    def navigate(self, listbox, path):
        try:
            selected = listbox.get(listbox.curselection()[0])[2:]  # Remove emoji prefix
            new_path = os.path.join(path, selected)
            if os.path.isdir(new_path):
                self.current_path = new_path
                self.path_var.set(new_path)
                self.update_lists()
            else:
                self.navigate_file(new_path)
        except Exception as e:
            logging.warning(f"Navigate error: {e}")

    def navigate_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        handler = self.file_types.get(ext, lambda p: messagebox.showinfo("Info", 
                                                                       "No handler for this file type"))
        try:
            handler(path)
            logging.info(f"Opened file: {path}")
        except Exception as e:
            logging.error(f"File open error: {path} - {e}")
            messagebox.showerror("Error", f"Cannot open file: {str(e)}")

    def show_file_menu(self, event, listbox):
        try:
            selected = [listbox.get(i)[2:] for i in listbox.curselection()]
            if not selected:
                return
            menu = tk.Menu(self.wm.root, tearoff=0, bg="rgba(0,0,0,0.4)", fg="white")
            menu.add_command(label="Open", command=lambda: self.navigate(listbox, self.current_path))
            menu.add_command(label="Copy", command=self.copy)
            menu.add_command(label="Delete", command=self.delete)
            menu.add_command(label="Rename", command=self.rename)
            menu.add_command(label="Add to Desktop", command=lambda: self.add_to_desktop(selected))
            menu.add_separator()
            menu.add_command(label="Properties", command=lambda: self.wm.show_properties(
                os.path.join(self.current_path, selected[0])))
            menu.post(event.x_root, event.y_root)
        except Exception as e:
            logging.warning(f"File menu error: {e}")

    def create_file(self):
        name = filedialog.asksavefilename(initialdir=self.current_path, 
                                         defaultextension=".txt")
        if name:
            open(name, 'a').close()
            self.update_lists()
            logging.info(f"Created file: {name}")

    def create_folder(self):
        name = filedialog.askdirectory(initialdir=self.current_path)
        if name:
            os.makedirs(name, exist_ok=True)
            self.update_lists()
            logging.info(f"Created folder: {name}")

    def copy(self):
        self.clipboard = [os.path.join(self.current_path, self.left_list.get(i)[2:]) 
                         for i in self.left_list.curselection()]
        self.wm.notifications.send("File Manager", f"Copied {len(self.clipboard)} items")
        logging.info(f"Copied files: {self.clipboard}")

    def paste(self):
        for item in self.clipboard:
            dest = os.path.join(self.current_path, os.path.basename(item))
            if os.path.isdir(item):
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        self.update_lists()
        self.wm.notifications.send("File Manager", f"Pasted {len(self.clipboard)} items")
        logging.info(f"Pasted files to: {self.current_path}")

    def delete(self):
        selected = [self.left_list.get(i)[2:] for i in self.left_list.curselection()]
        if messagebox.askyesno("Confirm", f"Delete {len(selected)} items?"):
            for item in selected:
                path = os.path.join(self.current_path, item)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            self.update_lists()
            self.wm.notifications.send("File Manager", f"Deleted {len(selected)} items")
            logging.info(f"Deleted files: {selected}")

    def rename(self):
        selected = self.left_list.get(self.left_list.curselection()[0])[2:]
        new_name = filedialog.asksavefilename(initialdir=self.current_path, 
                                             initialfile=selected)
        if new_name:
            os.rename(os.path.join(self.current_path, selected), new_name)
            self.update_lists()
            logging.info(f"Renamed {selected} to {new_name}")

    def add_to_desktop(self, items):
        for item in items:
            self.wm.add_desktop_icon(os.path.join(self.current_path, item), 100, 100)
        self.wm.notifications.send("File Manager", f"Added {len(items)} items to desktop")

    def extract_archive(self, path, archive_type):
        dest = os.path.splitext(path)[0] if archive_type == "zip" else path.replace(".tar.gz", "")
        try:
            if archive_type == "zip":
                with zipfile.ZipFile(path, 'r') as z:
                    z.extractall(dest)
            elif archive_type == "tar.gz":
                with tarfile.open(path, 'r:gz') as t:
                    t.extractall(dest)
            self.wm.notifications.send("File Manager", f"Extracted archive to {dest}")
            self.update_lists()
            logging.info(f"Extracted archive: {path}")
        except Exception as e:
            logging.error(f"Archive extraction error: {path} - {e}")
            messagebox.showerror("Error", f"Extraction failed: {str(e)}")

### --- TEXT EDITOR ---
class TextEditor:
    def __init__(self, wm):
        self.wm = wm
        self.file_path = None

    def open(self, file_path=None):
        self.file_path = file_path
        self.wm.create_window("Text Editor", lambda f: self.build_ui(f, file_path), width=800, height=600)

    def build_ui(self, frame, file_path):
        toolbar = tk.Frame(frame, bg="rgba(0,0,0,0.4)")
        toolbar.pack(fill=tk.X)
        tk.Button(toolbar, text="Save", command=self.save).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        
        self.text_area = tk.Text(frame, bg="rgba(0,0,0,0.6)", fg="white", insertbackground="white", 
                                font=("Monospace", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    self.text_area.insert(tk.END, f.read())
            except Exception as e:
                logging.error(f"Text editor open error: {file_path} - {e}")
                messagebox.showerror("Error", f"Cannot open file: {str(e)}")

    def save(self):
        if not self.file_path:
            self.file_path = filedialog.asksavefilename(defaultextension=".txt")
        if self.file_path:
            try:
                with open(self.file_path, 'w') as f:
                    f.write(self.text_area.get("1.0", tk.END))
                self.wm.notifications.send("Text Editor", f"Saved {self.file_path}")
                logging.info(f"Saved file: {self.file_path}")
            except Exception as e:
                logging.error(f"Text editor save error: {self.file_path} - {e}")
                messagebox.showerror("Error", f"Cannot save file: {str(e)}")

    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path = file_path
            self.text_area.delete("1.0", tk.END)
            try:
                with open(file_path, 'r') as f:
                    self.text_area.insert(tk.END, f.read())
                logging.info(f"Opened file: {file_path}")
            except Exception as e:
                logging.error(f"Text editor open error: {file_path} - {e}")
                messagebox.showerror("Error", f"Cannot open file: {str(e)}")

### --- CALCULATOR ---
class Calculator:
    def __init__(self, wm):
        self.wm = wm
        self.expression = ""

    def open(self):
        self.wm.create_window("Calculator", self.build_ui, width=300, height=400)

    def build_ui(self, frame):
        entry = tk.Entry(frame, textvariable=tk.StringVar(value="0"), bg="rgba(0,0,0,0.6)", 
                        fg="white", font=("Arial", 16), justify="right")
        entry.pack(fill=tk.X)
        entry.pack(fill=tk.X)

        # Create button grid for calculator
        button_frame = tk.Frame(frame, bg="#333333")
        button_frame.pack(fill=tk.BOTH, expand=True)

        # Define buttons: (text, row, column, colspan)
        buttons = [
            ('C', 1, 0), ('±', 1, 1), ('%', 1, 2), ('÷', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('×', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('−', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('+', 4, 3),
            ('0', 5, 0, 2), ('.', 5, 2), ('=', 5, 3)
        ]

        for btn_info in buttons:
            text = btn_info[0]
            row = btn_info[1]
            col = btn_info[2]
            colspan = btn_info[3] if len(btn_info) > 3 else 1
            cmd = lambda x=text: self.press(x)
            tk.Button(button_frame, text=text, command=cmd, fg="white", 
                     bg="#555555", font=("Arial", 12), 
                     relief=tk.RAISED).grid(row=row, column=col, 
                                           columnspan=colspan, 
                                           sticky="nsew", padx=2, pady=2)

        # Configure grid weights
        for i in range(6):
            button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)

        self.entry = entry

    def press(self, key):
        """Handle calculator button presses."""
        try:
            if key == 'C':
                self.expression = ""
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, "0")
            elif key == '±':
                if self.expression.startswith('-'):
                    self.expression = self.expression[1:]
                else:
                    self.expression = '-' + self.expression
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, self.expression or "0")
            elif key == '=':
                try:
                    result = str(eval(self.expression, {"__builtins__": {}, "sin": math.sin, "cos": math.cos, "tan": math.tan}))
                    self.expression = result
                    self.entry.delete(0, tk.END)
                    self.entry.insert(tk.END, result)
                except:
                    self.wm.notifications.send("Calculator", "Invalid expression")
                    self.expression = ""
                    self.entry.delete(0, tk.END)
                    self.entry.insert(tk.END, "0")
            else:
                if self.expression == "0":
                    self.expression = ""
                self.expression += key.replace('×', '*').replace('÷', '/').replace('−', '-')
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, self.expression)
        except Exception as e:
            self.wm.notifications.send("Calculator", f"Error: {str(e)}")

### --- WEB BROWSER ---
class WebBrowser:
    """A lightweight web browser using dillo."""
    def __init__(self, wm):
        self.wm = wm
        self.process = None

    def open(self):
        """Open the web browser window."""
        self.wm.create_window("Web Browser", self.build_ui, width=800, height=600)

    def build_ui(self, frame):
        """Build the browser UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            
            url_var = tk.StringVar(value="http://tinycorelinux.net")
            tk.Entry(toolbar, textvariable=url_var, bg="#555555", fg="white", 
                    font=("Arial", 12)).pack(side=tk.LEFT, fill=tk.X, 
                                            expand=True, padx=5, pady=5)
            tk.Button(toolbar, text="Go", command=lambda: self.navigate(url_var.get()), 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(toolbar, text="Home", command=lambda: self.navigate("http://tinycorelinux.net"), 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(toolbar, text="Stop", command=self.stop, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)

            # Placeholder for browser view
            tk.Label(frame, text="Dillo Browser (External Window)", fg="white", 
                    bg="#333333", font=("Arial", 14)).pack(expand=True)

            # Start dillo
            self.navigate(url_var.get())
        except Exception as e:
            self.wm.notifications.send("Web Browser", f"Error: {str(e)}")

    def navigate(self, url):
        """Navigate to a URL."""
        try:
            if self.process:
                self.stop()
            self.process = subprocess.Popen(["dillo", url], 
                                           stdout=subprocess.DEVNULL, 
                                           stderr=subprocess.DEVNULL)
        except Exception as e:
            self.wm.notifications.send("Web Browser", f"Failed to open URL: {str(e)}")

    def stop(self):
        """Stop the browser process."""
        if self.process:
            try:
                self.process.terminate()
                self.process = None
            except:
                pass

### --- SYSTEM INFO ---
class SystemInfo:
    """Display system information."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("System Info", self.build_ui, width=500, height=400)

    def build_ui(self, frame):
        """Build the system info UI."""
        try:
            info = self.get_system_info()
            text = (
                f"OS: Berke0S\n"
                f"Kernel: {info.get('kernel', 'Unknown')}\n"
                f"CPU: {info.get('cpu', 'Unknown')}\n"
                f"Memory: {info.get('memory', 'Unknown')}\n"
                f"Disk: {info.get('disk', 'Unknown')}\n"
                f"Network: {info.get('network', 'Unknown')}\n"
                f"Battery: {info.get('battery', 'Unknown')}"
            )
            tk.Label(frame, text=text, fg="white", bg="#333333", 
                    justify=tk.LEFT, font=("Arial", 12)).pack(padx=10, pady=10)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                    bg="#333333").pack(padx=10, pady=10)

    def get_system_info(self):
        """Collect system information."""
        info = {}
        try:
            info['kernel'] = subprocess.check_output(["uname", "-r"], text=True).strip()
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                model = re.search(r'model name\s*:\s*(.+)', cpuinfo)
                info['cpu'] = model.group(1) if model else "Unknown"
            mem = psutil.virtual_memory()
            info['memory'] = f"{mem.total // 1024**2} MB total, {mem.used // 1024**2} MB used"
            disk = psutil.disk_usage('/')
            info['disk'] = f"{disk.total // 1024**3} GB total, {disk.used // 1024**3} GB used"
            output = subprocess.check_output(["ip", "addr"], text=True)
            net = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+/\d+)', output)
            info['network'] = net.group(1) if net else "Not connected"
            if os.path.exists("/sys/class/power_supply/BAT0/capacity"):
                with open("/sys/class/power_supply/BAT0/capacity", 'r') as f:
                    info['battery'] = f"{f.read().strip()}%"
            else:
                info['battery'] = "No battery detected"
        except:
            pass
        return info

### --- PACKAGE MANAGER ---
class PackageManager:
    """Manage Tiny Core extensions."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Package Manager", self.build_ui, width=600, height=400)

    def build_ui(self, frame):
        """Build the package manager UI."""
        try:
            tk.Label(frame, text="Available Packages", fg="white", bg="#333333").pack(pady=5)
            self.package_list = tk.Listbox(frame, bg="#555555", fg="white", 
                                          selectmode=tk.SINGLE)
            self.package_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(frame, text="Install", command=self.install_package, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Remove", command=self.remove_package, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Refresh", command=self.refresh_packages, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            self.refresh_packages()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                    bg="#333333").pack(padx=10, pady=10)

    def refresh_packages(self):
        """Refresh the package list."""
        try:
            self.package_list.delete(0, tk.END)
            output = subprocess.check_output(["tce-ab"], text=True, stderr=subprocess.DEVNULL)
            packages = output.splitlines()
            for pkg in packages:
                if pkg.strip():
                    self.package_list.insert(tk.END, pkg.strip())
        except Exception as e:
            self.wm.notifications.send("Package Manager", f"Error: {str(e)}")

    def install_package(self):
        """Install a selected package."""
        try:
            selected = self.package_list.get(self.package_list.curselection()[0])
            subprocess.run(["sudo", "tce-load", "-wi", selected], check=True)
            self.wm.notifications.send("Package Manager", f"Installed {selected}")
        except Exception as e:
            self.wm.notifications.send("Package Manager", f"Error: {str(e)}")

    def remove_package(self):
        """Remove a selected package."""
        try:
            selected = self.package_list.get(self.package_list.curselection()[0])
            subprocess.run(["sudo", "tce-audit", "remove", selected], check=True)
            self.refresh_packages()
            self.wm.notifications.send("Package Manager", f"Removed {selected}")
        except Exception as e:
            self.wm.notifications.send("Package Manager", f"Error: {str(e)}")

### --- TASK MANAGER ---
class TaskManager:
    """Manage running processes."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Task Manager", self.build_ui, width=600, height=400)

    def build_ui(self, frame):
        """Build the task manager UI."""
        try:
            self.task_list = tk.Listbox(frame, bg="#555555", fg="white", 
                                       selectmode=tk.SINGLE)
            self.task_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(frame, text="End Process", command=self.end_process, 
                     bg="#555555", fg="white").pack(pady=5)
            self.update_tasks()
            self.wm.root.after(2000, self.update_tasks)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                    bg="#333333").pack(padx=10, pady=10)

    def update_tasks(self):
        """Update the task list."""
        try:
            self.task_list.delete(0, tk.END)
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    line = f"PID: {info['pid']} | {info['name']} | CPU: {info['cpu_percent']:.1f}% | Mem: {info['memory_percent']:.1f}%"
                    self.task_list.insert(tk.END, line)
                except:
                    pass
            self.wm.root.after(2000, self.update_tasks)
        except:
            pass

    def end_process(self):
        """Terminate a selected process."""
        try:
            selected = self.task_list.get(self.task_list.curselection()[0])
            pid = int(selected.split('|')[0].split(':')[1].strip())
            proc = psutil.Process(pid)
            proc.terminate()
            self.wm.notifications.send("Task Manager", f"Terminated process {pid}")
            self.update_tasks()
        except Exception as e:
            self.wm.notifications.error(f"Error: {str(e)}")

### --- FILE MANAGER ---
class FileManager:
    """A Windows-like file manager with shortcuts and search."""
    def __init__(self, wm):
        self.wm = wm
        self.current_path = os.path.expanduser("~")
        self.shortcuts = {}

    def open(self):
        self.wm.create_window("File Manager", self.build_ui, width=800, height=600)

    def build_ui(self, frame):
        """Build the file manager UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="Up", command=self.go_up, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="New Folder", command=self.create_folder, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Delete", command=self.delete_item, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Create Shortcut", command=self.create_shortcut, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            path_var = tk.StringVar(value=self.current_path)
            tk.Entry(toolbar, textvariable=path_var, bg="#555555").pack(
                side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Button(toolbar, text="Go", command=lambda: self.change_path(path_var.get()), 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            search_var = tk.StringVar()
            tk.Entry(toolbar, textvariable=search_var, width=15, bg="#555555").pack(
                side=tk.RIGHT, padx=2)
            tk.Button(toolbar, text="Search", command=lambda: self.search_files(search_var.get()), 
                     bg="#555555", fg="white").pack(side=tk.RIGHT, padx=2)

            # Main content
            main_frame = tk.Frame(frame, bg="#333333")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Directory tree
            tree_frame = tk.Frame(main_frame, bg="#333333")
            tree_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            tk.Label(tree_frame, text="Folders", fg="white", bg="#333333").pack()
            self.tree = ttk.Treeview(tree_frame, show="tree")
            self.tree.pack(fill=tk.Y, expand=True)
            self.tree.bind('<<TreeviewOpen>>', self.update_tree)
            self.tree.bind('<Double-1>', self.tree_select)
            self.populate_tree()

            # File list
            list_frame = tk.Frame(main_frame, bg="#333333")
            list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            tk.Label(list_frame, text="Files", fg="white", bg="#333333").pack()
            self.file_list = tk.Listbox(list_frame, bg="#555555", fg="white")
            self.file_list.pack(fill=tk.BOTH, expand=True)
            self.file_list.bind('<Double-1>', self.open_item)
            self.file_list.bind('<Button-3>', self.show_context_menu)
            self.update_file_list()

            # Context menu
            self.context_menu = tk.Menu(frame, tearoff=0, bg="#333333", fg="white")
            self.context_menu.add_command(label="Open", command=self.open_item)
            self.context_menu.add_command(label="Delete", command=self.delete_item)
            self.context_menu.add_command(label="Rename", command=self.rename_item)
            self.context_menu.add_command(label="Create Shortcut", command=self.create_shortcut)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def populate_tree(self):
        """Populate directory tree."""
        try:
            self.tree.delete(*self.tree.get_children())
            root_node = self.tree.insert("", "end", text="Home", open=True, 
                                    values=(os.path.expanduser("~"),))
            self._add_tree_nodes(root_node, os.path.expanduser("~"))
        except:
            pass

    def _add_tree_nodes(self, parent, path):
        """Recursively add directory nodes."""
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    node = self.tree.insert(parent, "end", text=item, 
                                          values=(item_path,))
                    self.tree.insert(node, "end", text="dummy")
        except:
            pass

    def update_tree(self, event):
        """Update tree when a node is expanded."""
        try:
            node = self.tree.focus()
            if not self.tree.get_children(node):
                return
            path = self.tree.item(node, "values")[0]
            self.tree.delete(*self.tree.get_children(node))
            self._add_tree_nodes(node, path)
        except:
            pass

    def tree_select(self, event):
        """Handle tree node selection."""
        try:
            node = self.tree.focus()
            path = self.tree.item(node, "values")[0]
            self.current_path = path
            self.update_file_list()
        except:
            pass

    def update_file_list(self):
        """Update the file list."""
        try:
            self.file_list.delete(0, tk.END)
            for item in sorted(os.listdir(self.current_path)):
                item_path = os.path.join(self.current_path, item)
                prefix = "[DIR] " if os.path.isdir(item_path) else ""
                self.file_list.insert(tk.END, f"{prefix}{item}")
        except:
            pass

    def go_up(self):
        """Navigate to parent directory."""
        try:
            parent = os.path.dirname(self.current_path)
            if parent != self.current_path:
                self.current_path = parent
                self.populate_tree()
                self.update_file_list()
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def change_path(self, path):
        """Change to a specified path."""
        try:
            if os.path.isdir(path):
                self.current_path = path
                self.populate_tree()
                self.update_file_list()
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def open_item(self, event=None):
        """Open a selected item based on extension."""
        try:
            selected = self.file_list.get(self.file_list.curselection()[0])
            item = selected.replace("[DIR] ", "")
            item_path = os.path.join(self.current_path, item)
            if os.path.isdir(item_path):
                self.current_path = item_path
                self.populate_tree()
                self.update_file_list()
            else:
                self.wm.open_file(item_path)
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def create_folder(self):
        """Create a new folder."""
        try:
            name = simpledialog.askstring("New Folder", "Folder name:")
            if name:
                os.makedirs(os.path.join(self.current_path, name))
                self.update_file_list()
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def delete_item(self):
        """Delete a selected item."""
        try:
            selected = self.file_list.get(self.file_list.curselection()[0])
            item = selected.replace("[DIR] ", "")
            item_path = os.path.join(self.current_path, item)
            if messagebox.askyesno("Confirm", f"Delete {item}?"):
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                self.update_file_list()
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def rename_item(self):
        """Rename a selected item."""
        try:
            selected = self.file_list.get(self.file_list.curselection()[0])
            item = selected.replace("[DIR] ", "")
            item_path = os.path.join(self.current_path, item)
            new_name = simpledialog.askstring("Rename", "New name:", initialvalue=item)
            if new_name:
                os.rename(item_path, os.path.join(self.current_path, new_name))
                self.update_file_list()
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def create_shortcut(self):
        """Create a desktop shortcut."""
        try:
            selected = self.file_list.get(self.file_list.curselection()[0])
            item = selected.replace("[DIR] ", "")
            item_path = os.path.join(self.current_path, item)
            self.wm.add_desktop_shortcut(item_path, 100, 100)
            self.wm.notifications.send("File Manager", f"Shortcut created for {item}")
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def search_files(self, query):
        """Search for files in the current directory."""
        try:
            self.file_list.delete(0, tk.END)
            for root, dirs, files in os.walk(self.current_path):
                for name in files + dirs:
                    if query.lower() in name.lower():
                        item_path = os.path.join(root, name)
                        prefix = "[DIR] " if os.path.isdir(item_path) else ""
                        self.file_list.insert(tk.END, f"{prefix}{name}")
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def show_context_menu(self, event):
        """Show context menu for file list."""
        try:
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(self.file_list.nearest(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

### --- ADVANCED CODE EDITOR ---
class CodeEditor:
    """Advanced code editor with syntax highlighting and runner."""
    def __init__(self, wm):
        self.wm = wm
        self.filename = None
        self.highlighter = None

    def open(self):
        self.wm.create_window("Code Editor", self.build_ui, width=800, height=600)

    def open_file(self, filename):
        """Open a specific file."""
        self.filename = filename
        self.open()
        self.load_file()

    def build_ui(self, frame):
        """Build the code editor UI."""
        try:
            # Menu bar
            menubar = tk.Menu(frame)
            file_menu = tk.Menu(menubar, tearoff=0, bg="#333333", fg="white")
            file_menu.add_command(label="New", command=self.new_file)
            file_menu.add_command(label="Open", command=self.open_dialog)
            file_menu.add_command(label="Save", command=self.save_file)
            file_menu.add_command(label="Save As", command=self.save_as)
            file_menu.add_separator()
            file_menu.add_command(label="Run", command=self.run_code)
            menubar.add_cascade(label="File", menu=file_menu)
            self.wm.root.config(menu=menubar)

            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="New", command=self.new_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Open", command=self.open_dialog, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Save", command=self.save_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Run", command=self.run_code, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            language_var = tk.StringVar(value="Python")
            tk.OptionMenu(toolbar, language_var, "Python", "Bash", command=self.update_highlighter).pack(side=tk.LEFT, padx=2)

            # Editor and output
            main_frame = tk.Frame(frame, bg="#333333")
            main_frame.pack(fill=tk.BOTH, expand=True)
            self.editor = tk.Text(main_frame, bg="#2e2e2e", fg="white", 
                                font=("Monospace", 12), insertbackground="white")
            self.editor.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            self.output = tk.Text(main_frame, bg="#2e2e2e", fg="white", 
                                font=("Monospace", 12), height=10)
            self.output.pack(fill=tk.X, side=tk.BOTTOM)
            scrollbar = tk.Scrollbar(main_frame, command=self.editor.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.editor.config(yscrollcommand=scrollbar.set)

            # Syntax highlighting
            self.highlighter = PygmentsHighlighter(self.editor, "python")
            self.editor.bind("<KeyRelease>", self.highlight_code)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def new_file(self):
        """Create a new file."""
        try:
            self.filename = None
            self.editor.delete(1.0, tk.END)
            self.output.delete(1.0, tk.END)
        except:
            pass

    def open_dialog(self):
        """Open a file dialog."""
        try:
            filename = filedialog.askopenfilename()
            if filename:
                self.filename = filename
                self.load_file()
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def load_file(self):
        """Load file content."""
        try:
            with open(self.filename, 'r') as f:
                content = f.read()
            self.editor.delete(1.0, tk.END)
            self.editor.insert(tk.END, content)
            self.update_highlighter(self.filename.split('.')[-1])
            self.highlight_code()
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def save_file(self):
        """Save the current file."""
        try:
            if self.filename:
                with open(self.filename, 'w') as f:
                    f.write(self.editor.get(1.0, tk.END).strip())
            else:
                self.save_as()
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def save_as(self):
        """Save file with a new name."""
        try:
            filename = filedialog.asksaveasfilename()
            if filename:
                self.filename = filename
                self.save_file()
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def run_code(self):
        """Run the code based on language."""
        try:
            code = self.editor.get(1.0, tk.END).strip()
            self.output.delete(1.0, tk.END)
            if not code:
                return
            if self.filename and self.filename.endswith('.py'):
                process = subprocess.run(["python3", "-"], input=code, text=True, 
                                       capture_output=True)
                self.output.insert(tk.END, process.stdout + process.stderr)
            elif self.filename and self.filename.endswith('.sh'):
                process = subprocess.run(["bash", "-c", code], text=True, 
                                       capture_output=True)
                self.output.insert(tk.END, process.stdout + process.stderr)
            else:
                self.wm.notifications.send("Code Editor", "Unsupported file type")
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def update_highlighter(self, language):
        """Update syntax highlighter."""
        try:
            language = language.lower()
            if language in ['py', 'python']:
                self.highlighter = PygmentsHighlighter(self.editor, "python")
            elif language in ['sh', 'bash']:
                self.highlighter = PygmentsHighlighter(self.editor, "bash")
            self.highlight_code()
        except:
            pass

    def highlight_code(self, event=None):
        """Apply syntax highlighting."""
        try:
            self.highlighter.highlight()
        except:
            pass

### --- SYNTAX HIGHLIGHTER ---
class PygmentsHighlighter:
    """Syntax highlighting using Pygments."""
    def __init__(self, text_widget, language):
        self.text = text_widget
        self.lexer = get_lexer_by_name(language)
        self.formatter = TkinterFormatter()
        self.text.tag_configure("keyword", foreground="#ff79c6")
        self.text.tag_configure("string", foreground="#f1fa8c")
        self.text.tag_configure("comment", foreground="#6272a4")
        self.text.tag_configure("builtin", foreground="#8be9fd")

    def highlight(self):
        """Highlight the text content."""
        try:
            code = self.text.get(1.0, tk.END).strip()
            self.text.tag_remove("keyword", 1.0, tk.END)
            self.text.tag_remove("string", 1.0, tk.END)
            self.text.tag_remove("comment", 1.0, tk.END)
            self.text.tag_remove("builtin", 1.0, tk.END)
            tokens = list(lex(code, self.lexer))
            index = "1.0"
            for ttype, value in tokens:
                tag = str(ttype).split('.')[-1].lower()
                if tag in ['keyword', 'string', 'comment', 'builtin']:
                    end_index = f"{index}+{len(value)}c"
                    self.text.tag_add(tag, index, end_index)
                    index = end_index
        except:
            pass

class TkinterFormatter(Formatter):
    """Custom Pygments formatter for Tkinter."""
    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            yield ttype, value

### --- IMAGE VIEWER ---
class ImageViewer:
    """View image files."""
    def __init__(self, wm):
        self.wm = wm
        self.image = None
        self.photo = None

    def open_file(self, filename):
        """Open an image file."""
        self.wm.create_window("Image Viewer", lambda f: self.build_ui(f, filename), 
                            width=800, height=600)

    def build_ui(self, frame, filename):
        """Build the image viewer UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="Zoom In", command=self.zoom_in, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Zoom Out", command=self.zoom_out, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Fit", command=self.fit_image, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)

            # Image canvas
            self.canvas = tk.Canvas(frame, bg="#333333")
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.image = Image.open(filename)
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def zoom_in(self):
        """Zoom in on the image."""
        try:
            self.image = self.image.resize((int(self.image.width * 1.2), 
                                          int(self.image.height * 1.2)), 
                                         Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        except:
            pass

    def zoom_out(self):
        """Zoom out on the image."""
        try:
            self.image = self.image.resize((int(self.image.width * 0.8), 
                                          int(self.image.height * 0.8)), 
                                         Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        except:
            pass

    def fit_image(self):
        """Fit image to window."""
        try:
            self.image = Image.open(self.image.filename)
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        except:
            pass

### --- PRESENTATION APP ---
class PresentationApp:
    """Basic presentation application."""
    def __init__(self, wm):
        self.wm = wm
        self.slides = []
        self.current_slide = 0

    def open(self):
        self.wm.create_window("Presentation", self.build_ui, width=800, height=600)

    def build_ui(self, frame):
        """Build the presentation UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="Add Slide", command=self.add_slide, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Next", command=self.next_slide, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Previous", command=self.prev_slide, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Open Images", command=self.load_images, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)

            # Slide canvas
            self.canvas = tk.Canvas(frame, bg="#333333")
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.add_slide()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def add_slide(self):
        """Add a new slide."""
        try:
            self.slides.append({"image": None, "text": ""})
            self.current_slide = len(self.slides) - 1
            self.update_slide()
        except:
            pass

    def load_images(self):
        """Load images for slides."""
        try:
            files = filedialog.askopenfilenames(filetypes=[("Images", "*.png *.jpg")])
            for file in files:
                self.slides.append({"image": file, "text": ""})
            self.current_slide = len(self.slides) - 1
            self.update_slide()
        except Exception as e:
            self.wm.notifications.send("Presentation", f"Error: {str(e)}")

    def next_slide(self):
        """Go to next slide."""
        try:
            if self.current_slide < len(self.slides) - 1:
                self.current_slide += 1
                self.update_slide()
        except:
            pass

    def prev_slide(self):
        """Go to previous slide."""
        try:
            if self.current_slide > 0:
                self.current_slide -= 1
                self.update_slide()
        except:
            pass

    def update_slide(self):
        """Update the current slide display."""
        try:
            self.canvas.delete("all")
            slide = self.slides[self.current_slide]
            if slide["image"]:
                img = Image.open(slide["image"])
                img = img.resize((400, 300), Image.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.canvas.create_image(200, 150, image=self.photo)
            self.canvas.create_text(200, 350, text=slide["text"], fill="white", 
                                  font=("Arial", 12))
        except:
            pass

### --- MEDIA PLAYER ---
class MediaPlayer:
    """Play media files using mpv."""
    def __init__(self, wm):
        self.wm = wm
        self.process = None

    def play(self, file_path):
        """Play a media file."""
        try:
            if self.process:
                self.stop()
            self.process = subprocess.Popen(["mpv", file_path], 
                                          stdout=subprocess.DEVNULL, 
                                          stderr=subprocess.DEVNULL)
            self.wm.notifications.send("Media Player", f"Playing {os.path.basename(file_path)}")
        except Exception as e:
            self.wm.notifications.send("Media Player", f"Error: {str(e)}")

    def stop(self):
        """Stop media playback."""
        if self.process:
            try:
                self.process.terminate()
                self.process = None
            except:
                pass

### --- CONTROL CENTER ---
class ControlCenter:
    """System settings with customization."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Control Center", self.build_ui, width=600, height=500)

    def build_ui(self, frame):
        """Build the control center UI."""
        try:
            notebook = ttk.Notebook(frame)
            notebook.pack(fill=tk.BOTH, expand=True)

            # Network tab
            network = ttk.Frame(notebook)
            notebook.add(network, text="Network")
            tk.Label(network, text="Wi-Fi SSID", fg="white", bg="#333333").pack(pady=5)
            ssid_var = tk.StringVar()
            self.ssid_menu = ttk.Combobox(network, textvariable=ssid_var, state="readonly")
            self.ssid_menu.pack(pady=5)
            tk.Label(network, text="Password", fg="white", bg="#333333").pack(pady=5)
            passwd_var = tk.StringVar()
            tk.Entry(network, textvariable=passwd_var, show="*", bg="#555555").pack(pady=5)
            tk.Button(network, text="Connect", 
                     command=lambda: self.connect_wifi(ssid_var.get(), passwd_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(network, text="Refresh", command=self.refresh_wifi, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(network, text="Connect Wired", command=self.connect_wired, 
                     bg="#555555", fg="white").pack(pady=5)

            # Display tab
            display = ttk.Frame(notebook)
            notebook.add(display, text="Display")
            tk.Label(display, text="Brightness", fg="white", bg="#333333").pack(pady=5)
            bright_var = tk.IntVar(value=50)
            tk.Scale(display, from_=0, to=100, orient=tk.HORIZONTAL, variable=bright_var, 
                    bg="#555555").pack(pady=5)
            tk.Button(display, text="Apply", 
                     command=lambda: self.set_brightness(bright_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)

            # Audio tab
            audio = ttk.Frame(notebook)
            notebook.add(audio, text="Audio")
            tk.Label(audio, text="Volume", fg="white", bg="#333333").pack(pady=5)
            volume_var = tk.IntVar(value=50)
            tk.Scale(audio, from_=0, to=100, orient=tk.HORIZONTAL, variable=volume_var, 
                    bg="#555555").pack(pady=5)
            tk.Button(audio, text="Apply", 
                     command=lambda: self.set_volume(volume_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)

            # User Management tab
            users = ttk.Frame(notebook)
            notebook.add(users, text="Users")
            tk.Label(users, text="User Management", fg="white", bg="#333333").pack(pady=5)
            self.user_list = tk.Listbox(users, bg="#555555", fg="white")
            self.user_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(users, text="Add User", command=self.add_user, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(users, text="Delete User", command=self.delete_user, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(users, text="Change Password", command=self.change_password, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            self.refresh_users()

            # Customization tab
            customize = ttk.Frame(notebook)
            notebook.add(customize, text="Customization")
            tk.Label(customize, text="Desktop Background", fg="white", bg="#333333").pack(pady=5)
            tk.Button(customize, text="Set Image", command=self.set_background_image, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(customize, text="Set Video", command=self.set_background_video, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Label(customize, text="Taskbar Color", fg="white", bg="#333333").pack(pady=5)
            color_var = tk.StringVar(value="#333333")
            tk.Entry(customize, textvariable=color_var, bg="#555555").pack(pady=5)
            tk.Button(customize, text="Apply Color", 
                     command=lambda: self.set_taskbar_color(color_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Label(customize, text="Theme", fg="white", bg="#333333").pack(pady=5)
            theme_var = tk.StringVar(value="Dark")
            tk.OptionMenu(customize, theme_var, "Dark", "Light", 
                         command=self.set_theme).pack(pady=5)

            self.refresh_wifi()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def refresh_wifi(self):
        """Refresh Wi-Fi networks."""
        try:
            output = subprocess.check_output(["sudo", "iwlist", "wlan0", "scan"], 
                                           text=True, stderr=subprocess.DEVNULL)
            ssids = re.findall(r'ESSID:"(.*?)"', output)
            self.ssid_menu["values"] = list(set(ssids))
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def connect_wifi(self, ssid, password):
        """Connect to Wi-Fi."""
        try:
            subprocess.run(["sudo", "iwconfig", "wlan0", "essid", ssid, "key", password], 
                          check=True)
            subprocess.run(["sudo", "udhcpc", "-i", "wlan0"], check=True)
            self.wm.notifications.send("Control Center", f"Connected to {ssid}")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def connect_wired(self):
        """Connect to wired network."""
        try:
            subprocess.run(["sudo", "udhcpc", "-i", "eth0"], check=True)
            self.wm.notifications.send("Control Center", "Connected to wired network")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_brightness(self, value):
        """Set screen brightness."""
        try:
            subprocess.run(["sudo", "sh", "-c", f"echo {value} > /sys/class/backlight/*/brightness"], 
                          check=True)
            self.wm.notifications.send("Control Center", f"Brightness set to {value}%")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_volume(self, value):
        """Set system volume."""
        try:
            subprocess.run(["amixer", "set", "Master", f"{value}%"], check=True)
            self.wm.notifications.send("Control Center", f"Volume set to {value}%")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def refresh_users(self):
        """Refresh user list."""
        try:
            self.user_list.delete(0, tk.END)
            output = subprocess.check_output(["cat", "/etc/passwd"], text=True)
            for line in output.splitlines():
                if line.startswith(("tc:", "user")):
                    username = line.split(":")[0]
                    self.user_list.insert(tk.END, username)
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def add_user(self):
        """Add a new user."""
        try:
            username = simpledialog.askstring("Add User", "Username:")
            if not username:
                return
            password = simpledialog.askstring("Add User", "Password:", show="*")
            if not password:
                return
            subprocess.run(["sudo", "useradd", "-m", username], check=True)
            subprocess.run(f"echo {username}:{password} | sudo chpasswd", 
                          shell=True, check=True)
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            self.wm.session_manager.add_user(username, hashed.decode())
            self.refresh_users()
            self.wm.notifications.send("Control Center", f"User {username} added")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def delete_user(self):
        """Delete a user."""
        try:
            selected = self.user_list.get(self.user_list.curselection()[0])
            if selected == "tc":
                self.wm.notifications.send("Control Center", "Cannot delete default user")
                return
            if messagebox.askyesno("Confirm", f"Delete user {selected}?"):
                subprocess.run(["sudo", "userdel", "-r", selected], check=True)
                self.wm.session_manager.remove_user(selected)
                self.refresh_users()
                self.wm.notifications.send("Control Center", f"User {selected} deleted")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def change_password(self):
        """Change user password."""
        try:
            selected = self.user_list.get(self.user_list.curselection()[0])
            password = simpledialog.askstring("Change Password", "New password:", show="*")
            if password:
                subprocess.run(f"echo {selected}:{password} | sudo chpasswd", 
                              shell=True, check=True)
                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
                self.wm.session_manager.update_password(selected, hashed.decode())
                self.wm.notifications.send("Control Center", f"Password changed for {selected}")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_background_image(self):
        """Set desktop background image."""
        try:
            filename = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg")])
            if filename:
                subprocess.run(["feh", "--bg-scale", filename], check=True)
                self.wm.config["background"] = filename
                self.wm.save_config()
                self.wm.notifications.send("Control Center", "Background set")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_background_video(self):
        """Set desktop background video."""
        try:
            filename = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.avi")])
            if filename:
                self.wm.stop_background_video()
                self.wm.background_video = subprocess.Popen(
                    ["mplayer", "-vo", "x11", "-loop", "0", filename], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.wm.config["background_video"] = filename
                self.wm.save_config()
                self.wm.notifications.send("Control Center", "Video background set")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_taskbar_color(self, color):
        """Set taskbar color."""
        try:
            self.wm.taskbar.config(bg=color)
            self.wm.config["taskbar_color"] = color
            self.wm.save_config()
            self.wm.notifications.send("Control Center", "Taskbar color set")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_theme(self, theme):
        """Set UI theme."""
        try:
            colors = {"Dark": {"bg": "#333333", "fg": "white", "entry": "#555555"}, 
                     "Light": {"bg": "#f0f0f0", "fg": "black", "entry": "#ffffff"}}
            self.wm.config["theme"] = theme
            self.wm.apply_theme(colors[theme])
            self.wm.save_config()
            self.wm.notifications.send("Control Center", f"Theme set to {theme}")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

### --- DISK MANAGER ---
class DiskManager:
    """Manage disk partitions."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Disk Manager", self.build_ui, width=600, height=400)

    def build_ui(self, frame):
        """Build the disk manager UI."""
        try:
            self.disk_list = tk.Listbox(frame, bg="#555555", fg="white", 
                                       selectmode=tk.SINGLE)
            self.disk_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(frame, text="Mount", command=self.mount_disk, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Unmount", command=self.unmount_disk, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Format", command=self.format_disk, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            self.refresh_disks()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def refresh_disks(self):
        """Refresh disk list."""
        try:
            self.disk_list.delete(0, tk.END)
            output = subprocess.check_output(["lsblk", "-o", "NAME,SIZE,MOUNTPOINT"], 
                                           text=True)
            for line in output.splitlines()[1:]:
                if line.strip():
                    self.disk_list.insert(tk.END, line.strip())
        except:
            pass

    def mount_disk(self):
        """Mount a disk."""
        try:
            selected = self.disk_list.get(self.disk_list.curselection()[0]).split()[0]
            mountpoint = f"/mnt/{selected}"
            os.makedirs(mountpoint, exist_ok=True)
            subprocess.run(["sudo", "mount", f"/dev/{selected}", mountpoint], check=True)
            self.wm.notifications.send("Disk Manager", f"Mounted {selected}")
            self.refresh_disks()
        except Exception as e:
            self.wm.notifications.send("Disk Manager", f"Error: {str(e)}")

    def unmount_disk(self):
        """Unmount a disk."""
        try:
            selected = self.disk_list.get(self.disk_list.curselection()[0]).split()[0]
            subprocess.run(["sudo", "umount", f"/dev/{selected}"], check=True)
            self.wm.notifications.send("Disk Manager", f"Unmounted {selected}")
            self.refresh_disks()
        except Exception as e:
            self.wm.notifications.send("Disk Manager", f"Error: {str(e)}")

    def format_disk(self):
        """Format a disk."""
        try:
            selected = self.disk_list.get(self.disk_list.curselection()[0]).split()[0]
            if messagebox.askyesno("Confirm", f"Format /dev/{selected}? Data will be lost!"):
                subprocess.run(["sudo", "mkfs.ext4", f"/dev/{selected}"], check=True)
                self.wm.notifications.send("Disk Manager", f"Formatted {selected}")
                self.refresh_disks()
        except Exception as e:
            self.wm.notifications.send("Disk Manager", f"Error: {str(e)}")

### --- TERMINAL EMULATOR ---
class TerminalEmulator:
    """Terminal emulator using pty."""
    def __init__(self, wm):
        self.wm = wm
        self.process = None
        self.master_fd = None

    def initialize(self):
        self.wm.create_window("Terminal", self.build_ui, width=800, height=600)

    def build_ui(self, frame):
        """Build the terminal UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="Clear", command=self.clear_terminal, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(toolbar, text="Close", command=self.close, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)

            # Terminal text
            self.text = tk.Text(frame, bg="black", fg="white", font=("Monospace", 12), 
                               insertbackground="white")
            self.text.pack(fill=tk.BOTH, expand=True)
            self.text.bind("<Key>", self.handle_input)
            
            # Start bash
            self.master_fd, slave_fd = pty.openpty()
            self.process = subprocess.Popen(["bash"], stdin=slave_fd, stdout=slave_fd, 
                                          stderr=slave_fd, text=True, bufsize=1)
            os.close(slave_fd)
            
            # Non-blocking read
            fl = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            self.read_output()
        except Exception as e:
            pass
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def handle_input(self, event):
        """Handle terminal input."""
        try:
            if event.keysym == "Return":
                self.text.insert(tk.END, "\n")
                os.write(self.master_fd, b"\n")
            elif event.char:
                os.write(self.master_fd, event.char.encode())
            return "break"
        except:
            return "break"

    def read_output(self):
        """Read terminal output."""
        try:
            data = os.read(self.master_fd, 1024).decode(errors='ignore')
            self.text.insert(tk.END, data)
            self.text.see(tk.END)
        except:
            pass
        if self.process and self.process.poll() is None:
            self.wm.root.after(100, self.read_output)

    def clear_terminal(self):
        """Clear terminal text."""
        try:
            self.text.delete(1.0, tk.END)
        except:
            pass

    def close(self):
        """Close the terminal."""
        if self.process:
            try:
                self.process.terminate()
                os.close(self.master_fd)
            except:
                pass

### --- SYSTEM MONITOR WIDGET ---
class SystemMonitorWidget:
    """Display system resources."""
    def __init__(self, wm):
        self.wm = wm
        self.visible = False
        self.window = None

    def toggle(self):
        if not self.visible:
            self.window = self.wm.create_window("System Monitor", self.build_ui, 
                                              width=300, height=200)
            self.visible = True
        else:
            self.wm.close_window(self.window)
            self.visible = False
            self.window = None

    def build_ui(self, frame):
        """Build the system monitor UI."""
        try:
            self.cpu_label = tk.Label(frame, text="CPU: 0%", fg="white", bg="#333333")
            self.cpu_label.pack(pady=5)
            self.mem_label = tk.Label(frame, text="Memory: 0%", fg="white", bg="#333333")
            self.mem_label.pack(pady=5)
            self.update_stats()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def update_stats(self):
        """Update system stats."""
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            self.cpu_label.config(text=f"CPU: {cpu:.1f}%")
            self.mem_label.config(text=f"Memory: {mem:.1f}%")
            if self.visible:
                self.wm.root.after(1000, self.update_stats)
        except:
            pass

### --- SCREENSHOT UTILITY ---
class ScreenshotUtility:
    """Capture screenshots."""
    def __init__(self, wm):
        self.wm = wm

    def take_screenshot(self):
        """Capture a screenshot."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{os.environ['HOME']}/screenshot_{timestamp}.png"
            subprocess.run(["scrot", path], check=True)
            self.wm.notifications.send("Screenshot", f"Saved to {path}")
            self.wm.add_desktop_shortcut(path, 100, 100)
        except Exception as e:
            self.wm.notifications.send("Screenshot", f"Error: {str(e)}")

### --- SESSION MANAGER ---
class SessionManager:
    """Manage user sessions and authentication."""
    def __init__(self, wm):
        self.wm = wm
        self.users = {}
        self.current_user = None
        self.load_users()

    def load_users(self):
        """Load user data."""
        try:
            user_file = os.path.expanduser("~/.berke0s/users.json")
            if os.path.exists(user_file):
                with open(user_file, 'r') as f:
                    self.users = json.load(f)
        except:
            pass

    def save_users(self):
        """Save user data."""
        try:
            user_file = os.path.expanduser("~/.berke0s/users.json")
            os.makedirs(os.path.dirname(user_file), exist_ok=True)
            with open(user_file, 'w') as f:
                json.dump(self.users, f)
        except:
            pass

    def add_user(self, username, hashed_password):
        """Add a user."""
        self.users[username] = hashed_password
        self.save_users()

    def remove_user(self, username):
        """Remove a user."""
        if username in self.users:
            del self.users[username]
            self.save_users()

    def update_password(self, username, hashed_password):
        """Update user password."""
        if username in self.users:
            self.users[username] = hashed_password
            self.save_users()

    def authenticate(self, username, password):
        """Authenticate a user."""
        try:
            if username in self.users:
                return bcrypt.checkpw(password.encode(), self.users[username].encode())
            return False
        except:
            return False

    def login(self, username):
        """Set current user."""
        self.current_user = username
        self.wm.config["current_user"] = username
        self.wm.save_config()

    def logout(self):
        """Log out current user."""
        self.current_user = None
        self.wm.config["current_user"] = None
        self.wm.save_config()
        self.wm.show_login()

### --- SYSTEM TRAY ---
class SystemTray:
    """System tray with clock and status."""
    def __init__(self, wm):
        self.wm = wm
        self.tray = None

    def build_ui(self, parent):
        """Build the system tray."""
        try:
            self.tray = tk.Frame(parent, bg="#333333")
            self.tray.pack(side=tk.RIGHT, padx=5)
            self.clock = tk.Label(self.tray, fg="white", bg="#333333", font=("Arial", 10))
            self.clock.pack(side=tk.RIGHT)
            self.network = tk.Label(self.tray, text="No Network", fg="white", bg="#333333")
            self.network.pack(side=tk.RIGHT, padx=5)
            self.battery = tk.Label(self.tray, text="N/A", fg="white", bg="#333333")
            self.battery.pack(side=tk.RIGHT, padx=5)
            self.update_status()
        except Exception as e:
            self.wm.notifications.send("System Tray", f"Error: {str(e)}")

    def update_status(self):
        """Update tray status."""
        try:
            # Clock
            self.clock.config(text=datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y"))
            
            # Network
            output = subprocess.check_output(["ip", "addr"], text=True)
            net = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+/\d+)', output)
            self.network.config(text=net.group(1) if net else "No Network")
            
            # Battery
            if os.path.exists("/sys/class/power_supply/BAT0/capacity"):
                with open("/sys/class/power_supply/BAT0/capacity", 'r') as f:
                    self.battery.config(text=f"{f.read().strip()}%")
            else:
                self.battery.config(text="N/A")
                
            self.wm.root.after(1000, self.update_status)
        except:
            pass

### --- BACKUP UTILITY ---
class BackupUtility:
    """Backup and restore user settings."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Backup Utility", self.build_ui, width=400, height=300)

    def build_ui(self, frame):
        """Build the backup UI."""
        try:
            tk.Label(frame, text="Backup and Restore", fg="white", bg="#333333").pack(pady=5)
            tk.Button(frame, text="Backup Settings", command=self.backup, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Restore Settings", command=self.restore, 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def backup(self):
        """Backup user settings."""
        try:
            backup_dir = os.path.expanduser("~/.berke0s/backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.tar.gz")
            subprocess.run(["tar", "-czf", backup_file, 
                           os.path.expanduser("~/.berke0s/config.json"), 
                           os.path.expanduser("~/.berke0s/session.json"), 
                           os.path.expanduser("~/.berke0s/users.json")], 
                          check=True)
            self.wm.notifications.send("Backup", f"Backup created: {backup_file}")
        except Exception as e:
            self.wm.notifications.send("Backup", f"Error: {str(e)}")

    def restore(self):
        """Restore user settings."""
        try:
            filename = filedialog.askopenfilename(filetypes=[("Tar", "*.tar.gz")])
            if filename:
                subprocess.run(["tar", "-xzf", filename, "-C", os.path.expanduser("~/.berke0s")], 
                              check=True)
                self.wm.notifications.send("Backup", "Settings restored")
                self.wm.load_config()
        except Exception as e:
            self.wm.notifications.send("Backup", f"Error: {str(e)}")

### --- UTILITY FUNCTIONS ---
def install_packages():
    """Install required packages."""
    try:
        packages = ["python3.9", "tk", "tcl", "python3.9-pip", "alsa", "bluez", 
                   "e2fsprogs", "nano", "htop", "bash", "tar", "zip", 
                   "wireless-tools", "scrot", "libnotify", "espeak", "mpv", 
                   "dillo", "flwm", "aterm", "feh", "mplayer", "pwgen", "bc"]
        for pkg in packages:
            subprocess.run(["sudo", "tce-load", "-wi", pkg], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pip3", "install", "--user", "psutil", "Pillow", "bcrypt", "pygments"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def setup_autostart():
    """Configure autostart."""
    try:
        with open("/opt/bootlocal.sh", "a") as f:
            f.write("python3 /usr/local/bin/BERKE0S.py &\n")
        subprocess.run(["sudo", "filetool.sh", "-b"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def load_config():
    """Load configuration."""
    try:
        config_path = os.path.expanduser("~/.berke0s/config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {"theme": "dark", "language": "en", "taskbar_color": "#333333"}
    except:
        return {"theme": "dark", "language": "en", "taskbar_color": "#333333"}

def load_session():
    """Load session data."""
    try:
        session_path = os.path.expanduser("~/.berke0s/session.json")
        if os.path.exists(session_path):
            with open(session_path, 'r') as f:
                return json.load(f)
        return {"open_windows": []}
    except:
        return {"open_windows": []}

### --- SPLASH SCREEN ---
def show_splash(wm):
    """Display splash screen."""
    try:
        splash = tk.Toplevel(wm.root)
        splash.overrideredirect(True)
        splash.geometry("300x200+{}+{}".format(
            (wm.root.winfo_screenwidth() - 300) // 2,
            (wm.root.winfo_screenheight() - 200) // 2
        ))
        tk.Label(splash, text="Berke0S\nLoading...", fg="white", bg="black", 
                font=("Arial", 16)).pack(expand=True)
        wm.root.after(3000, splash.destroy)
    except:
        pass

### --- MAIN APPLICATION ---
if __name__ == "__main__":
    try:
        # Install packages
        install_packages()
        
        # Setup autostart
        setup_autostart()
        
        # Load config
        config = load_config()
        
        # Initialize window manager
        wm = WindowManager()
        wm.notifications = NotificationSystem(wm)
        wm.session_manager = SessionManager(wm)
        wm.config = config
        
        # Show splash
        show_splash(wm)
        
        # System tray
        system_tray = SystemTray(wm)
        system_tray.build_ui(wm.taskbar)
        
        # Initialize apps
        file_manager = FileManager(wm)
        text_editor = TextEditor(wm)
        code_editor = CodeEditor(wm)
        calculator = Calculator(wm)
        web_browser = WebBrowser(wm)
        system_info = SystemInfo(wm)
        package_manager = PackageManager(wm)
        task_manager = TaskManager(wm)
        media_player = MediaPlayer(wm)
        image_viewer = ImageViewer(wm)
        presentation = PresentationApp(wm)
        control_center = ControlCenter(wm)
        disk_manager = DiskManager(wm)
        terminal = TerminalEmulator(wm)
        system_monitor = SystemMonitorWidget(wm)
        screenshot = ScreenshotUtility(wm)
        backup = BackupUtility(wm)
        
        # Assign apps to window manager for file handling
        wm.file_manager = file_manager
        wm.text_editor = text_editor
        wm.code_editor = code_editor
        wm.media_player = media_player
        wm.image_viewer = image_viewer
        wm.presentation = presentation
        
        # Start menu
        def show_start_menu(event):
            """Display the start menu with application options."""
            try:
                menu = tk.Menu(wm.root, tearoff=0, bg="#333333", fg="white")
                apps = {
                    "File Manager": file_manager.open,
                    "Text Editor": text_editor.open,
                    "Code Editor": code_editor.open,
                    "Calculator": calculator.open,
                    "Web Browser": web_browser.open,
                    "System Info": system_info.open,
                    "Package Manager": package_manager.open,
                    "Task Manager": task_manager.open,
                    "Media Player": lambda: media_player.play(os.path.expanduser("~/test.mp3")),
                    "Image Viewer": lambda: image_viewer.open_file(os.path.expanduser("~/test.png")),
                    "Presentation": presentation.open,
                    "Control Center": control_center.open,
                    "Disk Manager": disk_manager.open,
                    "Terminal": terminal.initialize,
                    "System Monitor": system_monitor.toggle,
                    "Screenshot": screenshot.take_screenshot,
                    "Backup Utility": backup.open
                }
                for name, cmd in apps.items():
                    menu.add_command(label=name, command=cmd)
                menu.add_separator()
                menu.add_command(label="Shutdown", command=wm.shutdown)
                menu.add_command(label="Reboot", command=wm.reboot)
                menu.add_command(label="Log Out", command=wm.logout)
                menu.post(wm.start_btn.winfo_rootx(), wm.start_btn.winfo_rooty() - 150)
            except Exception as e:
                wm.notifications.send("Start Menu", f"Error: {str(e)}")
        
        wm.start_btn.bind("<Button-1>", show_start_menu)
        
        # Desktop context menu
        def show_desktop_menu(event):
            """Display context menu on desktop right-click."""
            try:
                menu = tk.Menu(wm.root, tearoff=0, bg="#333333", fg="white")
                menu.add_command(label="New Folder", command=lambda: file_manager.create_folder())
                menu.add_command(label="New Text File", command=lambda: text_editor.new_file())
                menu.add_command(label="Open Terminal", command=terminal.initialize)
                menu.add_separator()
                menu.add_command(label="Control Center", command=control_center.open)
                menu.post(event.x_root, event.y_root)
            except Exception as e:
                wm.notifications.send("Desktop", f"Error: {str(e)}")
        
        wm.desktop.bind("<Button-3>", show_desktop_menu)
        
        # Keyboard shortcuts
        def handle_shortcuts(event):
            """Handle global keyboard shortcuts."""
            try:
                if event.keysym == 't' and event.state & 0x4 and event.state & 0x1:  # Ctrl+Alt+T
                    terminal.initialize()
                elif event.keysym == 'f' and event.state & 0x4:  # Ctrl+F
                    file_manager.open()
                elif event.keysym == 'e' and event.state & 0x4:  # Ctrl+E
                    code_editor.open()
            except:
                pass
        
        wm.root.bind("<KeyPress>", handle_shortcuts)
        
        # Restore session
        session = load_session()
        for win in session["open_windows"]:
            try:
                wm.create_window(win["title"], 
                                lambda f: tk.Label(f, text="Restored Window", fg="white", 
                                                  bg="#333333").pack(),
                                x=win["x"], y=win["y"], width=win["width"], height=win["height"])
            except:
                pass
        
        # Apply saved configuration
        wm.load_config()
        
        # Show login screen
        wm.show_login()
        
        # Main loop
        wm.root.mainloop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        wm.cleanup()
        sys.exit(1)

### --- WINDOW MANAGER ---
class WindowManager:
    """Manage windows, desktop, and system resources."""
    def __init__(self):
        """Initialize the window manager."""
        self.root = tk.Tk()
        self.root.title("Berke0S")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#333333")
        self.windows = {}
        self.notifications = None
        self.session_manager = None
        self.config = load_config()
        self.taskbar = None
        self.start_btn = None
        self.desktop = None
        self.background_video = None
        self.shortcuts = {}
        self.file_associations = {
            '.txt': self.text_editor,
            '.py': self.code_editor,
            '.sh': self.code_editor,
            '.png': self.image_viewer,
            '.jpg': self.image_viewer,
            '.mp3': self.media_player,
            '.mp4': self.media_player
        }
        self.current_user = None
        self.setup_ui()
        self.setup_file_associations()

    def setup_ui(self):
        """Set up the main UI components."""
        try:
            # Taskbar
            self.taskbar = tk.Frame(self.root, bg=self.config.get("taskbar_color", "#333333"), height=30)
            self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Start button
            self.start_btn = tk.Button(self.taskbar, text="Start", fg="white", 
                                      bg="#555555", relief=tk.RAISED)
            self.start_btn.pack(side=tk.LEFT, padx=5)
            
            # Desktop
            self.desktop = tk.Canvas(self.root, bg="#333333", highlightthickness=0)
            self.desktop.pack(fill=tk.BOTH, expand=True)
            self.desktop.bind("<B1-Motion>", self.drag_shortcut)
            self.desktop.bind("<ButtonRelease-1>", self.drop_shortcut)
            
            # Load background
            if "background" in self.config:
                subprocess.run(["feh", "--bg-scale", self.config["background"]], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if "background_video" in self.config:
                self.background_video = subprocess.Popen(
                    ["mplayer", "-vo", "x11", "-loop", "0", self.config["background_video"]], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Apply theme
            theme = self.config.get("theme", "dark")
            colors = {"dark": {"bg": "#333333", "fg": "white", "entry": "#555555"}, 
                     "light": {"bg": "#f0f0f0", "fg": "black", "entry": "#ffffff"}}
            self.apply_theme(colors[theme])
        except Exception as e:
            self.notifications.send("Window Manager", f"Error: {str(e)}")

    def setup_file_associations(self):
        """Load file associations from config."""
        try:
            assoc_file = os.path.expanduser("~/.berke0s/file_associations.json")
            if os.path.exists(assoc_file):
                with open(assoc_file, 'r') as f:
                    self.file_associations.update(json.load(f))
        except:
            pass

    def save_file_associations(self):
        """Save file associations."""
        try:
            assoc_file = os.path.expanduser("~/.berke0s/file_associations.json")
            os.makedirs(os.path.dirname(assoc_file), exist_ok=True)
            with open(assoc_file, 'w') as f:
                json.dump(self.file_associations, f)
        except:
            pass

    def create_window(self, title, build_func, x=100, y=100, width=400, height=300):
        """Create a new window."""
        try:
            window = tk.Toplevel(self.root)
            window.title(title)
            window.geometry(f"{width}x{height}+{x}+{y}")
            window.configure(bg="#333333")
            frame = tk.Frame(window, bg="#333333")
            frame.pack(fill=tk.BOTH, expand=True)
            build_func(frame)
            self.windows[window] = {"title": title, "x": x, "y": y, "width": width, "height": height}
            window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(window))
            return window
        except Exception as e:
            self.notifications.send("Window Manager", f"Error: {str(e)}")
            return None

    def close_window(self, window):
        """Close a window."""
        try:
            if window in self.windows:
                del self.windows[window]
                window.destroy()
                self.save_session()
        except:
            pass

    def add_desktop_shortcut(self, path, x, y):
        """Add a shortcut to the desktop."""
        try:
            name = os.path.basename(path)
            shortcut_id = self.desktop.create_text(x, y, text=name, fill="white", 
                                                 font=("Arial", 10), anchor=tk.NW)
            self.shortcuts[shortcut_id] = {"path": path, "x": x, "y": y}
            self.desktop.tag_bind(shortcut_id, "<Button-1>", 
                                 lambda e: self.start_drag(shortcut_id))
            self.desktop.tag_bind(shortcut_id, "<Double-1>", 
                                 lambda e: self.open_shortcut(shortcut_id))
            self.desktop.tag_bind(shortcut_id, "<Button-3>", 
                                 lambda e: self.show_shortcut_menu(shortcut_id, e))
            self.save_shortcuts()
        except Exception as e:
            self.notifications.send("Desktop", f"Error: {str(e)}")

    def start_drag(self, shortcut_id):
        """Start dragging a shortcut."""
        try:
            self.dragging = shortcut_id
        except:
            pass

    def drag_shortcut(self, event):
        """Drag a shortcut."""
        try:
            if hasattr(self, "dragging"):
                self.desktop.coords(self.dragging, event.x, event.y)
        except:
            pass

    def drop_shortcut(self, event):
        """Drop a shortcut."""
        try:
            if hasattr(self, "dragging"):
                self.shortcuts[self.dragging]["x"] = event.x
                self.shortcuts[self.dragging]["y"] = event.y
                delattr(self, "dragging")
                self.save_shortcuts()
        except:
            pass

    def show_shortcut_menu(self, shortcut_id, event):
        """Show context menu for a shortcut."""
        try:
            menu = tk.Menu(self.root, tearoff=0, bg="#333333", fg="white")
            menu.add_command(label="Open", 
                            command=lambda: self.open_shortcut(shortcut_id))
            menu.add_command(label="Delete", 
                            command=lambda: self.delete_shortcut(shortcut_id))
            menu.post(event.x_root, event.y_root)
        except:
            pass

    def open_shortcut(self, shortcut_id):
        """Open a shortcut."""
        try:
            path = self.shortcuts[shortcut_id]["path"]
            if os.path.isdir(path):
                self.file_manager.current_path = path
                self.file_manager.open()
            else:
                self.open_file(path)
        except Exception as e:
            self.notifications.send("Desktop", f"Error: {str(e)}")

    def delete_shortcut(self, shortcut_id):
        """Delete a shortcut."""
        try:
            self.desktop.delete(shortcut_id)
            del self.shortcuts[shortcut_id]
            self.save_shortcuts()
        except:
            pass

    def save_shortcuts(self):
        """Save shortcut positions."""
        try:
            shortcut_file = os.path.expanduser("~/.berke0s/shortcuts.json")
            os.makedirs(os.path.dirname(shortcut_file), exist_ok=True)
            with open(shortcut_file, 'w') as f:
                json.dump(self.shortcuts, f)
        except:
            pass

    def load_shortcuts(self):
        """Load shortcuts."""
        try:
            shortcut_file = os.path.expanduser("~/.berke0s/shortcuts.json")
            if os.path.exists(shortcut_file):
                with open(shortcut_file, 'r') as f:
                    self.shortcuts = json.load(f)
                for shortcut_id, data in list(self.shortcuts.items()):
                    if os.path.exists(data["path"]):
                        self.add_desktop_shortcut(data["path"], data["x"], data["y"])
                    else:
                        del self.shortcuts[shortcut_id]
        except:
            pass

    def open_file(self, path):
        """Open a file based on its extension."""
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext in self.file_associations:
                app = self.file_associations[ext]
                if hasattr(app, "open_file"):
                    app.open_file(path)
                else:
                    app.open()
            elif ext in ['.c', '.cpp']:
                self.code_editor.open_file(path)
            elif ext in ['.avi']:
                self.media_player.play(path)
            else:
                self.text_editor.open_file(path)
        except Exception as e:
            self.notifications.send("Window Manager", f"Error opening file: {str(e)}")

    def apply_theme(self, colors):
        """Apply theme to UI."""
        try:
            self.root.configure(bg=colors["bg"])
            self.desktop.configure(bg=colors["bg"])
            self.taskbar.configure(bg=self.config.get("taskbar_color", colors["bg"]))
            for window in self.windows:
                window.configure(bg=colors["bg"])
                for widget in window.winfo_children():
                    if isinstance(widget, (tk.Frame, tk.Label, tk.Button)):
                        widget.configure(bg=colors["bg"], fg=colors["fg"])
                    elif isinstance(widget, tk.Entry):
                        widget.configure(bg=colors["entry"], fg=colors["fg"])
        except:
            pass

    def save_config(self):
        """Save configuration."""
        try:
            config_path = os.path.expanduser("~/.berke0s/config.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.config, f)
        except:
            pass

    def load_config(self):
        """Load and apply configuration."""
        try:
            self.config = load_config()
            theme = self.config.get("theme", "dark")
            colors = {"dark": {"bg": "#333333", "fg": "white", "entry": "#555555"}, 
                     "light": {"bg": "#f0f0f0", "fg": "black", "entry": "#ffffff"}}
            self.apply_theme(colors[theme])
            if "taskbar_color" in self.config:
                self.taskbar.configure(bg=self.config["taskbar_color"])
            if "background" in self.config:
                subprocess.run(["feh", "--bg-scale", self.config["background"]], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if "background_video" in self.config:
                self.stop_background_video()
                self.background_video = subprocess.Popen(
                    ["mplayer", "-vo", "x11", "-loop", "0", self.config["background_video"]], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.load_shortcuts()
        except:
            pass

    def save_session(self):
        """Save session data."""
        try:
            session = {"open_windows": []}
            for window, data in self.windows.items():
                session["open_windows"].append({
                    "title": data["title"],
                    "x": window.winfo_x(),
                    "y": window.winfo_y(),
                    "width": window.winfo_width(),
                    "height": window.winfo_height()
                })
            session_path = os.path.expanduser("~/.berke0s/session.json")
            os.makedirs(os.path.dirname(session_path), exist_ok=True)
            with open(session_path, 'w') as f:
                json.dump(session, f)
        except:
            pass

    def stop_background_video(self):
        """Stop background video."""
        if self.background_video:
            try:
                self.background_video.terminate()
                self.background_video = None
            except:
                pass

    def show_login(self):
        """Show the login screen."""
        try:
            if self.session_manager.current_user:
                self.logout()
            for window in list(self.windows.keys()):
                self.close_window(window)
            login = LoginManager(self, self.config)
            login.show_login()
        except Exception as e:
            self.notifications.send("Window Manager", f"Error: {str(e)}")

    def shutdown(self):
        """Shutdown the system."""
        try:
            self.cleanup()
            subprocess.run(["sudo", "poweroff"], stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
        except:
            pass

    def reboot(self):
        """Reboot the system."""
        try:
            self.cleanup()
            subprocess.run(["sudo", "reboot"], stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
        except:
            pass

    def logout(self):
        """Log out the current user."""
        try:
            self.session_manager.logout()
            self.show_login()
        except:
            pass

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop_background_video()
            for window in list(self.windows.keys()):
                window.destroy()
            self.save_session()
            self.save_config()
        except:
            pass

### --- LOGIN MANAGER ---
class LoginManager:
    """Handle user login and authentication."""
    def __init__(self, wm, config):
        self.wm = wm
        self.config = config
        self.login_window = None

    def show_login(self):
        """Display the login screen."""
        try:
            self.login_window = tk.Toplevel(self.wm.root)
            self.login_window.title("Berke0S Login")
            self.login_window.geometry("400x300+{}+{}".format(
                (self.wm.root.winfo_screenwidth() - 400) // 2,
                (self.wm.root.winfo_screenheight() - 300) // 2
            ))
            self.login_window.overrideredirect(True)
            self.login_window.configure(bg="#333333")
            
            # UI elements
            tk.Label(self.login_window, text="Berke0S", fg="white", bg="#333333", 
                    font=("Arial", 20)).pack(pady=20)
            
            tk.Label(self.login_window, text="Username", fg="white", bg="#333333").pack()
            self.username_var = tk.StringVar()
            username_entry = tk.Entry(self.login_window, textvariable=self.username_var, 
                                    bg="#555555", fg="white")
            username_entry.pack(pady=5)
            username_entry.bind("<Return>", lambda e: password_entry.focus())
            
            tk.Label(self.login_window, text="Password", fg="white", bg="#333333").pack()
            self.password_var = tk.StringVar()
            password_entry = tk.Entry(self.login_window, textvariable=self.password_var, 
                                     show="*", bg="#555555", fg="white")
            password_entry.pack(pady=5)
            password_entry.bind("<Return>", lambda e: self.attempt_login())
            
            tk.Button(self.login_window, text="Login", command=self.attempt_login, 
                     bg="#555555", fg="white").pack(pady=10)
            
            # Populate username dropdown
            users = list(self.wm.session_manager.users.keys())
            if users:
                self.username_var.set(users[0])
            
            username_entry.focus()
        except Exception as e:
            self.wm.notifications.send("Login", f"Error: {str(e)}")

    def attempt_login(self):
        """Attempt to log in."""
        try:
            username = self.username_var.get()
            password = self.password_var.get()
            if self.wm.session_manager.authenticate(username, password):
                self.wm.session_manager.login(username)
                self.login_window.destroy()
                self.wm.notifications.send("Login", f"Welcome, {username}!")
                self.wm.load_shortcuts()
            else:
                self.wm.notifications.send("Login", "Invalid credentials")
                self.password_var.set("")
        except Exception as e:
            self.wm.notifications.send("Login", f"Error: {str(e)}")

### --- FILE ASSOCIATION EDITOR ---
class FileAssociationEditor:
    """Edit file associations."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("File Associations", self.build_ui, width=400, height=300)

    def build_ui(self, frame):
        """Build the file association editor UI."""
        try:
            tk.Label(frame, text="File Associations", fg="white", bg="#333333").pack(pady=5)
            self.assoc_list = tk.Listbox(frame, bg="#555555", fg="white")
            self.assoc_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(frame, text="Add Association", command=self.add_association, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Remove Association", command=self.remove_association, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            self.refresh_associations()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def refresh_associations(self):
        """Refresh the association list."""
        try:
            self.assoc_list.delete(0, tk.END)
            for ext, app in self.wm.file_associations.items():
                app_name = app.__class__.__name__
                self.assoc_list.insert(tk.END, f"{ext} -> {app_name}")
        except:
            pass

    def add_association(self):
        """Add a new file association."""
        try:
            ext = simpledialog.askstring("Add Association", "File extension (e.g., .txt):")
            if not ext:
                return
            apps = {
                "Text Editor": self.wm.text_editor,
                "Code Editor": self.wm.code_editor,
                "Media Player": self.wm.media_player,
                "Image Viewer": self.wm.image_viewer
            }
            app_name = simpledialog.askstring("Add Association", 
                                             f"Choose app ({', '.join(apps.keys())}):")
            if app_name in apps:
                self.wm.file_associations[ext] = apps[app_name]
                self.wm.save_file_associations()
                self.refresh_associations()
                self.wm.notifications.send("File Associations", f"Added {ext} -> {app_name}")
        except Exception as e:
            self.wm.notifications.send("File Associations", f"Error: {str(e)}")

    def remove_association(self):
        """Remove a file association."""
        try:
            selected = self.assoc_list.get(self.assoc_list.curselection()[0])
            ext = selected.split(" -> ")[0]
            if ext in self.wm.file_associations:
                del self.wm.file_associations[ext]
                self.wm.save_file_associations()
                self.refresh_associations()
                self.wm.notifications.send("File Associations", f"Removed {ext}")
        except Exception as e:
            self.wm.notifications.send("File Associations", f"Error: {str(e)}")

### --- SYSTEM UPDATER ---
class SystemUpdater:
    """Check and apply system updates."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("System Updater", self.build_ui, width=400, height=300)

    def build_ui(self, frame):
        """Build the system updater UI."""
        try:
            tk.Label(frame, text="System Updater", fg="white", bg="#333333").pack(pady=5)
            self.status_label = tk.Label(frame, text="Checking for updates...", 
                                        fg="white", bg="#333333")
            self.status_label.pack(pady=5)
            tk.Button(frame, text="Update Now", command=self.update_system, 
                     bg="#555555", fg="white").pack(pady=5)
            self.check_updates()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def check_updates(self):
        """Check for system updates."""
        try:
            subprocess.run(["sudo", "tce-update"], stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
            self.status_label.config(text="System is up to date")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")

    def update_system(self):
        """Apply system updates."""
        try:
            self.status_label.config(text="Updating system...")
            subprocess.run(["sudo", "tce-update"], check=True)
            self.wm.notifications.send("System Updater", "System updated successfully")
            self.status_label.config(text="System updated")
        except Exception as e:
            self.wm.notifications.send("System Updater", f"Error: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)}")

### --- ENHANCED PRESENTATION APP ---
class PresentationApp:
    """Enhanced presentation application with text editing."""
    def __init__(self, wm):
        self.wm = wm
        self.slides = []
        self.current_slide = 0
        self.photos = []

    def open(self):
        self.wm.create_window("Presentation", self.build_ui, width=800, height=600)

    def build_ui(self, frame):
        """Build the presentation UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="Add Slide", command=self.add_slide, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Next", command=self.next_slide, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Previous", command=self.prev_slide, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Add Image", command=self.add_image, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Save Presentation", command=self.save_presentation, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Load Presentation", command=self.load_presentation, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)

            # Main content
            main_frame = tk.Frame(frame, bg="#333333")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Slide canvas
            self.canvas = tk.Canvas(main_frame, bg="#333333", width=400, height=300)
            self.canvas.pack(side=tk.LEFT, padx=5)
            
            # Text editor
            text_frame = tk.Frame(main_frame, bg="#333333")
            text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            tk.Label(text_frame, text="Slide Text", fg="white", bg="#333333").pack()
            self.text_editor = tk.Text(text_frame, bg="#555555", fg="white", 
                                      font=("Arial", 12), height=10)
            self.text_editor.pack(fill=tk.BOTH, expand=True, padx=5)
            tk.Button(text_frame, text="Apply Text", command=self.apply_text, 
                     bg="#555555", fg="white").pack(pady=5)
            
            self.add_slide()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def add_slide(self):
        """Add a new slide."""
        try:
            self.slides.append({"image": None, "text": ""})
            self.current_slide = len(self.slides) - 1
            self.update_slide()
        except:
            pass

    def add_image(self):
        """Add an image to the current slide."""
        try:
            filename = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg")])
            if filename:
                self.slides[self.current_slide]["image"] = filename
                self.update_slide()
        except Exception as e:
            self.wm.notifications.send("Presentation", f"Error: {str(e)}")

    def apply_text(self):
        """Apply text to the current slide."""
        try:
            self.slides[self.current_slide]["text"] = self.text_editor.get(1.0, tk.END).strip()
            self.update_slide()
        except:
            pass

    def next_slide(self):
        """Go to next slide."""
        try:
            if self.current_slide < len(self.slides) - 1:
                self.current_slide += 1
                self.update_slide()
        except:
            pass

    def prev_slide(self):
        """Go to previous slide."""
        try:
            if self.current_slide > 0:
                self.current_slide -= 1
                self.update_slide()
        except:
            pass

    def update_slide(self):
        """Update the current slide display."""
        try:
            self.canvas.delete("all")
            self.photos = []
            slide = self.slides[self.current_slide]
            if slide["image"]:
                img = Image.open(slide["image"])
                img = img.resize((400, 300), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photos.append(photo)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas.create_text(200, 350, text=slide["text"], fill="white", 
                                  font=("Arial", 12))
            self.text_editor.delete(1.0, tk.END)
            self.text_editor.insert(tk.END, slide["text"])
        except:
            pass

    def save_presentation(self):
        """Save the presentation."""
        try:
            filename = filedialog.asksaveasfilename(filetypes=[("Presentation", "*.pres")])
            if filename:
                with open(filename, 'w') as f:
                    json.dump(self.slides, f)
                self.wm.notifications.send("Presentation", "Presentation saved")
        except Exception as e:
            self.wm.notifications.send("Presentation", f"Error: {str(e)}")

    def load_presentation(self):
        """Load a presentation."""
        try:
            filename = filedialog.askopenfilename(filetypes=[("Presentation", "*.pres")])
            if filename:
                with open(filename, 'r') as f:
                    self.slides = json.load(f)
                self.current_slide = 0
                self.update_slide()
                self.wm.notifications.send("Presentation", "Presentation loaded")
        except Exception as e:
            self.wm.notifications.send("Presentation", f"Error: {str(e)}")

### --- ENHANCED CODE EDITOR ---
class CodeEditor:
    """Enhanced code editor with debugging."""
    def __init__(self, wm):
        self.wm = wm
        self.filename = None
        self.highlighter = None
        self.debug_process = None

    def open(self):
        self.wm.create_window("Code Editor", self.build_ui, width=800, height=600)

    def open_file(self, filename):
        """Open a specific file."""
        self.filename = filename
        self.open()
        self.load_file()

    def build_ui(self, frame):
        """Build the code editor UI."""
        try:
            # Menu bar
            menubar = tk.Menu(frame)
            file_menu = tk.Menu(menubar, tearoff=0, bg="#333333", fg="white")
            file_menu.add_command(label="New", command=self.new_file)
            file_menu.add_command(label="Open", command=self.open_dialog)
            file_menu.add_command(label="Save", command=self.save_file)
            file_menu.add_command(label="Save As", command=self.save_as)
            file_menu.add_separator()
            file_menu.add_command(label="Run", command=self.run_code)
            file_menu.add_command(label="Debug", command=self.debug_code)
            menubar.add_cascade(label="File", menu=file_menu)
            self.wm.root.config(menu=menubar)

            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="New", command=self.new_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Open", command=self.open_dialog, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Save", command=self.save_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Run", command=self.run_code, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Debug", command=self.debug_code, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            language_var = tk.StringVar(value="Python")
            tk.OptionMenu(toolbar, language_var, "Python", "Bash", "C", 
                         command=self.update_highlighter).pack(side=tk.LEFT, padx=2)

            # Editor and output
            main_frame = tk.Frame(frame, bg="#333333")
            main_frame.pack(fill=tk.BOTH, expand=True)
            self.editor = tk.Text(main_frame, bg="#2e2e2e", fg="white", 
                                font=("Monospace", 12), insertbackground="white")
            self.editor.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            self.output = tk.Text(main_frame, bg="#2e2e2e", fg="white", 
                                font=("Monospace", 12), height=10)
            self.output.pack(fill=tk.X, side=tk.BOTTOM)
            scrollbar = tk.Scrollbar(main_frame, command=self.editor.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.editor.config(yscrollcommand=scrollbar.set)

            # Syntax highlighting
            self.highlighter = PygmentsHighlighter(self.editor, "python")
            self.editor.bind("<KeyRelease>", self.highlight_code)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def new_file(self):
        """Create a new file."""
        try:
            self.filename = None
            self.editor.delete(1.0, tk.END)
            self.output.delete(1.0, tk.END)
        except:
            pass

    def open_dialog(self):
        """Open a file dialog."""
        try:
            filename = filedialog.askopenfilename()
            if filename:
                self.filename = filename
                self.load_file()
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def load_file(self):
        """Load file content."""
        try:
            with open(self.filename, 'r') as f:
                content = f.read()
            self.editor.delete(1.0, tk.END)
            self.editor.insert(tk.END, content)
            ext = os.path.splitext(self.filename)[1].lower()
            self.update_highlighter(ext[1:] if ext else "python")
            self.highlight_code()
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def save_file(self):
        """Save the current file."""
        try:
            if self.filename:
                with open(self.filename, 'w') as f:
                    f.write(self.editor.get(1.0, tk.END).strip())
            else:
                self.save_as()
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def save_as(self):
        """Save file with a new name."""
        try:
            filename = filedialog.asksaveasfilename()
            if filename:
                self.filename = filename
                self.save_file()
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def run_code(self):
        """Run the code."""
        try:
            code = self.editor.get(1.0, tk.END).strip()
            self.output.delete(1.0, tk.END)
            if not code:
                return
            ext = os.path.splitext(self.filename or "")[1].lower() if self.filename else ".py"
            if ext == ".py":
                process = subprocess.run(["python3", "-"], input=code, text=True, 
                                       capture_output=True)
                self.output.insert(tk.END, process.stdout + process.stderr)
            elif ext == ".sh":
                process = subprocess.run(["bash", "-c", code], text=True, 
                                       capture_output=True)
                self.output.insert(tk.END, process.stdout + process.stderr)
            elif ext == ".c":
                with open("/tmp/temp.c", "w") as f:
                    f.write(code)
                process = subprocess.run(["gcc", "/tmp/temp.c", "-o", "/tmp/temp"], 
                                       text=True, capture_output=True)
                if process.returncode == 0:
                    run = subprocess.run(["/tmp/temp"], text=True, capture_output=True)
                    self.output.insert(tk.END, run.stdout + run.stderr)
                else:
                    self.output.insert(tk.END, process.stderr)
            else:
                self.wm.notifications.send("Code Editor", "Unsupported file type")
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def debug_code(self):
        """Debug the code (Python only)."""
        try:
            if self.debug_process:
                self.debug_process.terminate()
            code = self.editor.get(1.0, tk.END).strip()
            self.output.delete(1.0, tk.END)
            if not code:
                return
            if self.filename and self.filename.endswith('.py'):
                with open("/tmp/debug.py", "w") as f:
                    f.write(code)
                self.debug_process = subprocess.Popen(
                    ["python3", "-m", "pdb", "/tmp/debug.py"], 
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = self.debug_process.communicate()
                self.output.insert(tk.END, stdout + stderr)
            else:
                self.wm.notifications.send("Code Editor", "Debugging only supported for Python")
        except Exception as e:
            self.wm.notifications.send("Code Editor", f"Error: {str(e)}")

    def update_highlighter(self, language):
        """Update syntax highlighter."""
        try:
            language = language.lower()
            if language in ['py', 'python']:
                self.highlighter = PygmentsHighlighter(self.editor, "python")
            elif language in ['sh', 'bash']:
                self.highlighter = PygmentsHighlighter(self.editor, "bash")
            elif language in ['c', 'cpp']:
                self.highlighter = PygmentsHighlighter(self.editor, "c")
            self.highlight_code()
        except:
            pass

    def highlight_code(self, event=None):
        """Apply syntax highlighting."""
        try:
            self.highlighter.highlight()
        except:
            pass

### --- EMAIL CLIENT ---
class EmailClient:
    """Simple email client using mutt and Python libraries."""
    def __init__(self, wm):
        self.wm = wm
        self.email_config = self.load_email_config()

    def load_email_config(self):
        """Load email configuration."""
        try:
            config_path = os.path.expanduser("~/.berke0s/email.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            return {"smtp_server": "", "smtp_port": 587, "imap_server": "", "imap_port": 993, 
                    "username": "", "password": ""}
        except:
            return {"smtp_server": "", "smtp_port": 587, "imap_server": "", "imap_port": 993, 
                    "username": "", "password": ""}

    def save_email_config(self):
        """Save email configuration."""
        try:
            config_path = os.path.expanduser("~/.berke0s/email.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.email_config, f)
        except:
            pass

    def open(self):
        self.wm.create_window("Email Client", self.build_ui, width=800, height=600)

    def build_ui(self, frame):
        """Build the email client UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="Compose", command=self.compose_email, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Refresh", command=self.refresh_inbox, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Configure", command=self.configure_email, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)

            # Inbox
            self.inbox_list = tk.Listbox(frame, bg="#555555", fg="white", selectmode=tk.SINGLE)
            self.inbox_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.inbox_list.bind('<Double-1>', self.read_email)
            self.refresh_inbox()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def refresh_inbox(self):
        """Refresh the inbox."""
        try:
            self.inbox_list.delete(0, tk.END)
            if not all([self.email_config["imap_server"], self.email_config["username"], 
                       self.email_config["password"]]):
                self.wm.notifications.send("Email", "Please configure email settings")
                return
            mail = imaplib.IMAP4_SSL(self.email_config["imap_server"], self.email_config["imap_port"])
            mail.login(self.email_config["username"], self.email_config["password"])
            mail.select("INBOX")
            _, data = mail.search(None, "ALL")
            for num in data[0].split()[:10]:  # Limit to 10 emails
                _, msg_data = mail.fetch(num, "(RFC822)")
                email_msg = email.message_from_bytes(msg_data[0][1])
                subject = email.header.decode_header(email_msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                self.inbox_list.insert(tk.END, f"From: {email_msg['From']} | Subject: {subject}")
            mail.logout()
        except Exception as e:
            self.wm.notifications.send("Email", f"Error: {str(e)}")

    def compose_email(self):
        """Compose a new email."""
        try:
            window = self.wm.create_window("Compose Email", lambda f: self.build_compose_ui(f), 
                                         width=600, height=400)
        except Exception as e:
            self.wm.notifications.send("Email", f"Error: {str(e)}")

    def build_compose_ui(self, frame):
        """Build the compose email UI."""
        try:
            tk.Label(frame, text="To:", fg="white", bg="#333333").pack()
            to_var = tk.StringVar()
            tk.Entry(frame, textvariable=to_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Label(frame, text="Subject:", fg="white", bg="#333333").pack()
            subject_var = tk.StringVar()
            tk.Entry(frame, textvariable=subject_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Label(frame, text="Body:", fg="white", bg="#333333").pack()
            body_text = tk.Text(frame, bg="#555555", fg="white", height=10)
            body_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            tk.Button(frame, text="Send", 
                     command=lambda: self.send_email(to_var.get(), subject_var.get(), 
                                                    body_text.get(1.0, tk.END).strip()), 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def send_email(self, to, subject, body):
        """Send an email."""
        try:
            if not all([self.email_config["smtp_server"], self.email_config["username"], 
                       self.email_config["password"]]):
                self.wm.notifications.send("Email", "Please configure email settings")
                return
            msg = EmailMessage()
            msg.set_content(body)
            msg["Subject"] = subject
            msg["From"] = self.email_config["username"]
            msg["To"] = to
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["username"], self.email_config["password"])
                server.send_message(msg)
            self.wm.notifications.send("Email", "Email sent successfully")
        except Exception as e:
            self.wm.notifications.send("Email", f"Error: {str(e)}")

    def read_email(self, event):
        """Read a selected email."""
        try:
            selected = self.inbox_list.get(self.inbox_list.curselection()[0])
            mail = imaplib.IMAP4_SSL(self.email_config["imap_server"], self.email_config["imap_port"])
            mail.login(self.email_config["username"], self.email_config["password"])
            mail.select("INBOX")
            _, data = mail.search(None, "ALL")
            num = data[0].split()[self.inbox_list.curselection()[0]]
            _, msg_data = mail.fetch(num, "(RFC822)")
            email_msg = email.message_from_bytes(msg_data[0][1])
            body = ""
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_msg.get_payload(decode=True).decode()
            mail.logout()
            self.wm.create_window(f"Email: {selected}", 
                                lambda f: tk.Text(f, bg="#555555", fg="white", 
                                                 font=("Arial", 12)).insert(tk.END, body))
        except Exception as e:
            self.wm.notifications.send("Email", f"Error: {str(e)}")

    def configure_email(self):
        """Configure email settings."""
        try:
            window = self.wm.create_window("Email Settings", self.build_config_ui, 
                                         width=400, height=300)
        except Exception as e:
            self.wm.notifications.send("Email", f"Error: {str(e)}")

    def build_config_ui(self, frame):
        """Build the email configuration UI."""
        try:
            tk.Label(frame, text="SMTP Server:", fg="white", bg="#333333").pack()
            smtp_var = tk.StringVar(value=self.email_config["smtp_server"])
            tk.Entry(frame, textvariable=smtp_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Label(frame, text="SMTP Port:", fg="white", bg="#333333").pack()
            smtp_port_var = tk.IntVar(value=self.email_config["smtp_port"])
            tk.Entry(frame, textvariable=smtp_port_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Label(frame, text="IMAP Server:", fg="white", bg="#333333").pack()
            imap_var = tk.StringVar(value=self.email_config["imap_server"])
            tk.Entry(frame, textvariable=imap_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Label(frame, text="IMAP Port:", fg="white", bg="#333333").pack()
            imap_port_var = tk.IntVar(value=self.email_config["imap_port"])
            tk.Entry(frame, textvariable=imap_port_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Label(frame, text="Username:", fg="white", bg="#333333").pack()
            username_var = tk.StringVar(value=self.email_config["username"])
            tk.Entry(frame, textvariable=username_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Label(frame, text="Password:", fg="white", bg="#333333").pack()
            password_var = tk.StringVar(value=self.email_config["password"])
            tk.Entry(frame, textvariable=password_var, show="*", bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Button(frame, text="Save", 
                     command=lambda: self.save_email_settings(smtp_var.get(), smtp_port_var.get(), 
                                                            imap_var.get(), imap_port_var.get(), 
                                                            username_var.get(), password_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def save_email_settings(self, smtp, smtp_port, imap, imap_port, username, password):
        """Save email settings."""
        try:
            self.email_config.update({
                "smtp_server": smtp, "smtp_port": smtp_port, 
                "imap_server": imap, "imap_port": imap_port, 
                "username": username, "password": password
            })
            self.save_email_config()
            self.wm.notifications.send("Email", "Settings saved")
        except Exception as e:
            self.wm.notifications.send("Email", f"Error: {str(e)}")

### --- CALENDAR APP ---
class CalendarApp:
    """Calendar with event scheduling."""
    def __init__(self, wm):
        self.wm = wm
        self.events = self.load_events()
        self.current_date = datetime.datetime.now()

    def load_events(self):
        """Load events from file."""
        try:
            events_path = os.path.expanduser("~/.berke0s/events.json")
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}

    def save_events(self):
        """Save events to file."""
        try:
            events_path = os.path.expanduser("~/.berke0s/events.json")
            os.makedirs(os.path.dirname(events_path), exist_ok=True)
            with open(events_path, 'w') as f:
                json.dump(self.events, f)
        except:
            pass

    def open(self):
        self.wm.create_window("Calendar", self.build_ui, width=600, height=400)

    def build_ui(self, frame):
        """Build the calendar UI."""
        try:
            # Navigation
            nav = tk.Frame(frame, bg="#333333")
            nav.pack(fill=tk.X)
            tk.Button(nav, text="<< Prev", command=self.prev_month, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            self.month_label = tk.Label(nav, text=self.current_date.strftime("%B %Y"), 
                                       fg="white", bg="#333333")
            self.month_label.pack(side=tk.LEFT, expand=True)
            tk.Button(nav, text="Next >>", command=self.next_month, 
                     bg="#555555", fg="white").pack(side=tk.RIGHT, padx=5)
            tk.Button(nav, text="Add Event", command=self.add_event, 
                     bg="#555555", fg="white").pack(side=tk.RIGHT, padx=5)

            # Calendar grid
            self.calendar_frame = tk.Frame(frame, bg="#333333")
            self.calendar_frame.pack(fill=tk.BOTH, expand=True)
            self.update_calendar()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def update_calendar(self):
        """Update the calendar display."""
        try:
            for widget in self.calendar_frame.winfo_children():
                widget.destroy()
            cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for day in days:
                tk.Label(self.calendar_frame, text=day, fg="white", bg="#333333").grid(column=days.index(day), row=0)
            for week_idx, week in enumerate(cal):
                for day_idx, day in enumerate(week):
                    if day != 0:
                        date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
                        text = str(day)
                        if date_str in self.events:
                            text += f" ({len(self.events[date_str])})"
                        btn = tk.Button(self.calendar_frame, text=text, 
                                       command=lambda d=date_str: self.show_events(d), 
                                       bg="#555555", fg="white")
                        btn.grid(column=day_idx, row=week_idx + 1, sticky="nsew")
            for i in range(7):
                self.calendar_frame.grid_columnconfigure(i, weight=1)
            for i in range(len(cal) + 1):
                self.calendar_frame.grid_rowconfigure(i, weight=1)
            self.month_label.config(text=self.current_date.strftime("%B %Y"))
        except:
            pass

    def prev_month(self):
        """Go to previous month."""
        try:
            self.current_date = self.current_date - datetime.timedelta(days=self.current_date.day)
            self.update_calendar()
        except:
            pass

    def next_month(self):
        """Go to next month."""
        try:
            self.current_date = (self.current_date + 
                                datetime.timedelta(days=calendar.monthrange(
                                    self.current_date.year, self.current_date.month)[1] + 1))
            self.current_date = self.current_date.replace(day=1)
            self.update_calendar()
        except:
            pass

    def add_event(self):
        """Add a new event."""
        try:
            window = self.wm.create_window("Add Event", self.build_event_ui, width=400, height=200)
        except Exception as e:
            self.wm.notifications.send("Calendar", f"Error: {str(e)}")

    def build_event_ui(self, frame):
        """Build the event creation UI."""
        try:
            tk.Label(frame, text="Date (YYYY-MM-DD):", fg="white", bg="#333333").pack()
            date_var = tk.StringVar(value=self.current_date.strftime("%Y-%m-%d"))
            tk.Entry(frame, textvariable=date_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Label(frame, text="Event:", fg="white", bg="#333333").pack()
            event_var = tk.StringVar()
            tk.Entry(frame, textvariable=event_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            
            tk.Button(frame, text="Add", 
                     command=lambda: self.save_event(date_var.get(), event_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def save_event(self, date, event):
        """Save an event."""
        try:
            if not re.match(r"\d{4}-\d{2}-\d{2}", date):
                self.wm.notifications.send("Calendar", "Invalid date format")
                return
            if date not in self.events:
                self.events[date] = []
            self.events[date].append(event)
            self.save_events()
            self.update_calendar()
            self.wm.notifications.send("Calendar", "Event added")
        except Exception as e:
            self.wm.notifications.send("Calendar", f"Error: {str(e)}")

    def show_events(self, date):
        """Show events for a date."""
        try:
            events = self.events.get(date, [])
            window = self.wm.create_window(f"Events for {date}", 
                                         lambda f: self.build_events_ui(f, date, events), 
                                         width=400, height=200)
        except Exception as e:
            self.wm.notifications.send("Calendar", f"Error: {str(e)}")

    def build_events_ui(self, frame, date, events):
        """Build the events display UI."""
        try:
            tk.Label(frame, text=f"Events for {date}", fg="white", bg="#333333").pack()
            listbox = tk.Listbox(frame, bg="#555555", fg="white")
            listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            for event in events:
                listbox.insert(tk.END, event)
            tk.Button(frame, text="Delete Selected", 
                     command=lambda: self.delete_event(date, listbox.curselection()), 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def delete_event(self, date, indices):
        """Delete selected events."""
        try:
            for idx in reversed(indices):
                self.events[date].pop(idx)
            if not self.events[date]:
                del self.events[date]
            self.save_events()
            self.update_calendar()
            self.wm.notifications.send("Calendar", "Event deleted")
        except Exception as e:
            self.wm.notifications.send("Calendar", f"Error: {str(e)}")

### --- NOTES APP ---
class NotesApp:
    """Note-taking application with rich text support."""
    def __init__(self, wm):
        self.wm = wm
        self.filename = None
        self.recent_files = self.load_recent_files()

    def load_recent_files(self):
        """Load recent files."""
        try:
            recent_path = os.path.expanduser("~/.berke0s/notes_recent.json")
            if os.path.exists(recent_path):
                with open(recent_path, 'r') as f:
                    return json.load(f)
            return []
        except:
            return []

    def save_recent_files(self):
        """Save recent files."""
        try:
            recent_path = os.path.expanduser("~/.berke0s/notes_recent.json")
            os.makedirs(os.path.dirname(recent_path), exist_ok=True)
            with open(recent_path, 'w') as f:
                json.dump(self.recent_files[:10], f)
        except:
            pass

    def open(self):
        self.wm.create_window("Notes", self.build_ui, width=600, height=400)

    def open_file(self, filename):
        """Open a specific note file."""
        self.filename = filename
        self.open()
        self.load_file()

    def build_ui(self, frame):
        """Build the notes UI."""
        try:
            # Menu bar
            menubar = tk.Menu(frame)
            file_menu = tk.Menu(menubar, tearoff=0, bg="#333333", fg="white")
            file_menu.add_command(label="New", command=self.new_file)
            file_menu.add_command(label="Open", command=self.open_dialog)
            file_menu.add_command(label="Save", command=self.save_file)
            file_menu.add_command(label="Save As", command=self.save_as)
            recent_menu = tk.Menu(file_menu, tearoff=0, bg="#333333", fg="white")
            for recent in self.recent_files:
                recent_menu.add_command(label=os.path.basename(recent), 
                                      command=lambda f=recent: self.open_file(f))
            file_menu.add_cascade(label="Recent Files", menu=recent_menu)
            menubar.add_cascade(label="File", menu=file_menu)
            format_menu = tk.Menu(menubar, tearoff=0, bg="#333333", fg="white")
            format_menu.add_command(label="Bold", command=lambda: self.apply_format("bold"))
            format_menu.add_command(label="Italic", command=lambda: self.apply_format("italic"))
            menubar.add_cascade(label="Format", menu=format_menu)
            self.wm.root.config(menu=menubar)

            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="New", command=self.new_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Open", command=self.open_dialog, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Save", command=self.save_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Bold", command=lambda: self.apply_format("bold"), 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Italic", command=lambda: self.apply_format("italic"), 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)

            # Text area
            self.text = tk.Text(frame, bg="#555555", fg="white", font=("Arial", 12))
            self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.text.tag_configure("bold", font=("Arial", 12, "bold"))
            self.text.tag_configure("italic", font=("Arial", 12, "italic"))
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def new_file(self):
        """Create a new note."""
        try:
            self.filename = None
            self.text.delete(1.0, tk.END)
        except:
            pass

    def open_dialog(self):
        """Open a file dialog."""
        try:
            filename = filedialog.askopenfilename(filetypes=[("Notes", "*.txt *.note")])
            if filename:
                self.filename = filename
                self.load_file()
                if filename not in self.recent_files:
                    self.recent_files.insert(0, filename)
                    self.save_recent_files()
        except Exception as e:
            self.wm.notifications.send("Notes", f"Error: {str(e)}")

    def load_file(self):
        """Load note content."""
        try:
            with open(self.filename, 'r') as f:
                content = f.read()
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, content)
        except Exception as e:
            self.wm.notifications.send("Notes", f"Error: {str(e)}")

    def save_file(self):
        """Save the current note."""
        try:
            if self.filename:
                with open(self.filename, 'w') as f:
                    f.write(self.text.get(1.0, tk.END).strip())
                if self.filename not in self.recent_files:
                    self.recent_files.insert(0, self.filename)
                    self.save_recent_files()
            else:
                self.save_as()
        except Exception as e:
            self.wm.notifications.send("Notes", f"Error: {str(e)}")

    def save_as(self):
        """Save note with a new name."""
        try:
            filename = filedialog.asksaveasfilename(filetypes=[("Notes", "*.note")])
            if filename:
                self.filename = filename
                self.save_file()
        except Exception as e:
            self.wm.notifications.send("Notes", f"Error: {str(e)}")

    def apply_format(self, tag):
        """Apply text formatting."""
        try:
            sel_start, sel_end = self.text.tag_ranges(tk.SEL) or (None, None)
            if sel_start:
                self.text.tag_add(tag, sel_start, sel_end)
            else:
                self.wm.notifications.send("Notes", "Select text to format")
        except Exception as e:
            self.wm.notifications.send("Notes", f"Error: {str(e)}")

### --- NETWORK MONITOR ---
class NetworkMonitor:
    """Monitor network usage."""
    def __init__(self, wm):
        self.wm = wm
        self.visible = False
        self.window = None
        self.net_io = psutil.net_io_counters()

    def toggle(self):
        """Toggle the network monitor."""
        if not self.visible:
            self.window = self.wm.create_window("Network Monitor", self.build_ui, 
                                              width=400, height=200)
            self.visible = True
        else:
            self.wm.close_window(self.window)
            self.visible = False
            self.window = None

    def build_ui(self, frame):
        """Build the network monitor UI."""
        try:
            self.sent_label = tk.Label(frame, text="Sent: 0 KB/s", fg="white", bg="#333333")
            self.sent_label.pack(pady=5)
            self.recv_label = tk.Label(frame, text="Received: 0 KB/s", fg="white", bg="#333333")
            self.recv_label.pack(pady=5)
            self.update_stats()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def update_stats(self):
        """Update network stats."""
        try:
            new_io = psutil.net_io_counters()
            sent = (new_io.bytes_sent - self.net_io.bytes_sent) / 1024  # KB/s
            recv = (new_io.bytes_recv - self.net_io.bytes_recv) / 1024  # KB/s
            self.net_io = new_io
            self.sent_label.config(text=f"Sent: {sent:.2f} KB/s")
            self.recv_label.config(text=f"Received: {recv:.2f} KB/s")
            if self.visible:
                self.wm.root.after(1000, self.update_stats)
        except:
            pass

### --- SYSTEM LOG VIEWER ---
class SystemLogViewer:
    """View system logs."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("System Logs", self.build_ui, width=600, height=400)

    def build_ui(self, frame):
        """Build the log viewer UI."""
        try:
            tk.Label(frame, text="System Logs", fg="white", bg="#333333").pack(pady=5)
            self.log_text = tk.Text(frame, bg="#555555", fg="white", font=("Monospace", 10))
            self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(frame, text="Refresh", command=self.refresh_logs, 
                     bg="#555555", fg="white").pack(pady=5)
            self.refresh_logs()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def refresh_logs(self):
        """Refresh system logs."""
        try:
            self.log_text.delete(1.0, tk.END)
            log_path = "/var/log/messages"
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    self.log_text.insert(tk.END, f.read())
            else:
                self.log_text.insert(tk.END, "No logs found")
        except Exception as e:
            self.wm.notifications.send("Logs", f"Error: {str(e)}")

### --- ENHANCED WINDOW MANAGER ---
class WindowManager:
    """Enhanced window manager with snapping and virtual desktops."""
    def __init__(self):
        """Initialize the window manager."""
        self.root = tk.Tk()
        self.root.title("Berke0S")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#333333")
        self.windows = {}
        self.notifications = None
        self.session_manager = None
        self.config = load_config()
        self.taskbar = None
        self.start_btn = None
        self.desktop = None
        self.background_video = None
        self.shortcuts = {}
        self.pinned_apps = []
        self.virtual_desktops = [{}]  # List of window dictionaries
        self.current_desktop = 0
        self.file_associations = {
            '.txt': self.text_editor,
            '.py': self.code_editor,
            '.sh': self.code_editor,
            '.c': self.code_editor,
            '.png': self.image_viewer,
            '.jpg': self.image_viewer,
            '.mp3': self.media_player,
            '.mp4': self.media_player,
            '.note': self.notes
        }
        self.current_user = None
        self.session_timeout = None
        self.setup_ui()
        self.setup_file_associations()
        self.start_session_timeout()

    def setup_ui(self):
        """Set up the main UI components."""
        try:
            # Taskbar
            self.taskbar = tk.Frame(self.root, bg=self.config.get("taskbar_color", "#333333"), height=30)
            self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Start button
            self.start_btn = tk.Button(self.taskbar, text="Start", fg="white", 
                                      bg="#555555", relief=tk.RAISED)
            self.start_btn.pack(side=tk.LEFT, padx=5)
            
            # Search bar
            self.search_var = tk.StringVar()
            tk.Entry(self.taskbar, textvariable=self.search_var, bg="#555555", fg="white", 
                    width=20).pack(side=tk.LEFT, padx=5)
            tk.Button(self.taskbar, text="Search", command=self.global_search, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            
            # Pinned apps
            self.pinned_frame = tk.Frame(self.taskbar, bg="#333333")
            self.pinned_frame.pack(side=tk.LEFT, padx=5)
            self.update_pinned_apps()
            
            # Desktop
            self.desktop = tk.Canvas(self.root, bg="#333333", highlightthickness=0)
            self.desktop.pack(fill=tk.BOTH, expand=True)
            self.desktop.bind("<B1-Motion>", self.drag_shortcut)
            self.desktop.bind("<ButtonRelease-1>", self.drop_shortcut)
            
            # Load background
            if "background" in self.config:
                subprocess.run(["feh", "--bg-scale", self.config["background"]], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if "background_slideshow" in self.config:
                self.start_slideshow()
            if "background_video" in self.config:
                self.background_video = subprocess.Popen(
                    ["mplayer", "-vo", "x11", "-loop", "0", self.config["background_video"]], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Apply theme
            theme = self.config.get("theme", "dark")
            colors = {"dark": {"bg": "#333333", "fg": "white", "entry": "#555555"}, 
                     "light": {"bg": "#f0f0f0", "fg": "black", "entry": "#ffffff"}}
            self.apply_theme(colors[theme])
            
            # Virtual desktop controls
            desktop_frame = tk.Frame(self.taskbar, bg="#333333")
            desktop_frame.pack(side=tk.RIGHT, padx=5)
            tk.Button(desktop_frame, text="New Desktop", command=self.add_desktop, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(desktop_frame, text="Prev Desktop", command=self.prev_desktop, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(desktop_frame, text="Next Desktop", command=self.next_desktop, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
        except Exception as e:
            self.notifications.send("Window Manager", f"Error: {str(e)}")

    def start_slideshow(self):
        """Start wallpaper slideshow."""
        try:
            images = self.config.get("background_slideshow", [])
            if not images:
                return
            def cycle():
                try:
                    current = self.config.get("current_slideshow", 0)
                    subprocess.run(["feh", "--bg-scale", images[current]], 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.config["current_slideshow"] = (current + 1) % len(images)
                    self.save_config()
                    self.root.after(300000, cycle)  # 5 minutes
                except:
                    pass
            cycle()
        except:
            pass

    def update_pinned_apps(self):
        """Update pinned apps in taskbar."""
        try:
            for widget in self.pinned_frame.winfo_children():
                widget.destroy()
            apps = {
                "File Manager": self.file_manager.open,
                "Code Editor": self.code_editor.open,
                "Notes": self.notes.open
            }
            for app in self.pinned_apps:
                if app in apps:
                    tk.Button(self.pinned_frame, text=app, command=apps[app], 
                             bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
        except:
            pass

    def pin_app(self, app_name):
        """Pin an app to the taskbar."""
        try:
            if app_name not in self.pinned_apps:
                self.pinned_apps.append(app_name)
                self.update_pinned_apps()
                self.save_config()
        except:
            pass

    def unpin_app(self, app_name):
        """Unpin an app from the taskbar."""
        try:
            if app_name in self.pinned_apps:
                self.pinned_apps.remove(app_name)
                self.update_pinned_apps()
                self.save_config()
        except:
            pass

    def global_search(self):
        """Perform a global search for files and apps."""
        try:
            query = self.search_var.get().lower()
            results = []
            # Search apps
            apps = {
                "File Manager": self.file_manager.open,
                "Text Editor": self.text_editor.open,
                "Code Editor": self.code_editor.open,
                "Calculator": self.calculator.open,
                "Web Browser": self.web_browser.open,
                "System Info": self.system_info.open,
                "Package Manager": self.package_manager.open,
                "Task Manager": self.task_manager.open,
                "Media Player": lambda: self.media_player.play(os.path.expanduser("~/test.mp3")),
                "Image Viewer": lambda: self.image_viewer.open_file(os.path.expanduser("~/test.png")),
                "Presentation": self.presentation.open,
                "Control Center": self.control_center.open,
                "Disk Manager": self.disk_manager.open,
                "Terminal": self.terminal.initialize,
                "System Monitor": self.system_monitor.toggle,
                "Screenshot": self.screenshot.take_screenshot,
                "Backup Utility": self.backup.open,
                "Email Client": self.email_client.open,
                "Calendar": self.calendar.open,
                "Notes": self.notes.open,
                "Network Monitor": self.network_monitor.toggle,
                "System Logs": self.log_viewer.open
            }
            for app in apps:
                if query in app.lower():
                    results.append(f"App: {app}")
            # Search files
            for root, _, files in os.walk(os.path.expanduser("~")):
                for file in files:
                    if query in file.lower():
                        results.append(f"File: {os.path.join(root, file)}")
            # Display results
            self.wm.create_window("Search Results", 
                                lambda f: self.build_search_ui(f, results), 
                                width=600, height=400)
        except Exception as e:
            self.notifications.send("Search", f"Error: {str(e)}")

    def build_search_ui(self, frame, results):
        """Build the search results UI."""
        try:
            listbox = tk.Listbox(frame, bg="#555555", fg="white")
            listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            for result in results[:50]:  # Limit to 50 results
                listbox.insert(tk.END, result)
            listbox.bind('<Double-1>', lambda e: self.open_search_result(listbox.get(listbox.curselection()[0])))
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def open_search_result(self, result):
        """Open a search result."""
        try:
            if result.startswith("App: "):
                app_name = result[5:]
                apps = {
                    "File Manager": self.file_manager.open,
                    "Text Editor": self.text_editor.open,
                    "Code Editor": self.code_editor.open,
                    "Calculator": self.calculator.open,
                    "Web Browser": self.web_browser.open,
                    "System Info": self.system_info.open,
                    "Package Manager": self.package_manager.open,
                    "Task Manager": self.task_manager.open,
                    "Media Player": lambda: self.media_player.play(os.path.expanduser("~/test.mp3")),
                    "Image Viewer": lambda: self.image_viewer.open_file(os.path.expanduser("~/test.png")),
                    "Presentation": self.presentation.open,
                    "Control Center": self.control_center.open,
                    "Disk Manager": self.disk_manager.open,
                    "Terminal": self.terminal.initialize,
                    "System Monitor": self.system_monitor.toggle,
                    "Screenshot": self.screenshot.take_screenshot,
                    "Backup Utility": self.backup.open,
                    "Email Client": self.email_client.open,
                    "Calendar": self.calendar.open,
                    "Notes": self.notes.open,
                    "Network Monitor": self.network_monitor.toggle,
                    "System Logs": self.log_viewer.open
                }
                if app_name in apps:
                    apps[app_name]()
            elif result.startswith("File: "):
                self.open_file(result[6:])
        except Exception as e:
            self.notifications.send("Search", f"Error: {str(e)}")

    def create_window(self, title, build_func, x=100, y=100, width=400, height=300):
        """Create a new window with snapping and animations."""
        try:
            window = tk.Toplevel(self.root)
            window.title(title)
            window.geometry(f"{width}x{height}+{x}+{y}")
            window.configure(bg="#333333")
            frame = tk.Frame(window, bg="#333333")
            frame.pack(fill=tk.BOTH, expand=True)
            build_func(frame)
            self.windows[window] = {"title": title, "x": x, "y": y, "width": width, 
                                   "height": height, "desktop": self.current_desktop}
            window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(window))
            window.bind("<Configure>", lambda e: self.snap_window(window, e))
            window.bind("<Map>", lambda e: self.animate_window(window, "map"))
            window.bind("<Unmap>", lambda e: self.animate_window(window, "unmap"))
            # Add to current virtual desktop
            self.virtual_desktops[self.current_desktop][window] = self.windows[window]
            self.update_desktop()
            return window
        except Exception as e:
            self.notifications.send("Window Manager", f"Error: {str(e)}")
            return None

    def snap_window(self, window, event):
        """Snap windows to screen edges."""
        try:
            if window not in self.windows:
                return
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight() - 30  # Account for taskbar
            x, y = window.winfo_x(), window.winfo_y()
            if x < 10:
                window.geometry(f"{screen_width//2}x{screen_height}+0+0")
            elif x > screen_width - window.winfo_width() - 10:
                window.geometry(f"{screen_width//2}x{screen_height}+{screen_width//2}+0")
            elif y < 10:
                window.geometry(f"{screen_width}x{screen_height//2}+0+0")
            self.windows[window]["x"] = window.winfo_x()
            self.windows[window]["y"] = window.winfo_y()
            self.windows[window]["width"] = window.winfo_width()
            self.windows[window]["height"] = window.winfo_height()
            self.virtual_desktops[self.current_desktop][window] = self.windows[window]
            self.save_session()
        except:
            pass

    def animate_window(self, window, action):
        """Animate window mapping/unmapping."""
        try:
            if action == "map":
                window.attributes('-alpha', 0)
                for i in range(0, 11):
                    window.attributes('-alpha', i / 10)
                    window.update()
                    time.sleep(0.02)
            elif action == "unmap":
                for i in range(10, -1, -1):
                    window.attributes('-alpha', i / 10)
                    window.update()
                    time.sleep(0.02)
        except:
            pass

    def add_desktop(self):
        """Add a new virtual desktop."""
        try:
            self.virtual_desktops.append({})
            self.switch_desktop(len(self.virtual_desktops) - 1)
        except:
            pass

    def prev_desktop(self):
        """Switch to previous virtual desktop."""
        try:
            if self.current_desktop > 0:
                self.switch_desktop(self.current_desktop - 1)
        except:
            pass

    def next_desktop(self):
        """Switch to next virtual desktop."""
        try:
            if self.current_desktop < len(self.virtual_desktops) - 1:
                self.switch_desktop(self.current_desktop + 1)
        except:
            pass

    def switch_desktop(self, desktop_idx):
        """Switch to a virtual desktop."""
        try:
            # Hide current desktop windows
            for window in self.virtual_desktops[self.current_desktop]:
                window.withdraw()
            self.current_desktop = desktop_idx
            # Show new desktop windows
            for window in self.virtual_desktops[self.current_desktop]:
                window.deiconify()
            self.wm.notifications.send("Desktop", f"Switched to Desktop {desktop_idx + 1}")
        except:
            pass

    def update_desktop(self):
        """Update the current desktop."""
        try:
            for desktop_idx, windows in enumerate(self.virtual_desktops):
                for window in windows:
                    if desktop_idx == self.current_desktop:
                        window.deiconify()
                    else:
                        window.withdraw()
        except:
            pass

    def start_session_timeout(self):
        """Start session timeout timer."""
        try:
            timeout = self.config.get("session_timeout", 1800)  # 30 minutes
            if timeout > 0:
                self.session_timeout = self.root.after(timeout * 1000, self.logout)
        except:
            pass

    def reset_session_timeout(self):
        """Reset session timeout on activity."""
        try:
            if self.session_timeout:
                self.root.after_cancel(self.session_timeout)
            self.start_session_timeout()
        except:
            pass

    # Override previous methods for enhanced functionality
    def setup_file_associations(self):
        """Load file associations from config."""
        try:
            assoc_file = os.path.expanduser("~/.berke0s/file_associations.json")
            if os.path.exists(assoc_file):
                with open(assoc_file, 'r') as f:
                    loaded = json.load(f)
                for ext, app_name in loaded.items():
                    apps = {
                        "TextEditor": self.text_editor,
                        "CodeEditor": self.code_editor,
                        "MediaPlayer": self.media_player,
                        "ImageViewer": self.image_viewer,
                        "NotesApp": self.notes
                    }
                    if app_name in apps:
                        self.file_associations[ext] = apps[app_name]
        except:
            pass

    def open_file(self, path):
        """Open a file based on its extension."""
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext in self.file_associations:
                app = self.file_associations[ext]
                if hasattr(app, "open_file"):
                    app.open_file(path)
                else:
                    app.open()
            elif ext in ['.c', '.cpp']:
                self.code_editor.open_file(path)
            elif ext in ['.avi']:
                self.media_player.play(path)
            elif ext in ['.zip', '.tar.gz']:
                self.file_manager.extract_file(path)
            else:
                self.text_editor.open_file(path)
            if path not in self.recent_files:
                self.recent_files.insert(0, path)
                self.recent_files = self.recent_files[:10]
                self.save_recent_files()
        except Exception as e:
            self.notifications.send("Window Manager", f"Error opening file: {str(e)}")

    def save_recent_files(self):
        """Save recent files."""
        try:
            recent_path = os.path.expanduser("~/.berke0s/recent_files.json")
            os.makedirs(os.path.dirname(recent_path), exist_ok=True)
            with open(recent_path, 'w') as f:
                json.dump(self.recent_files, f)
        except:
            pass

    def add_desktop_shortcut(self, path, x, y):
        """Add a shortcut to the desktop."""
        try:
            name = os.path.basename(path)
            shortcut_id = self.desktop.create_text(x, y, text=name, fill="white", 
                                                 font=("Arial", self.config.get("icon_size", 10)), 
                                                 anchor=tk.NW)
            self.shortcuts[shortcut_id] = {"path": path, "x": x, "y": y}
            self.desktop.tag_bind(shortcut_id, "<Button-1>", 
                                 lambda e: self.start_drag(shortcut_id))
            self.desktop.tag_bind(shortcut_id, "<Double-1>", 
                                 lambda e: self.open_shortcut(shortcut_id))
            self.desktop.tag_bind(shortcut_id, "<Button-3>", 
                                 lambda e: self.show_shortcut_menu(shortcut_id, e))
            self.save_shortcuts()
        except Exception as e:
            self.notifications.send("Desktop", f"Error: {str(e)}")

    def apply_theme(self, colors):
        """Apply theme with font and cursor support."""
        try:
            self.root.configure(bg=colors["bg"], cursor=self.config.get("cursor", ""))
            self.desktop.configure(bg=colors["bg"])
            self.taskbar.configure(bg=self.config.get("taskbar_color", colors["bg"]))
            font_size = self.config.get("font_size", 12)
            for window in self.windows:
                window.configure(bg=colors["bg"])
                for widget in window.winfo_children():
                    if isinstance(widget, (tk.Frame, tk.Label, tk.Button)):
                        widget.configure(bg=colors["bg"], fg=colors["fg"], 
                                        font=("Arial", font_size))
                    elif isinstance(widget, tk.Entry):
                        widget.configure(bg=colors["entry"], fg=colors["fg"], 
                                        font=("Arial", font_size))
                    elif isinstance(widget, tk.Text):
                        widget.configure(bg=colors["entry"], fg=colors["fg"], 
                                        font=("Monospace", font_size))
        except:
            pass

### --- ENHANCED FILE MANAGER ---
class FileManager:
    """Enhanced file manager with compression and properties."""
    def __init__(self, wm):
        self.wm = wm
        self.current_path = os.path.expanduser("~")
        self.shortcuts = {}
        self.recent_files = self.wm.recent_files

    def extract_file(self, path):
        """Extract compressed files."""
        try:
            if path.endswith('.zip'):
                subprocess.run(["unzip", path, "-d", os.path.splitext(path)[0]], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif path.endswith('.tar.gz'):
                subprocess.run(["tar", "-xzf", path, "-C", os.path.dirname(path)], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.update_file_list()
            self.wm.notifications.send("File Manager", f"Extracted {os.path.basename(path)}")
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def compress_file(self):
        """Compress selected files."""
        try:
            selected = self.file_list.get(self.file_list.curselection()[0]).replace("[DIR] ", "")
            path = os.path.join(self.current_path, selected)
            output = filedialog.asksaveasfilename(filetypes=[("Zip", "*.zip"), ("Tar", "*.tar.gz")])
            if output:
                if output.endswith('.zip'):
                    subprocess.run(["zip", "-r", output, selected], cwd=self.current_path, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif output.endswith('.tar.gz'):
                    subprocess.run(["tar", "-czf", output, selected], cwd=self.current_path, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.update_file_list()
                self.wm.notifications.send("File Manager", f"Compressed to {os.path.basename(output)}")
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def show_properties(self):
        """Show file properties."""
        try:
            selected = self.file_list.get(self.file_list.curselection()[0]).replace("[DIR] ", "")
            path = os.path.join(self.current_path, selected)
            stat = os.stat(path)
            info = (
                f"Name: {selected}\n"
                f"Path: {path}\n"
                f"Size: {stat.st_size // 1024} KB\n"
                f"Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}\n"
                f"Permissions: {oct(stat.st_mode & 0o777)[2:]}"
            )
            self.wm.create_window(f"Properties: {selected}", 
                                lambda f: tk.Label(f, text=info, fg="white", bg="#333333", 
                                                  justify=tk.LEFT).pack(padx=10, pady=10), 
                                width=300, height=200)
        except Exception as e:
            self.wm.notifications.send("File Manager", f"Error: {str(e)}")

    def build_ui(self, frame):
        """Build the file manager UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(frame, bg="#333333")
            toolbar.pack(fill=tk.X)
            tk.Button(toolbar, text="Up", command=self.go_up, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="New Folder", command=self.create_folder, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Delete", command=self.delete_item, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Create Shortcut", command=self.create_shortcut, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Compress", command=self.compress_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Properties", command=self.show_properties, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            path_var = tk.StringVar(value=self.current_path)
            tk.Entry(toolbar, textvariable=path_var, bg="#555555").pack(
                side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Button(toolbar, text="Go", command=lambda: self.change_path(path_var.get()), 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            search_var = tk.StringVar()
            tk.Entry(toolbar, textvariable=search_var, width=15, bg="#555555").pack(
                side=tk.RIGHT, padx=2)
            tk.Button(toolbar, text="Search", command=lambda: self.search_files(search_var.get()), 
                     bg="#555555", fg="white").pack(side=tk.RIGHT, padx=2)

            # Main content
            main_frame = tk.Frame(frame, bg="#333333")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Directory tree
            tree_frame = tk.Frame(main_frame, bg="#333333")
            tree_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            tk.Label(tree_frame, text="Folders", fg="white", bg="#333333").pack()
            self.tree = ttk.Treeview(tree_frame, show="tree")
            self.tree.pack(fill=tk.Y, expand=True)
            self.tree.bind('<<TreeviewOpen>>', self.update_tree)
            self.tree.bind('<Double-1>', self.tree_select)
            self.populate_tree()

            # File list
            list_frame = tk.Frame(main_frame, bg="#333333")
            list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            tk.Label(list_frame, text="Files", fg="white", bg="#333333").pack()
            self.file_list = tk.Listbox(list_frame, bg="#555555", fg="white")
            self.file_list.pack(fill=tk.BOTH, expand=True)
            self.file_list.bind('<Double-1>', self.open_item)
            self.file_list.bind('<Button-3>', self.show_context_menu)
            self.update_file_list()

            # Context menu
            self.context_menu = tk.Menu(frame, tearoff=0, bg="#333333", fg="white")
            self.context_menu.add_command(label="Open", command=self.open_item)
            self.context_menu.add_command(label="Delete", command=self.delete_item)
            self.context_menu.add_command(label="Rename", command=self.rename_item)
            self.context_menu.add_command(label="Create Shortcut", command=self.create_shortcut)
            self.context_menu.add_command(label="Compress", command=self.compress_file)
            self.context_menu.add_command(label="Properties", command=self.show_properties)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

### --- ACCESSIBILITY MANAGER ---
class AccessibilityManager:
    """Manage accessibility features like screen reader."""
    def __init__(self, wm):
        self.wm = wm
        self.screen_reader_active = False

    def toggle_screen_reader(self):
        """Toggle screen reader."""
        try:
            self.screen_reader_active = not self.screen_reader_active
            if self.screen_reader_active:
                self.wm.notifications.send("Accessibility", "Screen reader enabled")
                self.wm.root.bind("<FocusIn>", self.read_widget)
            else:
                self.wm.notifications.send("Accessibility", "Screen reader disabled")
                self.wm.root.unbind("<FocusIn>")
        except Exception as e:
            self.wm.notifications.send("Accessibility", f"Error: {str(e)}")

    def read_widget(self, event):
        """Read focused widget's text."""
        try:
            widget = event.widget
            text = ""
            if isinstance(widget, tk.Label):
                text = widget.cget("text")
            elif isinstance(widget, tk.Button):
                text = widget.cget("text")
            elif isinstance(widget, tk.Entry):
                text = widget.get()
            elif isinstance(widget, tk.Text):
                text = widget.get(1.0, tk.END).strip()[:100]  # Limit to 100 chars
            if text:
                subprocess.run(["espeak", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

    def toggle_high_contrast(self):
        """Toggle high-contrast mode."""
        try:
            theme = self.wm.config.get("theme", "dark")
            if theme == "high_contrast":
                self.wm.config["theme"] = "dark"
                colors = {"bg": "#333333", "fg": "white", "entry": "#555555"}
            else:
                self.wm.config["theme"] = "high_contrast"
                colors = {"bg": "black", "fg": "yellow", "entry": "black"}
            self.wm.apply_theme(colors)
            self.wm.save_config()
            self.wm.notifications.send("Accessibility", f"High contrast {'enabled' if theme != 'high_contrast' else 'disabled'}")
        except Exception as e:
            self.wm.notifications.send("Accessibility", f"Error: {str(e)}")

### --- CLIPBOARD MANAGER ---
class ClipboardManager:
    """Manage clipboard history."""
    def __init__(self, wm):
        self.wm = wm
        self.history = []
        self.max_history = 10

    def open(self):
        self.wm.create_window("Clipboard Manager", self.build_ui, width=400, height=300)

    def build_ui(self, frame):
        """Build the clipboard manager UI."""
        try:
            self.clip_list = tk.Listbox(frame, bg="#555555", fg="white")
            self.clip_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(frame, text="Paste", command=self.paste_clip, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Clear", command=self.clear_history, 
                     bg="#555555", fg="white").pack(pady=5)
            self.wm.root.bind("<Control-c>", self.copy_event)
            self.wm.root.bind("<Control-x>", self.copy_event)
            self.update_clipboard()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def copy_event(self, event):
        """Handle copy/cut events."""
        try:
            clip = self.wm.root.clipboard_get()
            if clip and clip not in self.history:
                self.history.insert(0, clip)
                self.history = self.history[:self.max_history]
                self.update_clipboard()
        except:
            pass

    def update_clipboard(self):
        """Update clipboard history display."""
        try:
            self.clip_list.delete(0, tk.END)
            for clip in self.history:
                self.clip_list.insert(tk.END, clip[:50])  # Limit display length
        except:
            pass

    def paste_clip(self):
        """Paste selected clipboard item."""
        try:
            selected = self.clip_list.get(self.clip_list.curselection()[0])
            self.wm.root.clipboard_clear()
            self.wm.root.clipboard_append(selected)
            self.wm.notifications.send("Clipboard", "Item pasted")
        except Exception as e:
            self.wm.notifications.send("Clipboard", f"Error: {str(e)}")

    def clear_history(self):
        """Clear clipboard history."""
        try:
            self.history = []
            self.update_clipboard()
            self.wm.notifications.send("Clipboard", "History cleared")
        except:
            pass

### --- SYSTEM DIAGNOSTICS ---
class SystemDiagnostics:
    """Perform system health checks."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("System Diagnostics", self.build_ui, width=600, height=400)

    def build_ui(self, frame):
        """Build the diagnostics UI."""
        try:
            tk.Label(frame, text="System Diagnostics", fg="white", bg="#333333").pack(pady=5)
            self.diag_text = tk.Text(frame, bg="#555555", fg="white", font=("Monospace", 10))
            self.diag_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(frame, text="Run Diagnostics", command=self.run_diagnostics, 
                     bg="#555555", fg="white").pack(pady=5)
            self.run_diagnostics()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def run_diagnostics(self):
        """Run system diagnostics."""
        try:
            self.diag_text.delete(1.0, tk.END)
            diagnostics = []
            # CPU
            diagnostics.append(f"CPU Usage: {psutil.cpu_percent()}%")
            # Memory
            mem = psutil.virtual_memory()
            diagnostics.append(f"Memory: {mem.used // 1024**2} MB / {mem.total // 1024**2} MB")
            # Disk
            disk = psutil.disk_usage('/')
            diagnostics.append(f"Disk: {disk.used // 1024**3} GB / {disk.total // 1024**3} GB")
            # Network
            net = psutil.net_io_counters()
            diagnostics.append(f"Network Sent: {net.bytes_sent // 1024**2} MB")
            diagnostics.append(f"Network Received: {net.bytes_recv // 1024**2} MB")
            # Battery
            if os.path.exists("/sys/class/power_supply/BAT0/capacity"):
                with open("/sys/class/power_supply/BAT0/capacity", 'r') as f:
                    diagnostics.append(f"Battery: {f.read().strip()}%")
            else:
                diagnostics.append("Battery: Not detected")
            # System uptime
            uptime = subprocess.check_output(["uptime", "-p"], text=True).strip()
            diagnostics.append(f"Uptime: {uptime}")
            self.diag_text.insert(tk.END, "\n".join(diagnostics))
        except Exception as e:
            self.wm.notifications.send("Diagnostics", f"Error: {str(e)}")

### --- POWER MANAGER ---
class PowerManager:
    """Manage power settings like sleep/suspend."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Power Manager", self.build_ui, width=400, height=200)

    def build_ui(self, frame):
        """Build the power manager UI."""
        try:
            tk.Label(frame, text="Power Management", fg="white", bg="#333333").pack(pady=5)
            tk.Button(frame, text="Sleep", command=self.sleep_system, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Suspend", command=self.suspend_system, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Label(frame, text="Auto-sleep (minutes):", fg="white", bg="#333333").pack()
            sleep_var = tk.IntVar(value=self.wm.config.get("auto_sleep", 0))
            tk.Entry(frame, textvariable=sleep_var, bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Set Auto-sleep", 
                     command=lambda: self.set_auto_sleep(sleep_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", bg="#333333").pack(padx=10, pady=10)

    def sleep_system(self):
        """Put system to sleep."""
        try:
            subprocess.run(["sudo", "pm-sleep"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.wm.notifications.send("Power", "System entering sleep mode")
        except Exception as e:
            self.wm.notifications.send("Power", f"Error: {str(e)}")

    def suspend_system(self):
        """Suspend system."""
        try:
            subprocess.run(["sudo", "pm-suspend"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.wm.notifications.send("Power", "System suspended")
        except Exception as e:
            self.wm.notifications.send("Power", f"Error: {str(e)}")

    def set_auto_sleep(self, minutes):
        """Set auto-sleep timer."""
        try:
            self.wm.config["auto_sleep"] = minutes
            self.wm.save_config()
            if hasattr(self, "auto_sleep_timer"):
                self.wm.root.after_cancel(self.auto_sleep_timer)
            if minutes > 0:
                self.auto_sleep_timer = self.wm.root.after(minutes * 60 * 1000, self.sleep_system)
            self.wm.notifications.send("Power", f"Auto-sleep set to {minutes} minutes")
        except Exception as e:
            self.wm.notifications.send("Power", f"Error: {str(e)}")

### --- ENHANCED CONTROL CENTER ---
class ControlCenter:
    """Enhanced system settings with advanced customization."""
    def build_ui(self, frame):
        """Build the control center UI."""
        try:
            notebook = ttk.Notebook(frame)
            notebook.pack(fill=tk.BOTH, expand=True)

            # Existing tabs (Network, Display, Audio, Users)
            network = ttk.Frame(notebook)
            notebook.add(network, text="Network")
            tk.Label(network, text="Wi-Fi SSID", fg="white", bg="#333333").pack(pady=5)
            ssid_var = tk.StringVar()
            self.ssid_menu = ttk.Combobox(network, textvariable=ssid_var, state="readonly")
            self.ssid_menu.pack(pady=5)
            tk.Label(network, text="Password", fg="white", bg="#333333").pack(pady=5)
            passwd_var = tk.StringVar()
            tk.Entry(network, textvariable=passwd_var, show="*", bg="#555555").pack(pady=5)
            tk.Button(network, text="Connect", 
                     command=lambda: self.connect_wifi(ssid_var.get(), passwd_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(network, text="Refresh", command=self.refresh_wifi, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(network, text="Connect Wired", command=self.connect_wired, 
                     bg="#555555", fg="white").pack(pady=5)

            display = ttk.Frame(notebook)
            notebook.add(display, text="Display")
            tk.Label(display, text="Brightness", fg="white", bg="#333333").pack(pady=5)
            bright_var = tk.IntVar(value=50)
            tk.Scale(display, from_=0, to=100, orient=tk.HORIZONTAL, variable=bright_var, 
                    bg="#555555").pack(pady=5)
            tk.Button(display, text="Apply", 
                     command=lambda: self.set_brightness(bright_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)

            audio = ttk.Frame(notebook)
            notebook.add(audio, text="Audio")
            tk.Label(audio, text="Volume", fg="white", bg="#333333").pack(pady=5)
            volume_var = tk.IntVar(value=50)
            tk.Scale(audio, from_=0, to=100, orient=tk.HORIZONTAL, variable=volume_var, 
                    bg="#555555").pack(pady=5)
            tk.Button(audio, text="Apply", 
                     command=lambda: self.set_volume(volume_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)

            users = ttk.Frame(notebook)
            notebook.add(users, text="Users")
            tk.Label(users, text="User Management", fg="white", bg="#333333").pack(pady=5)
            self.user_list = tk.Listbox(users, bg="#555555", fg="white")
            self.user_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(users, text="Add User", command=self.add_user, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(users, text="Delete User", command=self.delete_user, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(users, text="Change Password", command=self.change_password, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            self.refresh_users()

            # Customization tab
            customize = ttk.Frame(notebook)
            notebook.add(customize, text="Customization")
            tk.Label(customize, text="Desktop Background", fg="white", bg="#333333").pack(pady=5)
            tk.Button(customize, text="Set Image", command=self.set_background_image, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(customize, text="Set Video", command=self.set_background_video, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(customize, text="Set Slideshow", command=self.set_slideshow, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Label(customize, text="Taskbar Color", fg="white", bg="#333333").pack(pady=5)
            color_var = tk.StringVar(value=self.wm.config.get("taskbar_color", "#333333"))
            tk.Entry(customize, textvariable=color_var, bg="#555555").pack(pady=5)
            tk.Button(customize, text="Apply Color", 
                     command=lambda: self.set_taskbar_color(color_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Label(customize, text="Theme", fg="white", bg="#333333").pack(pady=5)
            theme_var = tk.StringVar(value=self.wm.config.get("theme", "dark"))
            tk.OptionMenu(customize, theme_var, "Dark", "Light", "High Contrast", 
                         command=self.set_theme).pack(pady=5)
            tk.Label(customize, text="Icon Size", fg="white", bg="#333333").pack(pady=5)
            icon_size_var = tk.IntVar(value=self.wm.config.get("icon_size", 10))
            tk.OptionMenu(customize, icon_size_var, 8, 10, 12, 14, 
                         command=self.set_icon_size).pack(pady=5)
            tk.Label(customize, text="Font Size", fg="white", bg="#333333").pack(pady=5)
            font_size_var = tk.IntVar(value=self.wm.config.get("font_size", 12))
            tk.OptionMenu(customize, font_size_var, 10, 12, 14, 16, 
                         command=self.set_font_size).pack(pady=5)
            tk.Label(customize, text="Cursor Theme", fg="white", bg="#333333").pack(pady=5)
            cursor_var = tk.StringVar(value=self.wm.config.get("cursor", "arrow"))
            tk.OptionMenu(customize, cursor_var, "arrow", "hand2", "crosshair", 
                         command=self.set_cursor).pack(pady=5)
            tk.Label(customize, text="Session Timeout (minutes)", fg="white", bg="#333333").pack(pady=5)
            timeout_var = tk.IntVar(value=self.wm.config.get("session_timeout", 1800) // 60)
            tk.Entry(customize, textvariable=timeout_var, bg="#555555", fg="white").pack(pady=5)
            tk.Button(customize, text="Set Timeout", 
                     command=lambda: self.set_session_timeout(timeout_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)

            # Accessibility tab
            accessibility = ttk.Frame(notebook)
            notebook.add(accessibility, text="Accessibility")
            tk.Button(accessibility, text="Toggle Screen Reader", 
                     command=self.wm.accessibility.toggle_screen_reader, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(accessibility, text="Toggle High Contrast", 
                     command=self.wm.accessibility.toggle_high_contrast, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(accessibility, text="Open Magnifier", 
                     command=self.wm.magnifier.open, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(accessibility, text="Open Virtual Keyboard", 
                     command=self.wm.virtual_keyboard.open, 
                     bg="#555555", fg="white").pack(pady=5)

            # Security tab
            security = ttk.Frame(notebook)
            notebook.add(security, text="Security")
            tk.Button(security, text="Configure Firewall", 
                     command=self.configure_firewall, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(security, text="View Audit Log", 
                     command=self.view_audit_log, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(security, text="Open File Encryption", 
                     command=self.wm.file_encryption.open, 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def set_icon_size(self, size):
        """Set desktop icon size."""
        try:
            self.wm.config["icon_size"] = size
            self.wm.save_config()
            self.wm.load_shortcuts()  # Refresh shortcuts
            self.wm.notifications.send("Control Center", f"Icon size set to {size}")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_font_size(self, size):
        """Set UI font size."""
        try:
            self.wm.config["font_size"] = size
            self.wm.apply_theme(self.wm.config.get("theme", {"bg": "#333333", "fg": "white", 
                                                            "entry": "#555555"}))
            self.wm.save_config()
            self.wm.notifications.send("Control Center", f"Font size set to {size}")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_cursor(self, cursor):
        """Set cursor theme."""
        try:
            self.wm.config["cursor"] = cursor
            self.wm.apply_theme(self.wm.config.get("theme", {"bg": "#333333", "fg": "white", 
                                                            "entry": "#555555"}))
            self.wm.save_config()
            self.wm.notifications.send("Control Center", f"Cursor set to {cursor}")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def set_session_timeout(self, minutes):
        """Set session timeout."""
        try:
            self.wm.config["session_timeout"] = minutes * 60
            self.wm.reset_session_timeout()
            self.wm.save_config()
            self.wm.notifications.send("Control Center", f"Session timeout set to {minutes} minutes")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def configure_firewall(self):
        """Configure firewall settings."""
        try:
            window = self.wm.create_window("Firewall Settings", self.build_firewall_ui, 
                                         width=400, height=300)
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def build_firewall_ui(self, frame):
        """Build firewall configuration UI."""
        try:
            tk.Label(frame, text="Firewall Rules", fg="white", bg="#333333").pack(pady=5)
            rule_var = tk.StringVar()
            tk.Entry(frame, textvariable=rule_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            tk.Button(frame, text="Add Rule", 
                     command=lambda: self.add_firewall_rule(rule_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="View Rules", command=self.view_firewall_rules, 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def add_firewall_rule(self, rule):
        """Add a firewall rule using iptables."""
        try:
            subprocess.run(["sudo", "iptables", "-A", "INPUT"] + rule.split(), 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.wm.notifications.send("Control Center", "Firewall rule added")
            self.wm.audit_log(f"Added firewall rule: {rule}")
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def view_firewall_rules(self):
        """View current firewall rules."""
        try:
            output = subprocess.check_output(["sudo", "iptables", "-L"], text=True)
            self.wm.create_window("Firewall Rules", 
                                lambda f: tk.Text(f, bg="#555555", fg="white", 
                                                 font=("Monospace", 10)).insert(tk.END, output))
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

    def view_audit_log(self):
        """View audit log."""
        try:
            log_path = os.path.expanduser("~/.berke0s/audit.log")
            content = "No audit log found"
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    content = f.read()
            self.wm.create_window("Audit Log", 
                                lambda f: tk.Text(f, bg="#555555", fg="white", 
                                                 font=("Monospace", 10)).insert(tk.END, content))
        except Exception as e:
            self.wm.notifications.send("Control Center", f"Error: {str(e)}")

### --- WEATHER APP ---
class WeatherApp:
    """Display weather information using OpenWeatherMap API."""
    def __init__(self, wm):
        self.wm = wm
        self.api_key = self.wm.config.get("weather_api_key", "")
        self.city = self.wm.config.get("weather_city", "Istanbul")

    def open(self):
        self.wm.create_window("Weather", self.build_ui, width=400, height=300)

    def build_ui(self, frame):
        """Build the weather app UI."""
        try:
            tk.Label(frame, text="Weather", fg="white", bg="#333333").pack(pady=5)
            tk.Label(frame, text="City:", fg="white", bg="#333333").pack()
            city_var = tk.StringVar(value=self.city)
            tk.Entry(frame, textvariable=city_var, bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Update", 
                     command=lambda: self.update_weather(city_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Label(frame, text="API Key:", fg="white", bg="#333333").pack()
            api_var = tk.StringVar(value=self.api_key)
            tk.Entry(frame, textvariable=api_var, bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Set API Key", 
                     command=lambda: self.set_api_key(api_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
            self.weather_label = tk.Label(frame, text="Fetching weather...", 
                                        fg="white", bg="#333333")
            self.weather_label.pack(pady=5)
            self.update_weather(self.city)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def set_api_key(self, key):
        """Set OpenWeatherMap API key."""
        try:
            self.api_key = key
            self.wm.config["weather_api_key"] = key
            self.wm.save_config()
            self.wm.notifications.send("Weather", "API key updated")
        except Exception as e:
            self.wm.notifications.send("Weather", f"Error: {str(e)}")

    def update_weather(self, city):
        """Fetch and display weather data."""
        try:
            if not self.api_key:
                self.weather_label.config(text="Please set API key")
                return
            self.city = city
            self.wm.config["weather_city"] = city
            self.wm.save_config()
            response = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
            )
            data = response.json()
            if data["cod"] == 200:
                weather = (
                    f"City: {data['name']}\n"
                    f"Temperature: {data['main']['temp']}°C\n"
                    f"Condition: {data['weather'][0]['description'].title()}\n"
                    f"Humidity: {data['main']['humidity']}%\n"
                    f"Wind: {data['wind']['speed']} m/s"
                )
                self.weather_label.config(text=weather)
            else:
                self.weather_label.config(text=f"Error: {data['message']}")
        except Exception as e:
            self.weather_label.config(text=f"Error: {str(e)}")

### --- TASK SCHEDULER ---
class TaskScheduler:
    """Schedule system tasks using cron."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Task Scheduler", self.build_ui, width=600, height=400)

    def build_ui(self, frame):
        """Build the task scheduler UI."""
        try:
            tk.Label(frame, text="Scheduled Tasks", fg="white", bg="#333333").pack(pady=5)
            self.task_list = tk.Listbox(frame, bg="#555555", fg="white")
            self.task_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Button(frame, text="Add Task", command=self.add_task, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Remove Task", command=self.remove_task, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            self.refresh_tasks()
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def refresh_tasks(self):
        """Refresh task list."""
        try:
            self.task_list.delete(0, tk.END)
            crontab = subprocess.check_output(["crontab", "-l"], text=True, 
                                             stderr=subprocess.DEVNULL)
            for line in crontab.splitlines():
                if line.strip() and not line.startswith("#"):
                    self.task_list.insert(tk.END, line)
        except:
            self.task_list.insert(tk.END, "No tasks found")

    def add_task(self):
        """Add a new scheduled task."""
        try:
            window = self.wm.create_window("Add Task", self.build_task_ui, 
                                         width=400, height=300)
        except Exception as e:
            self.wm.notifications.send("Task Scheduler", f"Error: {str(e)}")

    def build_task_ui(self, frame):
        """Build the task creation UI."""
        try:
            tk.Label(frame, text="Schedule (cron format):", fg="white", bg="#333333").pack()
            schedule_var = tk.StringVar(value="0 0 * * *")  # Daily at midnight
            tk.Entry(frame, textvariable=schedule_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            tk.Label(frame, text="Command:", fg="white", bg="#333333").pack()
            command_var = tk.StringVar()
            tk.Entry(frame, textvariable=command_var, bg="#555555", fg="white").pack(fill=tk.X, padx=5)
            tk.Button(frame, text="Add", 
                     command=lambda: self.save_task(schedule_var.get(), command_var.get()), 
                     bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def save_task(self, schedule, command):
        """Save a new cron task."""
        try:
            crontab = subprocess.check_output(["crontab", "-l"], text=True, 
                                             stderr=subprocess.DEVNULL)
            with open("/tmp/crontab", "w") as f:
                f.write(crontab + f"{schedule} {command}\n")
            subprocess.run(["crontab", "/tmp/crontab"], stdout=subprocess.DEVNULL)
            self.refresh_tasks()
            self.wm.notifications.send("Task Scheduler", "Task added")
            self.wm.audit_log(f"Added cron task: {schedule} {command}")
        except Exception as e:
            self.wm.notifications.send("Task Scheduler", f"Error: {str(e)}")

    def remove_task(self):
        """Remove a scheduled task."""
        try:
            selected = self.task_list.get(self.task_list.curselection()[0])
            crontab = subprocess.check_output(["crontab", "-l"], text=True, 
                                             stderr=subprocess.DEVNULL)
            with open("/tmp/crontab", "w") as f:
                for line in crontab.splitlines():
                    if line.strip() != selected.strip():
                        f.write(line + "\n")
            subprocess.run(["crontab", "/tmp/crontab"], stdout=subprocess.DEVNULL)
            self.refresh_tasks()
            self.wm.notifications.send("Task Scheduler", "Task removed")
            self.wm.audit_log(f"Removed cron task: {selected}")
        except Exception as e:
            self.wm.notifications.send("Task Scheduler", f"Error: {str(e)}")

### --- FILE ENCRYPTION TOOL ---
class FileEncryptionTool:
    """Encrypt and decrypt files."""
    def __init__(self, wm):
        self.wm = wm
        self.key = None

    def open(self):
        self.wm.create_window("File Encryption", self.build_ui, width=400, height=300)

    def build_ui(self, frame):
        """Build the file encryption UI."""
        try:
            tk.Label(frame, text="File Encryption", fg="white", bg="#333333").pack(pady=5)
            tk.Button(frame, text="Encrypt File", command=self.encrypt_file, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Decrypt File", command=self.decrypt_file, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Label(frame, text="Password:", fg="white", bg="#333333").pack()
            self.password_var = tk.StringVar()
            tk.Entry(frame, textvariable=self.password_var, show="*", 
                    bg="#555555", fg="white").pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def generate_key(self, password):
        """Generate encryption key from password."""
        try:
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            salt = b"berke0s_salt"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            self.key = kdf.derive(password.encode())
        except Exception as e:
            self.wm.notifications.send("File Encryption", f"Error: {str(e)}")

    def encrypt_file(self):
        """Encrypt a file."""
        try:
            from cryptography.fernet import Fernet
            filename = filedialog.askopenfilename()
            if not filename or not self.password_var.get():
                return
            self.generate_key(self.password_var.get())
            fernet = Fernet(base64.urlsafe_b64encode(self.key))
            with open(filename, 'rb') as f:
                data = f.read()
            encrypted = fernet.encrypt(data)
            with open(filename + ".enc", 'wb') as f:
                f.write(encrypted)
            self.wm.notifications.send("File Encryption", f"Encrypted {filename}")
            self.wm.audit_log(f"Encrypted file: {filename}")
        except Exception as e:
            self.wm.notifications.send("File Encryption", f"Error: {str(e)}")

    def decrypt_file(self):
        """Decrypt a file."""
        try:
            from cryptography.fernet import Fernet
            filename = filedialog.askopenfilename(filetypes=[("Encrypted", "*.enc")])
            if not filename or not self.password_var.get():
                return
            self.generate_key(self.password_var.get())
            fernet = Fernet(base64.urlsafe_b64encode(self.key))
            with open(filename, 'rb') as f:
                encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            with open(filename[:-4], 'wb') as f:
                f.write(decrypted)
            self.wm.notifications.send("File Encryption", f"Decrypted {filename}")
            self.wm.audit_log(f"Decrypted file: {filename}")
        except Exception as e:
            self.wm.notifications.send("File Encryption", f"Error: {str(e)}")

### --- VIRTUAL KEYBOARD ---
class VirtualKeyboard:
    """On-screen keyboard for accessibility."""
    def __init__(self, wm):
        self.wm = wm
        self.window = None
        self.visible = False

    def open(self):
        if not self.visible:
            self.window = self.wm.create_window("Virtual Keyboard", self.build_ui, 
                                              width=600, height=200, y=self.wm.root.winfo_screenheight()-230)
            self.visible = True
        else:
            self.wm.close_window(self.window)
            self.visible = False
            self.window = None

    def build_ui(self, frame):
        """Build the virtual keyboard UI."""
        try:
            rows = [
                "` 1 2 3 4 5 6 7 8 9 0 - = Backspace".split(),
                "Tab q w e r t y u i o p [ ] \\".split(),
                "Caps a s d f g h j k l ; ' Enter".split(),
                "Shift z x c v b n m , . / Shift".split(),
                "Ctrl Alt Space Alt Ctrl".split()
            ]
            for row in rows:
                row_frame = tk.Frame(frame, bg="#333333")
                row_frame.pack(fill=tk.X)
                for key in row:
                    tk.Button(row_frame, text=key, 
                             command=lambda k=key: self.type_key(k), 
                             bg="#555555", fg="white", width=4).pack(side=tk.LEFT, padx=1)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def type_key(self, key):
        """Simulate key press."""
        try:
            if key == "Backspace":
                self.wm.root.event_generate("<BackSpace>")
            elif key == "Enter":
                self.wm.root.event_generate("<Return>")
            elif key == "Tab":
                self.wm.root.event_generate("<Tab>")
            elif key == "Space":
                self.wm.root.event_generate("<space>")
            elif key == "Shift":
                pass  # Toggle shift state if needed
            elif key == "Ctrl":
                pass
            elif key == "Alt":
                pass
            elif key == "Caps":
                pass
            else:
                self.wm.root.event_generate(f"<Key-{key}>")
            self.wm.accessibility.read_widget(tk.Event())  # Trigger screen reader
        except Exception as e:
            self.wm.notifications.send("Virtual Keyboard", f"Error: {str(e)}")

### --- MAGNIFIER TOOL ---
class MagnifierTool:
    """Screen magnifier for accessibility."""
    def __init__(self, wm):
        self.wm = wm
        self.visible = False
        self.window = None
        self.zoom = 2

    def open(self):
        if not self.visible:
            self.window = self.wm.create_window("Magnifier", self.build_ui, 
                                              width=200, height=200)
            self.visible = True
            self.update_magnifier()
        else:
            self.wm.close_window(self.window)
            self.visible = False
            self.window = None

    def build_ui(self, frame):
        """Build the magnifier UI."""
        try:
            self.canvas = tk.Canvas(frame, bg="black", width=200, height=200)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            tk.Button(frame, text="Zoom In", command=self.zoom_in, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Zoom Out", command=self.zoom_out, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def zoom_in(self):
        """Increase zoom level."""
        try:
            self.zoom = min(self.zoom + 0.5, 5)
            self.update_magnifier()
        except:
            pass

    def zoom_out(self):
        """Decrease zoom level."""
        try:
            self.zoom = max(self.zoom - 0.5, 1)
            self.update_magnifier()
        except:
            pass

    def update_magnifier(self):
        """Update magnifier display."""
        try:
            if not self.visible:
                return
            x, y = self.wm.root.winfo_pointerxy()
            screenshot = ImageGrab.grab(bbox=(x-50, y-50, x+50, y+50))
            zoomed = screenshot.resize((int(100 * self.zoom), int(100 * self.zoom)), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(zoomed)
            self.canvas.delete("all")
            self.canvas.create_image(100, 100, image=self.photo)
            self.wm.root.after(50, self.update_magnifier)
        except:
            pass

### --- PERFORMANCE OPTIMIZER ---
class PerformanceOptimizer:
    """Optimize system performance."""
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Performance Optimizer", self.build_ui, width=400, height=300)

    def build_ui(self, frame):
        """Build the optimizer UI."""
        try:
            tk.Label(frame, text="Performance Optimizer", fg="white", bg="#333333").pack(pady=5)
            tk.Button(frame, text="Clear Cache", command=self.clear_cache, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Kill Unused Processes", command=self.kill_unused, 
                     bg="#555555", fg="white").pack(pady=5)
            tk.Button(frame, text="Optimize Memory", command=self.optimize_memory, 
                     bg="#555555", fg="white").pack(pady=5)
            self.status_label = tk.Label(frame, text="Ready", fg="white", bg="#333333")
            self.status_label.pack(pady=5)
        except Exception as e:
            tk.Label(frame, text=f"Error: {str(e)}", fg="white", 
                     bg="#333333").pack(padx=10, pady=10)

    def clear_cache(self):
        """Clear system cache."""
        try:
            subprocess.run(["sudo", "sync"], stdout=subprocess.DEVNULL)
            subprocess.run(["sudo", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"], 
                          stdout=subprocess.DEVNULL)
            self.status_label.config(text="Cache cleared")
            self.wm.notifications.send("Optimizer", "System cache cleared")
            self.wm.audit_log("Cleared system cache")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")

    def kill_unused(self):
        """Kill unused processes."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.name() in ['idle', 'bash']:  # Safe list
                    continue
                if proc.cpu_percent(interval=0.1) < 1:
                    subprocess.run(["sudo", "kill", str(proc.pid)], stdout=subprocess.DEVNULL)
            self.status_label.config(text="Unused processes terminated")
            self.wm.notifications.send("Optimizer", "Unused processes terminated")
            self.wm.audit_log("Terminated unused processes")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")

    def optimize_memory(self):
        """Optimize memory usage."""
        try:
            self.clear_cache()
            self.kill_unused()
            self.status_label.config(text="Memory optimized")
            self.wm.notifications.send("Optimizer", "Memory optimized")
            self.wm.audit_log("Optimized system memory")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")

### --- ENHANCED WINDOW MANAGER ---
class WindowManager:
    """Enhanced window manager with transparency and navigation."""
    def __init__(self):
        """Initialize the window manager."""
        self.root = tk.Tk()
        self.root.title("Berke0S")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#333333")
        self.windows = {}
        self.notifications = NotificationSystem(self)
        self.session_manager = SessionManager(self)
        self.config = load_config()
        self.taskbar = None
        self.start_btn = None
        self.desktop = None
        self.background_video = None
        self.shortcuts = {}
        self.pinned_apps = self.config.get("pinned_apps", ["File Manager", "Code Editor", "Notes"])
        self.virtual_desktops = [{}]
        self.current_desktop = 0
        self.file_associations = {
            '.txt': self.text_editor,
            '.py': self.code_editor,
            '.sh': self.code_editor,
            '.c': self.code_editor,
            '.png': self.image_viewer,
            '.jpg': self.image_viewer,
            '.mp3': self.media_player,
            '.mp4': self.media_player,
            '.note': self.notes
        }
        self.recent_files = []
        self.current_user = None
        self.accessibility = AccessibilityManager(self)
        self.clipboard = ClipboardManager(self)
        self.magnifier = MagnifierTool(self)
        self.virtual_keyboard = VirtualKeyboard(self)
        self.file_encryption = FileEncryptionTool(self)
        self.setup_ui()
        self.setup_file_associations()
        self.start_session_timeout()
        self.root.bind("<Alt-Tab>", self.switch_window)

    def switch_window(self, event):
        """Switch between open windows with Alt+Tab."""
        try:
            window_list = list(self.virtual_desktops[self.current_desktop].keys())
            if not window_list:
                return
            current = self.root.focus_get()
            idx = window_list.index(current) if current in window_list else -1
            next_window = window_list[(idx + 1) % len(window_list)]
            next_window.lift()
            next_window.focus_set()
            self.wm.notifications.send("Window Manager", f"Switched to {self.windows[next_window]['title']}")
        except:
            pass

    def create_window(self, title, build_func, x=100, y=100, width=400, height=300):
        """Create a new window with transparency."""
        try:
            window = tk.Toplevel(self.root)
            window.title(title)
            window.geometry(f"{width}x{height}+{x}+{y}")
            window.configure(bg="#333333")
            window.attributes('-alpha', self.config.get("window_transparency", 0.95))
            frame = tk.Frame(window, bg="#333333")
            frame.pack(fill=tk.BOTH, expand=True)
            build_func(frame)
            self.windows[window] = {"title": title, "x": x, "y": y, "width": width, 
                                   "height": height, "desktop": self.current_desktop}
            self.virtual_desktops[self.current_desktop][window] = self.windows[window]
            window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(window))
            window.bind("<Configure>", lambda e: self.snap_window(window, e))
            window.bind("<Map>", lambda e: self.animate_window(window, "map"))
            window.bind("<Unmap>", lambda e: self.animate_window(window, "unmap"))
            self.update_taskbar()
            self.reset_session_timeout()
            return window
        except Exception as e:
            self.notifications.send("Window Manager", f"Error: {str(e)}")
            return None

    def update_taskbar(self):
        """Update taskbar with window previews."""
        try:
            for widget in self.taskbar_frame.winfo_children():
                if widget != self.start_btn and widget != self.pinned_frame:
                    widget.destroy()
            for window in self.virtual_desktops[self.current_desktop]:
                title = self.windows[window]["title"][:10]
                tk.Button(self.taskbar_frame, text=title, 
                         command=lambda w=window: w.lift(), 
                         bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
        except:
            pass

    def audit_log(self, action):
        """Log user actions."""
        try:
            log_path = os.path.expanduser("~/.berke0s/audit.log")
            with open(log_path, "a") as f:
                f.write(f"{datetime.now()}: {self.current_user[0]} - {action}\n")
        except:
            pass

### --- MAIN ---
if __name__ == "__main__":
    try:
        wm = WindowManager()
        # Initialize applications
        file_manager = FileManager(wm)
        text_editor = TextEditor(wm)
        code_editor = CodeEditor(wm)
        calculator = Calculator(wm)
        web_browser = WebBrowser(wm)
        system_info = SystemInfo(wm)
        package_manager = PackageManager(wm)
        task_manager = TaskManager(wm)
        media_player = MediaPlayer(wm)
        image_viewer = ImageViewer(wm)
        presentation = PresentationApp(wm)
        control_center = ControlCenter(wm)
        disk_manager = DiskManager(wm)
        terminal = TerminalEmulator(wm)
        system_monitor = SystemMonitorWidget(wm)
        screenshot = ScreenshotUtility(wm)
        backup = BackupUtility(wm)
        email_client = EmailClient(wm)
        calendar = CalendarApp(wm)
        notes = NotesApp(wm)
        network_monitor = NetworkMonitor(wm)
        log_viewer = SystemDiagnostics(wm)
        task_scheduler = TaskScheduler(wm)
        file_encryption = FileEncryptionTool(wm)
        weather = WeatherApp(wm)
        optimizer = PerformanceOptimizer(wm)

        # Assign apps to window manager
        wm.file_manager = file_manager
        wm.text_editor = text_editor
        wm.code_editor = code_editor
        wm.calculator = calculator
        wm.web_browser = web_browser
        wm.system_info = system_info
        wm.package_manager = package_manager
        wm.task_manager = task_manager
        wm.media_player = media_player
        wm.image_viewer = image_viewer
        wm.presentation = presentation
        wm.control_center = control_center
        wm.disk_manager = disk_manager
        wm.terminal = terminal
        wm.system_monitor = system_monitor
        wm.screenshot = screenshot
        wm.backup = backup
        wm.email_client = email_client
        wm.calendar = calendar
        wm.notes = notes
        wm.network_monitor = network_monitor
        wm.log_viewer = log_viewer
        wm.task_scheduler = task_scheduler
        wm.file_encryption = file_encryption
        wm.weather = weather
        wm.optimizer = optimizer

        # Start menu
        def show_start_menu(event):
            """Display the start menu with all applications."""
            try:
                menu = tk.Menu(wm.root, tearoff=0, bg="#333333", fg="white")
                apps = {
                    "File Explorer": file_manager.open,
                    "Text Editor": text_editor.open,
                    "Code Editor": code_editor.open,
                    "Calculator": calculator.open,
                    "Web Browser": web_browser.open,
                    "System Info": system_info.open,
                    "Package Manager": package_manager.open,
                    "Task Manager": task_manager.open,
                    "Media Player": lambda: media_player.play(os.path.expanduser("~/test.mp3")),
                    "Image Viewer": lambda: image_viewer.open_file(os.path.expanduser("~/test.png")),
                    "Presentation": presentation.open,
                    "Control Center": control_center.open,
                    "Disk Manager": disk_manager.open,
                    "Terminal": terminal.initialize,
                    "System Monitor": system_monitor.toggle,
                    "Screenshot": screenshot.take_screenshot,
                    "Backup Utility": backup.restore,
                    "Email Client": email_client.open,
                    "Calendar": calendar.open,
                    "Notes": notes.open,
                    "Network Monitor": network_monitor.toggle,
                    "System Diagnostics": log_viewer.open,
                    "Task Scheduler": task_scheduler.open,
                    "File Encryption": file_encryption.open,
                    "Weather": weather.open,
                    "Performance Optimizer": optimizer.open
                }
                pinned_menu = tk.Menu(menu, tearoff=0, bg="#333333", fg="white")
                for app in wm.pinned_apps:
                    if app in apps:
                        pinned_menu.add_command(label=app, command=apps[app])
                        pinned_menu.add_command(label=f"Unpin {app}", 
                                               command=lambda a=app: wm.unpin_app(a))
                for app, cmd in apps.items():
                    if app not in wm.pinned_apps:
                        pinned_menu.add_command(label=f"Pin {app}", 
                                               command=lambda a=app: wm.pin_app(a))
                menu.add_cascade(label="Pinned Apps", menu=pinned_menu)
                for name, cmd in apps.items():
                    menu.add_command(label=name, command=cmd)
                recent_menu = tk.Menu(menu, tearoff=0, bg="#333333", fg="white")
                for file in wm.recent_files:
                    recent_menu.add_command(label=os.path.basename(file), 
                                           command=lambda f=file: wm.open_file(f))
                menu.add_cascade(label="Recent Files", menu=recent_menu)
                menu.add_separator()
                menu.add_command(label="Shutdown", command=wm.shutdown)
                menu.add_command(label="Reboot", command=wm.reboot)
                menu.add_command(label="Log Out", command=wm.logout)
                menu.post(wm.start_btn.winfo_rootx(), wm.start_btn.winfo_rooty() - 300)
                wm.audit_log("Opened start menu")
            except Exception as e:
                wm.notifications.send("Start Menu", f"Error: {str(e)}")

        wm.start_btn.bind("<Button-1>", show_start_menu)

        # Desktop context menu
        def show_desktop_menu(event):
            """Display context menu on desktop right-click."""
            try:
                menu = tk.Menu(wm.root, tearoff=0, bg="#333333", fg="white")
                menu.add_command(label="New Folder", command=lambda: file_manager.create_folder())
                menu.add_command(label="New Text File", command=lambda: text_editor.new_file())
                menu.add_command(label="New Note", command=lambda: notes.open())
                menu.add_command(label="Open Terminal", command=lambda: terminal.initialize())
                menu.add_separator()
                menu.add_command(label="Control Center", command=lambda: control_center.open())
                # If sticky note functionality exists, add it here
                # menu.add_command(label="Sticky Note", command=lambda: wm.sticky_note())
                menu.post(event.x_root, event.y_root)
                wm.audit_log("Opened desktop context menu")
            except Exception as e:
                wm.notifications.send("Desktop", f"Error: {str(e)}")

        wm.desktop.bind("<Button-3>", show_desktop_menu)

        # Keyboard shortcuts
        def handle_shortcuts(self, event):
            """Handle global keyboard shortcuts."""
            try:
                if event.keysym == 't' and event.state & 0x4 and event.state & 0x1:  # Ctrl+Alt+T
                    terminal.initialize()
                    wm.audit_log("Opened terminal via Ctrl+Alt+T")
                elif event.keysym == 'f' and event.state & 0x4:  # Ctrl+F
                    file_manager.open()
                    wm.audit_log("Opened file explorer via Ctrl+F")
                elif event.keysym == 'e' and event.state & 0x4:  # Ctrl+E
                    code_editor.open()
                    wm.audit_log("Opened code editor via Ctrl+E")
                elif event.keysym == 's' and event.state & 0x4:  # Ctrl+S
                    wm.search_var.focus_set()
                    wm.audit_log("Focused search bar via Ctrl+S")
            except Exception as e:
                pass
        wm.root.bind("<KeyPress>", handle_shortcuts)

        # Restore session for user
        session = wm.session_manager.load_session()
        for win in session["open_windows"]:
            try:
                wm.create_window(win["title"], 
                                lambda f: tk.Label(f, text="Restored Window", fg="white", 
                                                  bg="#333333").pack(),
                                x=win["x"], y=win["y"], width=win["width"], height=win["height"])
                wm.audit_log(f"Restored window: {win['title']}")
            except:
                pass
        
        # Apply saved configuration
        wm.load_config()
        
        # Show login screen
        wm.show_login()
        
        # Main loop
        wm.root.mainloop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        wm.cleanup()
        sys.exit(1)

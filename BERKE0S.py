import os
import sys
import time
import json
import subprocess
import threading
import signal
import psutil
import socket
import re
import shutil
import getpass
import datetime
import hashlib
import logging
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
        "python3.8", "tk", "tcl", "python3.8-pip", "alsa", "bluez",
        "e2fsprogs", "nano", "htop", "bash", "nmcli", "tar", "zip"
    ]
    for pkg in packages:
        try:
            subprocess.run(["tce-load", "-wi", pkg], check=True, capture_output=True)
            logging.info(f"Installed package: {pkg}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Package install failed: {pkg} - {e}")
    try:
        subprocess.run(["pip3", "install", "psutil", "Pillow", "flask"], check=True)
        logging.info("Installed Python dependencies")
    except subprocess.CalledProcessError as e:
        logging.error(f"Python dependencies install failed: {e}")

# Setup autostart
def setup_autostart():
    try:
        bootlocal = "/opt/bootlocal.sh"
        cmd = f"python3 /usr/local/bin/berke0s.py &\n"
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
            logging.error(f"Notification error: {e}")

### --- DESKTOP AND WINDOW MANAGER ---
class WindowManager:
    def __init__(self):
        self.windows = []
        self.z_index = 100
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
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
            logging.error(f"Screen off error: {e}")

    def suspend(self):
        try:
            subprocess.run(["sudo", "pm-suspend"], check=True)
        except Exception as e:
            logging.error(f"Suspend error: {e}")

    def update_clock(self):
        self.clock.config(text=datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y"))
        self.root.after(1000, self.update_clock)

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
            logging.error(f"Battery widget error: {e}")

        # WiFi
        try:
            output = subprocess.check_output(["iwconfig"], text=True, stderr=subprocess.DEVNULL)
            strength = re.search(r"Signal level=(-?\d+)", output)
            if strength:
                level = int(strength.group(1))
                color = "#fff" if level > -70 else "#888"
                self.wifi_label.config(image=self.svg_to_photo(WIFI_ICON.replace("#fff", color)))
        except Exception as e:
            logging.error(f"WiFi widget error: {e}")

        # Volume
        try:
            output = subprocess.check_output(["amixer", "get", "Master"], text=True)
            volume = re.search(r"\[(\d+)%\]", output)
            if volume:
                vol = int(volume.group(1))
                color = "#fff" if vol > 0 else "#888"
                self.volume_label.config(image=self.svg_to_photo(VOLUME_ICON.replace("#fff", color)))
        except Exception as e:
            logging.error(f"Volume widget error: {e}")

        # Bluetooth
        try:
            output = subprocess.check_output(["bluetoothctl", "show"], text=True)
            powered = "Powered: yes" in output
            color = "#fff" if powered else "#888"
            self.bluetooth_label.config(image=self.svg_to_photo(BLUETOOTH_ICON.replace("#fff", color)))
        except Exception as e:
            logging.error(f"Bluetooth widget error: {e}")

        self.root.after(5000, self.update_widgets)

    def svg_to_photo(self, svg):
        try:
            img = Image.open(BytesIO(svg.encode())).convert("RGBA")
            img = img.resize((20, 20), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logging.error(f"SVG render error: {e}")
            return None

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
        self.windows.remove(window)
        window.taskbar_btn.destroy()
        session = load_session()
        session["open_windows"] = [w for w in session["open_windows"] if w["title"] != window.title()]
        save_session(session)
        window.destroy()

    def focus_window(self, window):
        window.lift()
        self.z_index += 1
        window.configure(takefocus=True)
        window.focus_force()

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
            img = Image.open(wallpaper)
            img = img.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.LANCZOS)
            self.desktop_bg = ImageTk.PhotoImage(img)
            self.desktop.create_image(0, 0, image=self.desktop_bg, anchor=tk.NW)

    def open_desktop_settings(self):
        def build_ui(frame):
            tk.Label(frame, text="Icon Size", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
            size_var = tk.IntVar(value=self.config["desktop"]["icon_size"])
            tk.Scale(frame, from_=32, to=96, orient=tk.HORIZONTAL, variable=size_var, 
                    bg="rgba(0,0,0,0.4)", fg="white").pack()
            snap_var = tk.BooleanVar(value=self.config["desktop"]["grid_snap"])
            tk.Checkbutton(frame, text="Grid Snap", variable=snap_var, fg="white", 
                          bg="grey").pack(pady=5)
            tk.Button(frame, text="Apply", command=lambda: self.save_desktop_settings(size_var.get(), snap_var.get())).pack(pady=10)
        self.create_window("Desktop Settings", build_ui)

    def save_desktop_settings(self, icon_size, grid_snap):
        config = load_config()
        config["desktop"].update({"icon_size": icon_size, "grid_snap": grid_snap})
        save_config(config)
        self.config = config
        # Refresh icons
        session = load_session()
        for icon in list(self.desktop_icons.values()):
            self.delete_icon(icon["icon"])
        self.load_desktop_icons()

    def shutdown(self):
        subprocess.run(["sudo", "poweroff"])

    def reboot(self):
        subprocess.run(["sudo", "reboot"])

    def logout(self):
        session = load_session()
        session["open_windows"] = []
        save_session(session)
        self.root.destroy()
        os.execv(sys.executable, [sys.executable] + sys.argv)

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
                
                # Clean zombie processes
                for proc in psutil.process_iter(['pid', 'status']):
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        try:
                            proc.terminate()
                            logging.info(f"Terminated zombie process: {proc.pid}")
                        except:
                            pass
                
                time.sleep(1)
            except Exception as e:
                logging.error(f"Resource monitor error: {e}")

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
                fg="white", bg="foreground", font=("Arial", 14)).pack(pady=20)

        # Language
        lang_frame = ttk.Frame(notebook)
        notebook.add(lang_frame, text="Language")
        tk.Label(lang_frame, text="Select Language", fg="white", bg="foreground").pack(pady=10)
        lang_var = tk.StringVar(value=self.config["language"])
        ttk.Combobox(lang_frame, textvariable=lang_var, values=list(self.locales.keys()), 
                    state="readonly").pack(pady=5)

        # Timezone
        tz_frame = ttk.Frame(notebook)
        notebook.add(tz_frame, text="Timezone")
        tk.Label(tz_frame, text="Select Timezone", fg="white", bg="foreground").pack(pady=10)
        tz_var = tk.StringVar(value=self.config["timezone"])
        ttk.Combobox(tz_frame, textvariable=tz_var, values=self.timezones, 
                    state="readonly").pack(pady=5)

        # WiFi
        wifi_frame = ttk.Frame(notebook)
        notebook.add(wifi_frame, text="Wi-Fi")
        tk.Label(wifi_frame, text="Wi-Fi Network", fg="white", bg="foreground").pack(pady=5)
        ssid_var = tk.StringVar()
        ssids = self.scan_wifi()
        ssid_menu = ttk.Combobox(wifi_frame, textvariable=ssid_var, values=ssids, 
                                state="readonly")
        ssid_menu.pack(pady=5)
        tk.Button(wifi_frame, text="Refresh", command=lambda: self.refresh_wifi(ssid_menu)).pack()
        tk.Label(wifi_frame, text="Password", fg="white", bg="foreground").pack(pady=5)
        passwd_var = tk.StringVar()
        tk.Entry(wifi_frame, textvariable=passwd_var, show="*", bg="rgba(0,0,0,255)", 
                fg="white").pack(pady=5)

        # User
        user_frame = ttk.Frame(notebook)
        notebook.add(user_frame, text="User")
        tk.Label(user_frame, text="Username", fg="white", bg="foreground").pack(pady=5)
        user_var = tk.StringVar()
        tk.Entry(user_frame, textvariable=user_var, bg="rgba(255,255,255,255)", 
                fg="white").pack(pady=5)
        tk.Label(user_frame, text="Password", fg="white", bg="foreground").pack(pady=5)
        user_passwd_var = tk.StringVar()
        tk.Entry(user_frame, textvariable=user_passwd_var, show="*", 
                bg="rgba(255,255,255,255)", fg="white").pack(pady=5)
        tk.Label(user_frame, text="Confirm Password", fg="white", bg="foreground").pack(pady=5)
        confirm_passwd_var = tk.StringVar()
        tk.Entry(user_frame, textvariable=confirm_passwd_var, show="*", 
                bg="rgba(255,255,255,255)", fg="white").pack(pady=5)

        # EULA
        eula_frame = ttk.Frame(notebook)
        notebook.add(eula_frame, text="EULA")
        eula_text = tk.Text(eula_frame, height=10, bg="rgba(0,0,0,255)", fg="white", 
                           wrap=tk.WORD)
        eula_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        eula_text.insert(tk.END, self.get_eula_text())
        eula_text.config(state="disabled")
        accept_var = tk.BooleanVar()
        tk.Checkbutton(eula_frame, text="I accept the terms", 
                      variable=accept_var, fg="white", bg="foreground").pack(pady=5)

        # Accessibility
        access_frame = ttk.Frame(notebook)
        notebook.add(access_frame, text="Accessibility")
        high_contrast_var = tk.BooleanVar(value=self.config["accessibility"]["high_contrast"])
        tk.Checkbutton(access_frame, text="High Contrast Mode", variable=high_contrast_var, 
                      fg="white", bg="foreground").pack(pady=5)
        screen_reader_var = tk.BooleanVar(value=self.config["accessibility"]["screen_reader"])
        tk.Checkbutton(access_frame, text="Enable Screen Reader", variable=screen_reader_var, 
                      fg="white", bg="foreground").pack(pady=5)
        font_scale_var = tk.DoubleVar(value=self.config["accessibility"]["font_scale"])
        tk.Label(access_frame, text="Font Scale", fg="white", bg="foreground").pack(pady=5)
        tk.Scale(access_frame, from_=0.8, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, 
                variable=font_scale_var, bg="rgba(0,0,0,255)", fg="white").pack(pady=5)

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
            logging.error(f"EULA load error: {e}")
            return default_eula

    def scan_wifi(self):
        try:
            output = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi", 
                                            "list"], text=True)
            return [line.strip() for line in output.splitlines() if line.strip()]
        except Exception as e:
            logging.error(f"WiFi scan error: {e}")
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
                subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, 
                               "password", passwd], check=True)
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
        tk.Label(frame, text="Welcome to Berke0S", fg="white", bg="rgba(0,0,0,255)", 
                font=("Arial", 16)).pack(pady=10)
        tk.Label(frame, text="Username", fg="white", bg="rgba(0,0,0,255)").pack()
        user_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=user_var, 
                    values=[u["username"] for u in self.config["users"]], 
                    state="readonly").pack(pady=5)
        tk.Label(frame, text="Password", fg="white", bg="rgba(0,0,0,255)").pack()
        passwd_var = tk.StringVar()
        tk.Entry(frame, textvariable=passwd_var, show="*", bg="rgba(0,0,0,255)", 
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
        toolbar = tk.Frame(frame, bg="rgba(0,0,0,255)")
        toolbar.pack(fill=tk.X)
        tk.Button(toolbar, text="New File", command=self.create_file).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="New Folder", command=self.create_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Copy", command=self.copy).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Paste", command=self.paste).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=2)
        
        # Path bar
        path_frame = tk.Frame(frame, bg="rgba(0,0,0,255)")
        path_frame.pack(fill=tk.X)
        self.path_var = tk.StringVar(value=self.current_path)
        tk.Entry(path_frame, textvariable=self.path_var, bg="rgba(0,0,0,255)", 
                fg="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(path_frame, text="Go", command=self.navigate_path).pack(side=tk.LEFT)

        # Main view
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left_panel = tk.Frame(paned, bg="rgba(0,0,0,255)")
        paned.add(left_panel, weight=1)
        right_panel = tk.Frame(paned, bg="rgba(0,0,0,255)")
        paned.add(right_panel, weight=1)

        self.left_list = tk.Listbox(left_panel, bg="rgba(0,0,0,255)", fg="white", 
                                   selectmode=tk.EXTENDED)
        self.left_list.pack(fill=tk.BOTH, expand=True)
        self.right_list = tk.Listbox(right_panel, bg="rgba(0,0,0,255)", fg="white", 
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
                logging.error(f"File list update error: {e}")

    def navigate_path(self):
        self.current_path = self.path_var.get()
        self.update_lists()

    def navigate(self, listbox, path):
        selected = listbox.get(listbox.curselection()[0])[2:]  # Remove emoji prefix
        new_path = os.path.join(path, selected)
        if os.path.isdir(new_path):
            self.current_path = new_path
            self.path_var.set(new_path)
            self.update_lists()
        else:
            self.navigate_file(new_path)

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
        selected = [listbox.get(i)[2:] for i in listbox.curselection()]
        if not selected:
            return
        menu = tk.Menu(self.wm.root, tearoff=0, bg="rgba(0,0,0,255)", fg="white")
        menu.add_command(label="Open", command=lambda: self.navigate(listbox, self.current_path))
        menu.add_command(label="Copy", command=self.copy)
        menu.add_command(label="Delete", command=self.delete)
        menu.add_command(label="Rename", command=self.rename)
        menu.add_command(label="Add to Desktop", command=lambda: self.add_to_desktop(selected))
        menu.add_separator()
        menu.add_command(label="Properties", command=lambda: self.wm.show_properties(
            os.path.join(self.current_path, selected[0])))
        menu.post(event.x_root, event.y_root)

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
        toolbar = tk.Frame(frame, bg="rgba(0,0,0,255)")
        toolbar.pack(fill=tk.X)
        tk.Button(toolbar, text="Save", command=self.save).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        
        self.text_area = tk.Text(frame, bg="rgba(0,0,0,255)", fg="white", insertbackground="white", 
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
        entry = tk.Entry(frame, textvariable=tk.StringVar(value="0"), bg="rgba(0,0,0,255)", 
                        fg="white", font=("Arial", 16), justify="right")
        entry.pack(fill=tk.X, padx=5, pady=5)
        
        buttons = [
            ("C", lambda: self.clear(entry)), ("%", lambda: self.add("%")),
            ("/", lambda: self.add("/")), ("7", lambda: self.add("7")),
            ("8", lambda: self.add("8")), ("9", lambda: self.add("9")),
            ("*", lambda: self.add("*")), ("4", lambda: self.add("4")),
            ("5", lambda: self.add("5")), ("6", lambda: self.add("6")),
            ("-", lambda: self.add("-")), ("1", lambda: self.add("1")),
            ("2", lambda: self.add("2")), ("3", lambda: self.add("3")),
            ("+", lambda: self.add("+")), ("0", lambda: self.add("0")),
            (".", lambda: self.add(".")), ("=", lambda: self.calculate(entry))
        ]
        
        btn_frame = tk.Frame(frame, bg="rgba(0,0,0,255)")
        btn_frame.pack(fill=tk.BOTH, expand=True)
        for i, (text, cmd) in enumerate(buttons):
            tk.Button(btn_frame, text=text, command=cmd, bg="rgba(255,255,255,0.2)", 
                     fg="white", font=("Arial", 12)).grid(row=i//4, column=i%4, sticky="nsew")
        for i in range(5):
            btn_frame.grid_rowconfigure(i, weight=1)
            btn_frame.grid_columnconfigure(i, weight=1)

    def add(self, char):
        self.expression += char
        self.update_entry()

    def clear(self, entry):
        self.expression = ""
        entry.delete(0, tk.END)
        entry.insert(0, "0")

    def calculate(self, entry):
        try:
            result = eval(self.expression)
            self.expression = str(result)
            entry.delete(0, tk.END)
            entry.insert(0, result)
            logging.info(f"Calculator result: {self.expression}")
        except Exception as e:
            logging.error(f"Calculator error: {e}")
            entry.delete(0, tk.END)
            entry.insert(0, "Error")

    def update_entry(self):
        entry = self.wm.windows[-1].winfo_children()[-1].winfo_children()[0]
        entry.delete(0, tk.END)
        entry.insert(0, self.expression or "0")

### --- SYSTEM INFO ---
class SystemInfo:
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("System Info", self.build_ui, width=500, height=400)

    def build_ui(self, frame):
        info = self.get_system_info()
        tk.Label(frame, text="System Information", fg="white", bg="rgba(0,0,0,255)", 
                font=("Arial", 16)).pack(pady=10)
        text = tk.Text(frame, bg="rgba(0,0,0,255)", fg="white", height=15, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert(tk.END, info)
        text.config(state="disabled")

    def get_system_info(self):
        try:
            info = []
            info.append(f"OS: TinyCore Linux")
            info.append(f"Kernel: {os.uname().release}")
            info.append(f"CPU: {psutil.cpu_count()} cores @ {psutil.cpu_freq().current:.1f} MHz")
            mem = psutil.virtual_memory()
            info.append(f"Memory: {mem.total / (1024**2):.1f} MB total, {mem.used / (1024**2):.1f} MB used")
            disk = psutil.disk_usage("/")
            info.append(f"Disk: {disk.total / (1024**3):.1f} GB total, {disk.used / (1024**3):.1f} GB used")
            return "\n".join(info)
        except Exception as e:
            logging.error(f"System info error: {e}")
            return "Error retrieving system information"

### --- PACKAGE MANAGER ---
class PackageManager:
    def __init__(self, wm):
        self.wm = wm
        self.cache = {}

    def open(self):
        self.wm.create_window("Package Manager", self.build_ui, width=700, height=500)

    def build_ui(self, frame):
        toolbar = tk.Frame(frame, bg="rgba(0,0,0,255)")
        toolbar.pack(fill=tk.X)
        tk.Label(toolbar, text="Search:", fg="white", bg="rgba(0,0,0,255)").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        tk.Entry(toolbar, textvariable=search_var, bg="rgba(0,0,0,255)", 
                fg="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(toolbar, text="Search", command=lambda: self.search_packages(search_var.get())).pack(side=tk.LEFT)
        
        self.listbox = tk.Listbox(frame, bg="rgba(0,0,0,255)", fg="white", 
                                 selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        tk.Button(frame, text="Install", command=self.install).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Uninstall", command=self.uninstall).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Update Cache", command=self.update_cache).pack(side=tk.LEFT, padx=5)
        
        self.update_cache()

    def update_cache(self):
        try:
            output = subprocess.check_output(["tce-status", "-u"], text=True)
            self.cache = {line.split()[0]: line for line in output.splitlines() if line}
            self.listbox.delete(0, tk.END)
            for pkg in sorted(self.cache.keys()):
                self.listbox.insert(tk.END, pkg)
            self.wm.notifications.send("Package Manager", "Cache updated")
            logging.info("Package cache updated")
        except Exception as e:
            logging.error(f"Package cache update error: {e}")
            messagebox.showerror("Error", f"Cache update failed: {str(e)}")

    def search_packages(self, query):
        self.listbox.delete(0, tk.END)
        for pkg in sorted(self.cache.keys()):
            if query.lower() in pkg.lower():
                self.listbox.insert(tk.END, pkg)

    def install(self):
        selected = self.listbox.get(self.listbox.curselection())
        try:
            subprocess.run(["tce-load", "-wi", selected], check=True)
            self.wm.notifications.send("Package Manager", f"Installed {selected}")
            logging.info(f"Installed package: {selected}")
        except Exception as e:
            logging.error(f"Package install error: {selected} - {e}")
            messagebox.showerror("Error", f"Install failed: {str(e)}")

    def uninstall(self):
        selected = self.listbox.get(self.listbox.curselection())
        try:
            subprocess.run(["tce-remove", selected], check=True)
            self.wm.notifications.send("Package Manager", f"Uninstalled {selected}")
            self.update_cache()
            logging.info(f"Uninstalled package: {selected}")
        except Exception as e:
            logging.error(f"Package uninstall error: {selected} - {e}")
            messagebox.showerror("Error", f"Uninstall failed: {str(e)}")

### --- TASK MANAGER ---
class TaskManager:
    def __init__(self, wm):
        self.wm = wm
        self.resource_monitor = ResourceMonitor(wm)

    def open(self):
        self.wm.create_window("Task Manager", self.build_ui, width=600, height=500)

    def build_ui(self, frame):
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Processes
        proc_frame = ttk.Frame(notebook)
        notebook.add(proc_frame, text="Processes")
        self.proc_list = tk.Listbox(proc_frame, bg="rgba(0,0,0,255)", fg="white", 
                                   width=50)
        self.proc_list.pack(fill=tk.BOTH, expand=True)
        tk.Button(proc_frame, text="Kill Process", command=self.kill).pack(pady=5)
        tk.Button(proc_frame, text="Refresh", command=self.update_procs).pack(pady=5)

        # Performance
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="Performance")
        self.cpu_canvas = tk.Canvas(perf_frame, bg="rgba(0,0,0,255)", height=100)
        self.cpu_canvas.pack(fill=tk.X, pady=5)
        self.ram_canvas = tk.Canvas(perf_frame, bg="rgba(0,0,0,255)", height=100)
        self.ram_canvas.pack(fill=tk.X, pady=5)
        tk.Label(perf_frame, text="CPU Usage", fg="white", bg="rgba(0,0,0,255)").pack()
        self.cpu_label = tk.Label(perf_frame, fg="white", bg="rgba(0,0,0,255)")
        self.cpu_label.pack()
        tk.Label(perf_frame, text="Memory Usage", fg="white", bg="rgba(0,0,0,255)").pack()
        self.ram_label = tk.Label(perf_frame, fg="white", bg="rgba(0,0,0,255)")
        self.ram_label.pack()

        self.update_procs()
        self.update_graphs()

    def update_procs(self):
        self.proc_list.delete(0, tk.END)
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                info = proc.info
                self.proc_list.insert(tk.END, 
                                     f"{info['pid']} - {info['name']} - CPU: {info['cpu_percent']:.1f}% - "
                                     f"Mem: {info['memory_percent']:.1f}%")
        except Exception as e:
            logging.error(f"Process list update error: {e}")

    def update_graphs(self):
        try:
            history = self.resource_monitor.get_usage_history()
            self.draw_graph(self.cpu_canvas, history["cpu"], "CPU")
            self.draw_graph(self.ram_canvas, history["ram"], "Memory")
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            self.cpu_label.config(text=f"{cpu:.1f}%")
            self.ram_label.config(text=f"{mem:.1f}%")
            self.wm.root.after(1000, self.update_graphs)
        except Exception as e:
            logging.error(f"Performance graph update error: {e}")

    def draw_graph(self, canvas, data, title):
        canvas.delete("all")
        width = canvas.winfo_width()
        height = 100
        if not data:
            return
        max_val = max(data, default=100)
        points = []
        for i, val in enumerate(data):
            x = (i / len(data)) * width
            y = height - (val / max_val) * height
            points.append((x, y))
        canvas.create_line(points, fill="white", width=2)
        canvas.create_text(10, 10, text=title, fill="white", anchor=tk.NW)

    def kill(self):
        selected = self.proc_list.get(self.proc_list.curselection())
        pid = int(selected.split(" - ")[0])
        try:
            psutil.Process(pid).terminate()
            self.wm.notifications.send("Task Manager", f"Killed process {pid}")
            self.update_procs()
            logging.info(f"Killed process: {pid}")
        except Exception as e:
            logging.error(f"Process kill error: {pid} - {e}")
            messagebox.showerror("Error", f"Cannot kill process: {str(e)}")

### --- MEDIA PLAYER ---
class MediaPlayer:
    def __init__(self, wm):
        self.wm = wm
        self.process = None

    def open(self):
        self.wm.create_window("Media Player", self.build_ui, width=500, height=300)

    def play(self, file_path):
        if self.process:
            self.process.terminate()
        try:
            self.process = subprocess.Popen(["mpv", "--no-video", file_path], 
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.wm.notifications.send("Media Player", f"Playing {os.path.basename(file_path)}")
            logging.info(f"Playing media: {file_path}")
        except Exception as e:
            logging.error(f"Media play error: {file_path} - {e}")
            messagebox.showerror("Error", f"Cannot play media: {str(e)}")

    def build_ui(self, frame):
        tk.Button(frame, text="Open File", 
                 command=lambda: self.play(filedialog.askopenfilename())).pack(pady=10)
        tk.Button(frame, text="Stop", command=self.stop).pack(pady=5)
        self.volume = tk.Scale(frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                              bg="rgba(0,0,0,255)", fg="white")
        self.volume.set(50)
        self.volume.pack(pady=5)
        self.volume.bind("<Motion>", self.set_volume)

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None
            self.wm.notifications.send("Media Player", "Playback stopped")
            logging.info("Media playback stopped")

    def set_volume(self, event):
        try:
            subprocess.run(["amixer", "set", "Master", f"{self.volume.get()}%"], 
                          check=True)
        except Exception as e:
            logging.error(f"Volume set error: {e}")

### --- CONTROL CENTER ---
class ControlCenter:
    def __init__(self, wm):
        self.wm = wm
        self.config = load_config()

    def open(self):
        self.wm.create_window("Control Center", self.build_ui, width=700, height=500)

    def build_ui(self, frame):
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Appearance
        appearance = ttk.Frame(notebook)
        notebook.add(appearance, text="Appearance")
        tk.Label(appearance, text="Theme", fg="white", bg="rgba(0,0,0,255)").pack(pady=5)
        theme_var = tk.StringVar(value=self.config["theme"])
        ttk.Combobox(appearance, textvariable=theme_var, values=["monochrome"], 
                    state="readonly").pack(pady=5)
        tk.Button(appearance, text="Change Wallpaper", 
                 command=self.wm.change_wallpaper).pack(pady=5)
        tk.Label(appearance, text="Font Scale", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        font_scale_var = tk.DoubleVar(value=self.config["accessibility"]["font_scale"])
        tk.Scale(appearance, from_=0.8, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, 
                variable=font_scale_var, bg="rgba(0,0,0,0.6)", fg="white").pack(pady=5)
        tk.Button(appearance, text="Apply", command=lambda: self.save_appearance(
            theme_var.get(), font_scale_var.get())).pack(pady=10)

        # Network
        network = ttk.Frame(notebook)
        notebook.add(network, text="Network")
        tk.Label(network, text="Wi-Fi Networks", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        self.network_list = tk.Listbox(network, bg="rgba(0,0,0,0.6)", fg="white")
        self.network_list.pack(fill=tk.BOTH, expand=True)
        tk.Button(network, text="Scan", command=self.scan_networks).pack(pady=5)
        tk.Label(network, text="Password", fg="white", bg="rgba(0,0,0,0.4)").pack()
        net_passwd_var = tk.StringVar()
        tk.Entry(network, textvariable=net_passwd_var, show="*", bg="rgba(0,0,0,0.6)", 
                fg="white").pack(pady=5)
        tk.Button(network, text="Connect", command=lambda: self.connect_network(
            net_passwd_var.get())).pack(pady=5)

        # Sound
        sound = ttk.Frame(notebook)
        notebook.add(sound, text="Sound")
        tk.Label(sound, text="Volume", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        volume = tk.Scale(sound, from_=0, to=100, orient=tk.HORIZONTAL, bg="rgba(0,0,0,0.6)", 
                         fg="white")
        volume.pack(pady=5)
        volume.bind("<Motion>", lambda e: self.set_volume(volume.get()))
        tk.Label(sound, text="Output Device", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        output_var = tk.StringVar()
        output_menu = ttk.Combobox(sound, textvariable=output_var, state="readonly")
        output_menu.pack(pady=5)
        self.update_audio_devices(output_menu)

        # Bluetooth
        bluetooth = ttk.Frame(notebook)
        notebook.add(bluetooth, text="Bluetooth")
        tk.Label(bluetooth, text="Bluetooth Devices", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        self.bt_list = tk.Listbox(bluetooth, bg="rgba(0,0,0,0.6)", fg="white")
        self.bt_list.pack(fill=tk.BOTH, expand=True)
        tk.Button(bluetooth, text="Scan", command=self.scan_bluetooth).pack(pady=5)
        tk.Button(bluetooth, text="Pair", command=self.pair_bluetooth).pack(pady=5)
        tk.Button(bluetooth, text="Disconnect", command=self.disconnect_bluetooth).pack(pady=5)
        tk.Checkbutton(bluetooth, text="Bluetooth Enabled", variable=tk.BooleanVar(
            value=self.is_bluetooth_enabled()), command=self.toggle_bluetooth, fg="white", 
            bg="rgba(0,0,0,0.4)").pack(pady=5)

        # Updates
        updates = ttk.Frame(notebook)
        notebook.add(updates, text="Updates")
        tk.Label(updates, text="System Updates", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        self.update_list = tk.Listbox(updates, bg="rgba(0,0,0,0.6)", fg="white")
        self.update_list.pack(fill=tk.BOTH, expand=True)
        tk.Button(updates, text="Check for Updates", command=self.check_updates).pack(pady=5)
        tk.Button(updates, text="Apply Updates", command=self.apply_updates).pack(pady=5)

        # Power
        power = ttk.Frame(notebook)
        notebook.add(power, text="Power")
        tk.Label(power, text="Screen Timeout (s)", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        screen_timeout = tk.Entry(power, bg="rgba(0,0,0,0.6)", fg="white")
        screen_timeout.insert(0, str(self.config["power"]["screen_off_timeout"]))
        screen_timeout.pack(pady=5)
        tk.Label(power, text="Sleep Timeout (s)", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        sleep_timeout = tk.Entry(power, bg="rgba(0,0,0,0.6)", fg="white")
        sleep_timeout.insert(0, str(self.config["power"]["sleep_timeout"]))
        sleep_timeout.pack(pady=5)
        tk.Button(power, text="Save", command=lambda: self.save_power_settings(
            screen_timeout.get(), sleep_timeout.get())).pack(pady=5)

        # Accessibility
        accessibility = ttk.Frame(notebook)
        notebook.add(accessibility, text="Accessibility")
        high_contrast_var = tk.BooleanVar(value=self.config["accessibility"]["high_contrast"])
        tk.Checkbutton(accessibility, text="High Contrast Mode", variable=high_contrast_var, 
                      fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        screen_reader_var = tk.BooleanVar(value=self.config["accessibility"]["screen_reader"])
        tk.Checkbutton(accessibility, text="Enable Screen Reader", variable=screen_reader_var, 
                      fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)
        tk.Button(accessibility, text="Apply", command=lambda: self.save_accessibility(
            high_contrast_var.get(), screen_reader_var.get())).pack(pady=10)

    def save_appearance(self, theme, font_scale):
        try:
            self.config["theme"] = theme
            self.config["accessibility"]["font_scale"] = font_scale
            save_config(self.config)
            self.wm.notifications.send("Appearance", "Settings applied")
            logging.info("Appearance settings saved")
        except Exception as e:
            logging.error(f"Appearance save error: {e}")
            self.wm.notifications.send("Appearance", "Failed to save settings")

    def scan_networks(self):
        try:
            self.network_list.delete(0, tk.END)
            output = subprocess.check_output(["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi", 
                                            "list"], text=True)
            for line in output.splitlines():
                if line.strip():
                    ssid, signal = line.split(":")
                    self.network_list.insert(tk.END, f"{ssid} ({signal}%)")
        except Exception as e:
            logging.error(f"Network scan error: {e}")
            self.wm.notifications.send("Network", "Failed to scan networks")

    def connect_network(self, password):
        try:
            selected = self.network_list.get(self.network_list.curselection())
            ssid = selected.split(" (")[0]
            subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], 
                          check=True)
            self.wm.notifications.send("Network", f"Connected to {ssid}")
            logging.info(f"Connected to Wi-Fi: {ssid}")
        except Exception as e:
            logging.error(f"Network connect error: {ssid} - {e}")
            self.wm.notifications.send("Network", f"Failed to connect to {ssid}")

    def set_volume(self, level):
        try:
            subprocess.run(["amixer", "set", "Master", f"{int(level)}%"], check=True)
            self.wm.notifications.send("Sound", f"Volume set to {int(level)}%")
            logging.info(f"Volume set to {level}%")
        except Exception as e:
            logging.error(f"Volume set error: {e}")

    def update_audio_devices(self, combobox):
        try:
            output = subprocess.check_output(["aplay", "-l"], text=True)
            devices = [line for line in output.splitlines() if "card" in line]
            combobox["values"] = devices
            if devices:
                combobox.set(devices[0])
        except Exception as e:
            logging.error(f"Audio device update error: {e}")

    def is_bluetooth_enabled(self):
        try:
            output = subprocess.check_output(["bluetoothctl", "show"], text=True)
            return "Powered: yes" in output
        except:
            return False

    def toggle_bluetooth(self):
        try:
            cmd = "power on" if not self.is_bluetooth_enabled() else "power off"
            subprocess.run(["bluetoothctl", cmd], check=True)
            self.wm.notifications.send("Bluetooth", f"Bluetooth {'enabled' if cmd == 'power on' else 'disabled'}")
            logging.info(f"Bluetooth toggled: {cmd}")
        except Exception as e:
            logging.error(f"Bluetooth toggle error: {e}")

    def scan_bluetooth(self):
        try:
            self.bt_list.delete(0, tk.END)
            subprocess.run(["bluetoothctl", "scan", "on"], check=True)
            time.sleep(5)
            subprocess.run(["bluetoothctl", "scan", "off"], check=True)
            output = subprocess.check_output(["bluetoothctl", "devices"], text=True)
            for line in output.splitlines():
                if line.startswith("Device"):
                    self.bt_list.insert(tk.END, line)
            self.wm.notifications.send("Bluetooth", "Scan complete")
            logging.info("Bluetooth scan completed")
        except Exception as e:
            logging.error(f"Bluetooth scan error: {e}")
            self.wm.notifications.send("Bluetooth", "Scan failed")

    def pair_bluetooth(self):
        try:
            selected = self.bt_list.get(self.bt_list.curselection())
            mac = selected.split()[1]
            subprocess.run(["bluetoothctl", "pair", mac], check=True)
            subprocess.run(["bluetoothctl", "connect", mac], check=True)
            self.wm.notifications.send("Bluetooth", f"Paired with {mac}")
            logging.info(f"Paired Bluetooth device: {mac}")
        except Exception as e:
            logging.error(f"Bluetooth pair error: {mac} - {e}")
            self.wm.notifications.send("Bluetooth", "Pairing failed")

    def disconnect_bluetooth(self):
        try:
            selected = self.bt_list.get(self.bt_list.curselection())
            mac = selected.split()[1]
            subprocess.run(["bluetoothctl", "disconnect", mac], check=True)
            self.wm.notifications.send("Bluetooth", f"Disconnected {mac}")
            logging.info(f"Disconnected Bluetooth device: {mac}")
        except Exception as e:
            logging.error(f"Bluetooth disconnect error: {mac} - {e}")
            self.wm.notifications.send("Bluetooth", "Disconnect failed")

    def check_updates(self):
        try:
            self.update_list.delete(0, tk.END)
            subprocess.run(["tce-update"], check=True)
            output = subprocess.check_output(["tce-status", "-u"], text=True)
            for line in output.splitlines():
                if line.strip():
                    self.update_list.insert(tk.END, line)
            self.wm.notifications.send("Updates", "Update check complete")
            logging.info("System update check completed")
        except Exception as e:
            logging.error(f"Update check error: {e}")
            self.wm.notifications.send("Updates", "Update check failed")

    def apply_updates(self):
        try:
            selected = [self.update_list.get(i) for i in self.update_list.curselection()]
            for pkg in selected:
                subprocess.run(["tce-load", "-wi", pkg.split()[0]], check=True)
            self.wm.notifications.send("Updates", f"Applied {len(selected)} updates")
            logging.info(f"Applied updates: {selected}")
        except Exception as e:
            logging.error(f"Update apply error: {e}")
            self.wm.notifications.send("Updates", "Update application failed")

    def save_power_settings(self, screen_timeout, sleep_timeout):
        try:
            self.config["power"].update({
                "screen_off_timeout": int(screen_timeout),
                "sleep_timeout": int(sleep_timeout)
            })
            save_config(self.config)
            self.wm.notifications.send("Power", "Settings saved")
            logging.info("Power settings saved")
        except Exception as e:
            logging.error(f"Power settings save error: {e}")
            self.wm.notifications.send("Power", "Failed to save settings")

    def save_accessibility(self, high_contrast, screen_reader):
        try:
            self.config["accessibility"].update({
                "high_contrast": high_contrast,
                "screen_reader": screen_reader
            })
            save_config(self.config)
            if screen_reader:
                subprocess.run(["espeak", "Accessibility settings applied"], check=True)
            self.wm.notifications.send("Accessibility", "Settings applied")
            logging.info("Accessibility settings saved")
        except Exception as e:
            logging.error(f"Accessibility save error: {e}")
            self.wm.notifications.send("Accessibility", "Failed to save settings")

### --- DISK MANAGER ---
class DiskManager:
    def __init__(self, wm):
        self.wm = wm

    def open(self):
        self.wm.create_window("Disk Manager", self.build_ui, width=700, height=500)

    def build_ui(self, frame):
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Disks
        disks = ttk.Frame(notebook)
        notebook.add(disks, text="Disks")
        self.disk_list = tk.Listbox(disks, bg="rgba(0,0,0,0.6)", fg="white", width=60)
        self.disk_list.pack(fill=tk.BOTH, expand=True)
        btn_frame = tk.Frame(disks, bg="rgba(0,0,0,0.4)")
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Mount", command=self.mount).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Unmount", command=self.unmount).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Format FAT32", command=lambda: self.format("vfat")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Format ext4", command=lambda: self.format("ext4")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.update_disks).pack(side=tk.LEFT, padx=5)

        # Usage
        usage = ttk.Frame(notebook)
        notebook.add(usage, text="Usage")
        self.usage_canvas = tk.Canvas(usage, bg="rgba(0,0,0,0.6)", height=200)
        self.usage_canvas.pack(fill=tk.BOTH, expand=True)
        tk.Label(usage, text="Select disk to view usage", fg="white", bg="rgba(0,0,0,0.4)").pack(pady=5)

        self.update_disks()
        self.disk_list.bind("<<ListboxSelect>>", self.update_usage)

    def update_disks(self):
        self.disk_list.delete(0, tk.END)
        try:
            output = subprocess.check_output(["lsblk", "-f", "-o", "NAME,FSTYPE,SIZE,MOUNTPOINT"], 
                                            text=True)
            for line in output.splitlines()[1:]:
                if line.strip():
                    self.disk_list.insert(tk.END, line)
        except Exception as e:
            logging.error(f"Disk list update error: {e}")
            self.wm.notifications.send("Disk Manager", "Failed to update disk list")

    def mount(self):
        try:
            selected = self.disk_list.get(self.disk_list.curselection())
            dev = selected.split()[0]
            mount_point = f"/mnt/{dev}"
            os.makedirs(mount_point, exist_ok=True)
            subprocess.run(["mount", f"/dev/{dev}", mount_point], check=True)
            self.wm.notifications.send("Disk Manager", f"Mounted /dev/{dev}")
            self.update_disks()
            logging.info(f"Mounted disk: /dev/{dev}")
        except Exception as e:
            logging.error(f"Mount error: /dev/{dev} - {e}")
            self.wm.notifications.send("Disk Manager", f"Mount failed: {dev}")

    def unmount(self):
        try:
            selected = self.disk_list.get(self.disk_list.curselection())
            dev = selected.split()[0]
            subprocess.run(["umount", f"/dev/{dev}"], check=True)
            self.wm.notifications.send("Disk Manager", f"Unmounted /dev/{dev}")
            self.update_disks()
            logging.info(f"Unmounted disk: /dev/{dev}")
        except Exception as e:
            logging.error(f"Unmount error: /dev/{dev} - {e}")
            self.wm.notifications.send("Disk Manager", f"Unmount failed: {dev}")

    def format(self, fs_type):
        try:
            selected = self.disk_list.get(self.disk_list.curselection())
            dev = selected.split()[0]
            if not messagebox.askyesno("Confirm", f"Format /dev/{dev} as {fs_type}? All data will be lost!"):
                return
            subprocess.run([f"mkfs.{fs_type}", f"/dev/{dev}"], check=True)
            self.wm.notifications.send("Disk Manager", f"Formatted /dev/{dev} as {fs_type}")
            self.update_disks()
            logging.info(f"Formatted disk: /dev/{dev} as {fs_type}")
        except Exception as e:
            logging.error(f"Format error: /dev/{dev} - {e}")
            self.wm.notifications.send("Disk Manager", f"Format failed: {dev}")

    def update_usage(self, event):
        try:
            selected = self.disk_list.get(self.disk_list.curselection())
            mount_point = selected.split()[-1] if selected.split()[-1].startswith("/") else None
            if not mount_point:
                return
            self.usage_canvas.delete("all")
            usage = shutil.disk_usage(mount_point)
            total = usage.total / (1024**3)  # GB
            used = usage.used / (1024**3)
            free = usage.free / (1024**3)
            
            width = self.usage_canvas.winfo_width()
            height = 200
            used_width = (used / total) * width
            
            self.usage_canvas.create_rectangle(0, 0, used_width, height, fill="black")
            self.usage_canvas.create_rectangle(used_width, 0, width, height, fill="grey")
            self.usage_canvas.create_text(width/2, height/2, 
                                        text=f"Used: {used:.1f}GB\nFree: {free:.1f}GB\nTotal: {total:.1f}GB",
                                        fill="black", font=("Arial", 12))
        except Exception as e:
            logging.error(f"Disk usage update error: {mount_point} - {e}")

### --- TERMINAL EMULATOR ---
class TerminalEmulator:
    def __init__(self, wm):
        self.wm = wm
        self.tabs = {}

    def initialize(self):
        self.wm.create_window("Terminal Emulator", self.create_ui, width=800, height=400)

    def create_ui(self, frame):
        self.notebook = ttk.Notebook(frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        tk.Button(frame, text="Open New Tab", command=self.add_new_tab).pack(pady=5)
        self.add_new_tab()

    def add_new_tab(self):
        tab = ttk.Frame(self.notebook)
        tab_id = str(uuid.uuid4())
        self.notebook.add(tab, text=f"Shell {len(self.tabs)+1}")
        
        master_fd, slave_fd = pty.openpty()
        pid = os.fork()
        if pid == 0:
            os.setsid()
            fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            os.execv("/bin/sh", ["/bin/sh"])
        else:
            text = tk.Text(tab, bg="black", fg="white", insertbackground="white", 
                          font=("Courier", 12))
            text.pack(fill=tk.BOTH, expand=True)
            self.tabs[tab_id] = {"fd": master_fd, "pid": pid, "text": text}
            threading.Thread(target=self.read_pty, args=(tab_id,), daemon=True).start()
            text.bind("<Key>", lambda e: self.write_pty(tab_id, e))
            text.bind("<Control-c>", lambda e: self.send_interrupt(tab_id))
            self.notebook.select(tab)

    def read_pty(self, tab_id):
        fd = self.tabs[tab_id]["fd"]
        text = self.tabs[tab_id]["text"]
        while True:
            try:
                data = os.read(fd, 1024).decode(errors="ignore")
                text.insert(tk.END, data)
                text.see(tk.END)
            except:
                break

    def write_pty(self, event, tab_id):
        if tab_id not in self.tabs:
            return
        fd = self.tabs[tab_id]["fd"]
        try:
            if event.char:
                os.write(fd, event.char.encode())
            elif event.keysym == "Return":
                os.write(fd, b"\n")
            elif event.keysym == "BackSpace":
                os.write(fd, b"\b")
            elif event.keysym == "Tab":
                os.write(fd, b"\t")
        except Exception as e:
            logging.error(f"Terminal write error: {tab_id} - {e}")

    def send_interrupt(self, tab_id):
        if tab_id not in self.tabs:
            return
        try:
            os.kill(self.tabs[tab_id]["pid"], signal.SIGINT)
            logging.info(f"Sent SIGINT to terminal: {tab_id}")
        except Exception as e:
            logging.error(f"Terminal interrupt error: {tab_id} - {e}")

### --- SYSTEM MONITOR WIDGET ---
class SystemMonitorWidget:
    def __init__(self, wm):
        self.wm = wm
        self.window = None

    def toggle(self):
        if self.window:
            self.window.destroy()
            self.window = None
        else:
            self.window = self.wm.create_window("System Monitor", self.build_monitor_ui, 
                                               x=200, y=150, width=200, height=100)

    def build_monitor_ui(self, frame):
        self.cpu_label = tk.Label(frame, text="CPU: 0%", fg="white", bg="rgba(0,0,0,0.4)")
        self.cpu_label.pack(pady=5)
        self.ram_label = tk.Label(frame, text="RAM: 0%", fg="white", bg="rgba(0,0,0,0.4)")
        self.ram_label.pack(pady=5)
        self.disk_label = tk.Label(frame, text="Disk: 0%", fg="white", bg="rgba(0,0,0,0.4)")
        self.disk_label.pack(pady=5)
        self.update_monitor_stats()

    def update_monitor_stats(self):
        if not self.window:
            return
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            self.cpu_label.config(text=f"CPU: {cpu:.1f}%")
            self.ram_label.config(text=f"RAM: {ram:.1f}%")
            self.disk_label.config(text=f"Disk: {disk:.1f}%")
            self.window.after(2000, self.update_monitor_stats)
        except Exception as e:
            logging.error(f"System monitor update error: {e}")

### --- SCREENSHOT UTILITY ---
class ScreenshotUtility:
    def __init__(self, wm):
        self.wm = wm

    def take_screenshot(self):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{os.environ['HOME']}/screenshot_{timestamp}.png"
            # Use scrot for TinyCore
            subprocess.run(["scrot", path], check=True)
            self.wm_notifications.send("Screenshot", f"Saved to {path}")
            self.wm.add_desktop_icon(path, 100, 100)
            logging.info(f"Screenshot saved: {path}")
        except Exception as e:
            logging.error(f"Screenshot error: {e}")
            self.wm_notifications.send("Screenshot", "Failed to capture screenshot")

### --- BOOT SPLASH ---
def show_splash(wm):
    splash = """
    ██████╗ ███████╗██████╗ ██╗  ██╗███████╗ ██████╗ ███████╗
    ██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔════╝ ██╔══██╗██╔════╝
    ██████╔╝█████╗  ██████╔╝█████╔╝ █████╗   ██████╔╝███████╗
    ██╔═══╝ ██╔══╝  ██╔═══╝ ██╔═██╗ ██╔══╝   ██╔═══╝ ██╔════╝
    ██║     ███████╗██║     ██║  ██╗███████╗ ██║     ███████╗
    ╚═╝     ╚══════╝╚═╝     ╚═╝  ╚═╝╚══════╝ ╚═╝     ╚══════╝
    """
    window = wm.create_window("Berke0S", 
                             lambda f: tk.Label(f, text=splash, fg="white", bg="rgba(0,0,0,0.4)", 
                                               font=("Courier", 14)).pack(padx=50, pady=50),
                             width=600, height=300)
    wm.root.after(3000, window.destroy)

### --- MAIN APPLICATION ---
if __name__ == "__main__":
    # Install packages
    install_packages()
    
    # Setup autostart
    setup_autostart()
    
    # Load config
    config = load_config()
    
    # Initialize window manager
    wm = WindowManager()
    
    # Show splash
    show_splash(wm)
    
    # Resource monitor
    monitor = ResourceMonitor(wm)
    
    # Onboarding
    wizard = OnboardingWizard(wm, config)
    wizard.open()
    
    # Login
    login = LoginManager(wm, config)
    login.show_login()
    
    # Initialize apps
    file_manager = FileManager(wm)
    text_editor = TextEditor(wm)
    calculator = Calculator(wm)
    system_info = SystemInfo(wm)
    package_manager = PackageManager(wm)
    task_manager = TaskManager(wm)
    media_player = MediaPlayer(wm)
    control_center = ControlCenter(wm)
    disk_manager = DiskManager(wm)
    terminal = TerminalEmulator(wm)
    system_monitor = SystemMonitorWidget(wm)
    screenshot = ScreenshotUtility(wm)
    
    # Start menu
    def show_start_menu(event):
        menu = tk.Menu(wm.root, tearoff=0, bg="rgba(0,0,0,0.4)", fg="white")
        apps = {
            "File Manager": file_manager.open,
            "Text Editor": text_editor.open,
            "Calculator": calculator.open,
            "System Info": system_info.open,
            "Package Manager": package_manager.open,
            "Task Manager": task_manager.open,
            "Media Player": media_player.open,
            "Control Center": control_center.open,
            "Disk Manager": disk_manager.open,
            "Terminal": terminal.open,
            "System Monitor": system_monitor.toggle,
            "Screenshot": screenshot.take_screenshot
        }
        for name, cmd in apps.items():
            menu.add_command(label=name, command=cmd)
        menu.add_separator()
        menu.add_command(label="Shutdown", command=wm.shutdown)
        menu.add_command(label="Reboot", command=wm.reboot)
        menu.add_command(label="Log Out", command=wm.logout)
        menu.post(wm.start_btn.winfo_rootx(), wm.start_btn.winfo_rooty() - 150)
    
    wm.start_btn.bind("<Button-1>", show_start_menu)
    
    # Restore session
    session = load_session()
    for win in session["open_windows"]:
        wm.create_window(win["title"], 
                        lambda f: tk.Label(f, text="Restored Window", fg="white", 
                                          bg="rgba(0,0,0,0.4)").pack(),
                        win["x"], win["y"], win["width"], win["height"])
    
    # Main loop
    wm.root.mainloop()

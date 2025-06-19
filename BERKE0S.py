#!/usr/bin/env python3
"""
Berke0S - A comprehensive desktop environment for Tiny Core Linux
Optimized single-file version with error handling and performance improvements
"""

import os
import sys
import time
import json
import subprocess
import threading
import signal
import logging
import queue
import math
import hashlib
import datetime
import uuid
import base64
import re
import shutil
import glob
import stat
import calendar
from io import BytesIO
from urllib.parse import quote
import zipfile
import tarfile

# GUI imports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

# System monitoring
try:
    import psutil
except ImportError:
    psutil = None

# Image processing
try:
    from PIL import Image, ImageTk, ImageGrab
except ImportError:
    Image = ImageTk = ImageGrab = None

# Encryption
try:
    import bcrypt
except ImportError:
    bcrypt = None

# Email support
try:
    import imaplib
    import email
    import smtplib
    from email.message import EmailMessage
except ImportError:
    imaplib = email = smtplib = EmailMessage = None

# Network requests
try:
    import requests
except ImportError:
    requests = None

# Configuration
CONFIG_DIR = os.path.expanduser("~/.berke0s")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
LOG_FILE = os.path.join(CONFIG_DIR, "berke0s.log")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Default configuration
DEFAULT_CONFIG = {
    "first_boot": True,
    "language": "en_US",
    "timezone": "UTC",
    "theme": "dark",
    "users": [],
    "wifi": {"ssid": "", "password": ""},
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
    },
    "taskbar_color": "#333333",
    "font_size": 12,
    "window_transparency": 0.95,
    "session_timeout": 1800,
    "pinned_apps": ["File Manager", "Text Editor", "Terminal"]
}

def load_config():
    """Load configuration from file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults for missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        logging.error(f"Config load error: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logging.error(f"Config save error: {e}")

def load_session():
    """Load session data."""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        return {"open_windows": [], "desktop_icons": []}
    except Exception as e:
        logging.error(f"Session load error: {e}")
        return {"open_windows": [], "desktop_icons": []}

def save_session(session):
    """Save session data."""
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session, f, indent=4)
    except Exception as e:
        logging.error(f"Session save error: {e}")

def install_packages():
    """Install required packages for TinyCore."""
    packages = [
        "python3.9", "tk", "tcl", "python3.9-pip", "alsa", "bluez",
        "e2fsprogs", "nano", "htop", "bash", "tar", "zip", "wireless-tools",
        "scrot", "libnotify", "espeak", "mpv", "dillo", "flwm", "aterm", "feh"
    ]
    
    for pkg in packages:
        try:
            subprocess.run(["tce-load", "-wi", pkg], 
                          check=True, capture_output=True, timeout=30)
            logging.info(f"Installed package: {pkg}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logging.warning(f"Package install failed: {pkg} - {e}")
    
    # Install Python dependencies
    try:
        subprocess.run(["pip3", "install", "--user", "psutil", "Pillow", "bcrypt"], 
                      check=True, timeout=60)
        logging.info("Installed Python dependencies")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.warning(f"Python dependencies install failed: {e}")

class NotificationSystem:
    """Handle system notifications."""
    
    def __init__(self):
        self.config = load_config()
    
    def send(self, title, message, timeout=5000):
        """Send a notification."""
        if not self.config["notifications"]["enabled"]:
            return
        
        try:
            subprocess.run(["notify-send", "-t", str(timeout), title, message], 
                          check=True, timeout=5)
            logging.info(f"Notification sent: {title} - {message}")
        except Exception as e:
            logging.warning(f"Notification error: {e}")
            # Fallback to console output
            print(f"NOTIFICATION: {title} - {message}")

class SessionManager:
    """Manage user sessions and authentication."""
    
    def __init__(self):
        self.users = {}
        self.current_user = None
        self.load_users()
    
    def load_users(self):
        """Load user data."""
        try:
            user_file = os.path.join(CONFIG_DIR, "users.json")
            if os.path.exists(user_file):
                with open(user_file, 'r') as f:
                    self.users = json.load(f)
            else:
                # Create default user
                self.add_user("tc", "password")
        except Exception as e:
            logging.error(f"User load error: {e}")
            self.add_user("tc", "password")
    
    def save_users(self):
        """Save user data."""
        try:
            user_file = os.path.join(CONFIG_DIR, "users.json")
            with open(user_file, 'w') as f:
                json.dump(self.users, f)
        except Exception as e:
            logging.error(f"User save error: {e}")
    
    def add_user(self, username, password):
        """Add a user."""
        try:
            if bcrypt:
                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            else:
                hashed = hashlib.sha256(password.encode()).hexdigest()
            self.users[username] = hashed
            self.save_users()
        except Exception as e:
            logging.error(f"Add user error: {e}")
    
    def authenticate(self, username, password):
        """Authenticate a user."""
        try:
            if username not in self.users:
                return False
            
            stored_hash = self.users[username]
            if bcrypt and stored_hash.startswith('$2b$'):
                return bcrypt.checkpw(password.encode(), stored_hash.encode())
            else:
                return stored_hash == hashlib.sha256(password.encode()).hexdigest()
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False
    
    def login(self, username):
        """Set current user."""
        self.current_user = username
        logging.info(f"User logged in: {username}")
    
    def logout(self):
        """Log out current user."""
        if self.current_user:
            logging.info(f"User logged out: {self.current_user}")
        self.current_user = None

class WindowManager:
    """Main window manager class."""
    
    def __init__(self):
        """Initialize the window manager."""
        try:
            self.root = tk.Tk()
            self.root.title("Berke0S")
            self.root.attributes('-fullscreen', True)
            self.root.configure(bg="#333333")
        except Exception as e:
            logging.error(f"Tkinter initialization error: {e}")
            raise RuntimeError("Failed to initialize GUI")
        
        self.config = load_config()
        self.notifications = NotificationSystem()
        self.session_manager = SessionManager()
        
        self.windows = {}
        self.shortcuts = {}
        self.recent_files = []
        self.virtual_desktops = [{}]
        self.current_desktop = 0
        
        # UI components
        self.taskbar = None
        self.start_btn = None
        self.desktop = None
        self.search_var = None
        
        # Applications
        self.applications = {}
        
        self.setup_ui()
        self.setup_applications()
        self.setup_bindings()
        
        # Session timeout
        self.session_timeout = None
        self.start_session_timeout()
    
    def setup_ui(self):
        """Set up the main UI components."""
        try:
            # Taskbar
            self.taskbar = tk.Frame(self.root, 
                                   bg=self.config.get("taskbar_color", "#333333"), 
                                   height=32)
            self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Start button
            self.start_btn = tk.Button(self.taskbar, text="☰ Start", 
                                      fg="white", bg="#555555", 
                                      relief=tk.RAISED, bd=1)
            self.start_btn.pack(side=tk.LEFT, padx=5, pady=2)
            
            # Search bar
            self.search_var = tk.StringVar()
            search_entry = tk.Entry(self.taskbar, textvariable=self.search_var, 
                                   bg="#555555", fg="white", width=20)
            search_entry.pack(side=tk.LEFT, padx=5, pady=2)
            search_entry.bind('<Return>', self.global_search)
            
            # Clock
            self.clock_label = tk.Label(self.taskbar, fg="white", 
                                       bg=self.config.get("taskbar_color", "#333333"), 
                                       font=("Arial", 10))
            self.clock_label.pack(side=tk.RIGHT, padx=10)
            
            # Desktop
            self.desktop = tk.Canvas(self.root, bg="#333333", highlightthickness=0)
            self.desktop.pack(fill=tk.BOTH, expand=True)
            
            # Update clock
            self.update_clock()
            
            # Apply theme
            self.apply_theme()
            
        except Exception as e:
            logging.error(f"UI setup error: {e}")
    
    def setup_applications(self):
        """Initialize all applications."""
        try:
            self.applications = {
                "File Manager": FileManager(self),
                "Text Editor": TextEditor(self),
                "Calculator": Calculator(self),
                "System Info": SystemInfo(self),
                "Terminal": Terminal(self),
                "Control Center": ControlCenter(self),
                "Notes": NotesApp(self),
                "Task Manager": TaskManager(self)
            }
        except Exception as e:
            logging.error(f"Application setup error: {e}")
    
    def setup_bindings(self):
        """Set up keyboard and mouse bindings."""
        try:
            # Start menu
            self.start_btn.bind("<Button-1>", self.show_start_menu)
            
            # Desktop context menu
            self.desktop.bind("<Button-3>", self.show_desktop_menu)
            
            # Keyboard shortcuts
            self.root.bind("<Control-Alt-t>", lambda e: self.open_app("Terminal"))
            self.root.bind("<Control-f>", lambda e: self.open_app("File Manager"))
            self.root.bind("<Control-s>", lambda e: self.search_var.get() and self.global_search())
            
            # Activity tracking for session timeout
            self.root.bind("<Any-KeyPress>", self.reset_session_timeout)
            self.root.bind("<Any-Motion>", self.reset_session_timeout)
            
        except Exception as e:
            logging.error(f"Bindings setup error: {e}")
    
    def update_clock(self):
        """Update the taskbar clock."""
        try:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.clock_label.config(text=current_time)
            self.root.after(1000, self.update_clock)
        except Exception as e:
            logging.warning(f"Clock update error: {e}")
    
    def apply_theme(self):
        """Apply the current theme."""
        try:
            theme = self.config.get("theme", "dark")
            if theme == "dark":
                colors = {"bg": "#333333", "fg": "white", "entry": "#555555"}
            elif theme == "light":
                colors = {"bg": "#f0f0f0", "fg": "black", "entry": "#ffffff"}
            else:  # high_contrast
                colors = {"bg": "black", "fg": "yellow", "entry": "black"}
            
            self.root.configure(bg=colors["bg"])
            self.desktop.configure(bg=colors["bg"])
            
        except Exception as e:
            logging.error(f"Theme apply error: {e}")
    
    def show_start_menu(self, event):
        """Display the start menu."""
        try:
            menu = tk.Menu(self.root, tearoff=0, bg="#333333", fg="white")
            
            for app_name in self.applications:
                menu.add_command(label=app_name, 
                               command=lambda name=app_name: self.open_app(name))
            
            menu.add_separator()
            menu.add_command(label="Shutdown", command=self.shutdown)
            menu.add_command(label="Reboot", command=self.reboot)
            menu.add_command(label="Log Out", command=self.logout)
            
            menu.post(self.start_btn.winfo_rootx(), 
                     self.start_btn.winfo_rooty() - 200)
            
        except Exception as e:
            logging.error(f"Start menu error: {e}")
    
    def show_desktop_menu(self, event):
        """Display desktop context menu."""
        try:
            menu = tk.Menu(self.root, tearoff=0, bg="#333333", fg="white")
            menu.add_command(label="New Folder", command=self.create_folder)
            menu.add_command(label="New File", command=self.create_file)
            menu.add_command(label="Open Terminal", 
                           command=lambda: self.open_app("Terminal"))
            menu.add_separator()
            menu.add_command(label="Control Center", 
                           command=lambda: self.open_app("Control Center"))
            
            menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            logging.error(f"Desktop menu error: {e}")
    
    def open_app(self, app_name):
        """Open an application."""
        try:
            if app_name in self.applications:
                self.applications[app_name].open()
                logging.info(f"Opened application: {app_name}")
            else:
                self.notifications.send("Error", f"Application not found: {app_name}")
        except Exception as e:
            logging.error(f"Open app error: {app_name} - {e}")
            self.notifications.send("Error", f"Failed to open {app_name}")
    
    def global_search(self, event=None):
        """Perform global search."""
        try:
            query = self.search_var.get().lower()
            if not query:
                return
            
            results = []
            
            # Search applications
            for app_name in self.applications:
                if query in app_name.lower():
                    results.append(f"App: {app_name}")
            
            # Search files in home directory
            try:
                for root, dirs, files in os.walk(os.path.expanduser("~")):
                    if len(results) >= 20:  # Limit results
                        break
                    for name in files + dirs:
                        if query in name.lower():
                            results.append(f"File: {os.path.join(root, name)}")
                            if len(results) >= 20:
                                break
            except Exception as e:
                logging.warning(f"File search error: {e}")
            
            # Display results
            if results:
                self.show_search_results(results)
            else:
                self.notifications.send("Search", "No results found")
                
        except Exception as e:
            logging.error(f"Global search error: {e}")
    
    def show_search_results(self, results):
        """Display search results in a window."""
        try:
            window = self.create_window("Search Results", 400, 300)
            
            listbox = tk.Listbox(window, bg="#555555", fg="white")
            listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            for result in results:
                listbox.insert(tk.END, result)
            
            def open_result(event):
                try:
                    selection = listbox.get(listbox.curselection()[0])
                    if selection.startswith("App: "):
                        app_name = selection[5:]
                        self.open_app(app_name)
                    elif selection.startswith("File: "):
                        file_path = selection[6:]
                        self.open_file(file_path)
                    window.destroy()
                except Exception as e:
                    logging.error(f"Open result error: {e}")
            
            listbox.bind('<Double-1>', open_result)
            
        except Exception as e:
            logging.error(f"Search results error: {e}")
    
    def create_window(self, title, width=400, height=300, x=None, y=None):
        """Create a new window."""
        try:
            if x is None:
                x = (self.root.winfo_screenwidth() - width) // 2
            if y is None:
                y = (self.root.winfo_screenheight() - height) // 2
            
            window = tk.Toplevel(self.root)
            window.title(title)
            window.geometry(f"{width}x{height}+{x}+{y}")
            window.configure(bg="#333333")
            window.attributes('-alpha', self.config.get("window_transparency", 0.95))
            
            self.windows[window] = {
                "title": title, "x": x, "y": y, 
                "width": width, "height": height
            }
            
            window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(window))
            
            return window
            
        except Exception as e:
            logging.error(f"Create window error: {e}")
            return None
    
    def close_window(self, window):
        """Close a window."""
        try:
            if window in self.windows:
                del self.windows[window]
            window.destroy()
        except Exception as e:
            logging.error(f"Close window error: {e}")
    
    def create_folder(self):
        """Create a new folder on desktop."""
        try:
            name = simpledialog.askstring("New Folder", "Folder name:")
            if name:
                path = os.path.join(os.path.expanduser("~"), name)
                os.makedirs(path, exist_ok=True)
                self.notifications.send("Desktop", f"Created folder: {name}")
        except Exception as e:
            logging.error(f"Create folder error: {e}")
    
    def create_file(self):
        """Create a new file on desktop."""
        try:
            name = simpledialog.askstring("New File", "File name:")
            if name:
                path = os.path.join(os.path.expanduser("~"), name)
                with open(path, 'w') as f:
                    f.write("")
                self.notifications.send("Desktop", f"Created file: {name}")
        except Exception as e:
            logging.error(f"Create file error: {e}")
    
    def open_file(self, file_path):
        """Open a file with appropriate application."""
        try:
            if os.path.isdir(file_path):
                self.applications["File Manager"].open_path(file_path)
            else:
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.txt', '.py', '.sh', '.c', '.cpp']:
                    self.applications["Text Editor"].open_file(file_path)
                else:
                    # Try to open with system default
                    subprocess.run(["xdg-open", file_path], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
        except Exception as e:
            logging.error(f"Open file error: {file_path} - {e}")
    
    def start_session_timeout(self):
        """Start session timeout timer."""
        try:
            timeout = self.config.get("session_timeout", 1800) * 1000  # Convert to ms
            if timeout > 0:
                self.session_timeout = self.root.after(timeout, self.logout)
        except Exception as e:
            logging.error(f"Session timeout error: {e}")
    
    def reset_session_timeout(self, event=None):
        """Reset session timeout on activity."""
        try:
            if self.session_timeout:
                self.root.after_cancel(self.session_timeout)
            self.start_session_timeout()
        except Exception as e:
            logging.error(f"Reset timeout error: {e}")
    
    def shutdown(self):
        """Shutdown the system."""
        try:
            self.cleanup()
            subprocess.run(["sudo", "poweroff"], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
        except Exception as e:
            logging.error(f"Shutdown error: {e}")
    
    def reboot(self):
        """Reboot the system."""
        try:
            self.cleanup()
            subprocess.run(["sudo", "reboot"], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
        except Exception as e:
            logging.error(f"Reboot error: {e}")
    
    def logout(self):
        """Log out current user."""
        try:
            self.session_manager.logout()
            self.cleanup()
            self.show_login()
        except Exception as e:
            logging.error(f"Logout error: {e}")
    
    def show_login(self):
        """Show login screen."""
        try:
            # Clear all windows
            for window in list(self.windows.keys()):
                self.close_window(window)
            
            login_window = self.create_window("Berke0S Login", 350, 250)
            
            # Title
            tk.Label(login_window, text="Berke0S", 
                    fg="white", bg="#333333", 
                    font=("Arial", 20)).pack(pady=20)
            
            # Username
            tk.Label(login_window, text="Username:", 
                    fg="white", bg="#333333").pack()
            username_var = tk.StringVar(value="tc")
            username_entry = tk.Entry(login_window, textvariable=username_var, 
                                     bg="#555555", fg="white")
            username_entry.pack(pady=5)
            
            # Password
            tk.Label(login_window, text="Password:", 
                    fg="white", bg="#333333").pack()
            password_var = tk.StringVar()
            password_entry = tk.Entry(login_window, textvariable=password_var, 
                                     show="*", bg="#555555", fg="white")
            password_entry.pack(pady=5)
            
            def attempt_login():
                try:
                    username = username_var.get()
                    password = password_var.get()
                    
                    if self.session_manager.authenticate(username, password):
                        self.session_manager.login(username)
                        login_window.destroy()
                        self.notifications.send("Login", f"Welcome, {username}!")
                    else:
                        self.notifications.send("Login", "Invalid credentials")
                        password_var.set("")
                except Exception as e:
                    logging.error(f"Login attempt error: {e}")
            
            # Login button
            tk.Button(login_window, text="Login", 
                     command=attempt_login, 
                     bg="#555555", fg="white").pack(pady=10)
            
            # Bind Enter key
            password_entry.bind('<Return>', lambda e: attempt_login())
            username_entry.focus()
            
        except Exception as e:
            logging.error(f"Show login error: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Save session
            session = {
                "open_windows": [
                    {
                        "title": data["title"],
                        "x": data["x"],
                        "y": data["y"],
                        "width": data["width"],
                        "height": data["height"]
                    }
                    for data in self.windows.values()
                ]
            }
            save_session(session)
            
            # Save config
            save_config(self.config)
            
            logging.info("Cleanup completed")
        except Exception as e:
            logging.error(f"Cleanup error: {e}")

class BaseApplication:
    """Base class for all applications."""
    
    def __init__(self, window_manager):
        self.wm = window_manager
        self.window = None
    
    def open(self):
        """Open the application."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = self.wm.create_window(self.get_title(), 
                                           self.get_width(), 
                                           self.get_height())
        if self.window:
            self.build_ui()
    
    def get_title(self):
        """Get application title."""
        return "Application"
    
    def get_width(self):
        """Get default window width."""
        return 600
    
    def get_height(self):
        """Get default window height."""
        return 400
    
    def build_ui(self):
        """Build the application UI."""
        tk.Label(self.window, text="Base Application", 
                fg="white", bg="#333333").pack(expand=True)

class FileManager(BaseApplication):
    """File manager application."""
    
    def __init__(self, window_manager):
        super().__init__(window_manager)
        self.current_path = os.path.expanduser("~")
    
    def get_title(self):
        return "File Manager"
    
    def get_width(self):
        return 800
    
    def get_height(self):
        return 600
    
    def build_ui(self):
        """Build file manager UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(self.window, bg="#333333")
            toolbar.pack(fill=tk.X, padx=5, pady=2)
            
            tk.Button(toolbar, text="Up", command=self.go_up, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Home", command=self.go_home, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="New Folder", command=self.new_folder, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            
            # Path bar
            path_frame = tk.Frame(self.window, bg="#333333")
            path_frame.pack(fill=tk.X, padx=5, pady=2)
            
            tk.Label(path_frame, text="Path:", fg="white", bg="#333333").pack(side=tk.LEFT)
            self.path_var = tk.StringVar(value=self.current_path)
            path_entry = tk.Entry(path_frame, textvariable=self.path_var, 
                                 bg="#555555", fg="white")
            path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            path_entry.bind('<Return>', self.navigate_to_path)
            
            # File list
            list_frame = tk.Frame(self.window, bg="#333333")
            list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Scrollbar
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.file_listbox = tk.Listbox(list_frame, bg="#555555", fg="white",
                                          yscrollcommand=scrollbar.set)
            self.file_listbox.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.file_listbox.yview)
            
            # Bindings
            self.file_listbox.bind('<Double-1>', self.open_selected)
            self.file_listbox.bind('<Button-3>', self.show_context_menu)
            
            self.refresh_list()
            
        except Exception as e:
            logging.error(f"File manager UI error: {e}")
    
    def refresh_list(self):
        """Refresh the file list."""
        try:
            self.file_listbox.delete(0, tk.END)
            self.path_var.set(self.current_path)
            
            if not os.path.exists(self.current_path):
                self.current_path = os.path.expanduser("~")
                self.path_var.set(self.current_path)
            
            try:
                items = os.listdir(self.current_path)
                items.sort(key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x.lower()))
                
                for item in items:
                    item_path = os.path.join(self.current_path, item)
                    if os.path.isdir(item_path):
                        self.file_listbox.insert(tk.END, f"📁 {item}")
                    else:
                        self.file_listbox.insert(tk.END, f"📄 {item}")
                        
            except PermissionError:
                self.file_listbox.insert(tk.END, "Permission denied")
            except Exception as e:
                self.file_listbox.insert(tk.END, f"Error: {str(e)}")
                
        except Exception as e:
            logging.error(f"Refresh list error: {e}")
    
    def go_up(self):
        """Navigate to parent directory."""
        try:
            parent = os.path.dirname(self.current_path)
            if parent != self.current_path:
                self.current_path = parent
                self.refresh_list()
        except Exception as e:
            logging.error(f"Go up error: {e}")
    
    def go_home(self):
        """Navigate to home directory."""
        try:
            self.current_path = os.path.expanduser("~")
            self.refresh_list()
        except Exception as e:
            logging.error(f"Go home error: {e}")
    
    def navigate_to_path(self, event=None):
        """Navigate to the path in the entry."""
        try:
            new_path = self.path_var.get()
            if os.path.exists(new_path) and os.path.isdir(new_path):
                self.current_path = new_path
                self.refresh_list()
            else:
                self.wm.notifications.send("File Manager", "Invalid path")
                self.path_var.set(self.current_path)
        except Exception as e:
            logging.error(f"Navigate to path error: {e}")
    
    def open_selected(self, event=None):
        """Open the selected item."""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                return
            
            item_text = self.file_listbox.get(selection[0])
            item_name = item_text[2:]  # Remove emoji prefix
            item_path = os.path.join(self.current_path, item_name)
            
            if os.path.isdir(item_path):
                self.current_path = item_path
                self.refresh_list()
            else:
                self.wm.open_file(item_path)
                
        except Exception as e:
            logging.error(f"Open selected error: {e}")
    
    def show_context_menu(self, event):
        """Show context menu for selected item."""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                return
            
            menu = tk.Menu(self.window, tearoff=0, bg="#333333", fg="white")
            menu.add_command(label="Open", command=self.open_selected)
            menu.add_command(label="Delete", command=self.delete_selected)
            menu.add_command(label="Rename", command=self.rename_selected)
            
            menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            logging.error(f"Context menu error: {e}")
    
    def new_folder(self):
        """Create a new folder."""
        try:
            name = simpledialog.askstring("New Folder", "Folder name:")
            if name:
                folder_path = os.path.join(self.current_path, name)
                os.makedirs(folder_path, exist_ok=True)
                self.refresh_list()
                self.wm.notifications.send("File Manager", f"Created folder: {name}")
        except Exception as e:
            logging.error(f"New folder error: {e}")
    
    def delete_selected(self):
        """Delete the selected item."""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                return
            
            item_text = self.file_listbox.get(selection[0])
            item_name = item_text[2:]  # Remove emoji prefix
            item_path = os.path.join(self.current_path, item_name)
            
            if messagebox.askyesno("Confirm Delete", f"Delete {item_name}?"):
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                self.refresh_list()
                self.wm.notifications.send("File Manager", f"Deleted: {item_name}")
                
        except Exception as e:
            logging.error(f"Delete error: {e}")
            self.wm.notifications.send("File Manager", f"Delete failed: {str(e)}")
    
    def rename_selected(self):
        """Rename the selected item."""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                return
            
            item_text = self.file_listbox.get(selection[0])
            item_name = item_text[2:]  # Remove emoji prefix
            item_path = os.path.join(self.current_path, item_name)
            
            new_name = simpledialog.askstring("Rename", "New name:", initialvalue=item_name)
            if new_name and new_name != item_name:
                new_path = os.path.join(self.current_path, new_name)
                os.rename(item_path, new_path)
                self.refresh_list()
                self.wm.notifications.send("File Manager", f"Renamed to: {new_name}")
                
        except Exception as e:
            logging.error(f"Rename error: {e}")
            self.wm.notifications.send("File Manager", f"Rename failed: {str(e)}")
    
    def open_path(self, path):
        """Open a specific path."""
        try:
            if os.path.exists(path) and os.path.isdir(path):
                self.current_path = path
                if self.window and self.window.winfo_exists():
                    self.refresh_list()
                else:
                    self.open()
        except Exception as e:
            logging.error(f"Open path error: {e}")

class TextEditor(BaseApplication):
    """Simple text editor application."""
    
    def __init__(self, window_manager):
        super().__init__(window_manager)
        self.current_file = None
        self.text_widget = None
    
    def get_title(self):
        return "Text Editor"
    
    def get_width(self):
        return 700
    
    def get_height(self):
        return 500
    
    def build_ui(self):
        """Build text editor UI."""
        try:
            # Menu bar
            menubar = tk.Menu(self.window)
            self.window.config(menu=menubar)
            
            file_menu = tk.Menu(menubar, tearoff=0, bg="#333333", fg="white")
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="New", command=self.new_file)
            file_menu.add_command(label="Open", command=self.open_file_dialog)
            file_menu.add_command(label="Save", command=self.save_file)
            file_menu.add_command(label="Save As", command=self.save_as_file)
            
            # Toolbar
            toolbar = tk.Frame(self.window, bg="#333333")
            toolbar.pack(fill=tk.X, padx=5, pady=2)
            
            tk.Button(toolbar, text="New", command=self.new_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Open", command=self.open_file_dialog, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Save", command=self.save_file, 
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            
            # Text area
            text_frame = tk.Frame(self.window, bg="#333333")
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Scrollbars
            v_scrollbar = tk.Scrollbar(text_frame)
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            h_scrollbar = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            self.text_widget = tk.Text(text_frame, 
                                      bg="#555555", fg="white", 
                                      insertbackground="white",
                                      font=("Monospace", 12),
                                      yscrollcommand=v_scrollbar.set,
                                      xscrollcommand=h_scrollbar.set,
                                      wrap=tk.NONE)
            self.text_widget.pack(fill=tk.BOTH, expand=True)
            
            v_scrollbar.config(command=self.text_widget.yview)
            h_scrollbar.config(command=self.text_widget.xview)
            
            # Status bar
            self.status_bar = tk.Label(self.window, text="Ready", 
                                      fg="white", bg="#333333", 
                                      anchor=tk.W)
            self.status_bar.pack(fill=tk.X, padx=5, pady=2)
            
            # Bindings
            self.text_widget.bind('<Control-s>', lambda e: self.save_file())
            self.text_widget.bind('<Control-o>', lambda e: self.open_file_dialog())
            self.text_widget.bind('<Control-n>', lambda e: self.new_file())
            
        except Exception as e:
            logging.error(f"Text editor UI error: {e}")
    
    def new_file(self):
        """Create a new file."""
        try:
            if self.text_widget:
                self.text_widget.delete(1.0, tk.END)
            self.current_file = None
            self.update_title()
            self.status_bar.config(text="New file")
        except Exception as e:
            logging.error(f"New file error: {e}")
    
    def open_file_dialog(self):
        """Open file dialog."""
        try:
            file_path = filedialog.askopenfilename(
                title="Open File",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Python files", "*.py"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                self.open_file(file_path)
        except Exception as e:
            logging.error(f"Open file dialog error: {e}")
    
    def open_file(self, file_path):
        """Open a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if self.text_widget:
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(1.0, content)
            
            self.current_file = file_path
            self.update_title()
            self.status_bar.config(text=f"Opened: {os.path.basename(file_path)}")
            
        except Exception as e:
            logging.error(f"Open file error: {e}")
            self.wm.notifications.send("Text Editor", f"Failed to open file: {str(e)}")
    
    def save_file(self):
        """Save the current file."""
        try:
            if not self.current_file:
                self.save_as_file()
                return
            
            if self.text_widget:
                content = self.text_widget.get(1.0, tk.END + '-1c')
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.status_bar.config(text=f"Saved: {os.path.basename(self.current_file)}")
                self.wm.notifications.send("Text Editor", "File saved")
                
        except Exception as e:
            logging.error(f"Save file error: {e}")
            self.wm.notifications.send("Text Editor", f"Save failed: {str(e)}")
    
    def save_as_file(self):
        """Save file with new name."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save As",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Python files", "*.py"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                self.current_file = file_path
                self.save_file()
                self.update_title()
                
        except Exception as e:
            logging.error(f"Save as error: {e}")
    
    def update_title(self):
        """Update window title."""
        try:
            if self.window and self.window.winfo_exists():
                if self.current_file:
                    title = f"Text Editor - {os.path.basename(self.current_file)}"
                else:
                    title = "Text Editor - Untitled"
                self.window.title(title)
        except Exception as e:
            logging.error(f"Update title error: {e}")

class Calculator(BaseApplication):
    """Calculator application."""
    
    def __init__(self, window_manager):
        super().__init__(window_manager)
        self.display_var = None
        self.expression = ""
    
    def get_title(self):
        return "Calculator"
    
    def get_width(self):
        return 300
    
    def get_height(self):
        return 400
    
    def build_ui(self):
        """Build calculator UI."""
        try:
            # Display
            self.display_var = tk.StringVar(value="0")
            display = tk.Entry(self.window, textvariable=self.display_var,
                              font=("Arial", 16), justify=tk.RIGHT,
                              bg="#555555", fg="white", state="readonly")
            display.pack(fill=tk.X, padx=5, pady=5)
            
            # Button frame
            button_frame = tk.Frame(self.window, bg="#333333")
            button_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Button layout
            buttons = [
                ['C', '±', '%', '÷'],
                ['7', '8', '9', '×'],
                ['4', '5', '6', '−'],
                ['1', '2', '3', '+'],
                ['0', '.', '=']
            ]
            
            for i, row in enumerate(buttons):
                for j, text in enumerate(row):
                    if text == '0':
                        # Make 0 button span 2 columns
                        btn = tk.Button(button_frame, text=text,
                                       command=lambda t=text: self.button_click(t),
                                       bg="#555555", fg="white",
                                       font=("Arial", 14))
                        btn.grid(row=i, column=j, columnspan=2, sticky="nsew", padx=1, pady=1)
                    elif text in ['=']:
                        btn = tk.Button(button_frame, text=text,
                                       command=lambda t=text: self.button_click(t),
                                       bg="#ff9500", fg="white",
                                       font=("Arial", 14))
                        btn.grid(row=i, column=j+1, sticky="nsew", padx=1, pady=1)
                    else:
                        btn = tk.Button(button_frame, text=text,
                                       command=lambda t=text: self.button_click(t),
                                       bg="#555555", fg="white",
                                       font=("Arial", 14))
                        btn.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
            
            # Configure grid weights
            for i in range(5):
                button_frame.grid_rowconfigure(i, weight=1)
            for j in range(4):
                button_frame.grid_columnconfigure(j, weight=1)
                
        except Exception as e:
            logging.error(f"Calculator UI error: {e}")
    
    def button_click(self, text):
        """Handle button clicks."""
        try:
            if text == 'C':
                self.expression = ""
                self.display_var.set("0")
            elif text == '±':
                if self.expression and self.expression != "0":
                    if self.expression.startswith('-'):
                        self.expression = self.expression[1:]
                    else:
                        self.expression = '-' + self.expression
                    self.display_var.set(self.expression)
            elif text == '=':
                try:
                    # Replace display symbols with Python operators
                    calc_expr = self.expression.replace('×', '*').replace('÷', '/').replace('−', '-')
                    result = str(eval(calc_expr))
                    self.expression = result
                    self.display_var.set(result)
                except:
                    self.display_var.set("Error")
                    self.expression = ""
            else:
                if self.expression == "0" or self.display_var.get() == "Error":
                    self.expression = text
                else:
                    self.expression += text
                self.display_var.set(self.expression)
                
        except Exception as e:
            logging.error(f"Calculator button error: {e}")

class SystemInfo(BaseApplication):
    """System information application."""
    
    def get_title(self):
        return "System Information"
    
    def get_width(self):
        return 500
    
    def get_height(self):
        return 400
    
    def build_ui(self):
        """Build system info UI."""
        try:
            # Create scrollable text widget
            text_frame = tk.Frame(self.window, bg="#333333")
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(text_frame, bg="#555555", fg="white",
                                 font=("Monospace", 10),
                                 yscrollcommand=scrollbar.set,
                                 state=tk.DISABLED)
            text_widget.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Refresh button
            tk.Button(self.window, text="Refresh", command=lambda: self.update_info(text_widget),
                     bg="#555555", fg="white").pack(pady=5)
            
            self.update_info(text_widget)
            
        except Exception as e:
            logging.error(f"System info UI error: {e}")
    
    def update_info(self, text_widget):
        """Update system information."""
        try:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            
            info = []
            info.append("=== BERKE0S SYSTEM INFORMATION ===\n")
            
            # Basic system info
            try:
                info.append(f"OS: {os.uname().sysname} {os.uname().release}")
                info.append(f"Hostname: {os.uname().nodename}")
                info.append(f"Architecture: {os.uname().machine}")
            except:
                info.append("OS: Unknown")
            
            # CPU info
            if psutil:
                try:
                    info.append(f"CPU Cores: {psutil.cpu_count()}")
                    info.append(f"CPU Usage: {psutil.cpu_percent()}%")
                except:
                    pass
            
            # Memory info
            if psutil:
                try:
                    mem = psutil.virtual_memory()
                    info.append(f"Memory Total: {mem.total // 1024**2} MB")
                    info.append(f"Memory Used: {mem.used // 1024**2} MB")
                    info.append(f"Memory Available: {mem.available // 1024**2} MB")
                    info.append(f"Memory Usage: {mem.percent}%")
                except:
                    pass
            
            # Disk info
            if psutil:
                try:
                    disk = psutil.disk_usage('/')
                    info.append(f"Disk Total: {disk.total // 1024**3} GB")
                    info.append(f"Disk Used: {disk.used // 1024**3} GB")
                    info.append(f"Disk Free: {disk.free // 1024**3} GB")
                    info.append(f"Disk Usage: {(disk.used / disk.total) * 100:.1f}%")
                except:
                    pass
            
            # Network info
            try:
                import socket
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                info.append(f"IP Address: {ip}")
            except:
                info.append("IP Address: Unknown")
            
            # Uptime
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                    uptime_hours = int(uptime_seconds // 3600)
                    uptime_minutes = int((uptime_seconds % 3600) // 60)
                    info.append(f"Uptime: {uptime_hours}h {uptime_minutes}m")
            except:
                info.append("Uptime: Unknown")
            
            # Python info
            info.append(f"Python Version: {sys.version}")
            
            text_widget.insert(tk.END, "\n".join(info))
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            logging.error(f"Update system info error: {e}")

class Terminal(BaseApplication):
    """Terminal emulator application."""
    
    def __init__(self, window_manager):
        super().__init__(window_manager)
        self.process = None
        self.text_widget = None
    
    def get_title(self):
        return "Terminal"
    
    def get_width(self):
        return 700
    
    def get_height(self):
        return 500
    
    def build_ui(self):
        """Build terminal UI."""
        try:
            # Terminal output
            text_frame = tk.Frame(self.window, bg="#333333")
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.text_widget = tk.Text(text_frame, bg="black", fg="white",
                                      font=("Monospace", 10),
                                      yscrollcommand=scrollbar.set)
            self.text_widget.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.text_widget.yview)
            
            # Command input
            input_frame = tk.Frame(self.window, bg="#333333")
            input_frame.pack(fill=tk.X, padx=5, pady=5)
            
            tk.Label(input_frame, text="$", fg="white", bg="#333333").pack(side=tk.LEFT)
            
            self.command_var = tk.StringVar()
            command_entry = tk.Entry(input_frame, textvariable=self.command_var,
                                    bg="#555555", fg="white",
                                    font=("Monospace", 10))
            command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            command_entry.bind('<Return>', self.execute_command)
            command_entry.focus()
            
            tk.Button(input_frame, text="Execute", command=self.execute_command,
                     bg="#555555", fg="white").pack(side=tk.RIGHT)
            
            # Welcome message
            self.text_widget.insert(tk.END, "Berke0S Terminal\n")
            self.text_widget.insert(tk.END, f"Current directory: {os.getcwd()}\n")
            self.text_widget.insert(tk.END, "Type 'help' for available commands.\n\n")
            
        except Exception as e:
            logging.error(f"Terminal UI error: {e}")
    
    def execute_command(self, event=None):
        """Execute a command."""
        try:
            command = self.command_var.get().strip()
            if not command:
                return
            
            self.text_widget.insert(tk.END, f"$ {command}\n")
            self.command_var.set("")
            
            # Handle built-in commands
            if command == "help":
                help_text = """Available commands:
help - Show this help
clear - Clear terminal
pwd - Print working directory
ls - List directory contents
cd <dir> - Change directory
cat <file> - Display file contents
echo <text> - Print text
exit - Close terminal
"""
                self.text_widget.insert(tk.END, help_text)
            elif command == "clear":
                self.text_widget.delete(1.0, tk.END)
            elif command == "pwd":
                self.text_widget.insert(tk.END, f"{os.getcwd()}\n")
            elif command.startswith("cd "):
                try:
                    new_dir = command[3:].strip()
                    if new_dir == "~":
                        new_dir = os.path.expanduser("~")
                    os.chdir(new_dir)
                    self.text_widget.insert(tk.END, f"Changed to: {os.getcwd()}\n")
                except Exception as e:
                    self.text_widget.insert(tk.END, f"cd: {str(e)}\n")
            elif command == "ls":
                try:
                    items = os.listdir(".")
                    for item in sorted(items):
                        if os.path.isdir(item):
                            self.text_widget.insert(tk.END, f"{item}/\n")
                        else:
                            self.text_widget.insert(tk.END, f"{item}\n")
                except Exception as e:
                    self.text_widget.insert(tk.END, f"ls: {str(e)}\n")
            elif command.startswith("cat "):
                try:
                    filename = command[4:].strip()
                    with open(filename, 'r') as f:
                        content = f.read()
                    self.text_widget.insert(tk.END, content)
                    if not content.endswith('\n'):
                        self.text_widget.insert(tk.END, '\n')
                except Exception as e:
                    self.text_widget.insert(tk.END, f"cat: {str(e)}\n")
            elif command.startswith("echo "):
                text = command[5:]
                self.text_widget.insert(tk.END, f"{text}\n")
            elif command == "exit":
                self.window.destroy()
                return
            else:
                # Execute external command
                try:
                    result = subprocess.run(command, shell=True, capture_output=True, 
                                          text=True, timeout=10)
                    if result.stdout:
                        self.text_widget.insert(tk.END, result.stdout)
                    if result.stderr:
                        self.text_widget.insert(tk.END, result.stderr)
                    if result.returncode != 0:
                        self.text_widget.insert(tk.END, f"Command exited with code {result.returncode}\n")
                except subprocess.TimeoutExpired:
                    self.text_widget.insert(tk.END, "Command timed out\n")
                except Exception as e:
                    self.text_widget.insert(tk.END, f"Error: {str(e)}\n")
            
            self.text_widget.insert(tk.END, "\n")
            self.text_widget.see(tk.END)
            
        except Exception as e:
            logging.error(f"Execute command error: {e}")

class ControlCenter(BaseApplication):
    """System control center."""
    
    def get_title(self):
        return "Control Center"
    
    def get_width(self):
        return 600
    
    def get_height(self):
        return 500
    
    def build_ui(self):
        """Build control center UI."""
        try:
            notebook = ttk.Notebook(self.window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Display tab
            display_frame = ttk.Frame(notebook)
            notebook.add(display_frame, text="Display")
            
            tk.Label(display_frame, text="Theme:", fg="white", bg="#333333").pack(pady=5)
            theme_var = tk.StringVar(value=self.wm.config.get("theme", "dark"))
            theme_combo = ttk.Combobox(display_frame, textvariable=theme_var,
                                      values=["dark", "light", "high_contrast"],
                                      state="readonly")
            theme_combo.pack(pady=5)
            
            def apply_theme():
                self.wm.config["theme"] = theme_var.get()
                self.wm.apply_theme()
                save_config(self.wm.config)
                self.wm.notifications.send("Control Center", "Theme applied")
            
            tk.Button(display_frame, text="Apply Theme", command=apply_theme,
                     bg="#555555", fg="white").pack(pady=5)
            
            # System tab
            system_frame = ttk.Frame(notebook)
            notebook.add(system_frame, text="System")
            
            tk.Label(system_frame, text="System Actions", fg="white", bg="#333333").pack(pady=10)
            
            tk.Button(system_frame, text="Shutdown", command=self.wm.shutdown,
                     bg="#ff5555", fg="white").pack(pady=5)
            tk.Button(system_frame, text="Reboot", command=self.wm.reboot,
                     bg="#ffaa55", fg="white").pack(pady=5)
            tk.Button(system_frame, text="Log Out", command=self.wm.logout,
                     bg="#5555ff", fg="white").pack(pady=5)
            
            # About tab
            about_frame = ttk.Frame(notebook)
            notebook.add(about_frame, text="About")
            
            about_text = """
Berke0S Desktop Environment

A lightweight desktop environment for Tiny Core Linux
Built with Python and Tkinter

Features:
- File Manager
- Text Editor
- Calculator
- Terminal
- System Information
- And more...

Version: 1.0
"""
            tk.Label(about_frame, text=about_text, fg="white", bg="#333333",
                    justify=tk.LEFT).pack(pady=20)
            
        except Exception as e:
            logging.error(f"Control center UI error: {e}")

class NotesApp(BaseApplication):
    """Simple notes application."""
    
    def __init__(self, window_manager):
        super().__init__(window_manager)
        self.notes_dir = os.path.join(CONFIG_DIR, "notes")
        os.makedirs(self.notes_dir, exist_ok=True)
        self.current_note = None
    
    def get_title(self):
        return "Notes"
    
    def get_width(self):
        return 600
    
    def get_height(self):
        return 400
    
    def build_ui(self):
        """Build notes UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(self.window, bg="#333333")
            toolbar.pack(fill=tk.X, padx=5, pady=2)
            
            tk.Button(toolbar, text="New Note", command=self.new_note,
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Save", command=self.save_note,
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Delete", command=self.delete_note,
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            
            # Main content
            main_frame = tk.Frame(self.window, bg="#333333")
            main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Notes list
            list_frame = tk.Frame(main_frame, bg="#333333")
            list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
            
            tk.Label(list_frame, text="Notes", fg="white", bg="#333333").pack()
            
            self.notes_listbox = tk.Listbox(list_frame, bg="#555555", fg="white", width=20)
            self.notes_listbox.pack(fill=tk.BOTH, expand=True)
            self.notes_listbox.bind('<Button-1>', self.select_note)
            
            # Note editor
            editor_frame = tk.Frame(main_frame, bg="#333333")
            editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Title entry
            tk.Label(editor_frame, text="Title:", fg="white", bg="#333333").pack(anchor=tk.W)
            self.title_var = tk.StringVar()
            title_entry = tk.Entry(editor_frame, textvariable=self.title_var,
                                  bg="#555555", fg="white")
            title_entry.pack(fill=tk.X, pady=(0, 5))
            
            # Content text
            tk.Label(editor_frame, text="Content:", fg="white", bg="#333333").pack(anchor=tk.W)
            
            text_frame = tk.Frame(editor_frame, bg="#333333")
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.content_text = tk.Text(text_frame, bg="#555555", fg="white",
                                       yscrollcommand=scrollbar.set)
            self.content_text.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.content_text.yview)
            
            self.refresh_notes_list()
            
        except Exception as e:
            logging.error(f"Notes UI error: {e}")
    
    def refresh_notes_list(self):
        """Refresh the notes list."""
        try:
            self.notes_listbox.delete(0, tk.END)
            
            for filename in os.listdir(self.notes_dir):
                if filename.endswith('.note'):
                    note_name = filename[:-5]  # Remove .note extension
                    self.notes_listbox.insert(tk.END, note_name)
                    
        except Exception as e:
            logging.error(f"Refresh notes error: {e}")
    
    def new_note(self):
        """Create a new note."""
        try:
            title = simpledialog.askstring("New Note", "Note title:")
            if title:
                self.title_var.set(title)
                self.content_text.delete(1.0, tk.END)
                self.current_note = title
                
        except Exception as e:
            logging.error(f"New note error: {e}")
    
    def save_note(self):
        """Save the current note."""
        try:
            title = self.title_var.get().strip()
            if not title:
                self.wm.notifications.send("Notes", "Please enter a title")
                return
            
            content = self.content_text.get(1.0, tk.END + '-1c')
            
            note_file = os.path.join(self.notes_dir, f"{title}.note")
            with open(note_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.current_note = title
            self.refresh_notes_list()
            self.wm.notifications.send("Notes", f"Saved: {title}")
            
        except Exception as e:
            logging.error(f"Save note error: {e}")
            self.wm.notifications.send("Notes", f"Save failed: {str(e)}")
    
    def select_note(self, event):
        """Select and load a note."""
        try:
            selection = self.notes_listbox.curselection()
            if not selection:
                return
            
            note_name = self.notes_listbox.get(selection[0])
            note_file = os.path.join(self.notes_dir, f"{note_name}.note")
            
            if os.path.exists(note_file):
                with open(note_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.title_var.set(note_name)
                self.content_text.delete(1.0, tk.END)
                self.content_text.insert(1.0, content)
                self.current_note = note_name
                
        except Exception as e:
            logging.error(f"Select note error: {e}")
    
    def delete_note(self):
        """Delete the selected note."""
        try:
            selection = self.notes_listbox.curselection()
            if not selection:
                return
            
            note_name = self.notes_listbox.get(selection[0])
            
            if messagebox.askyesno("Delete Note", f"Delete '{note_name}'?"):
                note_file = os.path.join(self.notes_dir, f"{note_name}.note")
                if os.path.exists(note_file):
                    os.remove(note_file)
                    self.refresh_notes_list()
                    self.title_var.set("")
                    self.content_text.delete(1.0, tk.END)
                    self.current_note = None
                    self.wm.notifications.send("Notes", f"Deleted: {note_name}")
                    
        except Exception as e:
            logging.error(f"Delete note error: {e}")

class TaskManager(BaseApplication):
    """Task manager application."""
    
    def get_title(self):
        return "Task Manager"
    
    def get_width(self):
        return 600
    
    def get_height(self):
        return 400
    
    def build_ui(self):
        """Build task manager UI."""
        try:
            # Toolbar
            toolbar = tk.Frame(self.window, bg="#333333")
            toolbar.pack(fill=tk.X, padx=5, pady=2)
            
            tk.Button(toolbar, text="Refresh", command=self.refresh_processes,
                     bg="#555555", fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="Kill Process", command=self.kill_process,
                     bg="#ff5555", fg="white").pack(side=tk.LEFT, padx=2)
            
            # Process list
            list_frame = tk.Frame(self.window, bg="#333333")
            list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Headers
            headers_frame = tk.Frame(list_frame, bg="#333333")
            headers_frame.pack(fill=tk.X)
            
            tk.Label(headers_frame, text="PID", fg="white", bg="#333333", width=8).pack(side=tk.LEFT)
            tk.Label(headers_frame, text="Name", fg="white", bg="#333333", width=20).pack(side=tk.LEFT)
            tk.Label(headers_frame, text="CPU%", fg="white", bg="#333333", width=8).pack(side=tk.LEFT)
            tk.Label(headers_frame, text="Memory%", fg="white", bg="#333333", width=10).pack(side=tk.LEFT)
            
            # Process listbox
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.process_listbox = tk.Listbox(list_frame, bg="#555555", fg="white",
                                             yscrollcommand=scrollbar.set,
                                             font=("Monospace", 10))
            self.process_listbox.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.process_listbox.yview)
            
            self.refresh_processes()
            
            # Auto-refresh every 5 seconds
            self.auto_refresh()
            
        except Exception as e:
            logging.error(f"Task manager UI error: {e}")
    
    def refresh_processes(self):
        """Refresh the process list."""
        try:
            self.process_listbox.delete(0, tk.END)
            
            if psutil:
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        info = proc.info
                        processes.append((
                            info['pid'],
                            info['name'][:18],  # Truncate long names
                            info['cpu_percent'],
                            info['memory_percent']
                        ))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Sort by CPU usage
                processes.sort(key=lambda x: x[2], reverse=True)
                
                for pid, name, cpu, mem in processes[:50]:  # Show top 50
                    line = f"{pid:>7} {name:<18} {cpu:>6.1f} {mem:>8.1f}"
                    self.process_listbox.insert(tk.END, line)
            else:
                self.process_listbox.insert(tk.END, "psutil not available")
                
        except Exception as e:
            logging.error(f"Refresh processes error: {e}")
    
    def kill_process(self):
        """Kill the selected process."""
        try:
            selection = self.process_listbox.curselection()
            if not selection:
                return
            
            line = self.process_listbox.get(selection[0])
            pid = int(line.split()[0])
            
            if messagebox.askyesno("Kill Process", f"Kill process {pid}?"):
                try:
                    if psutil:
                        proc = psutil.Process(pid)
                        proc.terminate()
                    else:
                        subprocess.run(["kill", str(pid)], check=True)
                    
                    self.wm.notifications.send("Task Manager", f"Killed process {pid}")
                    self.refresh_processes()
                    
                except Exception as e:
                    self.wm.notifications.send("Task Manager", f"Failed to kill process: {str(e)}")
                    
        except Exception as e:
            logging.error(f"Kill process error: {e}")
    
    def auto_refresh(self):
        """Auto-refresh the process list."""
        try:
            if self.window and self.window.winfo_exists():
                self.refresh_processes()
                self.window.after(5000, self.auto_refresh)  # Refresh every 5 seconds
        except Exception as e:
            logging.error(f"Auto refresh error: {e}")

def main():
    """Main function."""
    try:
        # Install packages if needed
        if len(sys.argv) > 1 and sys.argv[1] == "--install":
            print("Installing packages...")
            install_packages()
            print("Installation complete!")
            return
        
        # Initialize window manager
        wm = WindowManager()
        
        # Show login screen
        wm.show_login()
        
        # Start main loop
        wm.root.mainloop()
        
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
    finally:
        try:
            if 'wm' in locals():
                wm.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()

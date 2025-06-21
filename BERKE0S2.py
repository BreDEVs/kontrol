#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERKE0S - Advanced Desktop Operating System
Created by: Berke Oruç
Version: 2.0
License: MIT
"""

import os
import sys
import time
import json
import subprocess
import threading
import signal
import psutil
import socket
import hashlib
import re
import shutil
import getpass
import datetime
import logging
import queue
import math
import uuid
import base64
import zipfile
import tarfile
import glob
import stat
import calendar
import random
import sqlite3
from pathlib import Path
from urllib.parse import quote, unquote
from io import BytesIO
import tempfile
import configparser
import mimetypes

# Display ve GUI imports - hata yakalama ile
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, simpledialog, colorchooser
    from tkinter import font as tkFont
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("GUI libraries not available, running in console mode")

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available, using basic graphics")

# Display environment setup
def setup_display():
    """Setup display environment for GUI"""
    try:
        # X server kontrolü
        if 'DISPLAY' not in os.environ:
            print("Setting up display environment...")
            
            # Xvfb (Virtual framebuffer) başlat
            try:
                subprocess.run(['which', 'Xvfb'], check=True, capture_output=True)
                subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24'], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.environ['DISPLAY'] = ':99'
                time.sleep(2)
                print("Virtual display started on :99")
            except:
                # Fiziksel display dene
                for display in [':0', ':1', ':10']:
                    try:
                        os.environ['DISPLAY'] = display
                        subprocess.run(['xset', 'q'], check=True, capture_output=True)
                        print(f"Using display {display}")
                        break
                    except:
                        continue
                else:
                    # Console mode
                    print("No display available, starting in console mode")
                    return False
        
        # X server test
        try:
            subprocess.run(['xset', 'q'], check=True, capture_output=True)
            return True
        except:
            print("Display test failed, trying alternative methods...")
            
            # Startx dene
            try:
                subprocess.Popen(['startx'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(5)
                return True
            except:
                pass
                
            # Xinit dene
            try:
                subprocess.Popen(['xinit'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(5)
                return True
            except:
                pass
                
            return False
            
    except Exception as e:
        print(f"Display setup error: {e}")
        return False

# Console mode fallback
class ConsoleMode:
    """Console mode interface when GUI is not available"""
    
    def __init__(self):
        self.running = True
        self.current_user = None
        
    def start(self):
        """Start console interface"""
        self.show_banner()
        self.login()
        self.main_menu()
        
    def show_banner(self):
        """Show Berke0S banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                          BERKE0S                             ║
║                    Advanced Desktop OS                       ║
║                   Created by: Berke Oruç                     ║
║                        Version 2.0                          ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def login(self):
        """Console login"""
        while True:
            print("\n=== BERKE0S LOGIN ===")
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            
            if self.authenticate(username, password):
                self.current_user = username
                print(f"Welcome, {username}!")
                break
            else:
                print("Invalid credentials!")
                
    def authenticate(self, username, password):
        """Simple authentication"""
        # Default user for demo
        return username == "berke" and password == "berke0s"
        
    def main_menu(self):
        """Main console menu"""
        while self.running:
            print(f"\n=== BERKE0S CONSOLE - User: {self.current_user} ===")
            print("1. File Manager")
            print("2. System Info")
            print("3. Process Manager")
            print("4. Network Tools")
            print("5. Text Editor")
            print("6. Calculator")
            print("7. System Settings")
            print("8. Install GUI Mode")
            print("9. Logout")
            print("0. Shutdown")
            
            choice = input("\nSelect option: ")
            
            if choice == "1":
                self.file_manager()
            elif choice == "2":
                self.system_info()
            elif choice == "3":
                self.process_manager()
            elif choice == "4":
                self.network_tools()
            elif choice == "5":
                self.text_editor()
            elif choice == "6":
                self.calculator()
            elif choice == "7":
                self.system_settings()
            elif choice == "8":
                self.install_gui()
            elif choice == "9":
                self.logout()
            elif choice == "0":
                self.shutdown()
            else:
                print("Invalid option!")
                
    def file_manager(self):
        """Console file manager"""
        current_path = os.getcwd()
        
        while True:
            print(f"\n=== FILE MANAGER - {current_path} ===")
            try:
                items = os.listdir(current_path)
                for i, item in enumerate(items, 1):
                    path = os.path.join(current_path, item)
                    if os.path.isdir(path):
                        print(f"{i:2d}. [DIR]  {item}")
                    else:
                        size = os.path.getsize(path)
                        print(f"{i:2d}. [FILE] {item} ({size} bytes)")
            except PermissionError:
                print("Permission denied!")
                
            print("\nCommands: cd <dir>, up, home, quit")
            cmd = input("Command: ").strip()
            
            if cmd == "quit":
                break
            elif cmd == "up":
                current_path = os.path.dirname(current_path)
            elif cmd == "home":
                current_path = os.path.expanduser("~")
            elif cmd.startswith("cd "):
                new_path = cmd[3:].strip()
                if new_path.isdigit():
                    idx = int(new_path) - 1
                    if 0 <= idx < len(items):
                        new_path = os.path.join(current_path, items[idx])
                        if os.path.isdir(new_path):
                            current_path = new_path
                        else:
                            print("Not a directory!")
                    else:
                        print("Invalid index!")
                else:
                    full_path = os.path.join(current_path, new_path)
                    if os.path.isdir(full_path):
                        current_path = full_path
                    else:
                        print("Directory not found!")
                        
    def system_info(self):
        """Show system information"""
        print("\n=== SYSTEM INFORMATION ===")
        print(f"OS: Berke0S v2.0")
        print(f"Kernel: {os.uname().sysname} {os.uname().release}")
        print(f"Architecture: {os.uname().machine}")
        print(f"Hostname: {socket.gethostname()}")
        print(f"Uptime: {self.get_uptime()}")
        
        # Memory info
        try:
            mem = psutil.virtual_memory()
            print(f"Memory: {mem.used//1024//1024}MB / {mem.total//1024//1024}MB")
            print(f"Memory Usage: {mem.percent}%")
        except:
            print("Memory info not available")
            
        # Disk info
        try:
            disk = psutil.disk_usage('/')
            print(f"Disk: {disk.used//1024//1024//1024}GB / {disk.total//1024//1024//1024}GB")
            print(f"Disk Usage: {disk.percent}%")
        except:
            print("Disk info not available")
            
        input("\nPress Enter to continue...")
        
    def get_uptime(self):
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_hours = int(uptime_seconds // 3600)
                uptime_minutes = int((uptime_seconds % 3600) // 60)
                return f"{uptime_hours}h {uptime_minutes}m"
        except:
            return "Unknown"
            
    def process_manager(self):
        """Simple process manager"""
        print("\n=== PROCESS MANAGER ===")
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except:
                    continue
                    
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            print(f"{'PID':>6} {'NAME':<20} {'CPU%':>6} {'MEM%':>6}")
            print("-" * 40)
            
            for proc in processes[:20]:  # Top 20
                print(f"{proc['pid']:>6} {proc['name']:<20} {proc['cpu_percent']:>6.1f} {proc['memory_percent']:>6.1f}")
                
        except Exception as e:
            print(f"Error: {e}")
            
        input("\nPress Enter to continue...")
        
    def network_tools(self):
        """Network tools"""
        while True:
            print("\n=== NETWORK TOOLS ===")
            print("1. Show interfaces")
            print("2. Ping test")
            print("3. Port scan")
            print("4. Back")
            
            choice = input("Select: ")
            
            if choice == "1":
                self.show_interfaces()
            elif choice == "2":
                self.ping_test()
            elif choice == "3":
                self.port_scan()
            elif choice == "4":
                break
                
    def show_interfaces(self):
        """Show network interfaces"""
        try:
            interfaces = psutil.net_if_addrs()
            for name, addrs in interfaces.items():
                print(f"\n{name}:")
                for addr in addrs:
                    print(f"  {addr.family.name}: {addr.address}")
        except Exception as e:
            print(f"Error: {e}")
        input("\nPress Enter to continue...")
        
    def ping_test(self):
        """Ping test"""
        host = input("Enter host to ping: ")
        try:
            result = subprocess.run(['ping', '-c', '4', host], 
                                  capture_output=True, text=True)
            print(result.stdout)
        except Exception as e:
            print(f"Error: {e}")
        input("\nPress Enter to continue...")
        
    def port_scan(self):
        """Simple port scanner"""
        host = input("Enter host: ")
        port = input("Enter port: ")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, int(port)))
            if result == 0:
                print(f"Port {port} is open on {host}")
            else:
                print(f"Port {port} is closed on {host}")
            sock.close()
        except Exception as e:
            print(f"Error: {e}")
        input("\nPress Enter to continue...")
        
    def text_editor(self):
        """Simple text editor"""
        filename = input("Enter filename (or press Enter for new): ")
        
        if filename and os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read()
            print(f"\nCurrent content of {filename}:")
            print("-" * 40)
            print(content)
            print("-" * 40)
        else:
            content = ""
            
        print("\nEnter new content (type 'EOF' on a new line to finish):")
        lines = []
        while True:
            line = input()
            if line == "EOF":
                break
            lines.append(line)
            
        new_content = "\n".join(lines)
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(new_content)
                print(f"File saved: {filename}")
            except Exception as e:
                print(f"Error saving file: {e}")
        else:
            print("Content not saved (no filename provided)")
            
    def calculator(self):
        """Simple calculator"""
        print("\n=== CALCULATOR ===")
        print("Enter expressions (type 'quit' to exit)")
        print("Supported: +, -, *, /, **, sqrt(), sin(), cos(), tan()")
        
        while True:
            expr = input("calc> ")
            if expr.lower() == 'quit':
                break
                
            try:
                # Safe evaluation
                allowed_names = {
                    k: v for k, v in math.__dict__.items() if not k.startswith("__")
                }
                allowed_names.update({"abs": abs, "round": round})
                
                result = eval(expr, {"__builtins__": {}}, allowed_names)
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error: {e}")
                
    def system_settings(self):
        """System settings"""
        while True:
            print("\n=== SYSTEM SETTINGS ===")
            print("1. Change password")
            print("2. Set timezone")
            print("3. Configure network")
            print("4. View logs")
            print("5. Back")
            
            choice = input("Select: ")
            
            if choice == "1":
                self.change_password()
            elif choice == "2":
                self.set_timezone()
            elif choice == "3":
                self.configure_network()
            elif choice == "4":
                self.view_logs()
            elif choice == "5":
                break
                
    def change_password(self):
        """Change user password"""
        current = getpass.getpass("Current password: ")
        new_pass = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm password: ")
        
        if new_pass == confirm:
            print("Password changed successfully!")
        else:
            print("Passwords don't match!")
            
    def set_timezone(self):
        """Set system timezone"""
        print("Available timezones:")
        timezones = ["UTC", "Europe/Istanbul", "America/New_York", "Asia/Tokyo"]
        for i, tz in enumerate(timezones, 1):
            print(f"{i}. {tz}")
            
        choice = input("Select timezone: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(timezones):
                print(f"Timezone set to {timezones[idx]}")
            else:
                print("Invalid selection!")
        except:
            print("Invalid input!")
            
    def configure_network(self):
        """Configure network"""
        print("\n=== NETWORK CONFIGURATION ===")
        print("1. Configure WiFi")
        print("2. Configure Ethernet")
        print("3. View current config")
        
        choice = input("Select: ")
        
        if choice == "1":
            ssid = input("WiFi SSID: ")
            password = getpass.getpass("WiFi Password: ")
            print(f"Connecting to {ssid}...")
            # Simulate connection
            time.sleep(2)
            print("Connected successfully!")
        elif choice == "2":
            print("Configuring Ethernet...")
            time.sleep(1)
            print("Ethernet configured!")
        elif choice == "3":
            print("Current network configuration:")
            self.show_interfaces()
            
    def view_logs(self):
        """View system logs"""
        print("\n=== SYSTEM LOGS ===")
        log_files = ["/var/log/messages", "/var/log/syslog", "/tmp/berke0s.log"]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n--- {log_file} ---")
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-10:]:  # Last 10 lines
                            print(line.strip())
                except:
                    print("Cannot read log file")
                    
        input("\nPress Enter to continue...")
        
    def install_gui(self):
        """Install GUI components"""
        print("\n=== GUI INSTALLATION ===")
        print("Installing GUI components...")
        
        packages = ["python3-tk", "python3-pil", "xorg", "xinit"]
        
        for pkg in packages:
            print(f"Installing {pkg}...")
            time.sleep(1)
            # Simulate installation
            
        print("GUI installation completed!")
        print("Please restart Berke0S to use GUI mode.")
        input("Press Enter to continue...")
        
    def logout(self):
        """Logout"""
        print("Logging out...")
        self.current_user = None
        self.login()
        
    def shutdown(self):
        """Shutdown system"""
        confirm = input("Are you sure you want to shutdown? (y/N): ")
        if confirm.lower() == 'y':
            print("Shutting down Berke0S...")
            self.running = False
            sys.exit(0)

# Configuration and constants
CONFIG_DIR = os.path.expanduser("~/.berke0s")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
LOG_FILE = os.path.join(CONFIG_DIR, "berke0s.log")
THEMES_DIR = os.path.join(CONFIG_DIR, "themes")
PLUGINS_DIR = os.path.join(CONFIG_DIR, "plugins")
WALLPAPERS_DIR = os.path.join(CONFIG_DIR, "wallpapers")
SOUNDS_DIR = os.path.join(CONFIG_DIR, "sounds")
DATABASE_FILE = os.path.join(CONFIG_DIR, "berke0s.db")

# Ensure directories exist
for directory in [CONFIG_DIR, THEMES_DIR, PLUGINS_DIR, WALLPAPERS_DIR, SOUNDS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Default configuration
DEFAULT_CONFIG = {
    "version": "2.0",
    "first_run": True,
    "language": "en",
    "theme": "berke_dark",
    "wallpaper": "",
    "taskbar_position": "bottom",
    "taskbar_autohide": False,
    "animations_enabled": True,
    "transparency_enabled": True,
    "sound_enabled": True,
    "notifications_enabled": True,
    "auto_save": True,
    "session_timeout": 3600,
    "screen_saver_timeout": 600,
    "power_management": True,
    "window_effects": True,
    "font_family": "Ubuntu",
    "font_size": 10,
    "icon_theme": "berke_icons",
    "cursor_theme": "berke_cursor",
    "desktop_effects": True,
    "virtual_desktops": 4,
    "hot_corners": True,
    "dock_enabled": False,
    "widgets_enabled": True,
    "search_enabled": True,
    "recent_files_count": 10,
    "backup_enabled": True,
    "security_level": "medium",
    "network_monitoring": True,
    "system_monitoring": True,
    "developer_mode": False,
    "debug_mode": False
}

# Language support
LANGUAGES = {
    "en": {
        "welcome": "Welcome to Berke0S",
        "login": "Login",
        "username": "Username",
        "password": "Password",
        "logout": "Logout",
        "shutdown": "Shutdown",
        "restart": "Restart",
        "settings": "Settings",
        "applications": "Applications",
        "file_manager": "File Manager",
        "text_editor": "Text Editor",
        "calculator": "Calculator",
        "system_info": "System Information",
        "task_manager": "Task Manager",
        "terminal": "Terminal",
        "web_browser": "Web Browser",
        "media_player": "Media Player",
        "image_viewer": "Image Viewer",
        "code_editor": "Code Editor",
        "music_player": "Music Player",
        "video_player": "Video Player",
        "email_client": "Email Client",
        "calendar": "Calendar",
        "notes": "Notes",
        "clock": "Clock",
        "weather": "Weather",
        "games": "Games",
        "utilities": "Utilities",
        "preferences": "Preferences",
        "about": "About",
        "help": "Help",
        "search": "Search",
        "new": "New",
        "open": "Open",
        "save": "Save",
        "save_as": "Save As",
        "close": "Close",
        "exit": "Exit",
        "cut": "Cut",
        "copy": "Copy",
        "paste": "Paste",
        "delete": "Delete",
        "select_all": "Select All",
        "undo": "Undo",
        "redo": "Redo",
        "find": "Find",
        "replace": "Replace",
        "print": "Print",
        "properties": "Properties",
        "ok": "OK",
        "cancel": "Cancel",
        "yes": "Yes",
        "no": "No",
        "error": "Error",
        "warning": "Warning",
        "information": "Information",
        "question": "Question"
    },
    "tr": {
        "welcome": "Berke0S'a Hoş Geldiniz",
        "login": "Giriş",
        "username": "Kullanıcı Adı",
        "password": "Şifre",
        "logout": "Çıkış",
        "shutdown": "Kapat",
        "restart": "Yeniden Başlat",
        "settings": "Ayarlar",
        "applications": "Uygulamalar",
        "file_manager": "Dosya Yöneticisi",
        "text_editor": "Metin Editörü",
        "calculator": "Hesap Makinesi",
        "system_info": "Sistem Bilgisi",
        "task_manager": "Görev Yöneticisi",
        "terminal": "Terminal",
        "web_browser": "Web Tarayıcı",
        "media_player": "Medya Oynatıcı",
        "image_viewer": "Resim Görüntüleyici",
        "code_editor": "Kod Editörü",
        "music_player": "Müzik Çalar",
        "video_player": "Video Oynatıcı",
        "email_client": "E-posta İstemcisi",
        "calendar": "Takvim",
        "notes": "Notlar",
        "clock": "Saat",
        "weather": "Hava Durumu",
        "games": "Oyunlar",
        "utilities": "Araçlar",
        "preferences": "Tercihler",
        "about": "Hakkında",
        "help": "Yardım",
        "search": "Ara",
        "new": "Yeni",
        "open": "Aç",
        "save": "Kaydet",
        "save_as": "Farklı Kaydet",
        "close": "Kapat",
        "exit": "Çık",
        "cut": "Kes",
        "copy": "Kopyala",
        "paste": "Yapıştır",
        "delete": "Sil",
        "select_all": "Tümünü Seç",
        "undo": "Geri Al",
        "redo": "Yinele",
        "find": "Bul",
        "replace": "Değiştir",
        "print": "Yazdır",
        "properties": "Özellikler",
        "ok": "Tamam",
        "cancel": "İptal",
        "yes": "Evet",
        "no": "Hayır",
        "error": "Hata",
        "warning": "Uyarı",
        "information": "Bilgi",
        "question": "Soru"
    }
}

# Theme definitions
THEMES = {
    "berke_dark": {
        "name": "Berke Dark",
        "bg_primary": "#1a1a1a",
        "bg_secondary": "#2d2d2d",
        "bg_tertiary": "#404040",
        "fg_primary": "#ffffff",
        "fg_secondary": "#cccccc",
        "fg_tertiary": "#999999",
        "accent_primary": "#0078d4",
        "accent_secondary": "#106ebe",
        "success": "#107c10",
        "warning": "#ff8c00",
        "error": "#d13438",
        "info": "#0078d4",
        "border": "#555555",
        "shadow": "#000000",
        "gradient_start": "#1a1a1a",
        "gradient_end": "#2d2d2d",
        "transparency": 0.95
    },
    "berke_light": {
        "name": "Berke Light",
        "bg_primary": "#ffffff",
        "bg_secondary": "#f5f5f5",
        "bg_tertiary": "#e0e0e0",
        "fg_primary": "#000000",
        "fg_secondary": "#333333",
        "fg_tertiary": "#666666",
        "accent_primary": "#0078d4",
        "accent_secondary": "#106ebe",
        "success": "#107c10",
        "warning": "#ff8c00",
        "error": "#d13438",
        "info": "#0078d4",
        "border": "#cccccc",
        "shadow": "#00000020",
        "gradient_start": "#ffffff",
        "gradient_end": "#f5f5f5",
        "transparency": 0.98
    },
    "berke_ocean": {
        "name": "Berke Ocean",
        "bg_primary": "#0f1419",
        "bg_secondary": "#1e2328",
        "bg_tertiary": "#2d3748",
        "fg_primary": "#e2e8f0",
        "fg_secondary": "#cbd5e0",
        "fg_tertiary": "#a0aec0",
        "accent_primary": "#4299e1",
        "accent_secondary": "#3182ce",
        "success": "#38a169",
        "warning": "#ed8936",
        "error": "#e53e3e",
        "info": "#4299e1",
        "border": "#4a5568",
        "shadow": "#000000",
        "gradient_start": "#0f1419",
        "gradient_end": "#1e2328",
        "transparency": 0.92
    }
}

class DatabaseManager:
    """Database manager for Berke0S"""
    
    def __init__(self):
        self.db_path = DATABASE_FILE
        self.init_database()
        
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    full_name TEXT,
                    avatar_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_admin BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Applications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    icon_path TEXT,
                    executable_path TEXT,
                    category TEXT,
                    version TEXT,
                    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_system_app BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT UNIQUE NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    mime_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP,
                    accessed_at TIMESTAMP,
                    owner_id INTEGER,
                    permissions TEXT,
                    is_hidden BOOLEAN DEFAULT 0,
                    is_system_file BOOLEAN DEFAULT 0,
                    FOREIGN KEY (owner_id) REFERENCES users (id)
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'string',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, setting_key)
                )
            ''')
            
            # Logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    log_level TEXT DEFAULT 'INFO',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Database initialized successfully")
            
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            
    def create_user(self, username, password, email=None, full_name=None, is_admin=False):
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, full_name, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, email, full_name, is_admin))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logging.info(f"User created: {username}")
            return user_id
            
        except sqlite3.IntegrityError:
            logging.warning(f"User already exists: {username}")
            return None
        except Exception as e:
            logging.error(f"User creation error: {e}")
            return None
            
    def authenticate_user(self, username, password):
        """Authenticate user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                SELECT id, username, is_admin, is_active
                FROM users
                WHERE username = ? AND password_hash = ? AND is_active = 1
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user[0],))
                conn.commit()
                
                logging.info(f"User authenticated: {username}")
                
            conn.close()
            return user
            
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None
            
    def log_action(self, user_id, action, details=None, ip_address=None, log_level="INFO"):
        """Log user action"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO logs (user_id, action, details, ip_address, log_level)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, action, details, ip_address, log_level))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Logging error: {e}")

class ConfigManager:
    """Configuration manager for Berke0S"""
    
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"Config load error: {e}")
            return DEFAULT_CONFIG.copy()
            
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logging.info("Configuration saved")
        except Exception as e:
            logging.error(f"Config save error: {e}")
            
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
        
    def get_theme(self):
        """Get current theme"""
        theme_name = self.get("theme", "berke_dark")
        return THEMES.get(theme_name, THEMES["berke_dark"])

class NotificationManager:
    """Notification system for Berke0S"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.notifications = []
        self.max_notifications = 5
        
    def show(self, title, message, notification_type="info", duration=5000):
        """Show notification"""
        try:
            if not GUI_AVAILABLE or not self.parent:
                print(f"[{notification_type.upper()}] {title}: {message}")
                return
                
            notification = NotificationWindow(self.parent, title, message, notification_type, duration)
            self.notifications.append(notification)
            
            # Remove old notifications
            if len(self.notifications) > self.max_notifications:
                old_notification = self.notifications.pop(0)
                old_notification.destroy()
                
            logging.info(f"Notification: {title} - {message}")
            
        except Exception as e:
            logging.error(f"Notification error: {e}")
            print(f"[{notification_type.upper()}] {title}: {message}")

class NotificationWindow:
    """Individual notification window"""
    
    def __init__(self, parent, title, message, notification_type="info", duration=5000):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        
        # Configure window
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        # Get theme colors
        config_manager = ConfigManager()
        theme = config_manager.get_theme()
        
        # Set colors based on type
        colors = {
            "info": theme["info"],
            "success": theme["success"],
            "warning": theme["warning"],
            "error": theme["error"]
        }
        
        bg_color = colors.get(notification_type, theme["info"])
        
        # Create frame
        frame = tk.Frame(self.window, bg=bg_color, padx=10, pady=8)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(frame, text=title, font=("Ubuntu", 10, "bold"),
                              bg=bg_color, fg="white")
        title_label.pack(anchor="w")
        
        # Message
        message_label = tk.Label(frame, text=message, font=("Ubuntu", 9),
                                bg=bg_color, fg="white", wraplength=250)
        message_label.pack(anchor="w")
        
        # Position window
        self.position_window()
        
        # Show with animation
        self.show_animation()
        
        # Auto-hide
        if duration > 0:
            self.window.after(duration, self.hide_animation)
            
        # Click to close
        for widget in [self.window, frame, title_label, message_label]:
            widget.bind("<Button-1>", lambda e: self.hide_animation())
            
    def position_window(self):
        """Position notification window"""
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        x = screen_width - width - 20
        y = 50
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
    def show_animation(self):
        """Show notification with animation"""
        self.window.deiconify()
        self.window.attributes('-alpha', 0.0)
        
        def fade_in(alpha=0.0):
            if alpha < 1.0:
                alpha += 0.1
                self.window.attributes('-alpha', alpha)
                self.window.after(50, lambda: fade_in(alpha))
                
        fade_in()
        
    def hide_animation(self):
        """Hide notification with animation"""
        def fade_out(alpha=1.0):
            if alpha > 0.0:
                alpha -= 0.1
                self.window.attributes('-alpha', alpha)
                self.window.after(50, lambda: fade_out(alpha))
            else:
                self.destroy()
                
        fade_out()
        
    def destroy(self):
        """Destroy notification window"""
        try:
            self.window.destroy()
        except:
            pass

class SoundManager:
    """Sound management for Berke0S"""
    
    def __init__(self):
        self.sounds_enabled = True
        self.volume = 0.7
        
    def play_sound(self, sound_name):
        """Play system sound"""
        if not self.sounds_enabled:
            return
            
        try:
            sound_file = os.path.join(SOUNDS_DIR, f"{sound_name}.wav")
            if os.path.exists(sound_file):
                # Use aplay or paplay for sound
                subprocess.run(['aplay', sound_file], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
            
    def play_startup_sound(self):
        """Play startup sound"""
        self.play_sound("startup")
        
    def play_shutdown_sound(self):
        """Play shutdown sound"""
        self.play_sound("shutdown")
        
    def play_notification_sound(self):
        """Play notification sound"""
        self.play_sound("notification")
        
    def play_error_sound(self):
        """Play error sound"""
        self.play_sound("error")

class LanguageManager:
    """Language management for Berke0S"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.current_language = self.config_manager.get("language", "en")
        
    def get_text(self, key):
        """Get localized text"""
        return LANGUAGES.get(self.current_language, LANGUAGES["en"]).get(key, key)
        
    def set_language(self, language):
        """Set current language"""
        if language in LANGUAGES:
            self.current_language = language
            self.config_manager.set("language", language)
            
    def get_available_languages(self):
        """Get available languages"""
        return list(LANGUAGES.keys())

class InstallationWizard:
    """Installation wizard for first-time setup"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.lang_manager = LanguageManager()
        self.current_step = 0
        self.total_steps = 8
        self.installation_data = {}
        
        if GUI_AVAILABLE and parent:
            self.create_gui()
        else:
            self.console_installation()
            
    def create_gui(self):
        """Create GUI installation wizard"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Berke0S Installation Wizard")
        self.window.geometry("800x600")
        self.window.resizable(False, False)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
        
        # Main frame
        self.main_frame = tk.Frame(self.window, bg="#1a1a1a")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header()
        
        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg="#1a1a1a")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        # Navigation
        self.create_navigation()
        
        # Start with welcome step
        self.show_step()
        
    def create_header(self):
        """Create installation header"""
        header_frame = tk.Frame(self.main_frame, bg="#0078d4", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Logo and title
        title_frame = tk.Frame(header_frame, bg="#0078d4")
        title_frame.pack(expand=True, fill=tk.BOTH)
        
        tk.Label(title_frame, text="BERKE0S", font=("Ubuntu", 24, "bold"),
                bg="#0078d4", fg="white").pack(pady=10)
        
        tk.Label(title_frame, text="Advanced Desktop Operating System",
                font=("Ubuntu", 12), bg="#0078d4", fg="#cccccc").pack()
        
        # Progress bar
        self.progress_frame = tk.Frame(self.main_frame, bg="#2d2d2d", height=40)
        self.progress_frame.pack(fill=tk.X)
        self.progress_frame.pack_propagate(False)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var,
                                          maximum=self.total_steps, length=700)
        self.progress_bar.pack(pady=10)
        
    def create_navigation(self):
        """Create navigation buttons"""
        nav_frame = tk.Frame(self.main_frame, bg="#1a1a1a", height=60)
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM)
        nav_frame.pack_propagate(False)
        
        button_frame = tk.Frame(nav_frame, bg="#1a1a1a")
        button_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        self.back_button = tk.Button(button_frame, text="Back", font=("Ubuntu", 10),
                                   bg="#404040", fg="white", padx=20, pady=8,
                                   command=self.previous_step, state=tk.DISABLED)
        self.back_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(button_frame, text="Next", font=("Ubuntu", 10),
                                   bg="#0078d4", fg="white", padx=20, pady=8,
                                   command=self.next_step)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = tk.Button(button_frame, text="Cancel", font=("Ubuntu", 10),
                                     bg="#d13438", fg="white", padx=20, pady=8,
                                     command=self.cancel_installation)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
    def show_step(self):
        """Show current installation step"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Update progress
        self.progress_var.set(self.current_step)
        
        # Show appropriate step
        steps = [
            self.step_welcome,
            self.step_language,
            self.step_license,
            self.step_disk_setup,
            self.step_network,
            self.step_user_account,
            self.step_customization,
            self.step_installation
        ]
        
        if 0 <= self.current_step < len(steps):
            steps[self.current_step]()
            
        # Update navigation
        self.back_button.config(state=tk.NORMAL if self.current_step > 0 else tk.DISABLED)
        
        if self.current_step == len(steps) - 1:
            self.next_button.config(text="Install", bg="#107c10")
        elif self.current_step == len(steps):
            self.next_button.config(text="Finish", bg="#107c10")
        else:
            self.next_button.config(text="Next", bg="#0078d4")
            
    def step_welcome(self):
        """Welcome step"""
        tk.Label(self.content_frame, text="Welcome to Berke0S Installation",
                font=("Ubuntu", 18, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        
        welcome_text = """
Welcome to Berke0S, an advanced desktop operating system designed for modern computing.

Created by: Berke Oruç
Version: 2.0

Berke0S Features:
• Modern and intuitive desktop environment
• Advanced file management system
• Built-in development tools
• Comprehensive multimedia support
• Secure user management
• Customizable themes and layouts
• Extensive application suite
• Network and system monitoring tools

This installation wizard will guide you through the setup process.
Click Next to continue.
        """
        
        text_widget = tk.Text(self.content_frame, font=("Ubuntu", 11), bg="#2d2d2d",
                             fg="#cccccc", wrap=tk.WORD, height=15, width=70)
        text_widget.pack(pady=20)
        text_widget.insert(tk.END, welcome_text.strip())
        text_widget.config(state=tk.DISABLED)
        
    def step_language(self):
        """Language selection step"""
        tk.Label(self.content_frame, text="Select Language / Dil Seçin",
                font=("Ubuntu", 16, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        
        lang_frame = tk.Frame(self.content_frame, bg="#1a1a1a")
        lang_frame.pack(pady=40)
        
        self.language_var = tk.StringVar(value="en")
        
        languages = [
            ("en", "English"),
            ("tr", "Türkçe")
        ]
        
        for code, name in languages:
            rb = tk.Radiobutton(lang_frame, text=name, variable=self.language_var,
                               value=code, font=("Ubuntu", 12), bg="#1a1a1a",
                               fg="white", selectcolor="#0078d4", pady=10)
            rb.pack(anchor=tk.W, pady=5)
            
    def step_license(self):
        """License agreement step"""
        tk.Label(self.content_frame, text="License Agreement",
                font=("Ubuntu", 16, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        
        license_text = """
BERKE0S END USER LICENSE AGREEMENT

Copyright (c) 2024 Berke Oruç

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

By installing Berke0S, you agree to the terms and conditions of this license.
        """
        
        text_widget = tk.Text(self.content_frame, font=("Ubuntu", 10), bg="#2d2d2d",
                             fg="#cccccc", wrap=tk.WORD, height=12, width=80)
        text_widget.pack(pady=10)
        text_widget.insert(tk.END, license_text.strip())
        text_widget.config(state=tk.DISABLED)
        
        self.license_var = tk.BooleanVar()
        tk.Checkbutton(self.content_frame, text="I accept the license agreement",
                      variable=self.license_var, font=("Ubuntu", 11),
                      bg="#1a1a1a", fg="white", selectcolor="#0078d4").pack(pady=20)
                      
    def step_disk_setup(self):
        """Disk setup step"""
        tk.Label(self.content_frame, text="Disk Setup",
                font=("Ubuntu", 16, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        
        tk.Label(self.content_frame, text="Select installation location:",
                font=("Ubuntu", 12), bg="#1a1a1a", fg="#cccccc").pack(pady=10)
        
        # Disk selection
        disk_frame = tk.Frame(self.content_frame, bg="#2d2d2d", relief=tk.RAISED, bd=1)
        disk_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.disk_var = tk.StringVar(value="auto")
        
        tk.Radiobutton(disk_frame, text="Automatic partitioning (Recommended)",
                      variable=self.disk_var, value="auto", font=("Ubuntu", 11),
                      bg="#2d2d2d", fg="white", selectcolor="#0078d4").pack(anchor=tk.W, pady=5, padx=10)
        
        tk.Radiobutton(disk_frame, text="Manual partitioning (Advanced)",
                      variable=self.disk_var, value="manual", font=("Ubuntu", 11),
                      bg="#2d2d2d", fg="white", selectcolor="#0078d4").pack(anchor=tk.W, pady=5, padx=10)
        
        # Disk space info
        info_frame = tk.Frame(self.content_frame, bg="#1a1a1a")
        info_frame.pack(pady=20)
        
        try:
            disk_usage = psutil.disk_usage('/')
            total_gb = disk_usage.total // (1024**3)
            free_gb = disk_usage.free // (1024**3)
            
            tk.Label(info_frame, text=f"Available disk space: {free_gb} GB / {total_gb} GB",
                    font=("Ubuntu", 11), bg="#1a1a1a", fg="#cccccc").pack()
            tk.Label(info_frame, text="Minimum required: 2 GB",
                    font=("Ubuntu", 10), bg="#1a1a1a", fg="#999999").pack()
        except:
            tk.Label(info_frame, text="Disk information not available",
                    font=("Ubuntu", 11), bg="#1a1a1a", fg="#cccccc").pack()
                    
    def step_network(self):
        """Network configuration step"""
        tk.Label(self.content_frame, text="Network Configuration",
                font=("Ubuntu", 16, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        
        # Network type selection
        net_frame = tk.Frame(self.content_frame, bg="#1a1a1a")
        net_frame.pack(pady=20)
        
        self.network_var = tk.StringVar(value="dhcp")
        
        tk.Radiobutton(net_frame, text="Automatic (DHCP) - Recommended",
                      variable=self.network_var, value="dhcp", font=("Ubuntu", 12),
                      bg="#1a1a1a", fg="white", selectcolor="#0078d4").pack(anchor=tk.W, pady=5)
        
        tk.Radiobutton(net_frame, text="Manual configuration",
                      variable=self.network_var, value="manual", font=("Ubuntu", 12),
                      bg="#1a1a1a", fg="white", selectcolor="#0078d4").pack(anchor=tk.W, pady=5)
        
        # WiFi configuration
        wifi_frame = tk.LabelFrame(self.content_frame, text="WiFi Configuration",
                                  font=("Ubuntu", 12), bg="#2d2d2d", fg="white")
        wifi_frame.pack(fill=tk.X, pady=20, padx=20)
        
        tk.Label(wifi_frame, text="SSID:", font=("Ubuntu", 11),
                bg="#2d2d2d", fg="white").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.wifi_ssid_var = tk.StringVar()
        tk.Entry(wifi_frame, textvariable=self.wifi_ssid_var, font=("Ubuntu", 11),
                bg="#404040", fg="white", width=30).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(wifi_frame, text="Password:", font=("Ubuntu", 11),
                bg="#2d2d2d", fg="white").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.wifi_password_var = tk.StringVar()
        tk.Entry(wifi_frame, textvariable=self.wifi_password_var, font=("Ubuntu", 11),
                bg="#404040", fg="white", show="*", width=30).grid(row=1, column=1, padx=10, pady=5)
        
    def step_user_account(self):
        """User account creation step"""
        tk.Label(self.content_frame, text="Create User Account",
                font=("Ubuntu", 16, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        
        # User form
        form_frame = tk.Frame(self.content_frame, bg="#1a1a1a")
        form_frame.pack(pady=20)
        
        # Full name
        tk.Label(form_frame, text="Full Name:", font=("Ubuntu", 12),
                bg="#1a1a1a", fg="white").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.fullname_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.fullname_var, font=("Ubuntu", 11),
                bg="#404040", fg="white", width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # Username
        tk.Label(form_frame, text="Username:", font=("Ubuntu", 12),
                bg="#1a1a1a", fg="white").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.username_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.username_var, font=("Ubuntu", 11),
                bg="#404040", fg="white", width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # Password
        tk.Label(form_frame, text="Password:", font=("Ubuntu", 12),
                bg="#1a1a1a", fg="white").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.password_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.password_var, font=("Ubuntu", 11),
                bg="#404040", fg="white", show="*", width=30).grid(row=2, column=1, padx=10, pady=10)
        
        # Confirm password
        tk.Label(form_frame, text="Confirm Password:", font=("Ubuntu", 12),
                bg="#1a1a1a", fg="white").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.confirm_password_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.confirm_password_var, font=("Ubuntu", 11),
                bg="#404040", fg="white", show="*", width=30).grid(row=3, column=1, padx=10, pady=10)
        
        # Admin checkbox
        self.admin_var = tk.BooleanVar()
        tk.Checkbutton(form_frame, text="Make this user an administrator",
                      variable=self.admin_var, font=("Ubuntu", 11),
                      bg="#1a1a1a", fg="white", selectcolor="#0078d4").grid(row=4, column=0, columnspan=2, pady=10)
                      
    def step_customization(self):
        """Customization step"""
        tk.Label(self.content_frame, text="Customize Your Desktop",
                font=("Ubuntu", 16, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        
        # Theme selection
        theme_frame = tk.LabelFrame(self.content_frame, text="Theme",
                                   font=("Ubuntu", 12), bg="#2d2d2d", fg="white")
        theme_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.theme_var = tk.StringVar(value="berke_dark")
        
        themes = [
            ("berke_dark", "Berke Dark"),
            ("berke_light", "Berke Light"),
            ("berke_ocean", "Berke Ocean")
        ]
        
        for i, (code, name) in enumerate(themes):
            tk.Radiobutton(theme_frame, text=name, variable=self.theme_var,
                          value=code, font=("Ubuntu", 11), bg="#2d2d2d",
                          fg="white", selectcolor="#0078d4").grid(row=0, column=i, padx=20, pady=10)
        
        # Taskbar position
        taskbar_frame = tk.LabelFrame(self.content_frame, text="Taskbar Position",
                                     font=("Ubuntu", 12), bg="#2d2d2d", fg="white")
        taskbar_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.taskbar_var = tk.StringVar(value="bottom")
        
        positions = [
            ("bottom", "Bottom"),
            ("top", "Top"),
            ("left", "Left"),
            ("right", "Right")
        ]
        
        for i, (code, name) in enumerate(positions):
            tk.Radiobutton(taskbar_frame, text=name, variable=self.taskbar_var,
                          value=code, font=("Ubuntu", 11), bg="#2d2d2d",
                          fg="white", selectcolor="#0078d4").grid(row=0, column=i, padx=15, pady=10)
        
        # Additional options
        options_frame = tk.LabelFrame(self.content_frame, text="Additional Options",
                                     font=("Ubuntu", 12), bg="#2d2d2d", fg="white")
        options_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.animations_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Enable animations",
                      variable=self.animations_var, font=("Ubuntu", 11),
                      bg="#2d2d2d", fg="white", selectcolor="#0078d4").pack(anchor=tk.W, padx=10, pady=5)
        
        self.transparency_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Enable transparency effects",
                      variable=self.transparency_var, font=("Ubuntu", 11),
                      bg="#2d2d2d", fg="white", selectcolor="#0078d4").pack(anchor=tk.W, padx=10, pady=5)
        
        self.sounds_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Enable system sounds",
                      variable=self.sounds_var, font=("Ubuntu", 11),
                      bg="#2d2d2d", fg="white", selectcolor="#0078d4").pack(anchor=tk.W, padx=10, pady=5)
                      
    def step_installation(self):
        """Installation progress step"""
        tk.Label(self.content_frame, text="Installing Berke0S",
                font=("Ubuntu", 16, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        
        # Installation progress
        self.install_progress_var = tk.DoubleVar()
        self.install_progress = ttk.Progressbar(self.content_frame, 
                                              variable=self.install_progress_var,
                                              maximum=100, length=600)
        self.install_progress.pack(pady=20)
        
        # Status label
        self.install_status_var = tk.StringVar(value="Preparing installation...")
        self.install_status_label = tk.Label(self.content_frame, 
                                           textvariable=self.install_status_var,
                                           font=("Ubuntu", 11), bg="#1a1a1a", fg="#cccccc")
        self.install_status_label.pack(pady=10)
        
        # Installation log
        log_frame = tk.Frame(self.content_frame, bg="#1a1a1a")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.install_log = tk.Text(log_frame, font=("Ubuntu Mono", 9), bg="#000000",
                                  fg="#00ff00", height=15, width=80)
        self.install_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.install_log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.install_log.config(yscrollcommand=scrollbar.set)
        
        # Start installation
        self.start_installation()
        
    def start_installation(self):
        """Start the installation process"""
        self.next_button.config(state=tk.DISABLED)
        self.back_button.config(state=tk.DISABLED)
        
        # Installation steps
        steps = [
            ("Collecting installation data...", 5),
            ("Creating user account...", 10),
            ("Setting up database...", 15),
            ("Configuring system settings...", 25),
            ("Installing applications...", 40),
            ("Setting up desktop environment...", 60),
            ("Configuring network...", 75),
            ("Applying customizations...", 85),
            ("Finalizing installation...", 95),
            ("Installation completed!", 100)
        ]
        
        def run_step(step_index):
            if step_index < len(steps):
                status, progress = steps[step_index]
                self.install_status_var.set(status)
                self.install_progress_var.set(progress)
                self.install_log.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {status}\n")
                self.install_log.see(tk.END)
                
                # Simulate installation work
                self.window.after(2000, lambda: run_step(step_index + 1))
            else:
                self.installation_completed()
                
        run_step(0)
        
    def installation_completed(self):
        """Handle installation completion"""
        self.install_status_var.set("Installation completed successfully!")
        self.install_log.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Berke0S installation completed!\n")
        self.install_log.see(tk.END)
        
        # Save configuration
        self.save_installation_data()
        
        # Enable finish button
        self.next_button.config(state=tk.NORMAL, text="Finish")
        
    def save_installation_data(self):
        """Save installation data"""
        try:
            # Update configuration
            config_updates = {
                "first_run": False,
                "language": getattr(self, 'language_var', tk.StringVar()).get(),
                "theme": getattr(self, 'theme_var', tk.StringVar()).get(),
                "taskbar_position": getattr(self, 'taskbar_var', tk.StringVar()).get(),
                "animations_enabled": getattr(self, 'animations_var', tk.BooleanVar()).get(),
                "transparency_enabled": getattr(self, 'transparency_var', tk.BooleanVar()).get(),
                "sound_enabled": getattr(self, 'sounds_var', tk.BooleanVar()).get()
            }
            
            for key, value in config_updates.items():
                self.config_manager.set(key, value)
                
            # Create user account
            username = getattr(self, 'username_var', tk.StringVar()).get()
            password = getattr(self, 'password_var', tk.StringVar()).get()
            fullname = getattr(self, 'fullname_var', tk.StringVar()).get()
            is_admin = getattr(self, 'admin_var', tk.BooleanVar()).get()
            
            if username and password:
                self.db_manager.create_user(username, password, None, fullname, is_admin)
                
            logging.info("Installation data saved successfully")
            
        except Exception as e:
            logging.error(f"Error saving installation data: {e}")
            
    def next_step(self):
        """Go to next step"""
        if self.current_step == 2:  # License step
            if not getattr(self, 'license_var', tk.BooleanVar()).get():
                messagebox.showerror("Error", "You must accept the license agreement to continue.")
                return
                
        if self.current_step == 5:  # User account step
            username = getattr(self, 'username_var', tk.StringVar()).get()
            password = getattr(self, 'password_var', tk.StringVar()).get()
            confirm = getattr(self, 'confirm_password_var', tk.StringVar()).get()
            
            if not username or not password:
                messagebox.showerror("Error", "Username and password are required.")
                return
                
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                return
                
        if self.current_step < self.total_steps:
            self.current_step += 1
            self.show_step()
        else:
            # Finish installation
            self.window.destroy()
            
    def previous_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()
            
    def cancel_installation(self):
        """Cancel installation"""
        if messagebox.askyesno("Cancel Installation", 
                              "Are you sure you want to cancel the installation?"):
            self.window.destroy()
            
    def console_installation(self):
        """Console-based installation"""
        print("\n" + "="*60)
        print("BERKE0S INSTALLATION WIZARD")
        print("Created by: Berke Oruç")
        print("="*60)
        
        # Language selection
        print("\nSelect Language:")
        print("1. English")
        print("2. Türkçe")
        
        lang_choice = input("Choice (1-2): ")
        language = "tr" if lang_choice == "2" else "en"
        
        # License agreement
        print("\nLicense Agreement:")
        print("Do you accept the Berke0S license agreement? (y/n): ", end="")
        if input().lower() != 'y':
            print("Installation cancelled.")
            return
            
        # User account
        print("\nCreate User Account:")
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        fullname = input("Full Name (optional): ")
        
        # Theme selection
        print("\nSelect Theme:")
        print("1. Berke Dark")
        print("2. Berke Light")
        print("3. Berke Ocean")
        
        theme_choice = input("Choice (1-3): ")
        themes = ["berke_dark", "berke_light", "berke_ocean"]
        theme = themes[int(theme_choice) - 1] if theme_choice.isdigit() and 1 <= int(theme_choice) <= 3 else "berke_dark"
        
        # Installation
        print("\nInstalling Berke0S...")
        
        # Save configuration
        config_manager = ConfigManager()
        config_manager.set("first_run", False)
        config_manager.set("language", language)
        config_manager.set("theme", theme)
        
        # Create user
        db_manager = DatabaseManager()
        db_manager.create_user(username, password, None, fullname, True)
        
        print("Installation completed successfully!")
        print("You can now start Berke0S.")

class LoginManager:
    """Login and session management"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        self.lang_manager = LanguageManager()
        self.current_user = None
        self.session_token = None
        
        if GUI_AVAILABLE and parent:
            self.create_gui()
        else:
            self.console_login()
            
    def create_gui(self):
        """Create GUI login window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Berke0S Login")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"400x500+{x}+{y}")
        
        # Get theme
        theme = self.config_manager.get_theme()
        
        # Configure window
        self.window.configure(bg=theme["bg_primary"])
        
        # Main frame
        main_frame = tk.Frame(self.window, bg=theme["bg_primary"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Logo/Title
        tk.Label(main_frame, text="BERKE0S", font=("Ubuntu", 24, "bold"),
                bg=theme["bg_primary"], fg=theme["accent_primary"]).pack(pady=20)
        
        tk.Label(main_frame, text="Advanced Desktop OS", font=("Ubuntu", 12),
                bg=theme["bg_primary"], fg=theme["fg_secondary"]).pack(pady=(0, 30))
        
        # Login form
        form_frame = tk.Frame(main_frame, bg=theme["bg_secondary"], relief=tk.RAISED, bd=1)
        form_frame.pack(fill=tk.X, pady=20)
        
        # Username
        tk.Label(form_frame, text="Username:", font=("Ubuntu", 12),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(pady=(20, 5))
        
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(form_frame, textvariable=self.username_var,
                                 font=("Ubuntu", 12), bg=theme["bg_tertiary"],
                                 fg=theme["fg_primary"], relief=tk.FLAT, bd=5)
        username_entry.pack(pady=(0, 15), padx=20, fill=tk.X)
        username_entry.focus()
        
        # Password
        tk.Label(form_frame, text="Password:", font=("Ubuntu", 12),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(pady=(0, 5))
        
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=self.password_var,
                                 font=("Ubuntu", 12), bg=theme["bg_tertiary"],
                                 fg=theme["fg_primary"], show="*", relief=tk.FLAT, bd=5)
        password_entry.pack(pady=(0, 20), padx=20, fill=tk.X)
        
        # Login button
        login_btn = tk.Button(form_frame, text="Login", font=("Ubuntu", 12, "bold"),
                             bg=theme["accent_primary"], fg="white", relief=tk.FLAT,
                             padx=20, pady=10, command=self.attempt_login)
        login_btn.pack(pady=(0, 20))
        
        # Bind Enter key
        self.window.bind('<Return>', lambda e: self.attempt_login())
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(main_frame, textvariable=self.status_var,
                                    font=("Ubuntu", 10), bg=theme["bg_primary"],
                                    fg=theme["error"])
        self.status_label.pack(pady=10)
        
        # Footer
        tk.Label(main_frame, text="Created by Berke Oruç", font=("Ubuntu", 9),
                bg=theme["bg_primary"], fg=theme["fg_tertiary"]).pack(side=tk.BOTTOM, pady=10)
                
    def attempt_login(self):
        """Attempt to login"""
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            self.status_var.set("Please enter username and password")
            return
            
        user = self.db_manager.authenticate_user(username, password)
        
        if user:
            self.current_user = user
            self.session_token = str(uuid.uuid4())
            
            # Log successful login
            self.db_manager.log_action(user[0], "LOGIN", f"Successful login from GUI")
            
            self.status_var.set("Login successful!")
            self.window.after(1000, self.window.destroy)
            
            return True
        else:
            self.status_var.set("Invalid username or password")
            self.password_var.set("")
            
            # Log failed login attempt
            self.db_manager.log_action(None, "LOGIN_FAILED", f"Failed login attempt: {username}")
            
            return False
            
    def console_login(self):
        """Console login"""
        print("\n=== BERKE0S LOGIN ===")
        
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            
            user = self.db_manager.authenticate_user(username, password)
            
            if user:
                self.current_user = user
                self.session_token = str(uuid.uuid4())
                
                # Log successful login
                self.db_manager.log_action(user[0], "LOGIN", f"Successful login from console")
                
                print(f"Welcome, {user[1]}!")
                return True
            else:
                attempts += 1
                remaining = max_attempts - attempts
                
                if remaining > 0:
                    print(f"Invalid credentials. {remaining} attempts remaining.")
                else:
                    print("Too many failed attempts. Access denied.")
                    
                # Log failed login attempt
                self.db_manager.log_action(None, "LOGIN_FAILED", f"Failed login attempt: {username}")
                
        return False
        
    def logout(self):
        """Logout current user"""
        if self.current_user:
            self.db_manager.log_action(self.current_user[0], "LOGOUT", "User logged out")
            
        self.current_user = None
        self.session_token = None
        
    def is_logged_in(self):
        """Check if user is logged in"""
        return self.current_user is not None
        
    def get_current_user(self):
        """Get current user info"""
        return self.current_user

class FileManager:
    """Advanced file manager with modern features"""
    
    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.lang_manager = LanguageManager()
        self.current_path = os.path.expanduser("~")
        self.history = [self.current_path]
        self.history_index = 0
        self.bookmarks = []
        self.clipboard = []
        self.clipboard_operation = None  # 'cut' or 'copy'
        
        self.create_window()
        
    def create_window(self):
        """Create file manager window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("File Manager - Berke0S")
        self.window.geometry("900x600")
        
        # Get theme
        theme = self.config_manager.get_theme()
        self.window.configure(bg=theme["bg_primary"])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main layout
        self.create_main_layout()
        
        # Create status bar
        self.create_status_bar()
        
        # Load initial directory
        self.refresh_view()
        
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Folder", command=self.new_folder)
        file_menu.add_command(label="New File", command=self.new_file)
        file_menu.add_separator()
        file_menu.add_command(label="Properties", command=self.show_properties)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.destroy)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Cut", command=self.cut_files)
        edit_menu.add_command(label="Copy", command=self.copy_files)
        edit_menu.add_command(label="Paste", command=self.paste_files)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all)
        edit_menu.add_command(label="Invert Selection", command=self.invert_selection)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.refresh_view)
        view_menu.add_command(label="Show Hidden Files", command=self.toggle_hidden_files)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Search", command=self.open_search)
        tools_menu.add_command(label="Terminal Here", command=self.open_terminal_here)
        
    def create_toolbar(self):
        """Create toolbar"""
        theme = self.config_manager.get_theme()
        
        toolbar = tk.Frame(self.window, bg=theme["bg_secondary"], height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # Navigation buttons
        nav_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        nav_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.back_btn = tk.Button(nav_frame, text="◀", font=("Ubuntu", 12),
                                 bg=theme["bg_tertiary"], fg=theme["fg_primary"],
                                 command=self.go_back, width=3)
        self.back_btn.pack(side=tk.LEFT, padx=2)
        
        self.forward_btn = tk.Button(nav_frame, text="▶", font=("Ubuntu", 12),
                                    bg=theme["bg_tertiary"], fg=theme["fg_primary"],
                                    command=self.go_forward, width=3)
        self.forward_btn.pack(side=tk.LEFT, padx=2)
        
        self.up_btn = tk.Button(nav_frame, text="▲", font=("Ubuntu", 12),
                               bg=theme["bg_tertiary"], fg=theme["fg_primary"],
                               command=self.go_up, width=3)
        self.up_btn.pack(side=tk.LEFT, padx=2)
        
        self.home_btn = tk.Button(nav_frame, text="🏠", font=("Ubuntu", 12),
                                 bg=theme["bg_tertiary"], fg=theme["fg_primary"],
                                 command=self.go_home, width=3)
        self.home_btn.pack(side=tk.LEFT, padx=2)
        
        # Address bar
        address_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        address_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
        
        self.address_var = tk.StringVar(value=self.current_path)
        self.address_entry = tk.Entry(address_frame, textvariable=self.address_var,
                                     font=("Ubuntu", 10), bg=theme["bg_tertiary"],
                                     fg=theme["fg_primary"])
        self.address_entry.pack(fill=tk.X)
        self.address_entry.bind('<Return>', self.navigate_to_address)
        
        # Action buttons
        action_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        action_frame.pack(side=tk.RIGHT, padx=5, pady=5)
        
        tk.Button(action_frame, text="New", font=("Ubuntu", 10),
                 bg=theme["accent_primary"], fg="white",
                 command=self.new_folder).pack(side=tk.LEFT, padx=2)
        
        tk.Button(action_frame, text="Search", font=("Ubuntu", 10),
                 bg=theme["accent_primary"], fg="white",
                 command=self.open_search).pack(side=tk.LEFT, padx=2)
        
    def create_main_layout(self):
        """Create main layout with sidebar and file view"""
        theme = self.config_manager.get_theme()
        
        # Main paned window
        self.paned_window = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                                          bg=theme["bg_primary"], sashwidth=5)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        self.create_sidebar()
        
        # File view
        self.create_file_view()
        
    def create_sidebar(self):
        """Create sidebar with bookmarks and shortcuts"""
        theme = self.config_manager.get_theme()
        
        sidebar_frame = tk.Frame(self.paned_window, bg=theme["bg_secondary"], width=200)
        self.paned_window.add(sidebar_frame, minsize=150)
        
        # Bookmarks section
        tk.Label(sidebar_frame, text="Bookmarks", font=("Ubuntu", 12, "bold"),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(pady=10)
        
        self.bookmarks_listbox = tk.Listbox(sidebar_frame, bg=theme["bg_tertiary"],
                                           fg=theme["fg_primary"], font=("Ubuntu", 10),
                                           selectbackground=theme["accent_primary"])
        self.bookmarks_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.bookmarks_listbox.bind('<Double-1>', self.navigate_to_bookmark)
        
        # Add default bookmarks
        default_bookmarks = [
            ("Home", os.path.expanduser("~")),
            ("Documents", os.path.expanduser("~/Documents")),
            ("Downloads", os.path.expanduser("~/Downloads")),
            ("Desktop", os.path.expanduser("~/Desktop")),
            ("Root", "/")
        ]
        
        for name, path in default_bookmarks:
            self.bookmarks.append((name, path))
            self.bookmarks_listbox.insert(tk.END, name)
            
        # Bookmark buttons
        bookmark_btn_frame = tk.Frame(sidebar_frame, bg=theme["bg_secondary"])
        bookmark_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(bookmark_btn_frame, text="Add", font=("Ubuntu", 9),
                 bg=theme["accent_primary"], fg="white",
                 command=self.add_bookmark).pack(side=tk.LEFT, padx=2)
        
        tk.Button(bookmark_btn_frame, text="Remove", font=("Ubuntu", 9),
                 bg=theme["error"], fg="white",
                 command=self.remove_bookmark).pack(side=tk.LEFT, padx=2)
        
    def create_file_view(self):
        """Create file view area"""
        theme = self.config_manager.get_theme()
        
        file_frame = tk.Frame(self.paned_window, bg=theme["bg_primary"])
        self.paned_window.add(file_frame, minsize=400)
        
        # File list with scrollbars
        list_frame = tk.Frame(file_frame, bg=theme["bg_primary"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for file list
        columns = ('Name', 'Size', 'Type', 'Modified')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        
        # Configure columns
        self.file_tree.heading('#0', text='Icon')
        self.file_tree.column('#0', width=50, minwidth=50)
        
        for col in columns:
            self.file_tree.heading(col, text=col)
            if col == 'Name':
                self.file_tree.column(col, width=300, minwidth=200)
            elif col == 'Size':
                self.file_tree.column(col, width=100, minwidth=80)
            elif col == 'Type':
                self.file_tree.column(col, width=120, minwidth=100)
            elif col == 'Modified':
                self.file_tree.column(col, width=150, minwidth=120)
                
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
        self.file_tree.bind('<Double-1>', self.on_double_click)
        self.file_tree.bind('<Button-3>', self.show_context_menu)
        self.file_tree.bind('<KeyPress>', self.on_key_press)
        
    def create_status_bar(self):
        """Create status bar"""
        theme = self.config_manager.get_theme()
        
        self.status_bar = tk.Frame(self.window, bg=theme["bg_secondary"], height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.status_bar, textvariable=self.status_var,
                                    font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                    fg=theme["fg_secondary"])
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # File count and size info
        self.info_var = tk.StringVar()
        self.info_label = tk.Label(self.status_bar, textvariable=self.info_var,
                                  font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                  fg=theme["fg_secondary"])
        self.info_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
    def refresh_view(self):
        """Refresh file view"""
        try:
            # Clear current items
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
                
            # Update address bar
            self.address_var.set(self.current_path)
            
            # Get directory contents
            try:
                items = os.listdir(self.current_path)
                items.sort(key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x.lower()))
            except PermissionError:
                self.status_var.set("Permission denied")
                return
            except FileNotFoundError:
                self.status_var.set("Directory not found")
                return
                
            file_count = 0
            dir_count = 0
            total_size = 0
            
            for item in items:
                if item.startswith('.') and not self.config_manager.get("show_hidden_files", False):
                    continue
                    
                item_path = os.path.join(self.current_path, item)
                
                try:
                    stat_info = os.stat(item_path)
                    
                    # Get file info
                    if os.path.isdir(item_path):
                        icon = "📁"
                        file_type = "Folder"
                        size = ""
                        dir_count += 1
                    else:
                        icon = self.get_file_icon(item)
                        file_type = self.get_file_type(item)
                        size = self.format_size(stat_info.st_size)
                        total_size += stat_info.st_size
                        file_count += 1
                        
                    modified = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
                    
                    # Insert into treeview
                    self.file_tree.insert('', tk.END, text=icon,
                                         values=(item, size, file_type, modified))
                                         
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
                    
            # Update status
            self.status_var.set(f"Path: {self.current_path}")
            self.info_var.set(f"{dir_count} folders, {file_count} files ({self.format_size(total_size)})")
            
            # Update navigation buttons
            self.update_navigation_buttons()
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            logging.error(f"File manager refresh error: {e}")
            
    def get_file_icon(self, filename):
        """Get file icon based on extension"""
        ext = os.path.splitext(filename)[1].lower()
        
        icon_map = {
            '.txt': '📄', '.doc': '📄', '.docx': '📄', '.pdf': '📄',
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.mp4': '🎬', '.avi': '🎬',
            '.zip': '📦', '.tar': '📦', '.gz': '📦', '.rar': '📦',
            '.exe': '⚙️', '.deb': '📦', '.rpm': '📦'
        }
        
        return icon_map.get(ext, '📄')
        
    def get_file_type(self, filename):
        """Get file type description"""
        ext = os.path.splitext(filename)[1].lower()
        
        type_map = {
            '.txt': 'Text File',
            '.py': 'Python Script',
            '.js': 'JavaScript File',
            '.html': 'HTML Document',
            '.css': 'CSS Stylesheet',
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.png': 'PNG Image',
            '.gif': 'GIF Image',
            '.mp3': 'MP3 Audio',
            '.wav': 'WAV Audio',
            '.mp4': 'MP4 Video',
            '.avi': 'AVI Video',
            '.zip': 'ZIP Archive',
            '.tar': 'TAR Archive',
            '.gz': 'GZIP Archive'
        }
        
        return type_map.get(ext, 'File')
        
    def format_size(self, size):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
        
    def update_navigation_buttons(self):
        """Update navigation button states"""
        self.back_btn.config(state=tk.NORMAL if self.history_index > 0 else tk.DISABLED)
        self.forward_btn.config(state=tk.NORMAL if self.history_index < len(self.history) - 1 else tk.DISABLED)
        self.up_btn.config(state=tk.NORMAL if self.current_path != "/" else tk.DISABLED)
        
    def navigate_to(self, path):
        """Navigate to specified path"""
        if os.path.isdir(path):
            self.current_path = os.path.abspath(path)
            
            # Update history
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            self.history.append(self.current_path)
            self.history_index = len(self.history) - 1
            
            self.refresh_view()
            
            # Log navigation
            if self.user_info:
                self.db_manager.log_action(self.user_info[0], "NAVIGATE", f"Navigated to {path}")
        else:
            self.status_var.set("Invalid path")
            
    def navigate_to_address(self, event=None):
        """Navigate to address bar path"""
        path = self.address_var.get()
        self.navigate_to(path)
        
    def navigate_to_bookmark(self, event=None):
        """Navigate to selected bookmark"""
        selection = self.bookmarks_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.bookmarks):
                name, path = self.bookmarks[index]
                self.navigate_to(path)
                
    def go_back(self):
        """Go back in history"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_path = self.history[self.history_index]
            self.refresh_view()
            
    def go_forward(self):
        """Go forward in history"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_path = self.history[self.history_index]
            self.refresh_view()
            
    def go_up(self):
        """Go to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.navigate_to(parent)
            
    def go_home(self):
        """Go to home directory"""
        self.navigate_to(os.path.expanduser("~"))
        
    def on_double_click(self, event=None):
        """Handle double-click on file/folder"""
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            filename = item['values'][0]
            file_path = os.path.join(self.current_path, filename)
            
            if os.path.isdir(file_path):
                self.navigate_to(file_path)
            else:
                self.open_file(file_path)
                
    def open_file(self, file_path):
        """Open file with appropriate application"""
        try:
            # Log file access
            if self.user_info:
                self.db_manager.log_action(self.user_info[0], "OPEN_FILE", f"Opened {file_path}")
                
            # Get file extension
            ext = os.path.splitext(file_path)[1].lower()
            
            # Open with appropriate application
            if ext in ['.txt', '.py', '.js', '.html', '.css', '.md']:
                TextEditor(self.parent, file_path, self.user_info)
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                ImageViewer(self.parent, file_path, self.user_info)
            elif ext in ['.mp3', '.wav', '.ogg']:
                MusicPlayer(self.parent, file_path, self.user_info)
            elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                VideoPlayer(self.parent, file_path, self.user_info)
            else:
                # Try to open with system default
                subprocess.run(['xdg-open', file_path], check=True)
                
        except Exception as e:
            self.status_var.set(f"Cannot open file: {str(e)}")
            logging.error(f"File open error: {e}")
            
    def show_context_menu(self, event):
        """Show context menu"""
        theme = self.config_manager.get_theme()
        
        # Create context menu
        context_menu = tk.Menu(self.window, tearoff=0,
                              bg=theme["bg_secondary"], fg=theme["fg_primary"])
        
        selection = self.file_tree.selection()
        
        if selection:
            # File/folder selected
            item = self.file_tree.item(selection[0])
            filename = item['values'][0]
            file_path = os.path.join(self.current_path, filename)
            
            if os.path.isdir(file_path):
                context_menu.add_command(label="Open", command=lambda: self.navigate_to(file_path))
                context_menu.add_command(label="Open in New Window", command=lambda: self.open_in_new_window(file_path))
            else:
                context_menu.add_command(label="Open", command=lambda: self.open_file(file_path))
                context_menu.add_command(label="Open With...", command=lambda: self.open_with_dialog(file_path))
                
            context_menu.add_separator()
            context_menu.add_command(label="Cut", command=self.cut_files)
            context_menu.add_command(label="Copy", command=self.copy_files)
            context_menu.add_separator()
            context_menu.add_command(label="Rename", command=self.rename_file)
            context_menu.add_command(label="Delete", command=self.delete_files)
            context_menu.add_separator()
            context_menu.add_command(label="Properties", command=self.show_properties)
        else:
            # Empty space
            context_menu.add_command(label="New Folder", command=self.new_folder)
            context_menu.add_command(label="New File", command=self.new_file)
            context_menu.add_separator()
            
            if self.clipboard:
                context_menu.add_command(label="Paste", command=self.paste_files)
                context_menu.add_separator()
                
            context_menu.add_command(label="Refresh", command=self.refresh_view)
            context_menu.add_command(label="Properties", command=self.show_folder_properties)
            
        # Show menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def on_key_press(self, event):
        """Handle key press events"""
        if event.keysym == 'Delete':
            self.delete_files()
        elif event.keysym == 'F2':
            self.rename_file()
        elif event.keysym == 'F5':
            self.refresh_view()
        elif event.state & 0x4:  # Ctrl key
            if event.keysym == 'c':
                self.copy_files()
            elif event.keysym == 'x':
                self.cut_files()
            elif event.keysym == 'v':
                self.paste_files()
            elif event.keysym == 'a':
                self.select_all()
                
    def new_folder(self):
        """Create new folder"""
        name = simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            folder_path = os.path.join(self.current_path, name)
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.refresh_view()
                self.status_var.set(f"Created folder: {name}")
                
                # Log action
                if self.user_info:
                    self.db_manager.log_action(self.user_info[0], "CREATE_FOLDER", f"Created {folder_path}")
                    
            except Exception as e:
                self.status_var.set(f"Cannot create folder: {str(e)}")
                
    def new_file(self):
        """Create new file"""
        name = simpledialog.askstring("New File", "Enter file name:")
        if name:
            file_path = os.path.join(self.current_path, name)
            try:
                with open(file_path, 'w') as f:
                    f.write("")
                self.refresh_view()
                self.status_var.set(f"Created file: {name}")
                
                # Log action
                if self.user_info:
                    self.db_manager.log_action(self.user_info[0], "CREATE_FILE", f"Created {file_path}")
                    
            except Exception as e:
                self.status_var.set(f"Cannot create file: {str(e)}")
                
    def cut_files(self):
        """Cut selected files"""
        selection = self.file_tree.selection()
        if selection:
            self.clipboard = []
            for item_id in selection:
                item = self.file_tree.item(item_id)
                filename = item['values'][0]
                file_path = os.path.join(self.current_path, filename)
                self.clipboard.append(file_path)
            self.clipboard_operation = 'cut'
            self.status_var.set(f"Cut {len(self.clipboard)} items")
            
    def copy_files(self):
        """Copy selected files"""
        selection = self.file_tree.selection()
        if selection:
            self.clipboard = []
            for item_id in selection:
                item = self.file_tree.item(item_id)
                filename = item['values'][0]
                file_path = os.path.join(self.current_path, filename)
                self.clipboard.append(file_path)
            self.clipboard_operation = 'copy'
            self.status_var.set(f"Copied {len(self.clipboard)} items")
            
    def paste_files(self):
        """Paste files from clipboard"""
        if not self.clipboard:
            return
            
        try:
            for source_path in self.clipboard:
                filename = os.path.basename(source_path)
                dest_path = os.path.join(self.current_path, filename)
                
                # Handle name conflicts
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        new_name = f"{base}_copy{counter}{ext}"
                        dest_path = os.path.join(self.current_path, new_name)
                        counter += 1
                        
                if self.clipboard_operation == 'copy':
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, dest_path)
                    else:
                        shutil.copy2(source_path, dest_path)
                elif self.clipboard_operation == 'cut':
                    shutil.move(source_path, dest_path)
                    
            if self.clipboard_operation == 'cut':
                self.clipboard = []
                
            self.refresh_view()
            self.status_var.set(f"Pasted {len(self.clipboard)} items")
            
            # Log action
            if self.user_info:
                self.db_manager.log_action(self.user_info[0], "PASTE_FILES", 
                                         f"Pasted files to {self.current_path}")
                
        except Exception as e:
            self.status_var.set(f"Paste error: {str(e)}")
            
    def delete_files(self):
        """Delete selected files"""
        selection = self.file_tree.selection()
        if not selection:
            return
            
        files_to_delete = []
        for item_id in selection:
            item = self.file_tree.item(item_id)
            filename = item['values'][0]
            file_path = os.path.join(self.current_path, filename)
            files_to_delete.append((filename, file_path))
            
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete {len(files_to_delete)} items?"):
            try:
                for filename, file_path in files_to_delete:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                        
                self.refresh_view()
                self.status_var.set(f"Deleted {len(files_to_delete)} items")
                
                # Log action
                if self.user_info:
                    self.db_manager.log_action(self.user_info[0], "DELETE_FILES", 
                                             f"Deleted {len(files_to_delete)} items")
                    
            except Exception as e:
                self.status_var.set(f"Delete error: {str(e)}")
                
    def rename_file(self):
        """Rename selected file"""
        selection = self.file_tree.selection()
        if len(selection) != 1:
            return
            
        item = self.file_tree.item(selection[0])
        old_name = item['values'][0]
        old_path = os.path.join(self.current_path, old_name)
        
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=old_name)
        if new_name and new_name != old_name:
            new_path = os.path.join(self.current_path, new_name)
            try:
                os.rename(old_path, new_path)
                self.refresh_view()
                self.status_var.set(f"Renamed to: {new_name}")
                
                # Log action
                if self.user_info:
                    self.db_manager.log_action(self.user_info[0], "RENAME_FILE", 
                                             f"Renamed {old_name} to {new_name}")
                    
            except Exception as e:
                self.status_var.set(f"Rename error: {str(e)}")
                
    def select_all(self):
        """Select all files"""
        for item in self.file_tree.get_children():
            self.file_tree.selection_add(item)
            
    def invert_selection(self):
        """Invert file selection"""
        selected = set(self.file_tree.selection())
        all_items = set(self.file_tree.get_children())
        
        # Clear current selection
        self.file_tree.selection_remove(*selected)
        
        # Select unselected items
        unselected = all_items - selected
        self.file_tree.selection_add(*unselected)
        
    def show_properties(self):
        """Show properties of selected file"""
        selection = self.file_tree.selection()
        if len(selection) != 1:
            return
            
        item = self.file_tree.item(selection[0])
        filename = item['values'][0]
        file_path = os.path.join(self.current_path, filename)
        
        PropertiesDialog(self.window, file_path)
        
    def show_folder_properties(self):
        """Show properties of current folder"""
        PropertiesDialog(self.window, self.current_path)
        
    def add_bookmark(self):
        """Add current path to bookmarks"""
        name = simpledialog.askstring("Add Bookmark", "Enter bookmark name:",
                                     initialvalue=os.path.basename(self.current_path))
        if name:
            self.bookmarks.append((name, self.current_path))
            self.bookmarks_listbox.insert(tk.END, name)
            self.status_var.set(f"Added bookmark: {name}")
            
    def remove_bookmark(self):
        """Remove selected bookmark"""
        selection = self.bookmarks_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.bookmarks):
                name, path = self.bookmarks.pop(index)
                self.bookmarks_listbox.delete(index)
                self.status_var.set(f"Removed bookmark: {name}")
                
    def toggle_hidden_files(self):
        """Toggle showing hidden files"""
        current = self.config_manager.get("show_hidden_files", False)
        self.config_manager.set("show_hidden_files", not current)
        self.refresh_view()
        
    def open_search(self):
        """Open search dialog"""
        SearchDialog(self.window, self.current_path, self.user_info)
        
    def open_terminal_here(self):
        """Open terminal in current directory"""
        try:
            subprocess.Popen(['gnome-terminal', '--working-directory', self.current_path])
        except:
            try:
                subprocess.Popen(['xterm', '-e', f'cd "{self.current_path}" && bash'])
            except:
                self.status_var.set("Cannot open terminal")
                
    def open_in_new_window(self, path):
        """Open path in new file manager window"""
        new_fm = FileManager(self.parent, self.user_info)
        new_fm.navigate_to(path)
        
    def open_with_dialog(self, file_path):
        """Show open with dialog"""
        OpenWithDialog(self.window, file_path)

class PropertiesDialog:
    """File/folder properties dialog"""
    
    def __init__(self, parent, file_path):
        self.parent = parent
        self.file_path = file_path
        self.create_dialog()
        
    def create_dialog(self):
        """Create properties dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Properties - {os.path.basename(self.file_path)}")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"400x500+{x}+{y}")
        
        # Get theme
        config_manager = ConfigManager()
        theme = config_manager.get_theme()
        self.dialog.configure(bg=theme["bg_primary"])
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General tab
        self.create_general_tab(notebook, theme)
        
        # Permissions tab
        self.create_permissions_tab(notebook, theme)
        
        # OK button
        tk.Button(self.dialog, text="OK", command=self.dialog.destroy,
                 bg=theme["accent_primary"], fg="white", padx=20, pady=5).pack(pady=10)
                 
    def create_general_tab(self, notebook, theme):
        """Create general properties tab"""
        general_frame = tk.Frame(notebook, bg=theme["bg_primary"])
        notebook.add(general_frame, text="General")
        
        try:
            stat_info = os.stat(self.file_path)
            
            # File icon and name
            icon_frame = tk.Frame(general_frame, bg=theme["bg_primary"])
            icon_frame.pack(pady=20)
            
            if os.path.isdir(self.file_path):
                icon = "📁"
                file_type = "Folder"
            else:
                ext = os.path.splitext(self.file_path)[1].lower()
                icon = "📄"  # Default file icon
                file_type = f"{ext.upper()} File" if ext else "File"
                
            tk.Label(icon_frame, text=icon, font=("Ubuntu", 48),
                    bg=theme["bg_primary"]).pack()
            
            tk.Label(icon_frame, text=os.path.basename(self.file_path),
                    font=("Ubuntu", 14, "bold"), bg=theme["bg_primary"],
                    fg=theme["fg_primary"]).pack(pady=5)
            
            # Properties
            props_frame = tk.Frame(general_frame, bg=theme["bg_primary"])
            props_frame.pack(fill=tk.X, padx=20)
            
            properties = [
                ("Type:", file_type),
                ("Location:", os.path.dirname(self.file_path)),
                ("Size:", self.format_size(stat_info.st_size) if not os.path.isdir(self.file_path) else self.get_folder_size()),
                ("Created:", datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")),
                ("Modified:", datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")),
                ("Accessed:", datetime.datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S"))
            ]
            
            for i, (label, value) in enumerate(properties):
                tk.Label(props_frame, text=label, font=("Ubuntu", 10, "bold"),
                        bg=theme["bg_primary"], fg=theme["fg_primary"]).grid(row=i, column=0, sticky=tk.W, pady=2)
                tk.Label(props_frame, text=value, font=("Ubuntu", 10),
                        bg=theme["bg_primary"], fg=theme["fg_secondary"]).grid(row=i, column=1, sticky=tk.W, padx=10, pady=2)
                        
        except Exception as e:
            tk.Label(general_frame, text=f"Error reading properties: {str(e)}",
                    bg=theme["bg_primary"], fg=theme["error"]).pack(pady=20)
                    
    def create_permissions_tab(self, notebook, theme):
        """Create permissions tab"""
        perm_frame = tk.Frame(notebook, bg=theme["bg_primary"])
        notebook.add(perm_frame, text="Permissions")
        
        try:
            stat_info = os.stat(self.file_path)
            mode = stat_info.st_mode
            
            # Owner permissions
            owner_frame = tk.LabelFrame(perm_frame, text="Owner", bg=theme["bg_secondary"],
                                       fg=theme["fg_primary"])
            owner_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Checkbutton(owner_frame, text="Read", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IRUSR else tk.DISABLED).pack(anchor=tk.W)
            tk.Checkbutton(owner_frame, text="Write", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IWUSR else tk.DISABLED).pack(anchor=tk.W)
            tk.Checkbutton(owner_frame, text="Execute", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IXUSR else tk.DISABLED).pack(anchor=tk.W)
            
            # Group permissions
            group_frame = tk.LabelFrame(perm_frame, text="Group", bg=theme["bg_secondary"],
                                       fg=theme["fg_primary"])
            group_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Checkbutton(group_frame, text="Read", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IRGRP else tk.DISABLED).pack(anchor=tk.W)
            tk.Checkbutton(group_frame, text="Write", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IWGRP else tk.DISABLED).pack(anchor=tk.W)
            tk.Checkbutton(group_frame, text="Execute", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IXGRP else tk.DISABLED).pack(anchor=tk.W)
            
            # Others permissions
            others_frame = tk.LabelFrame(perm_frame, text="Others", bg=theme["bg_secondary"],
                                        fg=theme["fg_primary"])
            others_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Checkbutton(others_frame, text="Read", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IROTH else tk.DISABLED).pack(anchor=tk.W)
            tk.Checkbutton(others_frame, text="Write", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IWOTH else tk.DISABLED).pack(anchor=tk.W)
            tk.Checkbutton(others_frame, text="Execute", bg=theme["bg_secondary"],
                          fg=theme["fg_primary"], state=tk.NORMAL if mode & stat.S_IXOTH else tk.DISABLED).pack(anchor=tk.W)
            
            # Octal representation
            octal = oct(mode)[-3:]
            tk.Label(perm_frame, text=f"Octal: {octal}", font=("Ubuntu", 12, "bold"),
                    bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(pady=20)
                    
        except Exception as e:
            tk.Label(perm_frame, text=f"Error reading permissions: {str(e)}",
                    bg=theme["bg_primary"], fg=theme["error"]).pack(pady=20)
                    
    def format_size(self, size):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
        
    def get_folder_size(self):
        """Get total size of folder"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.file_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        continue
            return self.format_size(total_size)
        except:
            return "Unknown"

class SearchDialog:
    """File search dialog"""
    
    def __init__(self, parent, search_path, user_info=None):
        self.parent = parent
        self.search_path = search_path
        self.user_info = user_info
        self.search_thread = None
        self.search_cancelled = False
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create search dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Search Files")
        self.dialog.geometry("600x500")
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        # Get theme
        config_manager = ConfigManager()
        theme = config_manager.get_theme()
        self.dialog.configure(bg=theme["bg_primary"])
        
        # Search criteria
        criteria_frame = tk.Frame(self.dialog, bg=theme["bg_secondary"])
        criteria_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(criteria_frame, text="Search for:", font=("Ubuntu", 10),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.search_var = tk.StringVar()
        tk.Entry(criteria_frame, textvariable=self.search_var, font=("Ubuntu", 10),
                bg=theme["bg_tertiary"], fg=theme["fg_primary"], width=30).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(criteria_frame, text="In folder:", font=("Ubuntu", 10),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.path_var = tk.StringVar(value=self.search_path)
        tk.Entry(criteria_frame, textvariable=self.path_var, font=("Ubuntu", 10),
                bg=theme["bg_tertiary"], fg=theme["fg_primary"], width=30).grid(row=1, column=1, padx=5, pady=5)
        
        # Search options
        options_frame = tk.Frame(self.dialog, bg=theme["bg_secondary"])
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.case_sensitive_var = tk.BooleanVar()
        tk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive_var,
                      bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(side=tk.LEFT, padx=5)
        
        self.include_subfolders_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Include subfolders", variable=self.include_subfolders_var,
                      bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(side=tk.LEFT, padx=5)
        
        # Search buttons
        button_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.search_btn = tk.Button(button_frame, text="Search", command=self.start_search,
                                   bg=theme["accent_primary"], fg="white", padx=20)
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = tk.Button(button_frame, text="Cancel", command=self.cancel_search,
                                   bg=theme["error"], fg="white", padx=20)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready to search")
        tk.Label(self.dialog, textvariable=self.progress_var, font=("Ubuntu", 9),
                bg=theme["bg_primary"], fg=theme["fg_secondary"]).pack(pady=5)
        
        # Results
        results_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(results_frame, text="Search Results:", font=("Ubuntu", 10, "bold"),
                bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(anchor=tk.W)
        
        # Results listbox with scrollbar
        list_frame = tk.Frame(results_frame, bg=theme["bg_primary"])
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_listbox = tk.Listbox(list_frame, bg=theme["bg_tertiary"],
                                         fg=theme["fg_primary"], font=("Ubuntu", 9))
        scrollbar = tk.Scrollbar(list_frame, command=self.results_listbox.yview)
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_listbox.bind('<Double-1>', self.open_selected_result)
        
        # Bind Enter key to search
        self.dialog.bind('<Return>', lambda e: self.start_search())
        
    def start_search(self):
        """Start file search"""
        search_term = self.search_var.get().strip()
        if not search_term:
            return
            
        search_path = self.path_var.get().strip()
        if not os.path.isdir(search_path):
            messagebox.showerror("Error", "Invalid search path")
            return
            
        # Clear previous results
        self.results_listbox.delete(0, tk.END)
        
        # Update UI
        self.search_btn.config(state=tk.DISABLED)
        self.search_cancelled = False
        self.progress_var.set("Searching...")
        
        # Start search in thread
        self.search_thread = threading.Thread(target=self.perform_search,
                                             args=(search_term, search_path))
        self.search_thread.daemon = True
        self.search_thread.start()
        
    def perform_search(self, search_term, search_path):
        """Perform the actual search"""
        try:
            results = []
            case_sensitive = self.case_sensitive_var.get()
            include_subfolders = self.include_subfolders_var.get()
            
            if not case_sensitive:
                search_term = search_term.lower()
                
            def search_directory(directory):
                if self.search_cancelled:
                    return
                    
                try:
                    for item in os.listdir(directory):
                        if self.search_cancelled:
                            return
                            
                        item_path = os.path.join(directory, item)
                        
                        # Check if item matches search term
                        item_name = item if case_sensitive else item.lower()
                        if search_term in item_name:
                            results.append(item_path)
                            
                            # Update UI in main thread
                            self.dialog.after(0, lambda path=item_path: self.add_result(path))
                            
                        # Search subdirectories if enabled
                        if include_subfolders and os.path.isdir(item_path):
                            search_directory(item_path)
                            
                except PermissionError:
                    pass  # Skip directories we can't access
                except Exception as e:
                    logging.error(f"Search error in {directory}: {e}")
                    
            search_directory(search_path)
            
            # Update UI when search is complete
            if not self.search_cancelled:
                self.dialog.after(0, lambda: self.search_complete(len(results)))
                
        except Exception as e:
            logging.error(f"Search error: {e}")
            self.dialog.after(0, lambda: self.progress_var.set(f"Search error: {str(e)}"))
            
    def add_result(self, file_path):
        """Add search result to listbox"""
        self.results_listbox.insert(tk.END, file_path)
        self.progress_var.set(f"Found {self.results_listbox.size()} items...")
        
    def search_complete(self, count):
        """Handle search completion"""
        self.search_btn.config(state=tk.NORMAL)
        self.progress_var.set(f"Search complete. Found {count} items.")
        
        # Log search action
        if self.user_info:
            db_manager = DatabaseManager()
            db_manager.log_action(self.user_info[0], "SEARCH_FILES", 
                                f"Searched for '{self.search_var.get()}' in {self.path_var.get()}")
            
    def cancel_search(self):
        """Cancel ongoing search"""
        self.search_cancelled = True
        self.search_btn.config(state=tk.NORMAL)
        self.progress_var.set("Search cancelled")
        
    def open_selected_result(self, event=None):
        """Open selected search result"""
        selection = self.results_listbox.curselection()
        if selection:
            file_path = self.results_listbox.get(selection[0])
            
            if os.path.isdir(file_path):
                # Open in file manager
                FileManager(self.parent, self.user_info).navigate_to(file_path)
            else:
                # Open file with appropriate application
                try:
                    subprocess.run(['xdg-open', file_path])
                except:
                    messagebox.showerror("Error", "Cannot open file")

class OpenWithDialog:
    """Open with application dialog"""
    
    def __init__(self, parent, file_path):
        self.parent = parent
        self.file_path = file_path
        self.create_dialog()
        
    def create_dialog(self):
        """Create open with dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Open With")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        # Get theme
        config_manager = ConfigManager()
        theme = config_manager.get_theme()
        self.dialog.configure(bg=theme["bg_primary"])
        
        # File info
        tk.Label(self.dialog, text=f"Open: {os.path.basename(self.file_path)}",
                font=("Ubuntu", 12, "bold"), bg=theme["bg_primary"],
                fg=theme["fg_primary"]).pack(pady=10)
        
        # Application list
        tk.Label(self.dialog, text="Choose an application:",
                font=("Ubuntu", 10), bg=theme["bg_primary"],
                fg=theme["fg_secondary"]).pack(pady=5)
        
        list_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.app_listbox = tk.Listbox(list_frame, bg=theme["bg_tertiary"],
                                     fg=theme["fg_primary"], font=("Ubuntu", 10))
        scrollbar = tk.Scrollbar(list_frame, command=self.app_listbox.yview)
        self.app_listbox.config(yscrollcommand=scrollbar.set)
        
        self.app_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate applications
        self.populate_applications()
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(button_frame, text="OK", command=self.open_with_selected,
                 bg=theme["accent_primary"], fg="white", padx=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 bg=theme["error"], fg="white", padx=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Browse...", command=self.browse_application,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=20).pack(side=tk.RIGHT, padx=5)
        
    def populate_applications(self):
        """Populate application list"""
        # Common applications
        applications = [
            ("Text Editor", "gedit"),
            ("Code Editor", "code"),
            ("Image Viewer", "eog"),
            ("Web Browser", "firefox"),
            ("Media Player", "vlc"),
            ("Archive Manager", "file-roller"),
            ("Terminal", "gnome-terminal")
        ]
        
        for name, command in applications:
            self.app_listbox.insert(tk.END, f"{name} ({command})")
            
    def open_with_selected(self):
        """Open file with selected application"""
        selection = self.app_listbox.curselection()
        if selection:
            app_text = self.app_listbox.get(selection[0])
            # Extract command from text (between parentheses)
            start = app_text.find('(') + 1
            end = app_text.find(')')
            if start > 0 and end > start:
                command = app_text[start:end]
                try:
                    subprocess.run([command, self.file_path])
                    self.dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Cannot open with {command}: {str(e)}")
                    
    def browse_application(self):
        """Browse for application"""
        app_path = filedialog.askopenfilename(title="Select Application",
                                            filetypes=[("Executable files", "*")])
        if app_path:
            try:
                subprocess.run([app_path, self.file_path])
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open with {app_path}: {str(e)}")

class TextEditor:
    """Advanced text editor with syntax highlighting"""
    
    def __init__(self, parent, file_path=None, user_info=None):
        self.parent = parent
        self.file_path = file_path
        self.user_info = user_info
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.modified = False
        self.undo_stack = []
        self.redo_stack = []
        
        self.create_window()
        
        if file_path:
            self.load_file()
            
    def create_window(self):
        """Create text editor window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Text Editor - Berke0S")
        self.window.geometry("800x600")
        
        # Get theme
        theme = self.config_manager.get_theme()
        self.window.configure(bg=theme["bg_primary"])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create text area
        self.create_text_area()
        
        # Create status bar
        self.create_status_bar()
        
        # Bind events
        self.bind_events()
        
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Print", command=self.print_file, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.destroy)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="Find", command=self.find, accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace", command=self.replace, accelerator="Ctrl+H")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Word Wrap", command=self.toggle_word_wrap)
        view_menu.add_command(label="Line Numbers", command=self.toggle_line_numbers)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Word Count", command=self.word_count)
        tools_menu.add_command(label="Go to Line", command=self.go_to_line, accelerator="Ctrl+G")
        
    def create_toolbar(self):
        """Create toolbar"""
        theme = self.config_manager.get_theme()
        
        toolbar = tk.Frame(self.window, bg=theme["bg_secondary"], height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # File operations
        file_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        file_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(file_frame, text="New", command=self.new_file,
                 bg=theme["accent_primary"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="Open", command=self.open_file,
                 bg=theme["accent_primary"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="Save", command=self.save_file,
                 bg=theme["accent_primary"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        
        # Separator
        tk.Frame(toolbar, bg=theme["border"], width=2).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Edit operations
        edit_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        edit_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(edit_frame, text="Undo", command=self.undo,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(edit_frame, text="Redo", command=self.redo,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=10).pack(side=tk.LEFT, padx=2)
        
        # Separator
        tk.Frame(toolbar, bg=theme["border"], width=2).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Search
        search_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        search_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(search_frame, text="Find", command=self.find,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=10).pack(side=tk.LEFT, padx=2)
        
        # Font size
        font_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        font_frame.pack(side=tk.RIGHT, padx=5, pady=5)
        
        tk.Label(font_frame, text="Font Size:", bg=theme["bg_secondary"],
                fg=theme["fg_primary"]).pack(side=tk.LEFT, padx=2)
        
        self.font_size_var = tk.StringVar(value="12")
        font_combo = ttk.Combobox(font_frame, textvariable=self.font_size_var,
                                 values=["8", "9", "10", "11", "12", "14", "16", "18", "20", "24"],
                                 width=5, state="readonly")
        font_combo.pack(side=tk.LEFT, padx=2)
        font_combo.bind('<<ComboboxSelected>>', self.change_font_size)
        
    def create_text_area(self):
        """Create text editing area"""
        theme = self.config_manager.get_theme()
        
        # Main frame for text area
        text_frame = tk.Frame(self.window, bg=theme["bg_primary"])
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers frame
        self.line_numbers_frame = tk.Frame(text_frame, bg=theme["bg_secondary"], width=50)
        self.line_numbers_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.line_numbers = tk.Text(self.line_numbers_frame, width=4, padx=3, takefocus=0,
                                   border=0, state='disabled', wrap='none',
                                   bg=theme["bg_secondary"], fg=theme["fg_tertiary"],
                                   font=("Ubuntu Mono", 12))
        self.line_numbers.pack(side=tk.TOP, fill=tk.Y)
        
        # Text widget with scrollbars
        text_container = tk.Frame(text_frame, bg=theme["bg_primary"])
        text_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.text_widget = tk.Text(text_container, wrap=tk.WORD, undo=True,
                                  bg=theme["bg_primary"], fg=theme["fg_primary"],
                                  insertbackground=theme["fg_primary"],
                                  selectbackground=theme["accent_primary"],
                                  font=("Ubuntu Mono", 12))
        
        # Scrollbars
        v_scrollbar = tk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.text_widget.yview)
        h_scrollbar = tk.Scrollbar(text_container, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        
        self.text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure syntax highlighting
        self.configure_syntax_highlighting()
        
    def create_status_bar(self):
        """Create status bar"""
        theme = self.config_manager.get_theme()
        
        self.status_bar = tk.Frame(self.window, bg=theme["bg_secondary"], height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)
        
        # Status labels
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.status_bar, textvariable=self.status_var,
                                    font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                    fg=theme["fg_secondary"])
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Cursor position
        self.cursor_var = tk.StringVar(value="Line 1, Column 1")
        self.cursor_label = tk.Label(self.status_bar, textvariable=self.cursor_var,
                                    font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                    fg=theme["fg_secondary"])
        self.cursor_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
        # File encoding
        self.encoding_var = tk.StringVar(value="UTF-8")
        self.encoding_label = tk.Label(self.status_bar, textvariable=self.encoding_var,
                                      font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                      fg=theme["fg_secondary"])
        self.encoding_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
    def configure_syntax_highlighting(self):
        """Configure syntax highlighting"""
        theme = self.config_manager.get_theme()
        
        # Define syntax highlighting tags
        self.text_widget.tag_configure("keyword", foreground="#ff79c6", font=("Ubuntu Mono", 12, "bold"))
        self.text_widget.tag_configure("string", foreground="#f1fa8c")
        self.text_widget.tag_configure("comment", foreground="#6272a4", font=("Ubuntu Mono", 12, "italic"))
        self.text_widget.tag_configure("number", foreground="#bd93f9")
        self.text_widget.tag_configure("function", foreground="#50fa7b")
        
    def bind_events(self):
        """Bind keyboard and mouse events"""
        # Keyboard shortcuts
        self.window.bind('<Control-n>', lambda e: self.new_file())
        self.window.bind('<Control-o>', lambda e: self.open_file())
        self.window.bind('<Control-s>', lambda e: self.save_file())
        self.window.bind('<Control-Shift-S>', lambda e: self.save_as())
        self.window.bind('<Control-z>', lambda e: self.undo())
        self.window.bind('<Control-y>', lambda e: self.redo())
        self.window.bind('<Control-f>', lambda e: self.find())
        self.window.bind('<Control-h>', lambda e: self.replace())
        self.window.bind('<Control-g>', lambda e: self.go_to_line())
        self.window.bind('<Control-a>', lambda e: self.select_all())
        self.window.bind('<Control-plus>', lambda e: self.zoom_in())
        self.window.bind('<Control-minus>', lambda e: self.zoom_out())
        
        # Text change events
        self.text_widget.bind('<KeyRelease>', self.on_text_change)
        self.text_widget.bind('<Button-1>', self.update_cursor_position)
        self.text_widget.bind('<KeyPress>', self.update_cursor_position)
        
        # Window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_text_change(self, event=None):
        """Handle text change events"""
        self.modified = True
        self.update_title()
        self.update_line_numbers()
        self.apply_syntax_highlighting()
        self.update_cursor_position()
        
    def update_title(self):
        """Update window title"""
        title = "Text Editor - Berke0S"
        if self.file_path:
            title = f"{os.path.basename(self.file_path)} - Text Editor - Berke0S"
        if self.modified:
            title = "* " + title
        self.window.title(title)
        
    def update_line_numbers(self):
        """Update line numbers"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        # Get number of lines
        line_count = int(self.text_widget.index('end-1c').split('.')[0])
        
        # Generate line numbers
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert('1.0', line_numbers_text)
        
        self.line_numbers.config(state='disabled')
        
    def update_cursor_position(self, event=None):
        """Update cursor position in status bar"""
        cursor_pos = self.text_widget.index(tk.INSERT)
        line, column = cursor_pos.split('.')
        self.cursor_var.set(f"Line {line}, Column {int(column) + 1}")
        
    def apply_syntax_highlighting(self):
        """Apply syntax highlighting based on file extension"""
        if not self.file_path:
            return
            
        ext = os.path.splitext(self.file_path)[1].lower()
        
        # Clear existing tags
        for tag in ["keyword", "string", "comment", "number", "function"]:
            self.text_widget.tag_remove(tag, "1.0", tk.END)
            
        content = self.text_widget.get("1.0", tk.END)
        
        if ext == '.py':
            self.highlight_python(content)
        elif ext in ['.js', '.json']:
            self.highlight_javascript(content)
        elif ext in ['.html', '.htm']:
            self.highlight_html(content)
        elif ext == '.css':
            self.highlight_css(content)
            
    def highlight_python(self, content):
        """Highlight Python syntax"""
        import re
        
        # Keywords
        keywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 
                   'finally', 'import', 'from', 'as', 'return', 'yield', 'break', 'continue',
                   'pass', 'and', 'or', 'not', 'in', 'is', 'lambda', 'with', 'global', 'nonlocal']
        
        for keyword in keywords:
            pattern = r'\b' + keyword + r'\b'
            for match in re.finditer(pattern, content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text_widget.tag_add("keyword", start, end)
                
        # Strings
        string_patterns = [r'"[^"]*"', r"'[^']*'", r'""".*?"""', r"'''.*?'''"]
        for pattern in string_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text_widget.tag_add("string", start, end)
                
        # Comments
        for match in re.finditer(r'#.*$', content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("comment", start, end)
            
        # Numbers
        for match in re.finditer(r'\b\d+\.?\d*\b', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("number", start, end)
            
    def highlight_javascript(self, content):
        """Highlight JavaScript syntax"""
        import re
        
        # Keywords
        keywords = ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'do',
                   'switch', 'case', 'default', 'break', 'continue', 'return', 'try', 'catch',
                   'finally', 'throw', 'new', 'this', 'typeof', 'instanceof']
        
        for keyword in keywords:
            pattern = r'\b' + keyword + r'\b'
            for match in re.finditer(pattern, content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text_widget.tag_add("keyword", start, end)
                
        # Strings
        string_patterns = [r'"[^"]*"', r"'[^']*'", r'`[^`]*`']
        for pattern in string_patterns:
            for match in re.finditer(pattern, content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text_widget.tag_add("string", start, end)
                
        # Comments
        for match in re.finditer(r'//.*$|/\*.*?\*/', content, re.MULTILINE | re.DOTALL):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("comment", start, end)
            
    def highlight_html(self, content):
        """Highlight HTML syntax"""
        import re
        
        # Tags
        for match in re.finditer(r'<[^>]+>', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("keyword", start, end)
            
        # Strings (attributes)
        for match in re.finditer(r'"[^"]*"|\'[^\']*\'', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("string", start, end)
            
        # Comments
        for match in re.finditer(r'<!--.*?-->', content, re.DOTALL):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("comment", start, end)
            
    def highlight_css(self, content):
        """Highlight CSS syntax"""
        import re
        
        # Selectors
        for match in re.finditer(r'[^{]+(?=\s*{)', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("keyword", start, end)
            
        # Properties
        for match in re.finditer(r'[^:]+(?=\s*:)', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("function", start, end)
            
        # Values
        for match in re.finditer(r':\s*[^;]+', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("string", start, end)
            
        # Comments
        for match in re.finditer(r'/\*.*?\*/', content, re.DOTALL):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add("comment", start, end)
            
    def new_file(self):
        """Create new file"""
        if self.modified:
            if not self.ask_save_changes():
                return
                
        self.text_widget.delete("1.0", tk.END)
        self.file_path = None
        self.modified = False
        self.update_title()
        self.status_var.set("New file created")
        
    def open_file(self):
        """Open file dialog and load file"""
        if self.modified:
            if not self.ask_save_changes():
                return
                
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("JavaScript files", "*.js"),
                ("HTML files", "*.html *.htm"),
                ("CSS files", "*.css"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.file_path = file_path
            self.load_file()
            
    def load_file(self):
        """Load file content"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", content)
            
            self.modified = False
            self.update_title()
            self.update_line_numbers()
            self.apply_syntax_highlighting()
            
            self.status_var.set(f"Loaded: {os.path.basename(self.file_path)}")
            
            # Log file access
            if self.user_info:
                self.db_manager.log_action(self.user_info[0], "OPEN_TEXT_FILE", 
                                         f"Opened {self.file_path} in text editor")
                
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file: {str(e)}")
            self.status_var.set(f"Error loading file: {str(e)}")
            
    def save_file(self):
        """Save current file"""
        if not self.file_path:
            self.save_as()
            return
            
        try:
            content = self.text_widget.get("1.0", tk.END + "-1c")
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.modified = False
            self.update_title()
            self.status_var.set(f"Saved: {os.path.basename(self.file_path)}")
            
            # Log file save
            if self.user_info:
                self.db_manager.log_action(self.user_info[0], "SAVE_TEXT_FILE", 
                                         f"Saved {self.file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Cannot save file: {str(e)}")
            self.status_var.set(f"Error saving file: {str(e)}")
            
    def save_as(self):
        """Save file with new name"""
        file_path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("JavaScript files", "*.js"),
                ("HTML files", "*.html"),
                ("CSS files", "*.css"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.file_path = file_path
            self.save_file()
            
    def ask_save_changes(self):
        """Ask user to save changes"""
        if not self.modified:
            return True
            
        result = messagebox.askyesnocancel(
            "Save Changes",
            "Do you want to save changes to the current file?"
        )
        
        if result is True:  # Yes
            self.save_file()
            return not self.modified  # Return True if save was successful
        elif result is False:  # No
            return True
        else:  # Cancel
            return False
            
    def undo(self):
        """Undo last action"""
        try:
            self.text_widget.edit_undo()
            self.on_text_change()
        except tk.TclError:
            pass
            
    def redo(self):
        """Redo last undone action"""
        try:
            self.text_widget.edit_redo()
            self.on_text_change()
        except tk.TclError:
            pass
            
    def cut(self):
        """Cut selected text"""
        try:
            self.text_widget.event_generate("<<Cut>>")
            self.on_text_change()
        except tk.TclError:
            pass
            
    def copy(self):
        """Copy selected text"""
        try:
            self.text_widget.event_generate("<<Copy>>")
        except tk.TclError:
            pass
            
    def paste(self):
        """Paste text from clipboard"""
        try:
            self.text_widget.event_generate("<<Paste>>")
            self.on_text_change()
        except tk.TclError:
            pass
            
    def select_all(self):
        """Select all text"""
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        self.text_widget.see(tk.INSERT)
        
    def find(self):
        """Open find dialog"""
        FindDialog(self.window, self.text_widget)
        
    def replace(self):
        """Open replace dialog"""
        ReplaceDialog(self.window, self.text_widget)
        
    def go_to_line(self):
        """Go to specific line"""
        line_num = simpledialog.askinteger("Go to Line", "Enter line number:")
        if line_num:
            self.text_widget.mark_set(tk.INSERT, f"{line_num}.0")
            self.text_widget.see(tk.INSERT)
            self.update_cursor_position()
            
    def word_count(self):
        """Show word count dialog"""
        content = self.text_widget.get("1.0", tk.END + "-1c")
        
        lines = len(content.splitlines())
        words = len(content.split())
        chars = len(content)
        chars_no_spaces = len(content.replace(" ", "").replace("\n", "").replace("\t", ""))
        
        message = f"Lines: {lines}\nWords: {words}\nCharacters: {chars}\nCharacters (no spaces): {chars_no_spaces}"
        messagebox.showinfo("Word Count", message)
        
    def toggle_word_wrap(self):
        """Toggle word wrap"""
        current_wrap = self.text_widget.cget("wrap")
        new_wrap = tk.NONE if current_wrap == tk.WORD else tk.WORD
        self.text_widget.config(wrap=new_wrap)
        
    def toggle_line_numbers(self):
        """Toggle line numbers visibility"""
        if self.line_numbers_frame.winfo_viewable():
            self.line_numbers_frame.pack_forget()
        else:
            self.line_numbers_frame.pack(side=tk.LEFT, fill=tk.Y, before=self.text_widget.master)
            
    def zoom_in(self):
        """Increase font size"""
        current_size = int(self.font_size_var.get())
        new_size = min(current_size + 2, 24)
        self.font_size_var.set(str(new_size))
        self.change_font_size()
        
    def zoom_out(self):
        """Decrease font size"""
        current_size = int(self.font_size_var.get())
        new_size = max(current_size - 2, 8)
        self.font_size_var.set(str(new_size))
        self.change_font_size()
        
    def change_font_size(self, event=None):
        """Change font size"""
        size = int(self.font_size_var.get())
        font = ("Ubuntu Mono", size)
        self.text_widget.config(font=font)
        self.line_numbers.config(font=font)
        
    def print_file(self):
        """Print file (placeholder)"""
        messagebox.showinfo("Print", "Print functionality not implemented yet.")
        
    def on_closing(self):
        """Handle window closing"""
        if self.modified:
            if self.ask_save_changes():
                self.window.destroy()
        else:
            self.window.destroy()

class FindDialog:
    """Find text dialog"""
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        self.last_search_index = "1.0"
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create find dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Find")
        self.dialog.geometry("350x150")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"350x150+{x}+{y}")
        
        # Get theme
        config_manager = ConfigManager()
        theme = config_manager.get_theme()
        self.dialog.configure(bg=theme["bg_primary"])
        
        # Search input
        tk.Label(self.dialog, text="Find:", font=("Ubuntu", 10),
                bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(pady=10)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(self.dialog, textvariable=self.search_var,
                               font=("Ubuntu", 10), bg=theme["bg_tertiary"],
                               fg=theme["fg_primary"], width=30)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        # Options
        options_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        options_frame.pack(pady=10)
        
        self.case_sensitive_var = tk.BooleanVar()
        tk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive_var,
                      bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Find Next", command=self.find_next,
                 bg=theme["accent_primary"], fg="white", padx=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Close", command=self.dialog.destroy,
                 bg=theme["error"], fg="white", padx=15).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.find_next())
        
    def find_next(self):
        """Find next occurrence"""
        search_text = self.search_var.get()
        if not search_text:
            return
            
        # Clear previous highlights
        self.text_widget.tag_remove("search_highlight", "1.0", tk.END)
        
        # Search options
        nocase = 0 if self.case_sensitive_var.get() else 1
        
        # Find text
        pos = self.text_widget.search(search_text, self.last_search_index, tk.END, nocase=nocase)
        
        if pos:
            # Highlight found text
            end_pos = f"{pos}+{len(search_text)}c"
            self.text_widget.tag_add("search_highlight", pos, end_pos)
            self.text_widget.tag_config("search_highlight", background="yellow", foreground="black")
            
            # Move cursor and scroll to position
            self.text_widget.mark_set(tk.INSERT, pos)
            self.text_widget.see(pos)
            
            # Update search index for next search
            self.last_search_index = end_pos
        else:
            # Not found, start from beginning
            self.last_search_index = "1.0"
            messagebox.showinfo("Find", f"'{search_text}' not found.")

class ReplaceDialog:
    """Find and replace dialog"""
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        self.last_search_index = "1.0"
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create replace dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Find and Replace")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"400x200+{x}+{y}")
        
        # Get theme
        config_manager = ConfigManager()
        theme = config_manager.get_theme()
        self.dialog.configure(bg=theme["bg_primary"])
        
        # Find input
        tk.Label(self.dialog, text="Find:", font=("Ubuntu", 10),
                bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(pady=5)
        
        self.find_var = tk.StringVar()
        find_entry = tk.Entry(self.dialog, textvariable=self.find_var,
                             font=("Ubuntu", 10), bg=theme["bg_tertiary"],
                             fg=theme["fg_primary"], width=35)
        find_entry.pack(pady=2)
        find_entry.focus()
        
        # Replace input
        tk.Label(self.dialog, text="Replace with:", font=("Ubuntu", 10),
                bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(pady=5)
        
        self.replace_var = tk.StringVar()
        replace_entry = tk.Entry(self.dialog, textvariable=self.replace_var,
                                font=("Ubuntu", 10), bg=theme["bg_tertiary"],
                                fg=theme["fg_primary"], width=35)
        replace_entry.pack(pady=2)
        
        # Options
        options_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        options_frame.pack(pady=10)
        
        self.case_sensitive_var = tk.BooleanVar()
        tk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive_var,
                      bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Find Next", command=self.find_next,
                 bg=theme["accent_primary"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        
        tk.Button(button_frame, text="Replace", command=self.replace_current,
                 bg=theme["warning"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        
        tk.Button(button_frame, text="Replace All", command=self.replace_all,
                 bg=theme["warning"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        
        tk.Button(button_frame, text="Close", command=self.dialog.destroy,
                 bg=theme["error"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        
    def find_next(self):
        """Find next occurrence"""
        find_text = self.find_var.get()
        if not find_text:
            return
            
        # Clear previous highlights
        self.text_widget.tag_remove("search_highlight", "1.0", tk.END)
        
        # Search options
        nocase = 0 if self.case_sensitive_var.get() else 1
        
        # Find text
        pos = self.text_widget.search(find_text, self.last_search_index, tk.END, nocase=nocase)
        
        if pos:
            # Highlight found text
            end_pos = f"{pos}+{len(find_text)}c"
            self.text_widget.tag_add("search_highlight", pos, end_pos)
            self.text_widget.tag_config("search_highlight", background="yellow", foreground="black")
            
            # Move cursor and scroll to position
            self.text_widget.mark_set(tk.INSERT, pos)
            self.text_widget.see(pos)
            
            # Update search index for next search
            self.last_search_index = end_pos
        else:
            # Not found, start from beginning
            self.last_search_index = "1.0"
            messagebox.showinfo("Find", f"'{find_text}' not found.")
            
    def replace_current(self):
        """Replace current selection"""
        if self.text_widget.tag_ranges("search_highlight"):
            # Get highlighted text range
            start = self.text_widget.index("search_highlight.first")
            end = self.text_widget.index("search_highlight.last")
            
            # Replace text
            self.text_widget.delete(start, end)
            self.text_widget.insert(start, self.replace_var.get())
            
            # Clear highlight
            self.text_widget.tag_remove("search_highlight", "1.0", tk.END)
            
            # Find next occurrence
            self.find_next()
            
    def replace_all(self):
        """Replace all occurrences"""
        find_text = self.find_var.get()
        replace_text = self.replace_var.get()
        
        if not find_text:
            return
            
        # Get all text
        content = self.text_widget.get("1.0", tk.END + "-1c")
        
        # Count occurrences
        if self.case_sensitive_var.get():
            count = content.count(find_text)
            new_content = content.replace(find_text, replace_text)
        else:
            import re
            count = len(re.findall(re.escape(find_text), content, re.IGNORECASE))
            new_content = re.sub(re.escape(find_text), replace_text, content, flags=re.IGNORECASE)
            
        if count > 0:
            # Replace all text
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", new_content)
            
            messagebox.showinfo("Replace All", f"Replaced {count} occurrences.")
        else:
            messagebox.showinfo("Replace All", f"'{find_text}' not found.")

class Calculator:
    """Advanced scientific calculator"""
    
    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        
        self.expression = ""
        self.result = 0
        self.memory = 0
        self.history = []
        
        self.create_window()
        
    def create_window(self):
        """Create calculator window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Calculator - Berke0S")
        self.window.geometry("400x600")
        self.window.resizable(False, False)
        
        # Get theme
        theme = self.config_manager.get_theme()
        self.window.configure(bg=theme["bg_primary"])
        
        # Create display
        self.create_display()
        
        # Create buttons
        self.create_buttons()
        
        # Create menu
        self.create_menu()
        
        # Log calculator open
        if self.user_info:
            self.db_manager.log_action(self.user_info[0], "OPEN_CALCULATOR", "Opened calculator")
            
    def create_display(self):
        """Create calculator display"""
        theme = self.config_manager.get_theme()
        
        display_frame = tk.Frame(self.window, bg=theme["bg_secondary"], height=120)
        display_frame.pack(fill=tk.X, padx=10, pady=10)
        display_frame.pack_propagate(False)
        
        # Expression display
        self.expression_var = tk.StringVar(value="0")
        expression_label = tk.Label(display_frame, textvariable=self.expression_var,
                                   font=("Ubuntu Mono", 12), bg=theme["bg_secondary"],
                                   fg=theme["fg_secondary"], anchor="e")
        expression_label.pack(fill=tk.X, padx=10, pady=5)
        
        # Result display
        self.result_var = tk.StringVar(value="0")
        result_label = tk.Label(display_frame, textvariable=self.result_var,
                               font=("Ubuntu Mono", 20, "bold"), bg=theme["bg_secondary"],
                               fg=theme["fg_primary"], anchor="e")
        result_label.pack(fill=tk.X, padx=10, pady=5)
        
    def create_buttons(self):
        """Create calculator buttons"""
        theme = self.config_manager.get_theme()
        
        button_frame = tk.Frame(self.window, bg=theme["bg_primary"])
        button_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Button configuration
        button_config = {
            "font": ("Ubuntu", 12, "bold"),
            "width": 6,
            "height": 2,
            "relief": tk.RAISED,
            "bd": 2
        }
        
        # Button layout (text, row, col, colspan, color_type)
        buttons = [
            # Row 0 - Memory and functions
            ("MC", 0, 0, 1, "memory"),
            ("MR", 0, 1, 1, "memory"),
            ("M+", 0, 2, 1, "memory"),
            ("M-", 0, 3, 1, "memory"),
            ("MS", 0, 4, 1, "memory"),
            
            # Row 1 - Advanced functions
            ("sin", 1, 0, 1, "function"),
            ("cos", 1, 1, 1, "function"),
            ("tan", 1, 2, 1, "function"),
            ("log", 1, 3, 1, "function"),
            ("ln", 1, 4, 1, "function"),
            
            # Row 2 - More functions
            ("√", 2, 0, 1, "function"),
            ("x²", 2, 1, 1, "function"),
            ("x^y", 2, 2, 1, "function"),
            ("π", 2, 3, 1, "function"),
            ("e", 2, 4, 1, "function"),
            
            # Row 3 - Clear and operations
            ("C", 3, 0, 1, "clear"),
            ("CE", 3, 1, 1, "clear"),
            ("⌫", 3, 2, 1, "clear"),
            ("±", 3, 3, 1, "operation"),
            ("÷", 3, 4, 1, "operation"),
            
            # Row 4 - Numbers and operations
            ("7", 4, 0, 1, "number"),
            ("8", 4, 1, 1, "number"),
            ("9", 4, 2, 1, "number"),
            ("×", 4, 3, 1, "operation"),
            ("(", 4, 4, 1, "operation"),
            
            # Row 5
            ("4", 5, 0, 1, "number"),
            ("5", 5, 1, 1, "number"),
            ("6", 5, 2, 1, "number"),
            ("-", 5, 3, 1, "operation"),
            (")", 5, 4, 1, "operation"),
            
            # Row 6
            ("1", 6, 0, 1, "number"),
            ("2", 6, 1, 1, "number"),
            ("3", 6, 2, 1, "number"),
            ("+", 6, 3, 1, "operation"),
            ("=", 6, 4, 2, "equals"),
            
            # Row 7
            ("0", 7, 0, 2, "number"),
            (".", 7, 2, 1, "number"),
            ("%", 7, 3, 1, "operation"),
        ]
        
        # Color schemes for different button types
        colors = {
            "number": {"bg": theme["bg_tertiary"], "fg": theme["fg_primary"]},
            "operation": {"bg": theme["accent_primary"], "fg": "white"},
            "equals": {"bg": theme["success"], "fg": "white"},
            "clear": {"bg": theme["error"], "fg": "white"},
            "function": {"bg": theme["warning"], "fg": "white"},
            "memory": {"bg": theme["info"], "fg": "white"}
        }
        
        # Create buttons
        for button_text, row, col, colspan, color_type in buttons:
            color = colors[color_type]
            
            btn = tk.Button(button_frame, text=button_text,
                           command=lambda t=button_text: self.button_click(t),
                           bg=color["bg"], fg=color["fg"],
                           activebackground=color["bg"], activeforeground=color["fg"],
                           **button_config)
            
            btn.grid(row=row, column=col, columnspan=colspan, padx=2, pady=2, sticky="nsew")
            
        # Configure grid weights
        for i in range(8):
            button_frame.grid_rowconfigure(i, weight=1)
        for i in range(5):
            button_frame.grid_columnconfigure(i, weight=1)
            
    def create_menu(self):
        """Create calculator menu"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="History", command=self.show_history)
        view_menu.add_command(label="Copy Result", command=self.copy_result)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def button_click(self, button_text):
        """Handle button clicks"""
        try:
            if button_text.isdigit() or button_text == ".":
                self.add_to_expression(button_text)
            elif button_text in ["+", "-", "×", "÷", "%", "(", ")"]:
                self.add_operator(button_text)
            elif button_text == "=":
                self.calculate()
            elif button_text == "C":
                self.clear_all()
            elif button_text == "CE":
                self.clear_entry()
            elif button_text == "⌫":
                self.backspace()
            elif button_text == "±":
                self.toggle_sign()
            elif button_text in ["sin", "cos", "tan", "log", "ln", "√"]:
                self.apply_function(button_text)
            elif button_text == "x²":
                self.apply_function("square")
            elif button_text == "x^y":
                self.add_operator("^")
            elif button_text == "π":
                self.add_constant("π")
            elif button_text == "e":
                self.add_constant("e")
            elif button_text.startswith("M"):
                self.memory_operation(button_text)
                
        except Exception as e:
            self.show_error(str(e))
            
    def add_to_expression(self, text):
        """Add text to expression"""
        if self.expression == "0" or self.expression == "Error":
            self.expression = text
        else:
            self.expression += text
        self.update_display()
        
    def add_operator(self, operator):
        """Add operator to expression"""
        # Convert display operators to calculation operators
        op_map = {"×": "*", "÷": "/", "^": "**"}
        calc_op = op_map.get(operator, operator)
        
        if self.expression and self.expression[-1] not in "+-*/()^":
            self.expression += calc_op
        elif operator in ["(", ")"]:
            self.expression += operator
            
        self.update_display()
        
    def add_constant(self, constant):
        """Add mathematical constant"""
        if constant == "π":
            value = str(math.pi)
        elif constant == "e":
            value = str(math.e)
            
        if self.expression == "0" or self.expression == "Error":
            self.expression = value
        else:
            self.expression += value
            
        self.update_display()
        
    def apply_function(self, function):
        """Apply mathematical function"""
        try:
            if self.expression and self.expression != "Error":
                current_value = float(eval(self.expression))
                
                if function == "sin":
                    result = math.sin(math.radians(current_value))
                elif function == "cos":
                    result = math.cos(math.radians(current_value))
                elif function == "tan":
                    result = math.tan(math.radians(current_value))
                elif function == "log":
                    result = math.log10(current_value)
                elif function == "ln":
                    result = math.log(current_value)
                elif function == "√":
                    result = math.sqrt(current_value)
                elif function == "square":
                    result = current_value ** 2
                    
                self.expression = str(result)
                self.result = result
                self.update_display()
                
        except Exception as e:
            self.show_error("Math Error")
            
    def calculate(self):
        """Calculate expression result"""
        try:
            if self.expression and self.expression != "Error":
                # Replace display operators with Python operators
                calc_expression = self.expression.replace("×", "*").replace("÷", "/")
                
                # Evaluate expression
                result = eval(calc_expression)
                
                # Add to history
                self.history.append(f"{self.expression} = {result}")
                
                # Update display
                self.result = result
                self.expression = str(result)
                self.update_display()
                
                # Log calculation
                if self.user_info:
                    self.db_manager.log_action(self.user_info[0], "CALCULATE", 
                                             f"Calculated: {calc_expression} = {result}")
                    
        except Exception as e:
            self.show_error("Error")
            
    def clear_all(self):
        """Clear all"""
        self.expression = "0"
        self.result = 0
        self.update_display()
        
    def clear_entry(self):
        """Clear current entry"""
        self.expression = "0"
        self.update_display()
        
    def backspace(self):
        """Remove last character"""
        if len(self.expression) > 1:
            self.expression = self.expression[:-1]
        else:
            self.expression = "0"
        self.update_display()
        
    def toggle_sign(self):
        """Toggle sign of current number"""
        try:
            if self.expression and self.expression != "0" and self.expression != "Error":
                if self.expression.startswith("-"):
                    self.expression = self.expression[1:]
                else:
                    self.expression = "-" + self.expression
                self.update_display()
        except:
            pass
            
    def memory_operation(self, operation):
        """Handle memory operations"""
        try:
            if operation == "MC":  # Memory Clear
                self.memory = 0
            elif operation == "MR":  # Memory Recall
                self.expression = str(self.memory)
                self.update_display()
            elif operation == "M+":  # Memory Add
                if self.expression and self.expression != "Error":
                    self.memory += float(self.expression)
            elif operation == "M-":  # Memory Subtract
                if self.expression and self.expression != "Error":
                    self.memory -= float(self.expression)
            elif operation == "MS":  # Memory Store
                if self.expression and self.expression != "Error":
                    self.memory = float(self.expression)
                    
        except Exception as e:
            self.show_error("Memory Error")
            
    def update_display(self):
        """Update calculator display"""
        # Format expression for display
        display_expr = self.expression.replace("*", "×").replace("/", "÷")
        self.expression_var.set(display_expr)
        
        # Update result display
        if self.expression == "Error":
            self.result_var.set("Error")
        else:
            try:
                # Try to evaluate for live preview
                calc_expr = self.expression.replace("×", "*").replace("÷", "/")
                preview = eval(calc_expr)
                self.result_var.set(f"{preview:,.10g}")
            except:
                self.result_var.set(display_expr)
                
    def show_error(self, message):
        """Show error message"""
        self.expression = "Error"
        self.result_var.set(message)
        self.expression_var.set("")
        
    def show_history(self):
        """Show calculation history"""
        HistoryDialog(self.window, self.history)
        
    def copy_result(self):
        """Copy result to clipboard"""
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(str(self.result))
            messagebox.showinfo("Calculator", "Result copied to clipboard")
        except:
            messagebox.showerror("Calculator", "Cannot copy to clipboard")
            
    def show_about(self):
        """Show about dialog"""
        about_text = """
Calculator - Berke0S

Advanced Scientific Calculator
Version 2.0

Features:
• Basic arithmetic operations
• Scientific functions
• Memory operations
• Calculation history
• Keyboard shortcuts

Created by: Berke Oruç
        """
        messagebox.showinfo("About Calculator", about_text.strip())

class HistoryDialog:
    """Calculator history dialog"""
    
    def __init__(self, parent, history):
        self.parent = parent
        self.history = history
        self.create_dialog()
        
    def create_dialog(self):
        """Create history dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Calculation History")
        self.dialog.geometry("400x300")
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        # Get theme
        config_manager = ConfigManager()
        theme = config_manager.get_theme()
        self.dialog.configure(bg=theme["bg_primary"])
        
        # History list
        tk.Label(self.dialog, text="Calculation History", font=("Ubuntu", 12, "bold"),
                bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(pady=10)
        
        list_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.history_listbox = tk.Listbox(list_frame, bg=theme["bg_tertiary"],
                                         fg=theme["fg_primary"], font=("Ubuntu Mono", 10))
        scrollbar = tk.Scrollbar(list_frame, command=self.history_listbox.yview)
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate history
        for calculation in self.history:
            self.history_listbox.insert(tk.END, calculation)
            
        # Buttons
        button_frame = tk.Frame(self.dialog, bg=theme["bg_primary"])
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="Clear History", command=self.clear_history,
                 bg=theme["error"], fg="white", padx=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Close", command=self.dialog.destroy,
                 bg=theme["accent_primary"], fg="white", padx=15).pack(side=tk.RIGHT, padx=5)
        
    def clear_history(self):
        """Clear calculation history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the calculation history?"):
            self.history.clear()
            self.history_listbox.delete(0, tk.END)

class ImageViewer:
    """Advanced image viewer with editing capabilities"""
    
    def __init__(self, parent, image_path=None, user_info=None):
        self.parent = parent
        self.image_path = image_path
        self.user_info = user_info
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        
        self.original_image = None
        self.current_image = None
        self.photo = None
        self.zoom_factor = 1.0
        self.rotation_angle = 0
        
        self.create_window()
        
        if image_path:
            self.load_image()
            
    def create_window(self):
        """Create image viewer window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Image Viewer - Berke0S")
        self.window.geometry("800x600")
        
        # Get theme
        theme = self.config_manager.get_theme()
        self.window.configure(bg=theme["bg_primary"])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create image canvas
        self.create_canvas()
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_image)
        file_menu.add_command(label="Save As", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Print", command=self.print_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.destroy)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Rotate Left", command=self.rotate_left)
        edit_menu.add_command(label="Rotate Right", command=self.rotate_right)
        edit_menu.add_command(label="Flip Horizontal", command=self.flip_horizontal)
        edit_menu.add_command(label="Flip Vertical", command=self.flip_vertical)
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset", command=self.reset_image)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        view_menu.add_command(label="Fit to Window", command=self.fit_to_window)
        view_menu.add_command(label="Actual Size", command=self.actual_size)
        view_menu.add_separator()
        view_menu.add_command(label="Fullscreen", command=self.toggle_fullscreen)
        
    def create_toolbar(self):
        """Create toolbar"""
        theme = self.config_manager.get_theme()
        
        toolbar = tk.Frame(self.window, bg=theme["bg_secondary"], height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # File operations
        file_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        file_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(file_frame, text="Open", command=self.open_image,
                 bg=theme["accent_primary"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="Save", command=self.save_image,
                 bg=theme["accent_primary"], fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        
        # Separator
        tk.Frame(toolbar, bg=theme["border"], width=2).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Zoom operations
        zoom_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        zoom_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(zoom_frame, text="Zoom In", command=self.zoom_in,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(zoom_frame, text="Fit", command=self.fit_to_window,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=10).pack(side=tk.LEFT, padx=2)
        
        # Separator
        tk.Frame(toolbar, bg=theme["border"], width=2).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Rotation operations
        rotate_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        rotate_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(rotate_frame, text="↺", command=self.rotate_left,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(rotate_frame, text="↻", command=self.rotate_right,
                 bg=theme["bg_tertiary"], fg=theme["fg_primary"], padx=10).pack(side=tk.LEFT, padx=2)
        
        # Zoom level display
        zoom_info_frame = tk.Frame(toolbar, bg=theme["bg_secondary"])
        zoom_info_frame.pack(side=tk.RIGHT, padx=5, pady=5)
        
        tk.Label(zoom_info_frame, text="Zoom:", bg=theme["bg_secondary"],
                fg=theme["fg_primary"]).pack(side=tk.LEFT, padx=2)
        
        self.zoom_var = tk.StringVar(value="100%")
        tk.Label(zoom_info_frame, textvariable=self.zoom_var, bg=theme["bg_secondary"],
                fg=theme["fg_primary"], font=("Ubuntu", 10, "bold")).pack(side=tk.LEFT, padx=2)
        
    def create_canvas(self):
        """Create image canvas"""
        theme = self.config_manager.get_theme()
        
        # Canvas frame with scrollbars
        canvas_frame = tk.Frame(self.window, bg=theme["bg_primary"])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg=theme["bg_primary"],
                               highlightthickness=0)
        
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        
    def create_status_bar(self):
        """Create status bar"""
        theme = self.config_manager.get_theme()
        
        self.status_bar = tk.Frame(self.window, bg=theme["bg_secondary"], height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)
        
        # Status labels
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.status_bar, textvariable=self.status_var,
                                    font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                    fg=theme["fg_secondary"])
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Image info
        self.info_var = tk.StringVar()
        self.info_label = tk.Label(self.status_bar, textvariable=self.info_var,
                                  font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                  fg=theme["fg_secondary"])
        self.info_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
    def open_image(self):
        """Open image file"""
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("GIF files", "*.gif"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.image_path = file_path
            self.load_image()
            
    def load_image(self):
        """Load image from file"""
        if not PIL_AVAILABLE:
            messagebox.showerror("Error", "PIL library not available. Cannot load images.")
            return
            
        try:
            # Load original image
            self.original_image = Image.open(self.image_path)
            self.current_image = self.original_image.copy()
            
            # Reset transformations
            self.zoom_factor = 1.0
            self.rotation_angle = 0
            
            # Update display
            self.update_image_display()
            self.update_window_title()
            self.update_image_info()
            
            self.status_var.set(f"Loaded: {os.path.basename(self.image_path)}")
            
            # Log image access
            if self.user_info:
                self.db_manager.log_action(self.user_info[0], "OPEN_IMAGE", 
                                         f"Opened {self.image_path} in image viewer")
                
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load image: {str(e)}")
            self.status_var.set(f"Error loading image: {str(e)}")
            
    def update_image_display(self):
        """Update image display on canvas"""
        if not self.current_image:
            return
            
        try:
            # Apply zoom
            display_size = (
                int(self.current_image.width * self.zoom_factor),
                int(self.current_image.height * self.zoom_factor)
            )
            
            display_image = self.current_image.resize(display_size, Image.LANCZOS)
            
            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(display_image)
            
            # Clear canvas and add image
            self.canvas.delete("all")
            self.canvas.create_image(
                display_size[0] // 2, display_size[1] // 2,
                image=self.photo, anchor=tk.CENTER
            )
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Update zoom display
            self.zoom_var.set(f"{int(self.zoom_factor * 100)}%")
            
        except Exception as e:
            self.status_var.set(f"Display error: {str(e)}")
            
    def update_window_title(self):
        """Update window title"""
        if self.image_path:
            filename = os.path.basename(self.image_path)
            self.window.title(f"{filename} - Image Viewer - Berke0S")
        else:
            self.window.title("Image Viewer - Berke0S")
            
    def update_image_info(self):
        """Update image information in status bar"""
        if self.current_image:
            width, height = self.current_image.size
            mode = self.current_image.mode
            
            # Get file size
            try:
                file_size = os.path.getsize(self.image_path)
                size_str = self.format_file_size(file_size)
            except:
                size_str = "Unknown"
                
            self.info_var.set(f"{width}×{height} {mode} {size_str}")
        else:
            self.info_var.set("")
            
    def format_file_size(self, size):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
        
    def zoom_in(self):
        """Zoom in"""
        self.zoom_factor = min(self.zoom_factor * 1.25, 10.0)
        self.update_image_display()
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_factor = max(self.zoom_factor / 1.25, 0.1)
        self.update_image_display()
        
    def fit_to_window(self):
        """Fit image to window"""
        if not self.current_image:
            return
            
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        # Calculate zoom factor to fit image in window
        zoom_x = canvas_width / self.current_image.width
        zoom_y = canvas_height / self.current_image.height
        
        self.zoom_factor = min(zoom_x, zoom_y, 1.0)  # Don't zoom in beyond 100%
        self.update_image_display()
        
    def actual_size(self):
        """Show image at actual size"""
        self.zoom_factor = 1.0
        self.update_image_display()
        
    def rotate_left(self):
        """Rotate image 90 degrees left"""
        if not self.current_image:
            return
            
        self.current_image = self.current_image.rotate(90, expand=True)
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.update_image_display()
        self.update_image_info()
        
    def rotate_right(self):
        """Rotate image 90 degrees right"""
        if not self.current_image:
            return
            
        self.current_image = self.current_image.rotate(-90, expand=True)
        self.rotation_angle = (self.rotation_angle - 90) % 360
        self.update_image_display()
        self.update_image_info()
        
    def flip_horizontal(self):
        """Flip image horizontally"""
        if not self.current_image:
            return
            
        self.current_image = self.current_image.transpose(Image.FLIP_LEFT_RIGHT)
        self.update_image_display()
        
    def flip_vertical(self):
        """Flip image vertically"""
        if not self.current_image:
            return
            
        self.current_image = self.current_image.transpose(Image.FLIP_TOP_BOTTOM)
        self.update_image_display()
        
    def reset_image(self):
        """Reset image to original"""
        if not self.original_image:
            return
            
        self.current_image = self.original_image.copy()
        self.zoom_factor = 1.0
        self.rotation_angle = 0
        self.update_image_display()
        self.update_image_info()
        
    def save_image(self):
        """Save current image"""
        if not self.current_image or not self.image_path:
            return
            
        try:
            self.current_image.save(self.image_path)
            self.status_var.set(f"Saved: {os.path.basename(self.image_path)}")
            
            # Log save action
            if self.user_info:
                self.db_manager.log_action(self.user_info[0], "SAVE_IMAGE", 
                                         f"Saved {self.image_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Cannot save image: {str(e)}")
            
    def save_as(self):
        """Save image with new name"""
        if not self.current_image:
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Image As",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("GIF files", "*.gif"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.current_image.save(file_path)
                self.image_path = file_path
                self.update_window_title()
                self.status_var.set(f"Saved as: {os.path.basename(file_path)}")
                
                # Log save action
                if self.user_info:
                    self.db_manager.log_action(self.user_info[0], "SAVE_IMAGE_AS", 
                                             f"Saved image as {file_path}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Cannot save image: {str(e)}")
                
    def print_image(self):
        """Print image (placeholder)"""
        messagebox.showinfo("Print", "Print functionality not implemented yet.")
        
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        current_state = self.window.attributes('-fullscreen')
        self.window.attributes('-fullscreen', not current_state)
        
    def on_canvas_click(self, event):
        """Handle canvas click"""
        self.canvas.scan_mark(event.x, event.y)
        
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

class MusicPlayer:
    """Music player with playlist support"""
    
    def __init__(self, parent, music_file=None, user_info=None):
        self.parent = parent
        self.music_file = music_file
        self.user_info = user_info
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        self.duration = 0
        self.volume = 70
        
        self.create_window()
        
        if music_file:
            self.add_to_playlist(music_file)
            self.play_current()
            
    def create_window(self):
        """Create music player window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Music Player - Berke0S")
        self.window.geometry("500x400")
        
        # Get theme
        theme = self.config_manager.get_theme()
        self.window.configure(bg=theme["bg_primary"])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create player controls
        self.create_player_controls()
        
        # Create playlist
        self.create_playlist()
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Files", command=self.add_files)
        file_menu.add_command(label="Add Folder", command=self.add_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Save Playlist", command=self.save_playlist)
        file_menu.add_command(label="Load Playlist", command=self.load_playlist)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.destroy)
        
        # Playback menu
        playback_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Playback", menu=playback_menu)
        playback_menu.add_command(label="Play/Pause", command=self.toggle_playback)
        playback_menu.add_command(label="Stop", command=self.stop)
        playback_menu.add_command(label="Previous", command=self.previous_track)
        playback_menu.add_command(label="Next", command=self.next_track)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Shuffle", command=self.toggle_shuffle)
        view_menu.add_command(label="Repeat", command=self.toggle_repeat)
        
    def create_player_controls(self):
        """Create player control panel"""
        theme = self.config_manager.get_theme()
        
        # Main control frame
        control_frame = tk.Frame(self.window, bg=theme["bg_secondary"], height=120)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        control_frame.pack_propagate(False)
        
        # Track info
        info_frame = tk.Frame(control_frame, bg=theme["bg_secondary"])
        info_frame.pack(fill=tk.X, pady=5)
        
        self.track_var = tk.StringVar(value="No track loaded")
        track_label = tk.Label(info_frame, textvariable=self.track_var,
                              font=("Ubuntu", 12, "bold"), bg=theme["bg_secondary"],
                              fg=theme["fg_primary"])
        track_label.pack()
        
        self.artist_var = tk.StringVar(value="")
        artist_label = tk.Label(info_frame, textvariable=self.artist_var,
                               font=("Ubuntu", 10), bg=theme["bg_secondary"],
                               fg=theme["fg_secondary"])
        artist_label.pack()
        
        # Progress bar
        progress_frame = tk.Frame(control_frame, bg=theme["bg_secondary"])
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.time_var = tk.StringVar(value="00:00")
        time_label = tk.Label(progress_frame, textvariable=self.time_var,
                             font=("Ubuntu", 9), bg=theme["bg_secondary"],
                             fg=theme["fg_secondary"])
        time_label.pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar()
        self.progress_scale = tk.Scale(progress_frame, variable=self.progress_var,
                                      from_=0, to=100, orient=tk.HORIZONTAL,
                                      bg=theme["bg_secondary"], fg=theme["fg_primary"],
                                      highlightthickness=0, command=self.seek_position)
        self.progress_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.duration_var = tk.StringVar(value="00:00")
        duration_label = tk.Label(progress_frame, textvariable=self.duration_var,
                                 font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                 fg=theme["fg_secondary"])
        duration_label.pack(side=tk.RIGHT)
        
        # Control buttons
        button_frame = tk.Frame(control_frame, bg=theme["bg_secondary"])
        button_frame.pack(pady=10)
        
        # Previous button
        tk.Button(button_frame, text="⏮", font=("Ubuntu", 16),
                 bg=theme["accent_primary"], fg="white", width=3,
                 command=self.previous_track).pack(side=tk.LEFT, padx=5)
        
        # Play/Pause button
        self.play_button_var = tk.StringVar(value="▶")
        self.play_button = tk.Button(button_frame, textvariable=self.play_button_var,
                                    font=("Ubuntu", 16), bg=theme["success"], fg="white",
                                    width=3, command=self.toggle_playback)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        tk.Button(button_frame, text="⏹", font=("Ubuntu", 16),
                 bg=theme["error"], fg="white", width=3,
                 command=self.stop).pack(side=tk.LEFT, padx=5)
        
        # Next button
        tk.Button(button_frame, text="⏭", font=("Ubuntu", 16),
                 bg=theme["accent_primary"], fg="white", width=3,
                 command=self.next_track).pack(side=tk.LEFT, padx=5)
        
        # Volume control
        volume_frame = tk.Frame(button_frame, bg=theme["bg_secondary"])
        volume_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(volume_frame, text="🔊", font=("Ubuntu", 12),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(side=tk.LEFT)
        
        self.volume_var = tk.IntVar(value=self.volume)
        volume_scale = tk.Scale(volume_frame, variable=self.volume_var,
                               from_=0, to=100, orient=tk.HORIZONTAL,
                               bg=theme["bg_secondary"], fg=theme["fg_primary"],
                               highlightthickness=0, length=100,
                               command=self.change_volume)
        volume_scale.pack(side=tk.LEFT, padx=5)
        
    def create_playlist(self):
        """Create playlist panel"""
        theme = self.config_manager.get_theme()
        
        # Playlist frame
        playlist_frame = tk.Frame(self.window, bg=theme["bg_primary"])
        playlist_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Playlist label
        tk.Label(playlist_frame, text="Playlist", font=("Ubuntu", 12, "bold"),
                bg=theme["bg_primary"], fg=theme["fg_primary"]).pack(anchor=tk.W, pady=5)
        
        # Playlist listbox with scrollbar
        list_frame = tk.Frame(playlist_frame, bg=theme["bg_primary"])
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.playlist_listbox = tk.Listbox(list_frame, bg=theme["bg_tertiary"],
                                          fg=theme["fg_primary"], font=("Ubuntu", 10),
                                          selectbackground=theme["accent_primary"])
        scrollbar = tk.Scrollbar(list_frame, command=self.playlist_listbox.yview)
        self.playlist_listbox.config(yscrollcommand=scrollbar.set)
        
        self.playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.playlist_listbox.bind('<Double-1>', self.play_selected)
        self.playlist_listbox.bind('<Button-3>', self.show_playlist_menu)
        
    def create_status_bar(self):
        """Create status bar"""
        theme = self.config_manager.get_theme()
        
        self.status_bar = tk.Frame(self.window, bg=theme["bg_secondary"], height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)
        
        # Status labels
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.status_bar, textvariable=self.status_var,
                                    font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                    fg=theme["fg_secondary"])
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Playlist info
        self.playlist_info_var = tk.StringVar()
        self.playlist_info_label = tk.Label(self.status_bar, textvariable=self.playlist_info_var,
                                           font=("Ubuntu", 9), bg=theme["bg_secondary"],
                                           fg=theme["fg_secondary"])
        self.playlist_info_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
    def add_files(self):
        """Add music files to playlist"""
        files = filedialog.askopenfilenames(
            title="Add Music Files",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("MP3 files", "*.mp3"),
                ("WAV files", "*.wav"),
                ("OGG files", "*.ogg"),
                ("FLAC files", "*.flac"),
                ("All files", "*.*")
            ]
        )
        
        for file_path in files:
            self.add_to_playlist(file_path)
            
    def add_folder(self):
        """Add all music files from a folder"""
        folder = filedialog.askdirectory(title="Add Music Folder")
        if folder:
            audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in audio_extensions):
                        file_path = os.path.join(root, file)
                        self.add_to_playlist(file_path)
                        
    def add_to_playlist(self, file_path):
        """Add single file to playlist"""
        if file_path not in self.playlist:
            self.playlist.append(file_path)
            filename = os.path.basename(file_path)
            self.playlist_listbox.insert(tk.END, filename)
            self.update_playlist_info()
            
    def update_playlist_info(self):
        """Update playlist information"""
        count = len(self.playlist)
        if count == 0:
            self.playlist_info_var.set("Playlist empty")
        else:
            current = self.current_index + 1 if self.playlist else 0
            self.playlist_info_var.set(f"Track {current} of {count}")
            
    def play_selected(self, event=None):
        """Play selected track from playlist"""
        selection = self.playlist_listbox.curselection()
        if selection:
            self.current_index = selection[0]
            self.play_current()
            
    def play_current(self):
        """Play current track"""
        if not self.playlist or self.current_index >= len(self.playlist):
            return
            
        try:
            file_path = self.playlist[self.current_index]
            
            # Update track info
            filename = os.path.basename(file_path)
            self.track_var.set(filename)
            
            # Try to get metadata (simplified)
            try:
                # This is a placeholder - in a real implementation,
                # you would use a library like mutagen to read metadata
                self.artist_var.set("Unknown Artist")
                self.duration = 180  # Placeholder duration (3 minutes)
                self.duration_var.set(self.format_time(self.duration))
            except:
                self.artist_var.set("")
                self.duration = 0
                self.duration_var.set("00:00")
                
            # Highlight current track in playlist
            self.playlist_listbox.selection_clear(0, tk.END)
            self.playlist_listbox.selection_set(self.current_index)
            self.playlist_listbox.see(self.current_index)
            
            # Start playback (placeholder - would use actual audio library)
            self.is_playing = True
            self.is_paused = False
            self.position = 0
            self.play_button_var.set("⏸")
            
            self.status_var.set(f"Playing: {filename}")
            self.update_playlist_info()
            
            # Start position update timer
            self.update_position()
            
            # Log playback
            if self.user_info:
                self.db_manager.log_action(self.user_info[0], "PLAY_MUSIC", 
                                         f"Playing {file_path}")
                
        except Exception as e:
            self.status_var.set(f"Error playing file: {str(e)}")
            
    def toggle_playback(self):
        """Toggle play/pause"""
        if not self.playlist:
            return
            
        if self.is_playing:
            if self.is_paused:
                # Resume
                self.is_paused = False
                self.play_button_var.set("⏸")
                self.status_var.set("Resumed")
            else:
                # Pause
                self.is_paused = True
                self.play_button_var.set("▶")
                self.status_var.set("Paused")
        else:
            # Start playing
            self.play_current()
            
    def stop(self):
        """Stop playback"""
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        self.play_button_var.set("▶")
        self.progress_var.set(0)
        self.time_var.set("00:00")
        self.status_var.set("Stopped")
        
    def previous_track(self):
        """Play previous track"""
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_current()
            
    def next_track(self):
        """Play next track"""
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_current()
            
    def seek_position(self, value):
        """Seek to position"""
        if self.duration > 0:
            self.position = int((float(value) / 100) * self.duration)
            self.time_var.set(self.format_time(self.position))
            
    def change_volume(self, value):
        """Change volume"""
        self.volume = int(value)
        # In a real implementation, this would change the actual audio volume
        
    def update_position(self):
        """Update playback position"""
        if self.is_playing and not self.is_paused and self.duration > 0:
            self.position += 1
            
            if self.position >= self.duration:
                # Track finished, play next
                self.next_track()
                return
                
            # Update display
            progress = (self.position / self.duration) * 100
            self.progress_var.set(progress)
            self.time_var.set(self.format_time(self.position))
            
            # Schedule next update
            self.window.after(1000, self.update_position)
            
    def format_time(self, seconds):
        """Format time in MM:SS format"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
        
    def show_playlist_menu(self, event):
        """Show playlist context menu"""
        theme = self.config_manager.get_theme()
        
        menu = tk.Menu(self.window, tearoff=0,
                      bg=theme["bg_secondary"], fg=theme["fg_primary"])
        
        selection = self.playlist_listbox.curselection()
        
        if selection:
            menu.add_command(label="Play", command=self.play_selected)
            menu.add_separator()
            menu.add_command(label="Remove from Playlist", command=self.remove_from_playlist)
            menu.add_command(label="Show in File Manager", command=self.show_in_file_manager)
        else:
            menu.add_command(label="Add Files", command=self.add_files)
            menu.add_command(label="Add Folder", command=self.add_folder)
            menu.add_separator()
            menu.add_command(label="Clear Playlist", command=self.clear_playlist)
            
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
            
    def remove_from_playlist(self):
        """Remove selected track from playlist"""
        selection = self.playlist_listbox.curselection()
        if selection:
            index = selection[0]
            
            # Remove from playlist
            del self.playlist[index]
            self.playlist_listbox.delete(index)
            
            # Adjust current index if necessary
            if index <= self.current_index and self.current_index > 0:
                self.current_index -= 1
                
            self.update_playlist_info()
            
    def show_in_file_manager(self):
        """Show selected file in file manager"""
        selection = self.playlist_listbox.curselection()
        if selection:
            file_path = self.playlist[selection[0]]
            folder_path = os.path.dirname(file_path)
            
            # Open file manager at folder location
            FileManager(self.parent, self.user_info).navigate_to(folder_path)
            
    def clear_playlist(self):
        """Clear entire playlist"""
        if messagebox.askyesno("Clear Playlist", "Are you sure you want to clear the entire playlist?"):
            self.playlist.clear()
            self.playlist_listbox.delete(0, tk.END)
            self.current_index = 0
            self.stop()
            self.update_playlist_info()
            
    def save_playlist(self):
        """Save playlist to file"""
        if not self.playlist:
            messagebox.showwarning("Save Playlist", "Playlist is empty.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Playlist",
            defaultextension=".m3u",
            filetypes=[
                ("M3U Playlist", "*.m3u"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("#EXTM3U\n")
                    for track in self.playlist:
                        f.write(f"{track}\n")
                        
                self.status_var.set(f"Playlist saved: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Cannot save playlist: {str(e)}")
                
    def load_playlist(self):
        """Load playlist from file"""
        file_path = filedialog.askopenfilename(
            title="Load Playlist",
            filetypes=[
                ("M3U Playlist", "*.m3u"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Clear current playlist
                self.clear_playlist()
                
                # Load tracks
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and os.path.exists(line):
                        self.add_to_playlist(line)
                        
                self.status_var.set(f"Playlist loaded: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Cannot load playlist: {str(e)}")
                
    def toggle_shuffle(self):
        """Toggle shuffle mode (placeholder)"""
        messagebox.showinfo("Shuffle", "Shuffle mode not implemented yet.")
        
    def toggle_repeat(self):
        """Toggle repeat mode (placeholder)"""
        messagebox.showinfo("Repeat", "Repeat mode not implemented yet.")

class VideoPlayer:
    """Video player using external player"""
    
    def __init__(self, parent, video_file=None, user_info=None):
        self.parent = parent
        self.video_file = video_file
        self.user_info = user_info
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        
        if video_file:
            self.play_video(video_file)
            
    def play_video(self, video_file):
        """Play video using external player"""
        try:
            # Try different video players
            players = ['vlc', 'mpv', 'mplayer', 'totem']
            
            for player in players:
                try:
                    subprocess.run(['which', player], check=True, capture_output=True)
                    subprocess.Popen([player, video_file])
                    
                    # Log video playback
                    if self.user_info:
                        self.db_manager.log_action(self.user_info[0], "PLAY_VIDEO", 
                                                 f"Playing {video_file} with {player}")
                    return
                except subprocess.CalledProcessError:
                    continue
                    
            # No video player found
            messagebox.showerror("Error", 
                               "No video player found. Please install VLC, MPV, or MPlayer.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Cannot play video: {str(e)}")

class SystemMonitor:
    """System monitoring and performance tools"""
    
    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        
        self.monitoring = False
        self.update_interval = 1000  # 1 second
        
        self.create_window()
        self.start_monitoring()
        
    def create_window(self):
        """Create system monitor window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("System Monitor - Berke0S")
        self.window.geometry("700x500")
        
        # Get theme
        theme = self.config_manager.get_theme()
        self.window.configure(bg=theme["bg_primary"])
        
        # Create notebook for different tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_overview_tab()
        self.create_processes_tab()
        self.create_network_tab()
        self.create_disk_tab()
        
        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_overview_tab(self):
        """Create system overview tab"""
        theme = self.config_manager.get_theme()
        
        overview_frame = tk.Frame(self.notebook, bg=theme["bg_primary"])
        self.notebook.add(overview_frame, text="Overview")
        
        # CPU section
        cpu_frame = tk.LabelFrame(overview_frame, text="CPU", font=("Ubuntu", 12, "bold"),
                                 bg=theme["bg_secondary"], fg=theme["fg_primary"])
        cpu_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.cpu_var = tk.StringVar(value="CPU Usage: 0%")
        tk.Label(cpu_frame, textvariable=self.cpu_var, font=("Ubuntu", 11),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(pady=5)
        
        self.cpu_progress = ttk.Progressbar(cpu_frame, length=300, mode='determinate')
        self.cpu_progress.pack(pady=5)
        
        # Memory section
        memory_frame = tk.LabelFrame(overview_frame, text="Memory", font=("Ubuntu", 12, "bold"),
                                    bg=theme["bg_secondary"], fg=theme["fg_primary"])
        memory_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.memory_var = tk.StringVar(value="Memory Usage: 0%")
        tk.Label(memory_frame, textvariable=self.memory_var, font=("Ubuntu", 11),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(pady=5)
        
        self.memory_progress = ttk.Progressbar(memory_frame, length=300, mode='determinate')
        self.memory_progress.pack(pady=5)
        
        # Disk section
        disk_frame = tk.LabelFrame(overview_frame, text="Disk", font=("Ubuntu", 12, "bold"),
                                  bg=theme["bg_secondary"], fg=theme["fg_primary"])
        disk_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.disk_var = tk.StringVar(value="Disk Usage: 0%")
        tk.Label(disk_frame, textvariable=self.disk_var, font=("Ubuntu", 11),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(pady=5)
        
        self.disk_progress = ttk.Progressbar(disk_frame, length=300, mode='determinate')
        self.disk_progress.pack(pady=5)
        
        # Network section
        network_frame = tk.LabelFrame(overview_frame, text="Network", font=("Ubuntu", 12, "bold"),
                                     bg=theme["bg_secondary"], fg=theme["fg_primary"])
        
        network_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.network_var = tk.StringVar(value="Network: Disconnected")
        tk.Label(network_frame, textvariable=self.network_var, font=("Ubuntu", 11),
                bg=theme["bg_secondary"], fg=theme["fg_primary"]).pack(pady=5)
        
        # System info section
        info_frame = tk.LabelFrame(overview_frame, text="System Information", 
                                  font=("Ubuntu", 12, "bold"),
                                  bg=theme["bg_secondary"], fg=theme["fg_primary"])
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.info_text = tk.Text(info_frame, height=8, bg=theme["bg_tertiary"],
                                fg=theme["fg_primary"], font=("Ubuntu Mono", 10))
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.update_system_info()
        
    def create_processes_tab(self):
        """Create processes tab"""
        theme = self.config_manager.get_theme()
        
        processes_frame = tk.Frame(self.notebook, bg=theme["bg_primary"])
        self.notebook.add(processes_frame, text="Processes")
        
        # Toolbar
        toolbar = tk.Frame(processes_frame, bg=theme["bg_secondary"])
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="Refresh", command=self.update_processes,
                 bg=theme["accent_primary"], fg="white", padx=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="Kill Process", command=self.kill_process,
                 bg=theme["error"], fg="white", padx=15).pack(side=tk.LEFT, padx=5)
        
        # Process list
        list_frame = tk.Frame(processes_frame, bg=theme["bg_primary"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for processes
        columns = ('PID', 'Name', 'CPU%', 'Memory%', 'Status')
        self.process_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configure columns
        for col in columns:
            self.process_tree.heading(col, text=col)
            if col == 'PID':
                self.process_tree.column(col, width=80, minwidth=60)
            elif col == 'Name':
                self.process_tree.column(col, width=200, minwidth=150)
            elif col in ['CPU%', 'Memory%']:
                self.process_tree.column(col, width=80, minwidth=60)
            elif col == 'Status':
                self.process_tree.column(col, width=100, minwidth=80)
                
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.process_tree.xview)
        
        self.process_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_network_tab(self):
        """Create network monitoring tab"""
        theme = self.config_manager.get_theme()
        
        network_frame = tk.Frame(self.notebook, bg=theme["bg_primary"])
        self.notebook.add(network_frame, text="Network")
        
        # Network interfaces
        interfaces_frame = tk.LabelFrame(network_frame, text="Network Interfaces",
                                        font=("Ubuntu", 12, "bold"),
                                        bg=theme["bg_secondary"], fg=theme["fg_primary"])
        interfaces_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.interfaces_text = tk.Text(interfaces_frame, height=8, bg=theme["bg_tertiary"],
                                      fg=theme["fg_primary"], font=("Ubuntu Mono", 10))
        self.interfaces_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Network statistics
        stats_frame = tk.LabelFrame(network_frame, text="Network Statistics",
                                   font=("Ubuntu", 12, "bold"),
                                   bg=theme["bg_secondary"], fg=theme["fg_primary"])
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.network_stats_var = tk.StringVar()
        tk.Label(stats_frame, textvariable=self.network_stats_var, font=("Ubuntu", 11),
                bg=theme["bg_secondary"], fg=theme["fg_primary"], justify=tk.LEFT).pack(pady=5)
        
    def create_disk_tab(self):
        """Create disk monitoring tab"""
        theme = self.config_manager.get_theme()
        
        disk_frame = tk.Frame(self.notebook, bg=theme["bg_primary"])
        self.notebook.add(disk_frame, text="Disk")
        
        # Disk usage
        usage_frame = tk.LabelFrame(disk_frame, text="Disk Usage",
                                   font=("Ubuntu", 12, "bold"),
                                   bg=theme["bg_secondary"], fg=theme["fg_primary"])
        usage_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.disk_usage_text = tk.Text(usage_frame, height=6, bg=theme["bg_tertiary"],
                                      fg=theme["fg_primary"], font=("Ubuntu Mono", 10))
        self.disk_usage_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Disk I/O
        io_frame = tk.LabelFrame(disk_frame, text="Disk I/O",
                                font=("Ubuntu", 12, "bold"),
                                bg=theme["bg_secondary"], fg=theme["fg_primary"])
        io_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.disk_io_var = tk.StringVar()
        tk.Label(io_frame, textvariable=self.disk_io_var, font=("Ubuntu", 11),
                bg=theme["bg_secondary"], fg=theme["fg_primary"], justify=tk.LEFT).pack(pady=5)
        
    def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring = True
        self.update_system_stats()
        
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        
    def update_system_stats(self):
        """Update system statistics"""
        if not self.monitoring:
            return
            
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_var.set(f"CPU Usage: {cpu_percent:.1f}%")
            self.cpu_progress['value'] = cpu_percent
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used // (1024**3)  # GB
            memory_total = memory.total // (1024**3)  # GB
            self.memory_var.set(f"Memory Usage: {memory_percent:.1f}% ({memory_used}GB / {memory_total}GB)")
            self.memory_progress['value'] = memory_percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used = disk.used // (1024**3)  # GB
            disk_total = disk.total // (1024**3)  # GB
            self.disk_var.set(f"Disk Usage: {disk_percent:.1f}% ({disk_used}GB / {disk_total}GB)")
            self.disk_progress['value'] = disk_percent
            
            # Network status
            try:
                # Check if connected to internet
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                self.network_var.set("Network: Connected")
            except OSError:
                self.network_var.set("Network: Disconnected")
                
            # Update other tabs if they're visible
            current_tab = self.notebook.index(self.notebook.select())
            if current_tab == 1:  # Processes tab
                self.update_processes()
            elif current_tab == 2:  # Network tab
                self.update_network_info()
            elif current_tab == 3:  # Disk tab
                self.update_disk_info()
                
        except Exception as e:
            logging.error(f"System monitor update error: {e}")
            
        # Schedule next update
        if self.monitoring:
            self.window.after(self.update_interval, self.update_system_stats)
            
    def update_system_info(self):
        """Update system information"""
        try:
            info_lines = []
            
            # System info
            uname = os.uname()
            info_lines.append(f"System: {uname.sysname} {uname.release}")
            info_lines.append(f"Machine: {uname.machine}")
            info_lines.append(f"Hostname: {socket.gethostname()}")
            
            # CPU info
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            info_lines.append(f"CPU Cores: {cpu_count}")
            if cpu_freq:
                info_lines.append(f"CPU Frequency: {cpu_freq.current:.0f} MHz")
                
            # Boot time
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            info_lines.append(f"Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Uptime
            uptime = datetime.datetime.now() - boot_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            info_lines.append(f"Uptime: {days}d {hours}h {minutes}m")
            
            # Update text widget
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, '\n'.join(info_lines))
            
        except Exception as e:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Error getting system info: {str(e)}")
            
    def update_processes(self):
        """Update process list"""
        try:
            # Clear existing items
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
                
            # Get processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            # Add to treeview (top 50 processes)
            for proc in processes[:50]:
                self.process_tree.insert('', tk.END, values=(
                    proc['pid'],
                    proc['name'] or 'Unknown',
                    f"{proc['cpu_percent'] or 0:.1f}",
                    f"{proc['memory_percent'] or 0:.1f}",
                    proc['status'] or 'Unknown'
                ))
                
        except Exception as e:
            logging.error(f"Process update error: {e}")
            
    def update_network_info(self):
        """Update network information"""
        try:
            # Network interfaces
            interfaces_info = []
            interfaces = psutil.net_if_addrs()
            
            for interface, addrs in interfaces.items():
                interfaces_info.append(f"{interface}:")
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces_info.append(f"  IPv4: {addr.address}")
                    elif addr.family == socket.AF_INET6:
                        interfaces_info.append(f"  IPv6: {addr.address}")
                interfaces_info.append("")
                
            self.interfaces_text.delete(1.0, tk.END)
            self.interfaces_text.insert(tk.END, '\n'.join(interfaces_info))
            
            # Network statistics
            net_io = psutil.net_io_counters()
            stats = [
                f"Bytes Sent: {self.format_bytes(net_io.bytes_sent)}",
                f"Bytes Received: {self.format_bytes(net_io.bytes_recv)}",
                f"Packets Sent: {net_io.packets_sent:,}",
                f"Packets Received: {net_io.packets_recv:,}",
                f"Errors In: {net_io.errin}",
                f"Errors Out: {net_io.errout}",
                f"Drops In: {net_io.dropin}",
                f"Drops Out: {net_io.dropout}"
            ]
            
            self.network_stats_var.set('\n'.join(stats))
            
        except Exception as e:
            self.interfaces_text.delete(1.0, tk.END)
            self.interfaces_text.insert(tk.END, f"Error getting network info: {str(e)}")
            
    def update_disk_info(self):
        """Update disk information"""
        try:
            # Disk usage
            usage_info = []
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_gb = usage.total // (1024**3)
                    used_gb = usage.used // (1024**3)
                    free_gb = usage.free // (1024**3)
                    percent = (usage.used / usage.total) * 100
                    
                    usage_info.append(f"{partition.device} ({partition.fstype})")
                    usage_info.append(f"  Mountpoint: {partition.mountpoint}")
                    usage_info.append(f"  Total: {total_gb} GB")
                    usage_info.append(f"  Used: {used_gb} GB ({percent:.1f}%)")
                    usage_info.append(f"  Free: {free_gb} GB")
                    usage_info.append("")
                except PermissionError:
                    usage_info.append(f"{partition.device}: Permission denied")
                    usage_info.append("")
                    
            self.disk_usage_text.delete(1.0, tk.END)
            self.disk_usage_text.insert(tk.END, '\n'.join(usage_info))
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                io_stats = [
                    f"Read Count: {disk_io.read_count:,}",
                    f"Write Count: {disk_io.write_count:,}",
                    f"Read Bytes: {self.format_bytes(disk_io.read_bytes)}",
                    f"Write Bytes: {self.format_bytes(disk_io.write_bytes)}",
                    f"Read Time: {disk_io.read_time:,} ms",
                    f"Write Time: {disk_io.write_time:,} ms"
                ]
                
                self.disk_io_var.set('\n'.join(io_stats))
            else:
                self.disk_io_var.set("Disk I/O information not available")
                
        except Exception as e:
            self.disk_usage_text.delete(1.0, tk.END)
            self.disk_usage_text.insert(tk.END, f"Error getting disk info: {str(e)}")
            
    def format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
        
    def kill_process(self):
        """Kill selected process"""
        selection = self.process_tree.selection()
        if not selection:
            messagebox.showwarning("Kill Process", "Please select a process to kill.")
            return
            
        item = self.process_tree.item(selection[0])
        pid = int(item['values'][0])
        process_name = item['values'][1]
        
        if messagebox.askyesno("Kill Process", 
                              f"Are you sure you want to kill process '{process_name}' (PID: {pid})?"):
            try:
                process = psutil.Process(pid)
                process.terminate()
                
                # Wait for process to terminate
                try:
                    process.wait(timeout=3)
                except psutil.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    process.kill()
                    
                messagebox.showinfo("Kill Process", f"Process {process_name} (PID: {pid}) terminated.")
                
                # Log action
                if self.user_info:
                    self.db_manager.log_action(self.user_info[0], "KILL_PROCESS", 
                                             f"Killed process {process_name} (PID: {pid})")
                    
                # Refresh process list
                self.update_processes()
                
            except psutil.NoSuchProcess:
                messagebox.showwarning("Kill Process", "Process no longer exists.")
            except psutil.AccessDenied:
                messagebox.showerror("Kill Process", "Access denied. Cannot kill this process.")
            except Exception as e:
                messagebox.showerror("Kill Process", f"Error killing process: {str(e)}")
                
    def on_closing(self):
        """Handle window closing"""
        self.stop_monitoring()
        self.window.destroy()

class DesktopEnvironment:
    """Main desktop environment class"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.lang_manager = LanguageManager()
        self.sound_manager = SoundManager()
        
        self.current_user = None
        self.applications = {}
        self.windows = []
        self.desktop_icons = []
        
        # Check if first run
        if self.config_manager.get("first_run", True):
            self.run_installation()
        else:
            self.start_desktop()
            
    def run_installation(self):
        """Run installation wizard"""
        if GUI_AVAILABLE:
            root = tk.Tk()
            root.withdraw()  # Hide main window
            
            installer = InstallationWizard(root)
            root.mainloop()
            
            # After installation, start desktop
            self.start_desktop()
        else:
            # Console installation
            installer = InstallationWizard()
            self.start_desktop()
            
    def start_desktop(self):
        """Start desktop environment"""
        if not GUI_AVAILABLE:
            # Start console mode
            console = ConsoleMode()
            console.start()
            return
            
        # Initialize GUI desktop
        self.root = tk.Tk()
        self.root.title("Berke0S Desktop")
        self.root.attributes('-fullscreen', True)
        
        # Get theme
        theme = self.config_manager.get_theme()
        self.root.configure(bg=theme["bg_primary"])
        
        # Initialize managers
        self.notification_manager = NotificationManager(self.root)
        
        # Show login screen
        self.show_login()
        
        # Play startup sound
        self.sound_manager.play_startup_sound()
        
        # Start main loop
        self.root.mainloop()
        
    def show_login(self):
        """Show login screen"""
        login_manager = LoginManager(self.root)
        
        # Wait for login completion
        self.root.wait_window(login_manager.window)
        
        if login_manager.is_logged_in():
            self.current_user = login_manager.get_current_user()
            self.setup_desktop()
        else:
            self.root.quit()
            
    def setup_desktop(self):
        """Setup desktop after login"""
        theme = self.config_manager.get_theme()
        
        # Create desktop canvas
        self.desktop_canvas = tk.Canvas(self.root, bg=theme["bg_primary"],
                                       highlightthickness=0)
        self.desktop_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create taskbar
        self.create_taskbar()
        
        # Load desktop icons
        self.load_desktop_icons()
        
        # Initialize applications
        self.initialize_applications()
        
        # Show welcome notification
        self.notification_manager.show("Welcome", 
                                     f"Welcome to Berke0S, {self.current_user[1]}!",
                                     "success")
        
        # Bind events
        self.bind_events()
        
    def create_taskbar(self):
        """Create desktop taskbar"""
        theme = self.config_manager.get_theme()
        position = self.config_manager.get("taskbar_position", "bottom")
        
        # Taskbar frame
        self.taskbar = tk.Frame(self.root, bg=theme["bg_secondary"], height=40)
        
        if position == "bottom":
            self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
        elif position == "top":
            self.taskbar.pack(side=tk.TOP, fill=tk.X)
        elif position == "left":
            self.taskbar.configure(width=200, height=0)
            self.taskbar.pack(side=tk.LEFT, fill=tk.Y)
        elif position == "right":
            self.taskbar.configure(width=200, height=0)
            self.taskbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        self.taskbar.pack_propagate(False)
        
        # Start menu button
        self.start_button = tk.Button(self.taskbar, text="☰ Start",
                                     font=("Ubuntu", 12), bg=theme["accent_primary"],
                                     fg="white", command=self.show_start_menu)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Window buttons area
        self.window_buttons_frame = tk.Frame(self.taskbar, bg=theme["bg_secondary"])
        self.window_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # System tray
        self.system_tray = tk.Frame(self.taskbar, bg=theme["bg_secondary"])
        self.system_tray.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Clock
        self.clock_label = tk.Label(self.system_tray, font=("Ubuntu", 10),
                                   bg=theme["bg_secondary"], fg=theme["fg_primary"])
        self.clock_label.pack(side=tk.RIGHT, padx=5)
        
        # System indicators
        self.create_system_indicators()
        
        # Update clock
        self.update_clock()
        
    def create_system_indicators(self):
        """Create system status indicators"""
        theme = self.config_manager.get_theme()
        
        # Network indicator
        self.network_indicator = tk.Label(self.system_tray, text="📶",
                                         font=("Ubuntu", 12), bg=theme["bg_secondary"],
                                         fg=theme["fg_primary"])
        self.network_indicator.pack(side=tk.RIGHT, padx=2)
        
        # Battery indicator (if available)
        try:
            battery = psutil.sensors_battery()
            if battery:
                self.battery_indicator = tk.Label(self.system_tray, text="🔋",
                                                 font=("Ubuntu", 12), bg=theme["bg_secondary"],
                                                 fg=theme["fg_primary"])
                self.battery_indicator.pack(side=tk.RIGHT, padx=2)
        except:
            pass
            
        # Volume indicator
        self.volume_indicator = tk.Label(self.system_tray, text="🔊",
                                        font=("Ubuntu", 12), bg=theme["bg_secondary"],
                                        fg=theme["fg_primary"])
        self.volume_indicator.pack(side=tk.RIGHT, padx=2)
        
    def update_clock(self):
        """Update taskbar clock"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S\n%Y-%m-%d")
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)
        
    def load_desktop_icons(self):
        """Load desktop icons"""
        # Default desktop icons
        default_icons = [
            {"name": "File Manager", "x": 50, "y": 50, "app": "file_manager"},
            {"name": "Text Editor", "x": 50, "y": 150, "app": "text_editor"},
            {"name": "Calculator", "x": 50, "y": 250, "app": "calculator"},
            {"name": "System Monitor", "x": 50, "y": 350, "app": "system_monitor"}
        ]
        
        theme = self.config_manager.get_theme()
        
        for icon_info in default_icons:
            # Create icon
            icon_frame = tk.Frame(self.desktop_canvas, bg=theme["bg_primary"])
            
            # Icon image (placeholder)
            icon_label = tk.Label(icon_frame, text="📁", font=("Ubuntu", 32),
                                 bg=theme["bg_primary"], fg=theme["fg_primary"])
            icon_label.pack()
            
            # Icon text
            text_label = tk.Label(icon_frame, text=icon_info["name"],
                                 font=("Ubuntu", 10), bg=theme["bg_primary"],
                                 fg=theme["fg_primary"])
            text_label.pack()
            
            # Place icon on desktop
            self.desktop_canvas.create_window(icon_info["x"], icon_info["y"],
                                            window=icon_frame, anchor=tk.NW)
            
            # Bind double-click event
            app_name = icon_info["app"]
            icon_frame.bind("<Double-Button-1>", lambda e, app=app_name: self.launch_application(app))
            icon_label.bind("<Double-Button-1>", lambda e, app=app_name: self.launch_application(app))
            text_label.bind("<Double-Button-1>", lambda e, app=app_name: self.launch_application(app))
            
            self.desktop_icons.append({
                "frame": icon_frame,
                "app": app_name,
                "x": icon_info["x"],
                "y": icon_info["y"]
            })
            
    def initialize_applications(self):
        """Initialize available applications"""
        self.applications = {
            "file_manager": lambda: FileManager(self.root, self.current_user),
            "text_editor": lambda: TextEditor(self.root, None, self.current_user),
            "calculator": lambda: Calculator(self.root, self.current_user),
            "image_viewer": lambda: ImageViewer(self.root, None, self.current_user),
            "music_player": lambda: MusicPlayer(self.root, None, self.current_user),
            "system_monitor": lambda: SystemMonitor(self.root, self.current_user)
        }
        
    def launch_application(self, app_name):
        """Launch application"""
        if app_name in self.applications:
            try:
                app = self.applications[app_name]()
                
                # Log application launch
                if self.current_user:
                    self.db_manager.log_action(self.current_user[0], "LAUNCH_APP", 
                                             f"Launched {app_name}")
                    
                self.notification_manager.show("Application", 
                                             f"Launched {app_name.replace('_', ' ').title()}",
                                             "info")
                                             
            except Exception as e:
                self.notification_manager.show("Error", 
                                             f"Cannot launch {app_name}: {str(e)}",
                                             "error")
                logging.error(f"Application launch error: {app_name} - {e}")
                
    def show_start_menu(self):
        """Show start menu"""
        theme = self.config_manager.get_theme()
        
        # Create start menu window
        start_menu = tk.Toplevel(self.root)
        start_menu.title("Start Menu")
        start_menu.geometry("300x400")
        start_menu.configure(bg=theme["bg_secondary"])
        start_menu.overrideredirect(True)
        
        # Position menu
        x = self.start_button.winfo_rootx()
        y = self.start_button.winfo_rooty() - 400
        start_menu.geometry(f"300x400+{x}+{y}")
        
        # User info
        user_frame = tk.Frame(start_menu, bg=theme["accent_primary"])
        user_frame.pack(fill=tk.X)
        
        tk.Label(user_frame, text=f"👤 {self.current_user[1]}", font=("Ubuntu", 12, "bold"),
                bg=theme["accent_primary"], fg="white").pack(pady=10)
        
        # Applications
        apps_frame = tk.Frame(start_menu, bg=theme["bg_secondary"])
        apps_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        app_list = [
            ("📁 File Manager", "file_manager"),
            ("📝 Text Editor", "text_editor"),
            ("🧮 Calculator", "calculator"),
            ("🖼️ Image Viewer", "image_viewer"),
            ("🎵 Music Player", "music_player"),
            ("📊 System Monitor", "system_monitor")
        ]
        
        for app_text, app_name in app_list:
            btn = tk.Button(apps_frame, text=app_text, font=("Ubuntu", 11),
                           bg=theme["bg_tertiary"], fg=theme["fg_primary"],
                           anchor=tk.W, width=25,
                           command=lambda app=app_name: [self.launch_application(app), start_menu.destroy()])
            btn.pack(fill=tk.X, pady=2)
            
        # Separator
        tk.Frame(start_menu, bg=theme["border"], height=2).pack(fill=tk.X, padx=10)
        
        # System options
        system_frame = tk.Frame(start_menu, bg=theme["bg_secondary"])
        system_frame.pack(fill=tk.X, padx=10, pady=10)
        
        system_options = [
            ("⚙️ Settings", self.open_settings),
            ("🔒 Lock", self.lock_screen),
            ("🚪 Logout", self.logout),
            ("🔄 Restart", self.restart),
            ("⏻ Shutdown", self.shutdown)
        ]
        
        for option_text, command in system_options:
            btn = tk.Button(system_frame, text=option_text, font=("Ubuntu", 11),
                           bg=theme["bg_tertiary"], fg=theme["fg_primary"],
                           anchor=tk.W, width=25,
                           command=lambda cmd=command: [cmd(), start_menu.destroy()])
            btn.pack(fill=tk.X, pady=2)
            
        # Auto-close menu when clicking outside
        def close_menu(event):
            if event.widget != start_menu and not str(event.widget).startswith(str(start_menu)):
                start_menu.destroy()
                
        self.root.bind("<Button-1>", close_menu, add="+")
        start_menu.bind("<FocusOut>", lambda e: start_menu.destroy())
        
        # Focus menu
        start_menu.focus_set()
        
    def open_settings(self):
        """Open system settings"""
        self.notification_manager.show("Settings", "Settings not implemented yet", "info")
        
    def lock_screen(self):
        """Lock screen"""
        self.notification_manager.show("Lock", "Screen lock not implemented yet", "info")
        
    def logout(self):
        """Logout current user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            # Log logout
            if self.current_user:
                self.db_manager.log_action(self.current_user[0], "LOGOUT", "User logged out")
                
            self.sound_manager.play_shutdown_sound()
            self.root.quit()
            
    def restart(self):
        """Restart system"""
        if messagebox.askyesno("Restart", "Are you sure you want to restart?"):
            # Log restart
            if self.current_user:
                self.db_manager.log_action(self.current_user[0], "RESTART", "System restart")
                
            self.sound_manager.play_shutdown_sound()
            
            # In a real system, this would restart the computer
            self.notification_manager.show("Restart", "Restart functionality not available in demo", "warning")
            
    def shutdown(self):
        """Shutdown system"""
        if messagebox.askyesno("Shutdown", "Are you sure you want to shutdown?"):
            # Log shutdown
            if self.current_user:
                self.db_manager.log_action(self.current_user[0], "SHUTDOWN", "System shutdown")
                
            self.sound_manager.play_shutdown_sound()
            
            # In a real system, this would shutdown the computer
            self.root.quit()
            
    def bind_events(self):
        """Bind keyboard and mouse events"""
        # Global keyboard shortcuts
        self.root.bind('<Control-Alt-t>', lambda e: self.launch_application("terminal"))
        self.root.bind('<Control-Alt-f>', lambda e: self.launch_application("file_manager"))
        self.root.bind('<Control-Alt-c>', lambda e: self.launch_application("calculator"))
        
        # Desktop context menu
        self.desktop_canvas.bind("<Button-3>", self.show_desktop_menu)
        
    def show_desktop_menu(self, event):
        """Show desktop context menu"""
        theme = self.config_manager.get_theme()
        
        menu = tk.Menu(self.root, tearoff=0,
                      bg=theme["bg_secondary"], fg=theme["fg_primary"])
        
        menu.add_command(label="Refresh Desktop", command=self.refresh_desktop)
        menu.add_separator()
        menu.add_command(label="New Folder", command=self.create_desktop_folder)
        menu.add_command(label="New File", command=self.create_desktop_file)
        menu.add_separator()
        menu.add_command(label="Paste", command=self.paste_to_desktop)
        menu.add_separator()
        menu.add_command(label="Display Settings", command=self.open_display_settings)
        menu.add_command(label="Personalize", command=self.open_personalization)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
            
    def refresh_desktop(self):
        """Refresh desktop"""
        self.notification_manager.show("Desktop", "Desktop refreshed", "info")
        
    def create_desktop_folder(self):
        """Create new folder on desktop"""
        self.notification_manager.show("Desktop", "Create folder not implemented yet", "info")
        
    def create_desktop_file(self):
        """Create new file on desktop"""
        self.notification_manager.show("Desktop", "Create file not implemented yet", "info")
        
    def paste_to_desktop(self):
        """Paste to desktop"""
        self.notification_manager.show("Desktop", "Paste not implemented yet", "info")
        
    def open_display_settings(self):
        """Open display settings"""
        self.notification_manager.show("Settings", "Display settings not implemented yet", "info")
        
    def open_personalization(self):
        """Open personalization settings"""
        self.notification_manager.show("Settings", "Personalization not implemented yet", "info")

def main():
    """Main entry point"""
    try:
        # Setup display environment
        if not setup_display():
            print("Starting in console mode...")
            console = ConsoleMode()
            console.start()
            return
            
        # Check for installation argument
        if len(sys.argv) > 1 and sys.argv[1] == "--install":
            # Force installation mode
            config_manager = ConfigManager()
            config_manager.set("first_run", True)
            
        # Start desktop environment
        desktop = DesktopEnvironment()
        
    except KeyboardInterrupt:
        print("\nBerke0S interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

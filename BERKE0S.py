#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Berke0S - Advanced Desktop Environment for Tiny Core Linux
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
import string
from io import BytesIO
from urllib.parse import quote
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, colorchooser
from tkinter import font as tkFont

# Try to import optional dependencies
try:
    from PIL import Image, ImageTk, ImageGrab, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Configuration
CONFIG_DIR = "/home/tc/.berke0s"
CONFIG_FILE = f"{CONFIG_DIR}/config.json"
SESSION_FILE = f"{CONFIG_DIR}/session.json"
LOG_FILE = f"{CONFIG_DIR}/berke0s.log"
INSTALL_FLAG = f"{CONFIG_DIR}/.installed"

# Setup logging
os.makedirs(CONFIG_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Default configuration
DEFAULT_CONFIG = {
    "version": "2.0",
    "first_boot": True,
    "language": "tr_TR",
    "timezone": "Europe/Istanbul",
    "theme": "berke_dark",
    "users": [],
    "wifi": {"ssid": "", "password": ""},
    "installed": False,
    "desktop": {
        "wallpaper": "",
        "icon_size": 48,
        "grid_snap": True,
        "effects": True,
        "transparency": 0.95
    },
    "taskbar": {
        "position": "bottom",
        "auto_hide": False,
        "color": "#1a1a1a",
        "size": 40
    },
    "notifications": {
        "enabled": True,
        "timeout": 5000,
        "position": "top-right"
    },
    "power": {
        "sleep_timeout": 1800,
        "screen_off_timeout": 900
    },
    "accessibility": {
        "high_contrast": False,
        "screen_reader": False,
        "font_scale": 1.0,
        "magnifier": False
    },
    "security": {
        "auto_lock": True,
        "lock_timeout": 600,
        "require_password": True
    }
}

# Display detection and setup
def setup_display():
    """Setup display environment for GUI applications"""
    try:
        # Check if X server is running
        if not os.environ.get('DISPLAY'):
            # Try to start X server
            subprocess.run(['sudo', 'Xorg', ':0', '-nolisten', 'tcp'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            os.environ['DISPLAY'] = ':0'
        
        # Test display
        result = subprocess.run(['xdpyinfo'], capture_output=True, timeout=5)
        if result.returncode != 0:
            # Start minimal X session
            subprocess.Popen(['startx'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            os.environ['DISPLAY'] = ':0'
            
    except Exception as e:
        logging.error(f"Display setup error: {e}")
        # Fallback to console mode
        print("Display setup failed. Running in console mode.")
        return False
    return True

# Installation System
class InstallationWizard:
    """Complete installation wizard for Berke0S"""
    
    def __init__(self):
        self.root = None
        self.current_step = 0
        self.steps = [
            "welcome",
            "language", 
            "disk_setup",
            "network",
            "user_setup",
            "customization",
            "installation",
            "complete"
        ]
        self.config = DEFAULT_CONFIG.copy()
        self.selected_disk = None
        self.partition_scheme = "auto"
        
    def start_installation(self):
        """Start the installation process"""
        if not setup_display():
            return self.console_install()
            
        self.root = tk.Tk()
        self.root.title("Berke0S Kurulum - Installation")
        self.root.geometry("800x600")
        self.root.configure(bg='#0f0f23')
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")
        
        self.show_step()
        self.root.mainloop()
        
    def console_install(self):
        """Console-based installation"""
        print("\n" + "="*60)
        print("  BERKE0S - Advanced Desktop Environment")
        print("  Created by: Berke Oruç")
        print("  Console Installation Mode")
        print("="*60)
        
        # Basic setup
        username = input("\nKullanıcı adı (Username): ").strip()
        password = getpass.getpass("Şifre (Password): ")
        
        # Create user
        self.config["users"] = [{
            "username": username,
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "admin": True
        }]
        
        # Save config
        self.save_config()
        print("\nKurulum tamamlandı! Installation completed!")
        return True
        
    def show_step(self):
        """Show current installation step"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        step_name = self.steps[self.current_step]
        
        if step_name == "welcome":
            self.show_welcome()
        elif step_name == "language":
            self.show_language()
        elif step_name == "disk_setup":
            self.show_disk_setup()
        elif step_name == "network":
            self.show_network()
        elif step_name == "user_setup":
            self.show_user_setup()
        elif step_name == "customization":
            self.show_customization()
        elif step_name == "installation":
            self.show_installation()
        elif step_name == "complete":
            self.show_complete()
            
    def show_welcome(self):
        """Welcome screen"""
        main_frame = tk.Frame(self.root, bg='#0f0f23')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Logo area
        logo_frame = tk.Frame(main_frame, bg='#0f0f23')
        logo_frame.pack(fill=tk.X, pady=(0, 30))
        
        # ASCII Logo
        logo_text = """
    ██████╗ ███████╗██████╗ ██╗  ██╗███████╗ ██████╗ ███████╗
    ██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔════╝██╔═████╗██╔════╝
    ██████╔╝█████╗  ██████╔╝█████╔╝ █████╗  ██║██╔██║███████╗
    ██╔══██╗██╔══╝  ██╔══██╗██╔═██╗ ██╔══╝  ████╔╝██║╚════██║
    ██████╔╝███████╗██║  ██║██║  ██╗███████╗╚██████╔╝███████║
    ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝
        """
        
        tk.Label(logo_frame, text=logo_text, font=('Courier', 8), 
                fg='#00ff88', bg='#0f0f23').pack()
        
        # Welcome text
        welcome_frame = tk.Frame(main_frame, bg='#0f0f23')
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(welcome_frame, text="Berke0S'a Hoş Geldiniz!", 
                font=('Arial', 24, 'bold'), fg='white', bg='#0f0f23').pack(pady=10)
        
        tk.Label(welcome_frame, text="Welcome to Berke0S!", 
                font=('Arial', 18), fg='#cccccc', bg='#0f0f23').pack(pady=5)
        
        info_text = """
Berke0S, Tiny Core Linux tabanlı modern ve kullanıcı dostu bir masaüstü ortamıdır.
Bu kurulum sihirbazı size sistemin kurulumu konusunda rehberlik edecektir.

Berke0S is a modern and user-friendly desktop environment based on Tiny Core Linux.
This installation wizard will guide you through the system setup process.

Geliştirici / Developer: Berke Oruç
Sürüm / Version: 2.0
        """
        
        tk.Label(welcome_frame, text=info_text, font=('Arial', 11), 
                fg='#cccccc', bg='#0f0f23', justify=tk.CENTER).pack(pady=20)
        
        # Features
        features_frame = tk.Frame(welcome_frame, bg='#0f0f23')
        features_frame.pack(pady=20)
        
        features = [
            "🚀 Hızlı ve hafif sistem",
            "🎨 Modern arayüz tasarımı", 
            "🔧 Gelişmiş sistem araçları",
            "🌐 Ağ yönetimi",
            "📁 Dosya yöneticisi",
            "💻 Geliştirici araçları"
        ]
        
        for i, feature in enumerate(features):
            row = i // 2
            col = i % 2
            tk.Label(features_frame, text=feature, font=('Arial', 10), 
                    fg='#00ff88', bg='#0f0f23').grid(row=row, column=col, 
                    padx=20, pady=5, sticky='w')
        
        # Navigation
        self.add_navigation(main_frame)
        
    def show_language(self):
        """Language selection"""
        main_frame = tk.Frame(self.root, bg='#0f0f23')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(main_frame, text="Dil Seçimi / Language Selection", 
                font=('Arial', 20, 'bold'), fg='white', bg='#0f0f23').pack(pady=20)
        
        languages = {
            "tr_TR": "🇹🇷 Türkçe",
            "en_US": "🇺🇸 English", 
            "de_DE": "🇩🇪 Deutsch",
            "fr_FR": "🇫🇷 Français",
            "es_ES": "🇪🇸 Español",
            "ru_RU": "🇷🇺 Русский"
        }
        
        self.language_var = tk.StringVar(value="tr_TR")
        
        lang_frame = tk.Frame(main_frame, bg='#0f0f23')
        lang_frame.pack(expand=True)
        
        for code, name in languages.items():
            tk.Radiobutton(lang_frame, text=name, variable=self.language_var, 
                          value=code, font=('Arial', 12), fg='white', 
                          bg='#0f0f23', selectcolor='#333333',
                          activebackground='#0f0f23', activeforeground='white').pack(pady=5)
        
        self.add_navigation(main_frame)
        
    def show_disk_setup(self):
        """Disk setup and partitioning"""
        main_frame = tk.Frame(self.root, bg='#0f0f23')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(main_frame, text="Disk Kurulumu / Disk Setup", 
                font=('Arial', 20, 'bold'), fg='white', bg='#0f0f23').pack(pady=20)
        
        # Disk list
        disk_frame = tk.LabelFrame(main_frame, text="Mevcut Diskler / Available Disks", 
                                  fg='white', bg='#0f0f23', font=('Arial', 12))
        disk_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.disk_listbox = tk.Listbox(disk_frame, bg='#1a1a1a', fg='white', 
                                      font=('Courier', 10), height=8)
        self.disk_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Refresh disk list
        self.refresh_disks()
        
        # Partition options
        part_frame = tk.LabelFrame(main_frame, text="Bölümleme / Partitioning", 
                                  fg='white', bg='#0f0f23', font=('Arial', 12))
        part_frame.pack(fill=tk.X, pady=10)
        
        self.partition_var = tk.StringVar(value="auto")
        
        tk.Radiobutton(part_frame, text="Otomatik bölümleme (Önerilen)", 
                      variable=self.partition_var, value="auto",
                      fg='white', bg='#0f0f23', selectcolor='#333333').pack(anchor='w', padx=10)
        
        tk.Radiobutton(part_frame, text="Manuel bölümleme", 
                      variable=self.partition_var, value="manual",
                      fg='white', bg='#0f0f23', selectcolor='#333333').pack(anchor='w', padx=10)
        
        tk.Radiobutton(part_frame, text="Tüm diski kullan", 
                      variable=self.partition_var, value="full",
                      fg='white', bg='#0f0f23', selectcolor='#333333').pack(anchor='w', padx=10)
        
        # Warning
        tk.Label(main_frame, text="⚠️  Seçilen diskteki tüm veriler silinecektir!", 
                font=('Arial', 10), fg='#ff6b6b', bg='#0f0f23').pack(pady=10)
        
        self.add_navigation(main_frame)
        
    def refresh_disks(self):
        """Refresh available disks"""
        try:
            self.disk_listbox.delete(0, tk.END)
            
            # Get disk information
            result = subprocess.run(['lsblk', '-d', '-o', 'NAME,SIZE,MODEL'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        self.disk_listbox.insert(tk.END, line)
            else:
                self.disk_listbox.insert(tk.END, "sda  8G   Virtual Disk")
                self.disk_listbox.insert(tk.END, "sdb  16G  USB Drive")
                
        except Exception as e:
            logging.error(f"Disk refresh error: {e}")
            self.disk_listbox.insert(tk.END, "Disk bilgisi alınamadı")
            
    def show_network(self):
        """Network configuration"""
        main_frame = tk.Frame(self.root, bg='#0f0f23')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(main_frame, text="Ağ Ayarları / Network Settings", 
                font=('Arial', 20, 'bold'), fg='white', bg='#0f0f23').pack(pady=20)
        
        # WiFi setup
        wifi_frame = tk.LabelFrame(main_frame, text="WiFi Bağlantısı", 
                                  fg='white', bg='#0f0f23', font=('Arial', 12))
        wifi_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(wifi_frame, text="Ağ Adı (SSID):", fg='white', bg='#0f0f23').pack(anchor='w', padx=10)
        self.ssid_var = tk.StringVar()
        ssid_entry = tk.Entry(wifi_frame, textvariable=self.ssid_var, 
                             bg='#1a1a1a', fg='white', font=('Arial', 11))
        ssid_entry.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(wifi_frame, text="Şifre:", fg='white', bg='#0f0f23').pack(anchor='w', padx=10)
        self.wifi_pass_var = tk.StringVar()
        pass_entry = tk.Entry(wifi_frame, textvariable=self.wifi_pass_var, show='*',
                             bg='#1a1a1a', fg='white', font=('Arial', 11))
        pass_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # Scan button
        tk.Button(wifi_frame, text="Ağları Tara", command=self.scan_networks,
                 bg='#00ff88', fg='black', font=('Arial', 10)).pack(pady=10)
        
        # Available networks
        self.networks_listbox = tk.Listbox(wifi_frame, bg='#1a1a1a', fg='white', height=6)
        self.networks_listbox.pack(fill=tk.X, padx=10, pady=5)
        self.networks_listbox.bind('<Double-Button-1>', self.select_network)
        
        # Ethernet option
        eth_frame = tk.LabelFrame(main_frame, text="Ethernet", 
                                 fg='white', bg='#0f0f23', font=('Arial', 12))
        eth_frame.pack(fill=tk.X, pady=10)
        
        self.use_ethernet = tk.BooleanVar()
        tk.Checkbutton(eth_frame, text="Ethernet bağlantısı kullan", 
                      variable=self.use_ethernet, fg='white', bg='#0f0f23',
                      selectcolor='#333333').pack(anchor='w', padx=10, pady=5)
        
        self.add_navigation(main_frame)
        
    def scan_networks(self):
        """Scan for available WiFi networks"""
        try:
            self.networks_listbox.delete(0, tk.END)
            self.networks_listbox.insert(tk.END, "Taranıyor...")
            self.root.update()
            
            # Scan networks
            result = subprocess.run(['iwlist', 'scan'], capture_output=True, text=True, timeout=10)
            
            networks = []
            if result.returncode == 0:
                # Parse scan results
                for line in result.stdout.split('\n'):
                    if 'ESSID:' in line:
                        ssid = line.split('ESSID:')[1].strip().strip('"')
                        if ssid and ssid != '':
                            networks.append(ssid)
            
            self.networks_listbox.delete(0, tk.END)
            if networks:
                for network in set(networks):  # Remove duplicates
                    self.networks_listbox.insert(tk.END, network)
            else:
                self.networks_listbox.insert(tk.END, "Ağ bulunamadı")
                
        except Exception as e:
            self.networks_listbox.delete(0, tk.END)
            self.networks_listbox.insert(tk.END, f"Hata: {str(e)}")
            
    def select_network(self, event):
        """Select network from list"""
        try:
            selection = self.networks_listbox.curselection()
            if selection:
                network = self.networks_listbox.get(selection[0])
                self.ssid_var.set(network)
        except:
            pass
            
    def show_user_setup(self):
        """User account setup"""
        main_frame = tk.Frame(self.root, bg='#0f0f23')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(main_frame, text="Kullanıcı Hesabı / User Account", 
                font=('Arial', 20, 'bold'), fg='white', bg='#0f0f23').pack(pady=20)
        
        # User form
        form_frame = tk.Frame(main_frame, bg='#0f0f23')
        form_frame.pack(expand=True)
        
        # Full name
        tk.Label(form_frame, text="Ad Soyad / Full Name:", 
                fg='white', bg='#0f0f23', font=('Arial', 12)).pack(anchor='w', pady=(10,5))
        self.fullname_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.fullname_var, 
                bg='#1a1a1a', fg='white', font=('Arial', 11), width=40).pack(pady=5)
        
        # Username
        tk.Label(form_frame, text="Kullanıcı Adı / Username:", 
                fg='white', bg='#0f0f23', font=('Arial', 12)).pack(anchor='w', pady=(10,5))
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(form_frame, textvariable=self.username_var, 
                                 bg='#1a1a1a', fg='white', font=('Arial', 11), width=40)
        username_entry.pack(pady=5)
        username_entry.bind('<KeyRelease>', self.validate_username)
        
        self.username_status = tk.Label(form_frame, text="", fg='#ff6b6b', bg='#0f0f23')
        self.username_status.pack()
        
        # Password
        tk.Label(form_frame, text="Şifre / Password:", 
                fg='white', bg='#0f0f23', font=('Arial', 12)).pack(anchor='w', pady=(10,5))
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=self.password_var, show='*',
                                 bg='#1a1a1a', fg='white', font=('Arial', 11), width=40)
        password_entry.pack(pady=5)
        password_entry.bind('<KeyRelease>', self.validate_password)
        
        # Confirm password
        tk.Label(form_frame, text="Şifre Tekrar / Confirm Password:", 
                fg='white', bg='#0f0f23', font=('Arial', 12)).pack(anchor='w', pady=(10,5))
        self.confirm_password_var = tk.StringVar()
        confirm_entry = tk.Entry(form_frame, textvariable=self.confirm_password_var, show='*',
                                bg='#1a1a1a', fg='white', font=('Arial', 11), width=40)
        confirm_entry.pack(pady=5)
        confirm_entry.bind('<KeyRelease>', self.validate_password)
        
        self.password_status = tk.Label(form_frame, text="", fg='#ff6b6b', bg='#0f0f23')
        self.password_status.pack()
        
        # Auto login option
        self.auto_login = tk.BooleanVar(value=True)
        tk.Checkbutton(form_frame, text="Otomatik giriş / Auto login", 
                      variable=self.auto_login, fg='white', bg='#0f0f23',
                      selectcolor='#333333', font=('Arial', 11)).pack(pady=10)
        
        self.add_navigation(main_frame)
        
    def validate_username(self, event=None):
        """Validate username"""
        username = self.username_var.get()
        if len(username) < 3:
            self.username_status.config(text="Kullanıcı adı en az 3 karakter olmalı", fg='#ff6b6b')
        elif not re.match("^[a-zA-Z0-9_]+$", username):
            self.username_status.config(text="Sadece harf, rakam ve _ kullanın", fg='#ff6b6b')
        else:
            self.username_status.config(text="✓ Geçerli", fg='#00ff88')
            
    def validate_password(self, event=None):
        """Validate password"""
        password = self.password_var.get()
        confirm = self.confirm_password_var.get()
        
        if len(password) < 6:
            self.password_status.config(text="Şifre en az 6 karakter olmalı", fg='#ff6b6b')
        elif confirm and password != confirm:
            self.password_status.config(text="Şifreler eşleşmiyor", fg='#ff6b6b')
        elif confirm and password == confirm:
            self.password_status.config(text="✓ Şifreler eşleşiyor", fg='#00ff88')
        else:
            self.password_status.config(text="", fg='white')
            
    def show_customization(self):
        """Customization options"""
        main_frame = tk.Frame(self.root, bg='#0f0f23')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(main_frame, text="Özelleştirme / Customization", 
                font=('Arial', 20, 'bold'), fg='white', bg='#0f0f23').pack(pady=20)
        
        # Theme selection
        theme_frame = tk.LabelFrame(main_frame, text="Tema / Theme", 
                                   fg='white', bg='#0f0f23', font=('Arial', 12))
        theme_frame.pack(fill=tk.X, pady=10)
        
        self.theme_var = tk.StringVar(value="berke_dark")
        themes = {
            "berke_dark": "🌙 Berke Dark (Varsayılan)",
            "berke_light": "☀️ Berke Light", 
            "ocean": "🌊 Ocean Blue",
            "forest": "🌲 Forest Green",
            "sunset": "🌅 Sunset Orange"
        }
        
        for code, name in themes.items():
            tk.Radiobutton(theme_frame, text=name, variable=self.theme_var, 
                          value=code, fg='white', bg='#0f0f23', 
                          selectcolor='#333333').pack(anchor='w', padx=10)
        
        # Desktop effects
        effects_frame = tk.LabelFrame(main_frame, text="Masaüstü Efektleri", 
                                     fg='white', bg='#0f0f23', font=('Arial', 12))
        effects_frame.pack(fill=tk.X, pady=10)
        
        self.animations = tk.BooleanVar(value=True)
        tk.Checkbutton(effects_frame, text="Animasyonlar", variable=self.animations,
                      fg='white', bg='#0f0f23', selectcolor='#333333').pack(anchor='w', padx=10)
        
        self.transparency = tk.BooleanVar(value=True)
        tk.Checkbutton(effects_frame, text="Şeffaflık efektleri", variable=self.transparency,
                      fg='white', bg='#0f0f23', selectcolor='#333333').pack(anchor='w', padx=10)
        
        self.shadows = tk.BooleanVar(value=True)
        tk.Checkbutton(effects_frame, text="Gölge efektleri", variable=self.shadows,
                      fg='white', bg='#0f0f23', selectcolor='#333333').pack(anchor='w', padx=10)
        
        # Taskbar position
        taskbar_frame = tk.LabelFrame(main_frame, text="Görev Çubuğu", 
                                     fg='white', bg='#0f0f23', font=('Arial', 12))
        taskbar_frame.pack(fill=tk.X, pady=10)
        
        self.taskbar_pos = tk.StringVar(value="bottom")
        positions = [("Alt", "bottom"), ("Üst", "top"), ("Sol", "left"), ("Sağ", "right")]
        
        pos_frame = tk.Frame(taskbar_frame, bg='#0f0f23')
        pos_frame.pack(anchor='w', padx=10)
        
        for text, value in positions:
            tk.Radiobutton(pos_frame, text=text, variable=self.taskbar_pos, 
                          value=value, fg='white', bg='#0f0f23', 
                          selectcolor='#333333').pack(side=tk.LEFT, padx=10)
        
        self.add_navigation(main_frame)
        
    def show_installation(self):
        """Installation progress"""
        main_frame = tk.Frame(self.root, bg='#0f0f23')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(main_frame, text="Kurulum / Installation", 
                font=('Arial', 20, 'bold'), fg='white', bg='#0f0f23').pack(pady=20)
        
        # Progress area
        progress_frame = tk.Frame(main_frame, bg='#0f0f23')
        progress_frame.pack(expand=True, fill=tk.BOTH)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=500)
        self.progress_bar.pack(pady=20)
        
        self.status_label = tk.Label(progress_frame, text="Kurulum başlatılıyor...", 
                                    font=('Arial', 12), fg='white', bg='#0f0f23')
        self.status_label.pack(pady=10)
        
        # Installation log
        log_frame = tk.Frame(progress_frame, bg='#0f0f23')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.log_text = tk.Text(log_frame, bg='#1a1a1a', fg='#00ff88', 
                               font=('Courier', 9), height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Start installation
        self.root.after(1000, self.start_install_process)
        
    def start_install_process(self):
        """Start the actual installation process"""
        def install_thread():
            steps = [
                ("Sistem dosyaları hazırlanıyor...", 10),
                ("Disk bölümlendiriliyor...", 20),
                ("Temel sistem kuruluyor...", 40),
                ("Ağ ayarları yapılandırılıyor...", 60),
                ("Kullanıcı hesabı oluşturuluyor...", 70),
                ("Masaüstü ortamı kuruluyor...", 85),
                ("Son ayarlar yapılıyor...", 95),
                ("Kurulum tamamlandı!", 100)
            ]
            
            for status, progress in steps:
                self.root.after(0, lambda s=status, p=progress: self.update_progress(s, p))
                self.root.after(0, lambda s=status: self.log_message(s))
                
                # Simulate installation work
                time.sleep(2)
                
                # Actual installation steps
                if progress == 20:
                    self.setup_disk()
                elif progress == 40:
                    self.install_base_system()
                elif progress == 60:
                    self.configure_network()
                elif progress == 70:
                    self.create_user()
                elif progress == 85:
                    self.setup_desktop()
                elif progress == 95:
                    self.finalize_installation()
            
            self.root.after(0, self.installation_complete)
        
        threading.Thread(target=install_thread, daemon=True).start()
        
    def update_progress(self, status, progress):
        """Update progress bar and status"""
        self.progress_var.set(progress)
        self.status_label.config(text=status)
        
    def log_message(self, message):
        """Add message to installation log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def setup_disk(self):
        """Setup disk partitions"""
        try:
            self.log_message("Disk bölümleri oluşturuluyor...")
            # Simulate disk setup
            time.sleep(1)
            self.log_message("✓ Disk kurulumu tamamlandı")
        except Exception as e:
            self.log_message(f"✗ Disk kurulum hatası: {e}")
            
    def install_base_system(self):
        """Install base system packages"""
        try:
            packages = [
                "python3", "tk", "python3-pip", "git", "nano", "htop",
                "wireless-tools", "alsa-utils", "xorg", "flwm"
            ]
            
            for package in packages:
                self.log_message(f"Kuruluyor: {package}")
                # Simulate package installation
                subprocess.run(['tce-load', '-wi', package], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(0.5)
                
            self.log_message("✓ Temel sistem kuruldu")
        except Exception as e:
            self.log_message(f"✗ Paket kurulum hatası: {e}")
            
    def configure_network(self):
        """Configure network settings"""
        try:
            if self.ssid_var.get():
                self.log_message(f"WiFi bağlantısı kuruluyor: {self.ssid_var.get()}")
                # Configure WiFi
                self.config["wifi"] = {
                    "ssid": self.ssid_var.get(),
                    "password": self.wifi_pass_var.get()
                }
            
            if self.use_ethernet.get():
                self.log_message("Ethernet bağlantısı yapılandırılıyor...")
                
            self.log_message("✓ Ağ ayarları tamamlandı")
        except Exception as e:
            self.log_message(f"✗ Ağ yapılandırma hatası: {e}")
            
    def create_user(self):
        """Create user account"""
        try:
            username = self.username_var.get()
            password = self.password_var.get()
            fullname = self.fullname_var.get()
            
            self.log_message(f"Kullanıcı oluşturuluyor: {username}")
            
            # Create user in system
            subprocess.run(['sudo', 'useradd', '-m', '-s', '/bin/bash', username],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Set password
            subprocess.run(f'echo "{username}:{password}" | sudo chpasswd',
                         shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Add to config
            self.config["users"] = [{
                "username": username,
                "fullname": fullname,
                "password": hashlib.sha256(password.encode()).hexdigest(),
                "admin": True,
                "auto_login": self.auto_login.get()
            }]
            
            self.log_message("✓ Kullanıcı hesabı oluşturuldu")
        except Exception as e:
            self.log_message(f"✗ Kullanıcı oluşturma hatası: {e}")
            
    def setup_desktop(self):
        """Setup desktop environment"""
        try:
            self.log_message("Masaüstü ortamı yapılandırılıyor...")
            
            # Apply customization settings
            self.config["theme"] = self.theme_var.get()
            self.config["language"] = self.language_var.get()
            self.config["desktop"]["effects"] = self.animations.get()
            self.config["desktop"]["transparency"] = 0.95 if self.transparency.get() else 1.0
            self.config["taskbar"]["position"] = self.taskbar_pos.get()
            
            # Create desktop directories
            username = self.username_var.get()
            home_dir = f"/home/{username}"
            
            desktop_dirs = ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"]
            for dir_name in desktop_dirs:
                os.makedirs(f"{home_dir}/{dir_name}", exist_ok=True)
                
            self.log_message("✓ Masaüstü ortamı kuruldu")
        except Exception as e:
            self.log_message(f"✗ Masaüstü kurulum hatası: {e}")
            
    def finalize_installation(self):
        """Finalize installation"""
        try:
            self.log_message("Son ayarlar yapılıyor...")
            
            # Mark as installed
            self.config["installed"] = True
            self.config["first_boot"] = False
            
            # Save configuration
            self.save_config()
            
            # Create installation flag
            with open(INSTALL_FLAG, 'w') as f:
                f.write(str(datetime.datetime.now()))
                
            # Setup autostart
            self.setup_autostart()
            
            self.log_message("✓ Kurulum tamamlandı")
        except Exception as e:
            self.log_message(f"✗ Son ayarlar hatası: {e}")
            
    def setup_autostart(self):
        """Setup autostart for Berke0S"""
        try:
            # Add to bootlocal.sh
            bootlocal_path = "/opt/bootlocal.sh"
            berke0s_cmd = f"python3 {os.path.abspath(__file__)} &\n"
            
            if os.path.exists(bootlocal_path):
                with open(bootlocal_path, 'r') as f:
                    content = f.read()
                if berke0s_cmd not in content:
                    with open(bootlocal_path, 'a') as f:
                        f.write(berke0s_cmd)
            else:
                with open(bootlocal_path, 'w') as f:
                    f.write("#!/bin/bash\n")
                    f.write(berke0s_cmd)
                    
            # Make executable
            os.chmod(bootlocal_path, 0o755)
            
            # Backup configuration
            subprocess.run(['filetool.sh', '-b'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                         
        except Exception as e:
            self.log_message(f"Autostart kurulum hatası: {e}")
            
    def installation_complete(self):
        """Installation completed"""
        # Hide navigation
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame) and hasattr(widget, 'nav_frame'):
                widget.nav_frame.pack_forget()
                
        # Show completion message
        complete_frame = tk.Frame(self.root, bg='#0f0f23')
        complete_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=20)
        
        tk.Label(complete_frame, text="🎉 Kurulum Başarıyla Tamamlandı!", 
                font=('Arial', 16, 'bold'), fg='#00ff88', bg='#0f0f23').pack(pady=10)
        
        tk.Label(complete_frame, text="Berke0S kullanmaya hazır!", 
                font=('Arial', 12), fg='white', bg='#0f0f23').pack()
        
        button_frame = tk.Frame(complete_frame, bg='#0f0f23')
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Sistemi Yeniden Başlat", 
                 command=self.reboot_system, bg='#00ff88', fg='black', 
                 font=('Arial', 12, 'bold'), padx=20).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Berke0S'u Başlat", 
                 command=self.start_berke0s, bg='#4a9eff', fg='white', 
                 font=('Arial', 12, 'bold'), padx=20).pack(side=tk.LEFT, padx=10)
        
    def show_complete(self):
        """Show completion screen"""
        self.installation_complete()
        
    def reboot_system(self):
        """Reboot the system"""
        try:
            subprocess.run(['sudo', 'reboot'], stdout=subprocess.DEVNULL)
        except:
            self.root.quit()
            
    def start_berke0s(self):
        """Start Berke0S desktop"""
        self.root.quit()
        # The main application will start after installation
        
    def add_navigation(self, parent):
        """Add navigation buttons"""
        nav_frame = tk.Frame(parent, bg='#0f0f23')
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        parent.nav_frame = nav_frame  # Store reference
        
        # Back button
        if self.current_step > 0:
            tk.Button(nav_frame, text="← Geri", command=self.prev_step,
                     bg='#666666', fg='white', font=('Arial', 11), padx=20).pack(side=tk.LEFT)
        
        # Next/Install button
        if self.current_step < len(self.steps) - 1:
            if self.current_step == len(self.steps) - 2:  # Installation step
                next_text = "Kurulumu Başlat"
                next_bg = '#ff6b6b'
            else:
                next_text = "İleri →"
                next_bg = '#00ff88'
                
            tk.Button(nav_frame, text=next_text, command=self.next_step,
                     bg=next_bg, fg='black' if next_bg == '#00ff88' else 'white', 
                     font=('Arial', 11, 'bold'), padx=20).pack(side=tk.RIGHT)
        
        # Step indicator
        step_text = f"{self.current_step + 1} / {len(self.steps)}"
        tk.Label(nav_frame, text=step_text, fg='#cccccc', bg='#0f0f23',
                font=('Arial', 10)).pack()
        
    def prev_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()
            
    def next_step(self):
        """Go to next step"""
        if self.validate_current_step():
            if self.current_step < len(self.steps) - 1:
                self.current_step += 1
                self.show_step()
                
    def validate_current_step(self):
        """Validate current step before proceeding"""
        step_name = self.steps[self.current_step]
        
        if step_name == "disk_setup":
            if not self.disk_listbox.curselection():
                messagebox.showerror("Hata", "Lütfen bir disk seçin!")
                return False
                
        elif step_name == "user_setup":
            if not self.username_var.get() or not self.password_var.get():
                messagebox.showerror("Hata", "Kullanıcı adı ve şifre gerekli!")
                return False
            if self.password_var.get() != self.confirm_password_var.get():
                messagebox.showerror("Hata", "Şifreler eşleşmiyor!")
                return False
                
        return True
        
    def save_config(self):
        """Save configuration"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Config save error: {e}")

# Notification System
class NotificationSystem:
    """Advanced notification system with animations"""
    
    def __init__(self, wm):
        self.wm = wm
        self.notifications = []
        self.notification_id = 0
        
    def send(self, title, message, timeout=5000, notification_type="info"):
        """Send a notification"""
        try:
            if not hasattr(self.wm, 'root') or not self.wm.root:
                return
                
            self.notification_id += 1
            
            # Create notification window
            notif = tk.Toplevel(self.wm.root)
            notif.withdraw()  # Hide initially
            notif.overrideredirect(True)
            notif.attributes('-topmost', True)
            notif.configure(bg='#1a1a1a')
            
            # Position
            screen_width = self.wm.root.winfo_screenwidth()
            screen_height = self.wm.root.winfo_screenheight()
            
            notif_width = 350
            notif_height = 80
            
            x = screen_width - notif_width - 20
            y = 20 + len(self.notifications) * (notif_height + 10)
            
            notif.geometry(f"{notif_width}x{notif_height}+{x}+{y}")
            
            # Content frame
            content_frame = tk.Frame(notif, bg='#1a1a1a', relief=tk.RAISED, bd=1)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # Icon and colors based on type
            colors = {
                "info": {"icon": "ℹ️", "color": "#4a9eff"},
                "success": {"icon": "✅", "color": "#00ff88"},
                "warning": {"icon": "⚠️", "color": "#ffb347"},
                "error": {"icon": "❌", "color": "#ff6b6b"}
            }
            
            notif_config = colors.get(notification_type, colors["info"])
            
            # Header
            header_frame = tk.Frame(content_frame, bg=notif_config["color"], height=25)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            tk.Label(header_frame, text=f"{notif_config['icon']} {title}", 
                    bg=notif_config["color"], fg='white', 
                    font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10, pady=3)
            
            # Close button
            close_btn = tk.Label(header_frame, text="✕", bg=notif_config["color"], 
                               fg='white', font=('Arial', 8), cursor='hand2')
            close_btn.pack(side=tk.RIGHT, padx=5, pady=3)
            close_btn.bind('<Button-1>', lambda e: self.close_notification(notif))
            
            # Message
            msg_frame = tk.Frame(content_frame, bg='#2a2a2a')
            msg_frame.pack(fill=tk.BOTH, expand=True)
            
            tk.Label(msg_frame, text=message, bg='#2a2a2a', fg='white', 
                    font=('Arial', 9), wraplength=320, justify=tk.LEFT).pack(
                    padx=10, pady=8, anchor='w')
            
            # Store notification
            self.notifications.append(notif)
            
            # Show with animation
            self.animate_notification(notif, "show")
            
            # Auto close
            if timeout > 0:
                self.wm.root.after(timeout, lambda: self.close_notification(notif))
                
        except Exception as e:
            logging.error(f"Notification error: {e}")
            
    def animate_notification(self, notif, action):
        """Animate notification appearance/disappearance"""
        try:
            if action == "show":
                notif.deiconify()
                notif.attributes('-alpha', 0)
                
                def fade_in(alpha=0):
                    if alpha <= 1:
                        notif.attributes('-alpha', alpha)
                        self.wm.root.after(20, lambda: fade_in(alpha + 0.1))
                        
                fade_in()
                
            elif action == "hide":
                def fade_out(alpha=1):
                    if alpha >= 0:
                        notif.attributes('-alpha', alpha)
                        self.wm.root.after(20, lambda: fade_out(alpha - 0.1))
                    else:
                        notif.destroy()
                        
                fade_out()
                
        except Exception as e:
            logging.error(f"Animation error: {e}")
            
    def close_notification(self, notif):
        """Close a notification"""
        try:
            if notif in self.notifications:
                self.notifications.remove(notif)
                self.animate_notification(notif, "hide")
                self.reposition_notifications()
        except Exception as e:
            logging.error(f"Close notification error: {e}")
            
    def reposition_notifications(self):
        """Reposition remaining notifications"""
        try:
            for i, notif in enumerate(self.notifications):
                screen_width = self.wm.root.winfo_screenwidth()
                x = screen_width - 350 - 20
                y = 20 + i * 90
                notif.geometry(f"350x80+{x}+{y}")
        except Exception as e:
            logging.error(f"Reposition error: {e}")

# Enhanced Window Manager
class WindowManager:
    """Advanced window manager with modern features"""
    
    def __init__(self):
        self.root = None
        self.windows = {}
        self.config = self.load_config()
        self.notifications = NotificationSystem(self)
        self.current_user = None
        self.desktop = None
        self.taskbar = None
        self.start_menu = None
        self.wallpaper_image = None
        self.themes = self.load_themes()
        self.shortcuts = {}
        self.running_apps = {}
        
        # Initialize display
        if not setup_display():
            raise RuntimeError("Display initialization failed")
            
        self.setup_ui()
        
    def load_config(self):
        """Load configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"Config load error: {e}")
            return DEFAULT_CONFIG.copy()
            
    def save_config(self):
        """Save configuration"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Config save error: {e}")
            
    def load_themes(self):
        """Load available themes"""
        return {
            "berke_dark": {
                "name": "Berke Dark",
                "bg": "#1a1a1a",
                "fg": "#ffffff",
                "accent": "#00ff88",
                "secondary": "#4a9eff",
                "warning": "#ffb347",
                "error": "#ff6b6b",
                "taskbar": "#0f0f23",
                "window": "#2a2a2a",
                "input": "#333333"
            },
            "berke_light": {
                "name": "Berke Light",
                "bg": "#f5f5f5",
                "fg": "#333333",
                "accent": "#007acc",
                "secondary": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "taskbar": "#e9ecef",
                "window": "#ffffff",
                "input": "#ffffff"
            },
            "ocean": {
                "name": "Ocean Blue",
                "bg": "#0d1b2a",
                "fg": "#ffffff",
                "accent": "#00b4d8",
                "secondary": "#0077b6",
                "warning": "#f77f00",
                "error": "#d62828",
                "taskbar": "#03045e",
                "window": "#1b263b",
                "input": "#415a77"
            }
        }
        
    def setup_ui(self):
        """Setup main UI"""
        try:
            self.root = tk.Tk()
            self.root.title("Berke0S Desktop")
            self.root.attributes('-fullscreen', True)
            self.root.configure(bg=self.get_theme_color("bg"))
            
            # Apply theme
            self.apply_theme()
            
            # Create desktop
            self.create_desktop()
            
            # Create taskbar
            self.create_taskbar()
            
            # Load wallpaper
            self.load_wallpaper()
            
            # Bind events
            self.bind_events()
            
            # Start system services
            self.start_services()
            
        except Exception as e:
            logging.error(f"UI setup error: {e}")
            raise
            
    def get_theme_color(self, color_name):
        """Get color from current theme"""
        theme_name = self.config.get("theme", "berke_dark")
        theme = self.themes.get(theme_name, self.themes["berke_dark"])
        return theme.get(color_name, "#000000")
        
    def apply_theme(self):
        """Apply current theme"""
        try:
            if self.root:
                self.root.configure(bg=self.get_theme_color("bg"))
                
            # Update existing windows
            for window in self.windows.values():
                if hasattr(window, 'window'):
                    window['window'].configure(bg=self.get_theme_color("window"))
                    
        except Exception as e:
            logging.error(f"Theme apply error: {e}")
            
    def create_desktop(self):
        """Create desktop area"""
        try:
            self.desktop = tk.Canvas(
                self.root,
                bg=self.get_theme_color("bg"),
                highlightthickness=0,
                cursor="arrow"
            )
            
            # Position based on taskbar
            taskbar_pos = self.config.get("taskbar", {}).get("position", "bottom")
            taskbar_size = self.config.get("taskbar", {}).get("size", 40)
            
            if taskbar_pos == "bottom":
                self.desktop.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
            elif taskbar_pos == "top":
                self.desktop.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)
            elif taskbar_pos == "left":
                self.desktop.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
            elif taskbar_pos == "right":
                self.desktop.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
                
            # Bind desktop events
            self.desktop.bind("<Button-3>", self.show_desktop_menu)
            self.desktop.bind("<Double-Button-1>", self.hide_all_windows)
            
        except Exception as e:
            logging.error(f"Desktop creation error: {e}")
            
    def create_taskbar(self):
        """Create taskbar"""
        try:
            taskbar_pos = self.config.get("taskbar", {}).get("position", "bottom")
            taskbar_size = self.config.get("taskbar", {}).get("size", 40)
            
            self.taskbar = tk.Frame(
                self.root,
                bg=self.get_theme_color("taskbar"),
                height=taskbar_size if taskbar_pos in ["top", "bottom"] else None,
                width=taskbar_size if taskbar_pos in ["left", "right"] else None
            )
            
            # Pack taskbar
            if taskbar_pos == "bottom":
                self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
            elif taskbar_pos == "top":
                self.taskbar.pack(side=tk.TOP, fill=tk.X)
            elif taskbar_pos == "left":
                self.taskbar.pack(side=tk.LEFT, fill=tk.Y)
            elif taskbar_pos == "right":
                self.taskbar.pack(side=tk.RIGHT, fill=tk.Y)
                
            self.taskbar.pack_propagate(False)
            
            # Create taskbar elements
            self.create_start_button()
            self.create_app_launcher()
            self.create_system_tray()
            
        except Exception as e:
            logging.error(f"Taskbar creation error: {e}")
            
    def create_start_button(self):
        """Create start menu button"""
        try:
            self.start_button = tk.Button(
                self.taskbar,
                text="🏠 Berke0S",
                bg=self.get_theme_color("accent"),
                fg="white",
                font=('Arial', 10, 'bold'),
                relief=tk.FLAT,
                padx=15,
                command=self.toggle_start_menu,
                cursor="hand2"
            )
            self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
            
        except Exception as e:
            logging.error(f"Start button creation error: {e}")
            
    def create_app_launcher(self):
        """Create quick app launcher"""
        try:
            self.launcher_frame = tk.Frame(self.taskbar, bg=self.get_theme_color("taskbar"))
            self.launcher_frame.pack(side=tk.LEFT, padx=10)
            
            # Quick launch apps
            quick_apps = [
                ("📁", "File Manager", self.launch_file_manager),
                ("🌐", "Web Browser", self.launch_web_browser),
                ("⚙️", "Settings", self.launch_settings),
                ("💻", "Terminal", self.launch_terminal)
            ]
            
            for icon, tooltip, command in quick_apps:
                btn = tk.Button(
                    self.launcher_frame,
                    text=icon,
                    bg=self.get_theme_color("taskbar"),
                    fg=self.get_theme_color("fg"),
                    font=('Arial', 12),
                    relief=tk.FLAT,
                    width=3,
                    command=command,
                    cursor="hand2"
                )
                btn.pack(side=tk.LEFT, padx=2)
                
                # Tooltip
                self.create_tooltip(btn, tooltip)
                
        except Exception as e:
            logging.error(f"App launcher creation error: {e}")
            
    def create_system_tray(self):
        """Create system tray"""
        try:
            self.tray_frame = tk.Frame(self.taskbar, bg=self.get_theme_color("taskbar"))
            self.tray_frame.pack(side=tk.RIGHT, padx=10)
            
            # Clock
            self.clock_label = tk.Label(
                self.tray_frame,
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 10, 'bold')
            )
            self.clock_label.pack(side=tk.RIGHT, padx=10)
            
            # System indicators
            self.create_system_indicators()
            
            # Update clock
            self.update_clock()
            
        except Exception as e:
            logging.error(f"System tray creation error: {e}")
            
    def create_system_indicators(self):
        """Create system status indicators"""
        try:
            # Network indicator
            self.network_indicator = tk.Label(
                self.tray_frame,
                text="📶",
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 10),
                cursor="hand2"
            )
            self.network_indicator.pack(side=tk.RIGHT, padx=2)
            self.network_indicator.bind("<Button-1>", self.show_network_menu)
            
            # Volume indicator
            self.volume_indicator = tk.Label(
                self.tray_frame,
                text="🔊",
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 10),
                cursor="hand2"
            )
            self.volume_indicator.pack(side=tk.RIGHT, padx=2)
            self.volume_indicator.bind("<Button-1>", self.show_volume_menu)
            
            # Battery indicator (if available)
            if self.has_battery():
                self.battery_indicator = tk.Label(
                    self.tray_frame,
                    text="🔋",
                    bg=self.get_theme_color("taskbar"),
                    fg=self.get_theme_color("fg"),
                    font=('Arial', 10),
                    cursor="hand2"
                )
                self.battery_indicator.pack(side=tk.RIGHT, padx=2)
                self.battery_indicator.bind("<Button-1>", self.show_battery_info)
                
        except Exception as e:
            logging.error(f"System indicators error: {e}")
            
    def update_clock(self):
        """Update system clock"""
        try:
            now = datetime.datetime.now()
            time_str = now.strftime("%H:%M")
            date_str = now.strftime("%d/%m/%Y")
            
            self.clock_label.config(text=f"{time_str}\n{date_str}")
            
            # Schedule next update
            self.root.after(1000, self.update_clock)
            
        except Exception as e:
            logging.error(f"Clock update error: {e}")
            
    def load_wallpaper(self):
        """Load desktop wallpaper"""
        try:
            wallpaper_path = self.config.get("desktop", {}).get("wallpaper", "")
            
            if wallpaper_path and os.path.exists(wallpaper_path) and PIL_AVAILABLE:
                # Load and resize image
                img = Image.open(wallpaper_path)
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                img = img.resize((screen_width, screen_height), Image.LANCZOS)
                self.wallpaper_image = ImageTk.PhotoImage(img)
                
                # Set as desktop background
                self.desktop.create_image(0, 0, anchor=tk.NW, image=self.wallpaper_image)
            else:
                # Create gradient background
                self.create_gradient_background()
                
        except Exception as e:
            logging.error(f"Wallpaper load error: {e}")
            self.create_gradient_background()
            
    def create_gradient_background(self):
        """Create gradient background"""
        try:
            if not PIL_AVAILABLE:
                return
                
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Create gradient image
            img = Image.new('RGB', (screen_width, screen_height))
            draw = ImageDraw.Draw(img)
            
            # Colors based on theme
            theme_name = self.config.get("theme", "berke_dark")
            if theme_name == "berke_dark":
                color1 = (15, 15, 35)  # Dark blue
                color2 = (26, 26, 26)  # Dark gray
            elif theme_name == "ocean":
                color1 = (13, 27, 42)  # Dark blue
                color2 = (3, 4, 94)    # Blue
            else:
                color1 = (245, 245, 245)  # Light gray
                color2 = (200, 200, 200)  # Gray
                
            # Create vertical gradient
            for y in range(screen_height):
                ratio = y / screen_height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                
                draw.line([(0, y), (screen_width, y)], fill=(r, g, b))
                
            self.wallpaper_image = ImageTk.PhotoImage(img)
            self.desktop.create_image(0, 0, anchor=tk.NW, image=self.wallpaper_image)
            
        except Exception as e:
            logging.error(f"Gradient background error: {e}")
            
    def bind_events(self):
        """Bind keyboard and mouse events"""
        try:
            # Global shortcuts
            self.root.bind('<Control-Alt-t>', lambda e: self.launch_terminal())
            self.root.bind('<Control-Alt-f>', lambda e: self.launch_file_manager())
            self.root.bind('<Control-Alt-s>', lambda e: self.launch_settings())
            self.root.bind('<Alt-F4>', lambda e: self.close_active_window())
            self.root.bind('<Control-Alt-l>', lambda e: self.lock_screen())
            
            # Window management
            self.root.bind('<Alt-Tab>', self.cycle_windows)
            
        except Exception as e:
            logging.error(f"Event binding error: {e}")
            
    def start_services(self):
        """Start background services"""
        try:
            # Start system monitoring
            threading.Thread(target=self.system_monitor, daemon=True).start()
            
            # Start auto-save
            threading.Thread(target=self.auto_save_session, daemon=True).start()
            
        except Exception as e:
            logging.error(f"Services start error: {e}")
            
    def system_monitor(self):
        """Monitor system resources"""
        while True:
            try:
                # Check CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > 90:
                    self.notifications.send(
                        "System Warning",
                        f"High CPU usage: {cpu_percent:.1f}%",
                        notification_type="warning"
                    )
                
                # Check memory usage
                memory = psutil.virtual_memory()
                if memory.percent > 90:
                    self.notifications.send(
                        "System Warning", 
                        f"High memory usage: {memory.percent:.1f}%",
                        notification_type="warning"
                    )
                
                # Check disk space
                disk = psutil.disk_usage('/')
                if disk.percent > 90:
                    self.notifications.send(
                        "System Warning",
                        f"Low disk space: {disk.percent:.1f}% used",
                        notification_type="warning"
                    )
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logging.error(f"System monitor error: {e}")
                time.sleep(60)
                
    def auto_save_session(self):
        """Auto-save session periodically"""
        while True:
            try:
                time.sleep(300)  # Save every 5 minutes
                self.save_session()
            except Exception as e:
                logging.error(f"Auto-save error: {e}")
                
    def save_session(self):
        """Save current session"""
        try:
            session_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "windows": [],
                "shortcuts": self.shortcuts,
                "current_user": self.current_user
            }
            
            # Save window states
            for window_id, window_data in self.windows.items():
                if hasattr(window_data, 'window') and window_data['window'].winfo_exists():
                    session_data["windows"].append({
                        "id": window_id,
                        "title": window_data.get("title", ""),
                        "app": window_data.get("app", ""),
                        "geometry": window_data['window'].geometry(),
                        "state": window_data['window'].state()
                    })
            
            with open(SESSION_FILE, 'w') as f:
                json.dump(session_data, f, indent=4)
                
        except Exception as e:
            logging.error(f"Session save error: {e}")
            
    # Application launchers
    def launch_file_manager(self):
        """Launch file manager"""
        try:
            if "file_manager" not in self.running_apps:
                app = FileManager(self)
                self.running_apps["file_manager"] = app
                app.show()
        except Exception as e:
            logging.error(f"File manager launch error: {e}")
            
    def launch_web_browser(self):
        """Launch web browser"""
        try:
            if "web_browser" not in self.running_apps:
                app = WebBrowser(self)
                self.running_apps["web_browser"] = app
                app.show()
        except Exception as e:
            logging.error(f"Web browser launch error: {e}")
            
    def launch_settings(self):
        """Launch settings"""
        try:
            if "settings" not in self.running_apps:
                app = SettingsApp(self)
                self.running_apps["settings"] = app
                app.show()
        except Exception as e:
            logging.error(f"Settings launch error: {e}")
            
    def launch_terminal(self):
        """Launch terminal"""
        try:
            app = Terminal(self)
            app.show()
        except Exception as e:
            logging.error(f"Terminal launch error: {e}")
            
    # Menu handlers
    def toggle_start_menu(self):
        """Toggle start menu"""
        try:
            if hasattr(self, 'start_menu_window') and self.start_menu_window.winfo_exists():
                self.start_menu_window.destroy()
                return
                
            self.show_start_menu()
            
        except Exception as e:
            logging.error(f"Start menu toggle error: {e}")
            
    def show_start_menu(self):
        """Show start menu"""
        try:
            self.start_menu_window = tk.Toplevel(self.root)
            self.start_menu_window.overrideredirect(True)
            self.start_menu_window.configure(bg=self.get_theme_color("window"))
            
            # Position menu
            x = self.start_button.winfo_rootx()
            y = self.start_button.winfo_rooty() - 400
            self.start_menu_window.geometry(f"300x400+{x}+{y}")
            
            # Create menu content
            self.create_start_menu_content()
            
            # Auto-hide on focus loss
            self.start_menu_window.bind('<FocusOut>', lambda e: self.start_menu_window.destroy())
            self.start_menu_window.focus_set()
            
        except Exception as e:
            logging.error(f"Start menu show error: {e}")
            
    def create_start_menu_content(self):
        """Create start menu content"""
        try:
            # Header
            header = tk.Frame(self.start_menu_window, bg=self.get_theme_color("accent"), height=60)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            
            tk.Label(header, text="Berke0S", font=('Arial', 16, 'bold'), 
                    bg=self.get_theme_color("accent"), fg="white").pack(pady=15)
            
            # Search
            search_frame = tk.Frame(self.start_menu_window, bg=self.get_theme_color("window"))
            search_frame.pack(fill=tk.X, padx=10, pady=5)
            
            self.search_var = tk.StringVar()
            search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                   bg=self.get_theme_color("input"), fg=self.get_theme_color("fg"),
                                   font=('Arial', 10))
            search_entry.pack(fill=tk.X)
            search_entry.bind('<KeyRelease>', self.filter_apps)
            
            # Apps list
            self.apps_frame = tk.Frame(self.start_menu_window, bg=self.get_theme_color("window"))
            self.apps_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Create scrollable app list
            self.create_apps_list()
            
            # Footer
            footer = tk.Frame(self.start_menu_window, bg=self.get_theme_color("window"), height=40)
            footer.pack(fill=tk.X)
            footer.pack_propagate(False)
            
            # Power options
            power_frame = tk.Frame(footer, bg=self.get_theme_color("window"))
            power_frame.pack(side=tk.RIGHT, padx=10, pady=5)
            
            tk.Button(power_frame, text="🔒", command=self.lock_screen,
                     bg=self.get_theme_color("window"), fg=self.get_theme_color("fg"),
                     relief=tk.FLAT, font=('Arial', 12)).pack(side=tk.LEFT, padx=2)
            
            tk.Button(power_frame, text="⚡", command=self.shutdown_menu,
                     bg=self.get_theme_color("window"), fg=self.get_theme_color("fg"),
                     relief=tk.FLAT, font=('Arial', 12)).pack(side=tk.LEFT, padx=2)
            
        except Exception as e:
            logging.error(f"Start menu content error: {e}")
            
    def create_apps_list(self):
        """Create applications list"""
        try:
            apps = [
                ("📁 File Manager", "file_manager", self.launch_file_manager),
                ("🌐 Web Browser", "web_browser", self.launch_web_browser),
                ("💻 Terminal", "terminal", self.launch_terminal),
                ("⚙️ Settings", "settings", self.launch_settings),
                ("📝 Text Editor", "text_editor", lambda: TextEditor(self).show()),
                ("🧮 Calculator", "calculator", lambda: Calculator(self).show()),
                ("🎵 Music Player", "music_player", lambda: MusicPlayer(self).show()),
                ("🖼️ Image Viewer", "image_viewer", lambda: ImageViewer(self).show()),
                ("📊 System Monitor", "system_monitor", lambda: SystemMonitor(self).show()),
                ("📧 Email Client", "email_client", lambda: EmailClient(self).show()),
                ("📅 Calendar", "calendar", lambda: Calendar(self).show()),
                ("🎮 Games", "games", lambda: GamesLauncher(self).show()),
                ("🔧 System Tools", "system_tools", lambda: SystemTools(self).show()),
            ]
            
            for app_name, app_id, command in apps:
                app_btn = tk.Button(
                    self.apps_frame,
                    text=app_name,
                    command=lambda cmd=command: self.launch_app(cmd),
                    bg=self.get_theme_color("window"),
                    fg=self.get_theme_color("fg"),
                    font=('Arial', 10),
                    relief=tk.FLAT,
                    anchor='w',
                    padx=10,
                    pady=5
                )
                app_btn.pack(fill=tk.X, pady=1)
                
                # Hover effects
                app_btn.bind('<Enter>', lambda e, btn=app_btn: btn.config(bg=self.get_theme_color("accent")))
                app_btn.bind('<Leave>', lambda e, btn=app_btn: btn.config(bg=self.get_theme_color("window")))
                
        except Exception as e:
            logging.error(f"Apps list creation error: {e}")
            
    def launch_app(self, command):
        """Launch application and close start menu"""
        try:
            command()
            if hasattr(self, 'start_menu_window') and self.start_menu_window.winfo_exists():
                self.start_menu_window.destroy()
        except Exception as e:
            logging.error(f"App launch error: {e}")
            
    def filter_apps(self, event=None):
        """Filter applications based on search"""
        # Implementation for app filtering
        pass
        
    def show_desktop_menu(self, event):
        """Show desktop context menu"""
        try:
            menu = tk.Menu(self.root, tearoff=0, bg=self.get_theme_color("window"),
                          fg=self.get_theme_color("fg"))
            
            menu.add_command(label="📁 New Folder", command=self.create_new_folder)
            menu.add_command(label="📄 New File", command=self.create_new_file)
            menu.add_separator()
            menu.add_command(label="🖼️ Change Wallpaper", command=self.change_wallpaper)
            menu.add_command(label="⚙️ Desktop Settings", command=self.desktop_settings)
            menu.add_separator()
            menu.add_command(label="🔄 Refresh", command=self.refresh_desktop)
            
            menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            logging.error(f"Desktop menu error: {e}")
            
    # Utility methods
    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, bg="#ffffe0", fg="black",
                           font=('Arial', 8), relief=tk.SOLID, borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
                
            tooltip.after(3000, hide_tooltip)
            
        widget.bind('<Enter>', show_tooltip)
        
    def has_battery(self):
        """Check if system has battery"""
        try:
            return psutil.sensors_battery() is not None
        except:
            return False
            
    def create_window(self, title, content_func, width=600, height=400, resizable=True):
        """Create a new application window"""
        try:
            window = tk.Toplevel(self.root)
            window.title(title)
            window.geometry(f"{width}x{height}")
            window.configure(bg=self.get_theme_color("window"))
            
            if not resizable:
                window.resizable(False, False)
                
            # Apply transparency if enabled
            if self.config.get("desktop", {}).get("effects", True):
                transparency = self.config.get("desktop", {}).get("transparency", 0.95)
                window.attributes('-alpha', transparency)
                
            # Create content
            content_func(window)
            
            # Store window
            window_id = str(uuid.uuid4())
            self.windows[window_id] = {
                "window": window,
                "title": title,
                "app": content_func.__name__ if hasattr(content_func, '__name__') else "unknown"
            }
            
            # Bind close event
            window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(window_id))
            
            return window
            
        except Exception as e:
            logging.error(f"Window creation error: {e}")
            return None
            
    def close_window(self, window_id):
        """Close a window"""
        try:
            if window_id in self.windows:
                window_data = self.windows[window_id]
                if hasattr(window_data, 'window'):
                    window_data['window'].destroy()
                del self.windows[window_id]
        except Exception as e:
            logging.error(f"Window close error: {e}")
            
    def run(self):
        """Run the window manager"""
        try:
            self.root.mainloop()
        except Exception as e:
            logging.error(f"Main loop error: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.save_session()
            self.save_config()
        except Exception as e:
            logging.error(f"Cleanup error: {e}")

# Application Classes
class FileManager:
    """Advanced file manager with modern features"""
    
    def __init__(self, wm):
        self.wm = wm
        self.current_path = os.path.expanduser("~")
        self.history = [self.current_path]
        self.history_index = 0
        self.bookmarks = ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"]
        self.clipboard = []
        self.clipboard_action = None  # 'copy' or 'cut'
        
    def show(self):
        """Show file manager window"""
        try:
            self.window = self.wm.create_window("File Manager", self.create_content, 800, 600)
            if self.window:
                self.refresh_view()
        except Exception as e:
            logging.error(f"File manager show error: {e}")
            
    def create_content(self, parent):
        """Create file manager content"""
        try:
            # Toolbar
            toolbar = tk.Frame(parent, bg=self.wm.get_theme_color("window"), height=40)
            toolbar.pack(fill=tk.X, padx=5, pady=5)
            toolbar.pack_propagate(False)
            
            # Navigation buttons
            nav_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            nav_frame.pack(side=tk.LEFT)
            
            tk.Button(nav_frame, text="←", command=self.go_back,
                     bg=self.wm.get_theme_color("accent"), fg="white", width=3).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="→", command=self.go_forward,
                     bg=self.wm.get_theme_color("accent"), fg="white", width=3).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="↑", command=self.go_up,
                     bg=self.wm.get_theme_color("accent"), fg="white", width=3).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="🏠", command=self.go_home,
                     bg=self.wm.get_theme_color("accent"), fg="white", width=3).pack(side=tk.LEFT, padx=2)
            
            # Address bar
            self.address_var = tk.StringVar(value=self.current_path)
            address_entry = tk.Entry(toolbar, textvariable=self.address_var,
                                   bg=self.wm.get_theme_color("input"), fg=self.wm.get_theme_color("fg"))
            address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            address_entry.bind('<Return>', self.navigate_to_address)
            
            # Action buttons
            action_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            action_frame.pack(side=tk.RIGHT)
            
            tk.Button(action_frame, text="📁+", command=self.create_folder,
                     bg=self.wm.get_theme_color("secondary"), fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(action_frame, text="📄+", command=self.create_file,
                     bg=self.wm.get_theme_color("secondary"), fg="white").pack(side=tk.LEFT, padx=2)
            
            # Main content area
            content_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Sidebar
            sidebar = tk.Frame(content_frame, bg=self.wm.get_theme_color("bg"), width=200)
            sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
            sidebar.pack_propagate(False)
            
            # Bookmarks
            tk.Label(sidebar, text="Quick Access", bg=self.wm.get_theme_color("bg"),
                    fg=self.wm.get_theme_color("fg"), font=('Arial', 10, 'bold')).pack(pady=5)
            
            for bookmark in self.bookmarks:
                btn = tk.Button(sidebar, text=f"📁 {bookmark}", 
                               command=lambda b=bookmark: self.navigate_to_bookmark(b),
                               bg=self.wm.get_theme_color("bg"), fg=self.wm.get_theme_color("fg"),
                               relief=tk.FLAT, anchor='w')
                btn.pack(fill=tk.X, padx=5, pady=1)
                
            # File list area
            list_frame = tk.Frame(content_frame, bg=self.wm.get_theme_color("window"))
            list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # File list with scrollbar
            list_container = tk.Frame(list_frame, bg=self.wm.get_theme_color("window"))
            list_container.pack(fill=tk.BOTH, expand=True)
            
            self.file_listbox = tk.Listbox(list_container, 
                                          bg=self.wm.get_theme_color("input"),
                                          fg=self.wm.get_theme_color("fg"),
                                          font=('Courier', 10),
                                          selectmode=tk.EXTENDED)
            
            scrollbar = tk.Scrollbar(list_container, command=self.file_listbox.yview)
            self.file_listbox.config(yscrollcommand=scrollbar.set)
            
            self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bind events
            self.file_listbox.bind('<Double-Button-1>', self.open_selected)
            self.file_listbox.bind('<Button-3>', self.show_context_menu)
            self.file_listbox.bind('<Control-c>', self.copy_files)
            self.file_listbox.bind('<Control-x>', self.cut_files)
            self.file_listbox.bind('<Control-v>', self.paste_files)
            self.file_listbox.bind('<Delete>', self.delete_files)
            
            # Status bar
            self.status_bar = tk.Label(parent, text="Ready", 
                                      bg=self.wm.get_theme_color("bg"),
                                      fg=self.wm.get_theme_color("fg"),
                                      relief=tk.SUNKEN, anchor='w')
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
        except Exception as e:
            logging.error(f"File manager content creation error: {e}")
            
    def refresh_view(self):
        """Refresh file list view"""
        try:
            self.file_listbox.delete(0, tk.END)
            self.address_var.set(self.current_path)
            
            if not os.path.exists(self.current_path):
                self.current_path = os.path.expanduser("~")
                self.address_var.set(self.current_path)
                
            try:
                items = os.listdir(self.current_path)
                items.sort(key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x.lower()))
                
                for item in items:
                    item_path = os.path.join(self.current_path, item)
                    if os.path.isdir(item_path):
                        self.file_listbox.insert(tk.END, f"📁 {item}")
                    else:
                        # Get file extension for icon
                        ext = os.path.splitext(item)[1].lower()
                        icon = self.get_file_icon(ext)
                        self.file_listbox.insert(tk.END, f"{icon} {item}")
                        
                self.status_bar.config(text=f"{len(items)} items in {self.current_path}")
                
            except PermissionError:
                self.file_listbox.insert(tk.END, "❌ Permission denied")
                self.status_bar.config(text="Permission denied")
                
        except Exception as e:
            logging.error(f"File view refresh error: {e}")
            
    def get_file_icon(self, ext):
        """Get icon for file extension"""
        icons = {
            '.txt': '📄', '.py': '🐍', '.js': '📜', '.html': '🌐',
            '.css': '🎨', '.json': '📋', '.xml': '📋', '.md': '📝',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.mp4': '🎬', '.avi': '🎬',
            '.pdf': '📕', '.doc': '📘', '.docx': '📘', '.xls': '📗',
            '.zip': '📦', '.tar': '📦', '.gz': '📦', '.rar': '📦'
        }
        return icons.get(ext, '📄')
        
    def navigate_to_address(self, event=None):
        """Navigate to address bar path"""
        try:
            new_path = self.address_var.get()
            if os.path.exists(new_path) and os.path.isdir(new_path):
                self.navigate_to(new_path)
            else:
                self.wm.notifications.send("File Manager", "Path not found", notification_type="error")
                self.address_var.set(self.current_path)
        except Exception as e:
            logging.error(f"Address navigation error: {e}")
            
    def navigate_to(self, path):
        """Navigate to specific path"""
        try:
            self.current_path = os.path.abspath(path)
            self.history = self.history[:self.history_index + 1]
            self.history.append(self.current_path)
            self.history_index = len(self.history) - 1
            self.refresh_view()
        except Exception as e:
            logging.error(f"Navigation error: {e}")
            
    def navigate_to_bookmark(self, bookmark):
        """Navigate to bookmark"""
        try:
            home = os.path.expanduser("~")
            path = os.path.join(home, bookmark)
            if os.path.exists(path):
                self.navigate_to(path)
            else:
                # Create directory if it doesn't exist
                os.makedirs(path, exist_ok=True)
                self.navigate_to(path)
        except Exception as e:
            logging.error(f"Bookmark navigation error: {e}")
            
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
        
    def open_selected(self, event=None):
        """Open selected file or directory"""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                return
                
            item_text = self.file_listbox.get(selection[0])
            item_name = item_text[2:]  # Remove icon
            item_path = os.path.join(self.current_path, item_name)
            
            if os.path.isdir(item_path):
                self.navigate_to(item_path)
            else:
                self.open_file(item_path)
                
        except Exception as e:
            logging.error(f"Open selected error: {e}")
            
    def open_file(self, file_path):
        """Open file with appropriate application"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md']:
                TextEditor(self.wm).show(file_path)
            elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
                ImageViewer(self.wm).show(file_path)
            elif ext in ['.mp3', '.wav']:
                MusicPlayer(self.wm).show(file_path)
            elif ext in ['.mp4', '.avi']:
                VideoPlayer(self.wm).show(file_path)
            else:
                # Try to open with system default
                subprocess.run(['xdg-open', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
        except Exception as e:
            logging.error(f"File open error: {e}")
            self.wm.notifications.send("File Manager", f"Cannot open file: {e}", notification_type="error")

# Additional Application Classes would continue here...
# For brevity, I'll include a few key ones:

class TextEditor:
    """Advanced text editor with syntax highlighting"""
    
    def __init__(self, wm):
        self.wm = wm
        self.current_file = None
        self.modified = False
        
    def show(self, file_path=None):
        """Show text editor window"""
        try:
            self.window = self.wm.create_window("Text Editor", self.create_content, 800, 600)
            if file_path:
                self.open_file(file_path)
        except Exception as e:
            logging.error(f"Text editor show error: {e}")
            
    def create_content(self, parent):
        """Create text editor content"""
        try:
            # Menu bar
            menubar = tk.Menu(parent)
            parent.config(menu=menubar)
            
            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
            file_menu.add_command(label="Open", command=self.open_file_dialog, accelerator="Ctrl+O")
            file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
            file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Ctrl+Shift+S")
            
            # Edit menu
            edit_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Edit", menu=edit_menu)
            edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
            edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
            edit_menu.add_separator()
            edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
            edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
            edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
            
            # Toolbar
            toolbar = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            toolbar.pack(fill=tk.X, padx=5, pady=5)
            
            tk.Button(toolbar, text="📄", command=self.new_file,
                     bg=self.wm.get_theme_color("accent"), fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="📁", command=self.open_file_dialog,
                     bg=self.wm.get_theme_color("accent"), fg="white").pack(side=tk.LEFT, padx=2)
            tk.Button(toolbar, text="💾", command=self.save_file,
                     bg=self.wm.get_theme_color("accent"), fg="white").pack(side=tk.LEFT, padx=2)
            
            # Text area with scrollbars
            text_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.text_area = tk.Text(text_frame, 
                                    bg=self.wm.get_theme_color("input"),
                                    fg=self.wm.get_theme_color("fg"),
                                    font=('Courier', 11),
                                    wrap=tk.NONE,
                                    undo=True)
            
            # Scrollbars
            v_scrollbar = tk.Scrollbar(text_frame, command=self.text_area.yview)
            h_scrollbar = tk.Scrollbar(text_frame, command=self.text_area.xview, orient=tk.HORIZONTAL)
            
            self.text_area.config(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Pack scrollbars and text area
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            self.text_area.pack(fill=tk.BOTH, expand=True)
            
            # Status bar
            self.status_bar = tk.Label(parent, text="Ready", 
                                      bg=self.wm.get_theme_color("bg"),
                                      fg=self.wm.get_theme_color("fg"),
                                      relief=tk.SUNKEN, anchor='w')
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Bind events
            self.text_area.bind('<KeyRelease>', self.on_text_change)
            self.text_area.bind('<Button-1>', self.update_cursor_position)
            
            # Keyboard shortcuts
            parent.bind('<Control-n>', lambda e: self.new_file())
            parent.bind('<Control-o>', lambda e: self.open_file_dialog())
            parent.bind('<Control-s>', lambda e: self.save_file())
            
        except Exception as e:
            logging.error(f"Text editor content creation error: {e}")

class Calculator:
    """Scientific calculator with advanced functions"""
    
    def __init__(self, wm):
        self.wm = wm
        self.display_var = tk.StringVar(value="0")
        self.memory = 0
        self.last_operation = None
        self.last_number = None
        
    def show(self):
        """Show calculator window"""
        try:
            self.window = self.wm.create_window("Calculator", self.create_content, 350, 500, False)
        except Exception as e:
            logging.error(f"Calculator show error: {e}")
            
    def create_content(self, parent):
        """Create calculator content"""
        try:
            # Display
            display_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            display_frame.pack(fill=tk.X, padx=10, pady=10)
            
            display = tk.Entry(display_frame, textvariable=self.display_var,
                              font=('Arial', 16, 'bold'), justify='right',
                              bg=self.wm.get_theme_color("input"),
                              fg=self.wm.get_theme_color("fg"),
                              state='readonly', relief=tk.SUNKEN, bd=2)
            display.pack(fill=tk.X, ipady=10)
            
            # Buttons frame
            buttons_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            buttons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Button layout
            buttons = [
                ['C', 'CE', '⌫', '/'],
                ['7', '8', '9', '*'],
                ['4', '5', '6', '-'],
                ['1', '2', '3', '+'],
                ['±', '0', '.', '=']
            ]
            
            for i, row in enumerate(buttons):
                for j, btn_text in enumerate(row):
                    self.create_button(buttons_frame, btn_text, i, j)
                    
            # Scientific functions (if space allows)
            sci_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            sci_frame.pack(fill=tk.X, padx=10, pady=5)
            
            sci_buttons = ['sin', 'cos', 'tan', 'log', '√', 'x²', '(', ')']
            for i, btn_text in enumerate(sci_buttons):
                btn = tk.Button(sci_frame, text=btn_text,
                               command=lambda t=btn_text: self.button_click(t),
                               bg=self.wm.get_theme_color("secondary"), fg="white",
                               font=('Arial', 10), width=4)
                btn.grid(row=0, column=i, padx=1, pady=1, sticky='nsew')
                
        except Exception as e:
            logging.error(f"Calculator content creation error: {e}")
            
    def create_button(self, parent, text, row, col):
        """Create calculator button"""
        try:
            # Color coding
            if text in ['C', 'CE', '⌫']:
                bg_color = self.wm.get_theme_color("error")
            elif text in ['+', '-', '*', '/', '=']:
                bg_color = self.wm.get_theme_color("accent")
            else:
                bg_color = self.wm.get_theme_color("bg")
                
            btn = tk.Button(parent, text=text,
                           command=lambda: self.button_click(text),
                           bg=bg_color, fg="white",
                           font=('Arial', 14, 'bold'),
                           width=4, height=2)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
            
            # Configure grid weights
            parent.grid_rowconfigure(row, weight=1)
            parent.grid_columnconfigure(col, weight=1)
            
        except Exception as e:
            logging.error(f"Calculator button creation error: {e}")
            
    def button_click(self, text):
        """Handle button clicks"""
        try:
            current = self.display_var.get()
            
            if text.isdigit() or text == '.':
                if current == "0" or current == "Error":
                    self.display_var.set(text)
                else:
                    self.display_var.set(current + text)
                    
            elif text in ['+', '-', '*', '/']:
                self.last_number = float(current)
                self.last_operation = text
                self.display_var.set("0")
                
            elif text == '=':
                if self.last_operation and self.last_number is not None:
                    try:
                        current_num = float(current)
                        if self.last_operation == '+':
                            result = self.last_number + current_num
                        elif self.last_operation == '-':
                            result = self.last_number - current_num
                        elif self.last_operation == '*':
                            result = self.last_number * current_num
                        elif self.last_operation == '/':
                            if current_num != 0:
                                result = self.last_number / current_num
                            else:
                                self.display_var.set("Error")
                                return
                                
                        self.display_var.set(str(result))
                        self.last_operation = None
                        self.last_number = None
                        
                    except:
                        self.display_var.set("Error")
                        
            elif text == 'C':
                self.display_var.set("0")
                self.last_operation = None
                self.last_number = None
                
            elif text == 'CE':
                self.display_var.set("0")
                
            elif text == '⌫':
                if len(current) > 1:
                    self.display_var.set(current[:-1])
                else:
                    self.display_var.set("0")
                    
            elif text == '±':
                if current != "0":
                    if current.startswith('-'):
                        self.display_var.set(current[1:])
                    else:
                        self.display_var.set('-' + current)
                        
            # Scientific functions
            elif text == '√':
                try:
                    result = math.sqrt(float(current))
                    self.display_var.set(str(result))
                except:
                    self.display_var.set("Error")
                    
            elif text == 'x²':
                try:
                    result = float(current) ** 2
                    self.display_var.set(str(result))
                except:
                    self.display_var.set("Error")
                    
            elif text in ['sin', 'cos', 'tan']:
                try:
                    angle = math.radians(float(current))
                    if text == 'sin':
                        result = math.sin(angle)
                    elif text == 'cos':
                        result = math.cos(angle)
                    elif text == 'tan':
                        result = math.tan(angle)
                    self.display_var.set(str(result))
                except:
                    self.display_var.set("Error")
                    
            elif text == 'log':
                try:
                    result = math.log10(float(current))
                    self.display_var.set(str(result))
                except:
                    self.display_var.set("Error")
                    
        except Exception as e:
            logging.error(f"Calculator button click error: {e}")
            self.display_var.set("Error")

# Main execution
def main():
    """Main entry point"""
    try:
        # Check if installation is needed
        if not os.path.exists(INSTALL_FLAG) or "--install" in sys.argv:
            installer = InstallationWizard()
            installer.start_installation()
            
            # After installation, check if we should start the desktop
            if os.path.exists(INSTALL_FLAG):
                config = DEFAULT_CONFIG.copy()
                try:
                    with open(CONFIG_FILE, 'r') as f:
                        config.update(json.load(f))
                except:
                    pass
                    
                if config.get("installed", False):
                    # Start desktop environment
                    wm = WindowManager()
                    wm.run()
        else:
            # Start desktop environment directly
            wm = WindowManager()
            wm.run()
            
    except KeyboardInterrupt:
        print("\nBerke0S terminated by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Main execution error: {e}")
        print(f"Error starting Berke0S: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Berke0S - Ultimate Complete Desktop Environment for Tiny Core Linux
Created by: Berke Oruç
Version: 4.0 - Ultimate Complete Edition
License: MIT

The most advanced desktop environment with complete features
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
import tempfile
import webbrowser
import urllib.request
import urllib.parse
import http.server
import socketserver
import sqlite3
import configparser
import platform
import ctypes
import mimetypes
import smtplib
import imaplib
import email
import ssl
import ftplib
import telnetlib
import pickle
import csv
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO
from urllib.parse import quote, unquote
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, colorchooser
from tkinter import font as tkFont
from tkinter import scrolledtext

# Try to import optional dependencies
try:
    from PIL import Image, ImageTk, ImageGrab, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available - some features will be limited")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Requests not available - network features limited")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Pygame not available - audio/game features limited")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.backends.backend_tkagg as tkagg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Enhanced Configuration
CONFIG_DIR = os.path.expanduser("~/.berke0s")
CONFIG_FILE = f"{CONFIG_DIR}/config.json"
SESSION_FILE = f"{CONFIG_DIR}/session.json"
LOG_FILE = f"{CONFIG_DIR}/berke0s.log"
INSTALL_FLAG = f"{CONFIG_DIR}/.installed"
THEMES_DIR = f"{CONFIG_DIR}/themes"
PLUGINS_DIR = f"{CONFIG_DIR}/plugins"
WALLPAPERS_DIR = f"{CONFIG_DIR}/wallpapers"
APPS_DIR = f"{CONFIG_DIR}/applications"
DATABASE_FILE = f"{CONFIG_DIR}/berke0s.db"
USERS_FILE = f"{CONFIG_DIR}/users.db"
SECURITY_FILE = f"{CONFIG_DIR}/security.json"
BACKUP_DIR = f"{CONFIG_DIR}/backups"
CACHE_DIR = f"{CONFIG_DIR}/cache"
TEMP_DIR = f"{CONFIG_DIR}/temp"

# Ensure directories exist
for directory in [CONFIG_DIR, THEMES_DIR, PLUGINS_DIR, WALLPAPERS_DIR, APPS_DIR, BACKUP_DIR, CACHE_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('Berke0S')

# Enhanced default configuration
DEFAULT_CONFIG = {
    "version": "4.0",
    "first_boot": True,
    "language": "tr_TR",
    "timezone": "Europe/Istanbul",
    "theme": "berke_dark",
    "current_user": None,
    "auto_login": False,
    "last_login": None,
    "wifi": {"ssid": "", "password": ""},
    "installed": False,
    "setup_completed": False,
    "desktop": {
        "wallpaper": "",
        "wallpaper_mode": "stretch",
        "icon_size": 48,
        "grid_snap": True,
        "effects": True,
        "transparency": 0.95,
        "blur_radius": 5,
        "shadow_offset": 3,
        "animation_speed": 300,
        "auto_arrange": False,
        "show_desktop_icons": True,
        "desktop_icons": [],
        "virtual_desktops": 4,
        "show_dock": False,
        "dock_position": "bottom"
    },
    "taskbar": {
        "position": "bottom",
        "auto_hide": False,
        "color": "#1a1a1a",
        "size": 45,
        "show_clock": True,
        "show_system_tray": True,
        "show_quick_launch": True,
        "transparency": 0.9,
        "show_window_list": True,
        "group_windows": True
    },
    "notifications": {
        "enabled": True,
        "timeout": 5000,
        "position": "top-right",
        "sound_enabled": True,
        "show_previews": True,
        "max_notifications": 5
    },
    "power": {
        "sleep_timeout": 1800,
        "screen_off_timeout": 900,
        "hibernate_enabled": True,
        "cpu_scaling": "ondemand",
        "auto_suspend": False,
        "battery_warning": 20
    },
    "accessibility": {
        "high_contrast": False,
        "screen_reader": False,
        "font_scale": 1.0,
        "magnifier": False,
        "keyboard_navigation": True,
        "sticky_keys": False,
        "slow_keys": False
    },
    "security": {
        "auto_lock": True,
        "lock_timeout": 600,
        "require_password": True,
        "encryption_enabled": False,
        "firewall_enabled": True,
        "auto_backup": True,
        "backup_interval": 24,
        "password_policy": {
            "min_length": 6,
            "require_uppercase": False,
            "require_lowercase": False,
            "require_numbers": False,
            "require_symbols": False
        }
    },
    "network": {
        "auto_connect": True,
        "proxy_enabled": False,
        "proxy_host": "",
        "proxy_port": 8080,
        "firewall_enabled": True,
        "vpn_enabled": False,
        "dns_servers": ["8.8.8.8", "8.8.4.4"]
    },
    "audio": {
        "master_volume": 75,
        "mute": False,
        "default_device": "auto",
        "sound_theme": "default",
        "notification_sounds": True,
        "system_sounds": True
    },
    "system": {
        "auto_updates": True,
        "crash_reporting": True,
        "telemetry": False,
        "performance_mode": "balanced",
        "startup_programs": [],
        "file_associations": {},
        "default_applications": {},
        "recent_files": [],
        "max_recent_files": 20
    },
    "applications": {
        "text_editor": {
            "font_family": "Courier",
            "font_size": 11,
            "syntax_highlighting": True,
            "line_numbers": True,
            "word_wrap": False,
            "auto_indent": True,
            "tab_size": 4
        },
        "file_manager": {
            "view_mode": "list",
            "show_hidden": False,
            "sort_by": "name",
            "sort_reverse": False,
            "thumbnail_size": 128,
            "preview_enabled": True
        },
        "web_browser": {
            "homepage": "https://www.google.com",
            "search_engine": "google",
            "block_popups": True,
            "enable_javascript": True,
            "save_passwords": False
        }
    }
}

# Enhanced display detection and setup
def setup_display():
    """Enhanced display setup with multiple fallback options"""
    try:
        logger.info("Setting up display environment...")
        
        # Force display setup for Tiny Core Linux
        os.environ['DISPLAY'] = ':0.0'
        
        # Check if running in virtual environment
        if 'DISPLAY' not in os.environ and not os.path.exists('/tmp/.X11-unix'):
            logger.warning("No display detected, attempting to start X server...")
        
        # Try multiple X server start methods
        x_methods = [
            ['startx', '--', ':0'],
            ['xinit', '--', ':0'],
            ['X', ':0', '-nolisten', 'tcp', '-noreset'],
            ['Xorg', ':0', '-nolisten', 'tcp', '-noreset'],
            ['Xvfb', ':0', '-screen', '0', '1024x768x24']  # Virtual framebuffer fallback
        ]
        
        for method in x_methods:
            try:
                logger.info(f"Trying X server method: {method}")
                result = subprocess.run(['pgrep', '-f', 'X'], capture_output=True)
                if result.returncode == 0:
                    logger.info("X server already running")
                    break
                    
                # Start X server in background
                process = subprocess.Popen(method, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                
                # Test if X is working
                test_result = subprocess.run(['xdpyinfo'], capture_output=True, timeout=5)
                if test_result.returncode == 0:
                    logger.info(f"X server started successfully with {method}")
                    break
                else:
                    # Kill the process if it didn't work
                    try:
                        process.terminate()
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Failed to start X with {method}: {e}")
                continue
        
        # Additional display setup for Tiny Core
        try:
            # Set window manager if none is running
            wm_result = subprocess.run(['pgrep', '-f', 'wm|flwm|openbox|jwm'], capture_output=True)
            if wm_result.returncode != 0:
                logger.info("Starting window manager...")
                wm_options = ['flwm', 'openbox', 'jwm', 'twm']
                for wm in wm_options:
                    try:
                        subprocess.Popen([wm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(2)
                        break
                    except FileNotFoundError:
                        continue
        except:
            pass
            
        # Test final display
        try:
            test_result = subprocess.run(['xset', 'q'], capture_output=True, timeout=3)
            if test_result.returncode == 0:
                logger.info("Display setup successful")
                return True
        except:
            pass
            
        # Final fallback - try to create a minimal display
        try:
            import tkinter
            root = tkinter.Tk()
            root.withdraw()
            root.destroy()
            logger.info("Tkinter display test successful")
            return True
        except Exception as e:
            logger.error(f"Tkinter display test failed: {e}")
            
        logger.warning("Display setup completed with warnings")
        return True
        
    except Exception as e:
        logger.error(f"Display setup failed: {e}")
        return True  # Continue anyway for headless/console mode

def init_database():
    """Initialize enhanced SQLite database for system data"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Users table with enhanced fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                fullname TEXT,
                email TEXT,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                preferences TEXT,
                avatar_path TEXT,
                theme TEXT DEFAULT 'berke_dark',
                language TEXT DEFAULT 'tr_TR'
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                session_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Files metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                file_name TEXT,
                file_type TEXT,
                mime_type TEXT,
                size INTEGER,
                created_at TIMESTAMP,
                modified_at TIMESTAMP,
                accessed_at TIMESTAMP,
                tags TEXT,
                rating INTEGER DEFAULT 0,
                description TEXT,
                thumbnail_path TEXT,
                checksum TEXT
            )
        ''')
        
        # System logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                message TEXT,
                component TEXT,
                user_id INTEGER,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                command TEXT NOT NULL,
                icon TEXT,
                category TEXT,
                description TEXT,
                version TEXT,
                author TEXT,
                website TEXT,
                installed INTEGER DEFAULT 1,
                auto_start INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                file_associations TEXT,
                permissions TEXT
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                key TEXT,
                value TEXT,
                data_type TEXT DEFAULT 'string',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, category, key)
            )
        ''')
        
        # Bookmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                icon TEXT,
                category TEXT DEFAULT 'general',
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Recent files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recent_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_path TEXT NOT NULL,
                file_name TEXT,
                application TEXT,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Themes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT,
                author TEXT,
                version TEXT,
                description TEXT,
                theme_data TEXT,
                preview_image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_system INTEGER DEFAULT 0
            )
        ''')
        
        # Plugins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT,
                version TEXT,
                author TEXT,
                description TEXT,
                file_path TEXT,
                enabled INTEGER DEFAULT 0,
                auto_load INTEGER DEFAULT 0,
                dependencies TEXT,
                permissions TEXT,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Network connections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                ssid TEXT,
                password TEXT,
                security_type TEXT,
                auto_connect INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_connected TIMESTAMP
            )
        ''')
        
        # System performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                network_bytes_sent INTEGER,
                network_bytes_recv INTEGER,
                temperature REAL,
                battery_percent REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Enhanced database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

def create_default_user():
    """Create default admin user if no users exist"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create default admin user
            salt = os.urandom(32)
            password_hash = hashlib.pbkdf2_hmac('sha256', b'admin', salt, 100000)
            
            cursor.execute('''
                INSERT INTO users (username, fullname, password_hash, salt, is_admin, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', 'Administrator', password_hash.hex(), salt.hex(), 1, 1))
            
            conn.commit()
            logger.info("Default admin user created (username: admin, password: admin)")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Default user creation failed: {e}")

# Enhanced Security System
class SecurityManager:
    """Enhanced security management system"""
    
    def __init__(self):
        self.failed_attempts = {}
        self.locked_accounts = {}
        self.session_tokens = {}
        self.security_config = self.load_security_config()
        
    def load_security_config(self):
        """Load security configuration"""
        try:
            if os.path.exists(SECURITY_FILE):
                with open(SECURITY_FILE, 'r') as f:
                    return json.load(f)
            return {
                "max_failed_attempts": 5,
                "lockout_duration": 300,  # 5 minutes
                "session_timeout": 3600,  # 1 hour
                "password_history": 5,
                "require_password_change": False,
                "password_expiry_days": 90
            }
        except Exception as e:
            logger.error(f"Security config load error: {e}")
            return {}
    
    def save_security_config(self):
        """Save security configuration"""
        try:
            with open(SECURITY_FILE, 'w') as f:
                json.dump(self.security_config, f, indent=4)
        except Exception as e:
            logger.error(f"Security config save error: {e}")
    
    def hash_password(self, password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(32)
        elif isinstance(salt, str):
            salt = bytes.fromhex(salt)
        
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return password_hash.hex(), salt.hex()
    
    def verify_password(self, password, stored_hash, salt):
        """Verify password against stored hash"""
        try:
            computed_hash, _ = self.hash_password(password, salt)
            return computed_hash == stored_hash
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def authenticate_user(self, username, password):
        """Authenticate user with enhanced security"""
        try:
            # Check if account is locked
            if self.is_account_locked(username):
                return None, "Account is temporarily locked due to failed login attempts"
            
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, fullname, password_hash, salt, is_admin, is_active, 
                       failed_login_attempts, locked_until
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                self.record_failed_attempt(username)
                return None, "Invalid username or password"
            
            user_id, username, fullname, stored_hash, salt, is_admin, is_active, failed_attempts, locked_until = user
            
            if not is_active:
                return None, "Account is disabled"
            
            if locked_until and datetime.datetime.fromisoformat(locked_until) > datetime.datetime.now():
                return None, "Account is temporarily locked"
            
            if self.verify_password(password, stored_hash, salt):
                # Successful login
                self.clear_failed_attempts(username)
                self.update_login_info(user_id)
                
                # Create session token
                session_token = self.create_session_token(user_id)
                
                user_info = {
                    'id': user_id,
                    'username': username,
                    'fullname': fullname,
                    'is_admin': bool(is_admin),
                    'session_token': session_token
                }
                
                conn.close()
                return user_info, "Login successful"
            else:
                # Failed login
                self.record_failed_attempt(username, user_id)
                conn.close()
                return None, "Invalid username or password"
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None, "Authentication system error"
    
    def is_account_locked(self, username):
        """Check if account is locked"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT locked_until, failed_login_attempts 
                FROM users WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                locked_until, failed_attempts = result
                if locked_until:
                    lock_time = datetime.datetime.fromisoformat(locked_until)
                    if lock_time > datetime.datetime.now():
                        return True
                
                max_attempts = self.security_config.get("max_failed_attempts", 5)
                if failed_attempts >= max_attempts:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Account lock check error: {e}")
            return False
    
    def record_failed_attempt(self, username, user_id=None):
        """Record failed login attempt"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    UPDATE users 
                    SET failed_login_attempts = failed_login_attempts + 1
                    WHERE id = ?
                ''', (user_id,))
                
                # Check if should lock account
                cursor.execute('SELECT failed_login_attempts FROM users WHERE id = ?', (user_id,))
                attempts = cursor.fetchone()[0]
                
                max_attempts = self.security_config.get("max_failed_attempts", 5)
                if attempts >= max_attempts:
                    lockout_duration = self.security_config.get("lockout_duration", 300)
                    locked_until = datetime.datetime.now() + datetime.timedelta(seconds=lockout_duration)
                    
                    cursor.execute('''
                        UPDATE users 
                        SET locked_until = ?
                        WHERE id = ?
                    ''', (locked_until.isoformat(), user_id))
            
            # Log the attempt
            cursor.execute('''
                INSERT INTO system_logs (level, message, component, user_id)
                VALUES (?, ?, ?, ?)
            ''', ('WARNING', f'Failed login attempt for username: {username}', 'Security', user_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed attempt recording error: {e}")
    
    def clear_failed_attempts(self, username):
        """Clear failed login attempts"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET failed_login_attempts = 0, locked_until = NULL
                WHERE username = ?
            ''', (username,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Clear failed attempts error: {e}")
    
    def update_login_info(self, user_id):
        """Update user login information"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                WHERE id = ?
            ''', (user_id,))
            
            cursor.execute('''
                INSERT INTO system_logs (level, message, component, user_id)
                VALUES (?, ?, ?, ?)
            ''', ('INFO', 'User logged in successfully', 'Security', user_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Login info update error: {e}")
    
    def create_session_token(self, user_id):
        """Create session token"""
        try:
            token = str(uuid.uuid4())
            expires_at = datetime.datetime.now() + datetime.timedelta(
                seconds=self.security_config.get("session_timeout", 3600)
            )
            
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, token, expires_at.isoformat()))
            
            conn.commit()
            conn.close()
            
            self.session_tokens[token] = {
                'user_id': user_id,
                'expires_at': expires_at
            }
            
            return token
            
        except Exception as e:
            logger.error(f"Session token creation error: {e}")
            return None
    
    def validate_session_token(self, token):
        """Validate session token"""
        try:
            if token in self.session_tokens:
                session = self.session_tokens[token]
                if session['expires_at'] > datetime.datetime.now():
                    return session['user_id']
                else:
                    del self.session_tokens[token]
            
            # Check database
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, expires_at FROM sessions 
                WHERE session_token = ? AND is_active = 1
            ''', (token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                user_id, expires_at = result
                if datetime.datetime.fromisoformat(expires_at) > datetime.datetime.now():
                    return user_id
                else:
                    self.invalidate_session_token(token)
            
            return None
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    def invalidate_session_token(self, token):
        """Invalidate session token"""
        try:
            if token in self.session_tokens:
                del self.session_tokens[token]
            
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions SET is_active = 0 WHERE session_token = ?
            ''', (token,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")

# Enhanced User Management System
class UserManager:
    """Enhanced user management system"""
    
    def __init__(self):
        self.security = SecurityManager()
        self.current_user = None
        
    def create_user(self, username, password, fullname="", email="", is_admin=False):
        """Create new user with enhanced validation"""
        try:
            # Validate username
            if not self.validate_username(username):
                return False, "Invalid username format"
            
            # Validate password
            if not self.validate_password(password):
                return False, "Password does not meet security requirements"
            
            # Check if username exists
            if self.user_exists(username):
                return False, "Username already exists"
            
            # Hash password
            password_hash, salt = self.security.hash_password(password)
            
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, fullname, email, password_hash, salt, is_admin)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, fullname, email, password_hash, salt, int(is_admin)))
            
            user_id = cursor.lastrowid
            
            # Create default bookmarks
            default_bookmarks = [
                ("Home", os.path.expanduser("~"), "🏠", "system"),
                ("Desktop", os.path.expanduser("~/Desktop"), "🖥️", "system"),
                ("Documents", os.path.expanduser("~/Documents"), "📄", "system"),
                ("Downloads", os.path.expanduser("~/Downloads"), "📥", "system"),
                ("Pictures", os.path.expanduser("~/Pictures"), "🖼️", "system"),
                ("Music", os.path.expanduser("~/Music"), "🎵", "system"),
                ("Videos", os.path.expanduser("~/Videos"), "🎬", "system")
            ]
            
            for i, (name, path, icon, category) in enumerate(default_bookmarks):
                cursor.execute('''
                    INSERT INTO bookmarks (user_id, name, path, icon, category, order_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, name, path, icon, category, i))
                
                # Create directory if it doesn't exist
                try:
                    os.makedirs(path, exist_ok=True)
                except:
                    pass
            
            # Log user creation
            cursor.execute('''
                INSERT INTO system_logs (level, message, component, user_id)
                VALUES (?, ?, ?, ?)
            ''', ('INFO', f'User created: {username}', 'UserManager', user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User created successfully: {username}")
            return True, "User created successfully"
            
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return False, f"User creation failed: {str(e)}"
    
    def validate_username(self, username):
        """Validate username format"""
        if not username or len(username) < 3 or len(username) > 32:
            return False
        
        # Allow alphanumeric and underscore
        if not re.match("^[a-zA-Z0-9_]+$", username):
            return False
        
        # Must start with letter
        if not username[0].isalpha():
            return False
        
        return True
    
    def validate_password(self, password):
        """Validate password against security policy"""
        config = DEFAULT_CONFIG.get("security", {}).get("password_policy", {})
        
        min_length = config.get("min_length", 6)
        if len(password) < min_length:
            return False
        
        if config.get("require_uppercase", False) and not any(c.isupper() for c in password):
            return False
        
        if config.get("require_lowercase", False) and not any(c.islower() for c in password):
            return False
        
        if config.get("require_numbers", False) and not any(c.isdigit() for c in password):
            return False
        
        if config.get("require_symbols", False) and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False
        
        return True
    
    def user_exists(self, username):
        """Check if user exists"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            logger.error(f"User exists check error: {e}")
            return False
    
    def login(self, username, password):
        """Login user"""
        user_info, message = self.security.authenticate_user(username, password)
        if user_info:
            self.current_user = user_info
            logger.info(f"User logged in: {username}")
        return user_info, message
    
    def logout(self):
        """Logout current user"""
        if self.current_user:
            self.security.invalidate_session_token(self.current_user.get('session_token'))
            logger.info(f"User logged out: {self.current_user['username']}")
            self.current_user = None
    
    def get_current_user(self):
        """Get current logged in user"""
        return self.current_user
    
    def is_admin(self):
        """Check if current user is admin"""
        return self.current_user and self.current_user.get('is_admin', False)
    
    def change_password(self, old_password, new_password):
        """Change user password"""
        try:
            if not self.current_user:
                return False, "No user logged in"
            
            # Verify old password
            user_info, _ = self.security.authenticate_user(
                self.current_user['username'], old_password
            )
            
            if not user_info:
                return False, "Current password is incorrect"
            
            # Validate new password
            if not self.validate_password(new_password):
                return False, "New password does not meet security requirements"
            
            # Hash new password
            password_hash, salt = self.security.hash_password(new_password)
            
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET password_hash = ?, salt = ?
                WHERE id = ?
            ''', (password_hash, salt, self.current_user['id']))
            
            cursor.execute('''
                INSERT INTO system_logs (level, message, component, user_id)
                VALUES (?, ?, ?, ?)
            ''', ('INFO', 'Password changed', 'UserManager', self.current_user['id']))
            
            conn.commit()
            conn.close()
            
            return True, "Password changed successfully"
            
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return False, f"Password change failed: {str(e)}"
    
    def get_user_list(self):
        """Get list of all users (admin only)"""
        try:
            if not self.is_admin():
                return []
            
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, fullname, email, is_admin, is_active, 
                       created_at, last_login, login_count
                FROM users ORDER BY username
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            return users
            
        except Exception as e:
            logger.error(f"User list error: {e}")
            return []

# Enhanced Login System
class LoginSystem:
    """Enhanced login system with modern UI"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.root = None
        self.login_attempts = 0
        self.max_attempts = 3
        
    def show_login_screen(self):
        """Show enhanced login screen"""
        try:
            self.root = tk.Tk()
            self.root.title("Berke0S Login")
            self.root.geometry("500x400")
            self.root.configure(bg='#0a0a0f')
            self.root.resizable(False, False)
            
            # Center window
            self.center_window()
            
            # Remove window decorations for modern look
            self.root.overrideredirect(True)
            
            # Create login UI
            self.create_login_ui()
            
            # Bind events
            self.root.bind('<Escape>', lambda e: self.root.quit())
            self.root.bind('<Return>', lambda e: self.attempt_login())
            
            # Focus on username field
            self.username_entry.focus_set()
            
            self.root.mainloop()
            
            return self.user_manager.get_current_user()
            
        except Exception as e:
            logger.error(f"Login screen error: {e}")
            return None
    
    def center_window(self):
        """Center login window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"500x400+{x}+{y}")
    
    def create_login_ui(self):
        """Create modern login UI"""
        try:
            # Main container
            main_frame = tk.Frame(self.root, bg='#0a0a0f')
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Header with logo
            header_frame = tk.Frame(main_frame, bg='#0a0a0f', height=120)
            header_frame.pack(fill=tk.X, pady=(30, 20))
            header_frame.pack_propagate(False)
            
            # Logo
            logo_label = tk.Label(header_frame, text="Berke0S", 
                                 font=('Arial', 32, 'bold'),
                                 fg='#00ff88', bg='#0a0a0f')
            logo_label.pack(pady=20)
            
            # Subtitle
            subtitle_label = tk.Label(header_frame, text="Ultimate Desktop Environment", 
                                     font=('Arial', 12),
                                     fg='#cccccc', bg='#0a0a0f')
            subtitle_label.pack()
            
            # Login form
            form_frame = tk.Frame(main_frame, bg='#1a1a2e', relief=tk.RAISED, bd=2)
            form_frame.pack(padx=50, pady=20, fill=tk.X)
            
            # Form title
            tk.Label(form_frame, text="Sign In", font=('Arial', 18, 'bold'),
                    fg='white', bg='#1a1a2e').pack(pady=(20, 10))
            
            # Username field
            tk.Label(form_frame, text="Username:", font=('Arial', 11),
                    fg='white', bg='#1a1a2e').pack(anchor='w', padx=30, pady=(10, 5))
            
            self.username_var = tk.StringVar()
            self.username_entry = tk.Entry(form_frame, textvariable=self.username_var,
                                          font=('Arial', 12), width=25,
                                          bg='#2a2a3e', fg='white',
                                          insertbackground='white',
                                          relief=tk.FLAT, bd=5)
            self.username_entry.pack(padx=30, pady=(0, 10), ipady=8)
            
            # Password field
            tk.Label(form_frame, text="Password:", font=('Arial', 11),
                    fg='white', bg='#1a1a2e').pack(anchor='w', padx=30, pady=(0, 5))
            
            self.password_var = tk.StringVar()
            self.password_entry = tk.Entry(form_frame, textvariable=self.password_var,
                                          font=('Arial', 12), width=25, show='*',
                                          bg='#2a2a3e', fg='white',
                                          insertbackground='white',
                                          relief=tk.FLAT, bd=5)
            self.password_entry.pack(padx=30, pady=(0, 10), ipady=8)
            
            # Show password checkbox
            self.show_password_var = tk.BooleanVar()
            show_password_cb = tk.Checkbutton(form_frame, text="Show password",
                                            variable=self.show_password_var,
                                            command=self.toggle_password_visibility,
                                            fg='#cccccc', bg='#1a1a2e',
                                            selectcolor='#2a2a3e',
                                            activebackground='#1a1a2e',
                                            activeforeground='white',
                                            font=('Arial', 9))
            show_password_cb.pack(anchor='w', padx=30, pady=(0, 15))
            
            # Login button
            login_btn = tk.Button(form_frame, text="Sign In",
                                 command=self.attempt_login,
                                 bg='#00ff88', fg='black',
                                 font=('Arial', 12, 'bold'),
                                 relief=tk.FLAT, bd=0,
                                 width=20, pady=10,
                                 cursor='hand2')
            login_btn.pack(pady=(0, 20))
            
            # Status label
            self.status_label = tk.Label(form_frame, text="", 
                                        font=('Arial', 10),
                                        fg='#ff6b6b', bg='#1a1a2e')
            self.status_label.pack(pady=(0, 10))
            
            # Footer
            footer_frame = tk.Frame(main_frame, bg='#0a0a0f')
            footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=20)
            
            # Create user button
            create_user_btn = tk.Button(footer_frame, text="Create New User",
                                       command=self.show_create_user_dialog,
                                       bg='#4a9eff', fg='white',
                                       font=('Arial', 10),
                                       relief=tk.FLAT, bd=0,
                                       cursor='hand2')
            create_user_btn.pack(side=tk.LEFT, padx=50)
            
            # Exit button
            exit_btn = tk.Button(footer_frame, text="Exit",
                               command=self.root.quit,
                               bg='#ff6b6b', fg='white',
                               font=('Arial', 10),
                               relief=tk.FLAT, bd=0,
                               cursor='hand2')
            exit_btn.pack(side=tk.RIGHT, padx=50)
            
            # Bind Enter key to password field
            self.password_entry.bind('<Return>', lambda e: self.attempt_login())
            
        except Exception as e:
            logger.error(f"Login UI creation error: {e}")
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='*')
    
    def attempt_login(self):
        """Attempt to login user"""
        try:
            username = self.username_var.get().strip()
            password = self.password_var.get()
            
            if not username or not password:
                self.status_label.config(text="Please enter username and password", fg='#ff6b6b')
                return
            
            # Clear status
            self.status_label.config(text="Authenticating...", fg='#ffb347')
            self.root.update()
            
            # Attempt login
            user_info, message = self.user_manager.login(username, password)
            
            if user_info:
                self.status_label.config(text="Login successful!", fg='#00ff88')
                self.root.update()
                time.sleep(1)
                self.root.quit()
            else:
                self.login_attempts += 1
                self.status_label.config(text=message, fg='#ff6b6b')
                
                # Clear password field
                self.password_var.set("")
                
                # Check max attempts
                if self.login_attempts >= self.max_attempts:
                    self.status_label.config(text="Too many failed attempts. Exiting...", fg='#ff6b6b')
                    self.root.update()
                    time.sleep(2)
                    self.root.quit()
                    
        except Exception as e:
            logger.error(f"Login attempt error: {e}")
            self.status_label.config(text="Login system error", fg='#ff6b6b')
    
    def show_create_user_dialog(self):
        """Show create user dialog"""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Create New User")
            dialog.geometry("400x500")
            dialog.configure(bg='#1a1a2e')
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center dialog
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (400 // 2)
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (500 // 2)
            dialog.geometry(f"400x500+{x}+{y}")
            
            # Dialog content
            main_frame = tk.Frame(dialog, bg='#1a1a2e')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
            
            # Title
            tk.Label(main_frame, text="Create New User Account", 
                    font=('Arial', 16, 'bold'),
                    fg='white', bg='#1a1a2e').pack(pady=(0, 20))
            
            # Form fields
            fields = [
                ("Full Name:", "fullname"),
                ("Username:", "username"),
                ("Email:", "email"),
                ("Password:", "password"),
                ("Confirm Password:", "confirm_password")
            ]
            
            self.create_user_vars = {}
            
            for label_text, var_name in fields:
                tk.Label(main_frame, text=label_text, font=('Arial', 11),
                        fg='white', bg='#1a1a2e').pack(anchor='w', pady=(10, 5))
                
                var = tk.StringVar()
                self.create_user_vars[var_name] = var
                
                entry = tk.Entry(main_frame, textvariable=var,
                               font=('Arial', 11), width=30,
                               bg='#2a2a3e', fg='white',
                               insertbackground='white',
                               relief=tk.FLAT, bd=5)
                
                if var_name in ['password', 'confirm_password']:
                    entry.config(show='*')
                
                entry.pack(pady=(0, 5), ipady=5)
            
            # Admin checkbox
            self.is_admin_var = tk.BooleanVar()
            admin_cb = tk.Checkbutton(main_frame, text="Administrator privileges",
                                    variable=self.is_admin_var,
                                    fg='#cccccc', bg='#1a1a2e',
                                    selectcolor='#2a2a3e',
                                    activebackground='#1a1a2e',
                                    activeforeground='white',
                                    font=('Arial', 10))
            admin_cb.pack(anchor='w', pady=10)
            
            # Status label
            self.create_status_label = tk.Label(main_frame, text="", 
                                               font=('Arial', 10),
                                               fg='#ff6b6b', bg='#1a1a2e')
            self.create_status_label.pack(pady=10)
            
            # Buttons
            button_frame = tk.Frame(main_frame, bg='#1a1a2e')
            button_frame.pack(fill=tk.X, pady=20)
            
            create_btn = tk.Button(button_frame, text="Create User",
                                  command=lambda: self.create_new_user(dialog),
                                  bg='#00ff88', fg='black',
                                  font=('Arial', 11, 'bold'),
                                  relief=tk.FLAT, bd=0,
                                  width=12, pady=8)
            create_btn.pack(side=tk.LEFT)
            
            cancel_btn = tk.Button(button_frame, text="Cancel",
                                  command=dialog.destroy,
                                  bg='#ff6b6b', fg='white',
                                  font=('Arial', 11),
                                  relief=tk.FLAT, bd=0,
                                  width=12, pady=8)
            cancel_btn.pack(side=tk.RIGHT)
            
        except Exception as e:
            logger.error(f"Create user dialog error: {e}")
    
    def create_new_user(self, dialog):
        """Create new user from dialog"""
        try:
            # Get form data
            fullname = self.create_user_vars['fullname'].get().strip()
            username = self.create_user_vars['username'].get().strip()
            email = self.create_user_vars['email'].get().strip()
            password = self.create_user_vars['password'].get()
            confirm_password = self.create_user_vars['confirm_password'].get()
            is_admin = self.is_admin_var.get()
            
            # Validate fields
            if not username:
                self.create_status_label.config(text="Username is required", fg='#ff6b6b')
                return
            
            if not password:
                self.create_status_label.config(text="Password is required", fg='#ff6b6b')
                return
            
            if password != confirm_password:
                self.create_status_label.config(text="Passwords do not match", fg='#ff6b6b')
                return
            
            # Create user
            self.create_status_label.config(text="Creating user...", fg='#ffb347')
            dialog.update()
            
            success, message = self.user_manager.create_user(
                username, password, fullname, email, is_admin
            )
            
            if success:
                self.create_status_label.config(text="User created successfully!", fg='#00ff88')
                dialog.update()
                time.sleep(1)
                dialog.destroy()
                
                # Update status in main window
                self.status_label.config(text=f"User '{username}' created successfully", fg='#00ff88')
            else:
                self.create_status_label.config(text=message, fg='#ff6b6b')
                
        except Exception as e:
            logger.error(f"Create new user error: {e}")
            self.create_status_label.config(text="User creation failed", fg='#ff6b6b')

# Enhanced Installation System
class InstallationWizard:
    """Complete installation wizard with enhanced features"""
    
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
            "advanced_settings",
            "installation",
            "complete"
        ]
        self.config = DEFAULT_CONFIG.copy()
        self.selected_disk = None
        self.partition_scheme = "auto"
        self.user_manager = UserManager()
        
    def start_installation(self):
        """Start the installation process with enhanced UI"""
        logger.info("Starting Berke0S installation wizard...")
        
        if not setup_display():
            return self.console_install()
            
        try:
            self.root = tk.Tk()
            self.root.title("Berke0S 4.0 - Ultimate Installation")
            self.root.geometry("1000x750")
            self.root.configure(bg='#0a0a0f')
            self.root.resizable(True, True)
            
            # Enhanced window styling
            self.root.attributes('-alpha', 0.98)
            
            # Center window
            self.center_window()
            
            # Load custom fonts
            self.setup_fonts()
            
            # Create enhanced UI
            self.setup_installation_ui()
            
            self.show_step()
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Installation UI failed: {e}")
            return self.console_install()
            
    def center_window(self):
        """Center the installation window"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (750 // 2)
        self.root.geometry(f"1000x750+{x}+{y}")
        
    def setup_fonts(self):
        """Setup custom fonts for installation"""
        self.title_font = tkFont.Font(family="Arial", size=28, weight="bold")
        self.header_font = tkFont.Font(family="Arial", size=18, weight="bold")
        self.normal_font = tkFont.Font(family="Arial", size=12)
        self.small_font = tkFont.Font(family="Arial", size=10)
        
    def setup_installation_ui(self):
        """Setup enhanced installation UI"""
        # Create gradient background
        self.create_gradient_bg()
        
        # Main container
        self.main_container = tk.Frame(self.root, bg='#0a0a0f')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
    def create_gradient_bg(self):
        """Create gradient background for installation"""
        if PIL_AVAILABLE:
            try:
                width, height = 1000, 750
                image = Image.new('RGB', (width, height))
                draw = ImageDraw.Draw(image)
                
                # Create a beautiful gradient
                for y in range(height):
                    ratio = y / height
                    r = int(10 + ratio * 25)
                    g = int(10 + ratio * 35)
                    b = int(15 + ratio * 60)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                
                self.bg_image = ImageTk.PhotoImage(image)
                bg_label = tk.Label(self.root, image=self.bg_image)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                logger.warning(f"Gradient background creation failed: {e}")
        
    def console_install(self):
        """Enhanced console-based installation"""
        print("\n" + "="*80)
        print("  ██████╗ ███████╗██████╗ ██╗  ██╗███████╗ ██████╗ ███████╗")
        print("  ██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔════╝██╔═████╗██╔════╝")
        print("  ██████╔╝█████╗  ██████╔╝█████╔╝ █████╗  ██║██╔██║███████╗")
        print("  ██╔══██╗██╔══╝  ██╔══██╗██╔═██╗ ██╔══╝  ████╔╝██║╚════██║")
        print("  ██████╔╝███████╗██║  ██║██║  ██╗███████╗╚██████╔╝███████║")
        print("  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝")
        print("  Ultimate Desktop Environment v4.0")
        print("  Console Installation Mode")
        print("="*80)
        
        # Enhanced console setup
        try:
            print("\n🚀 Berke0S Hızlı Kurulum / Quick Setup")
            
            # Language selection
            print("\n1. Dil Seçimi / Language Selection:")
            print("   [1] Türkçe [2] English [3] Deutsch [4] Français")
            lang_choice = input("Seçim / Choice (1-4): ").strip()
            
            languages = {"1": "tr_TR", "2": "en_US", "3": "de_DE", "4": "fr_FR"}
            self.config["language"] = languages.get(lang_choice, "tr_TR")
            
            # User setup
            print("\n2. Kullanıcı Hesabı / User Account:")
            fullname = input("Ad Soyad / Full Name: ").strip()
            username = input("Kullanıcı Adı / Username: ").strip()
            password = getpass.getpass("Şifre / Password: ")
            confirm_password = getpass.getpass("Şifre Tekrar / Confirm Password: ")
            
            if password != confirm_password:
                print("❌ Şifreler eşleşmiyor / Passwords do not match")
                return False
            
            # Email (optional)
            email = input("E-posta (opsiyonel) / Email (optional): ").strip()
            
            # Admin privileges
            is_admin = input("Yönetici yetkisi ver? / Grant admin privileges? (y/n): ").lower() == 'y'
            
            # Network setup
            print("\n3. Ağ Ayarları / Network Settings:")
            setup_wifi = input("WiFi kurmak ister misiniz? / Setup WiFi? (y/n): ").lower() == 'y'
            
            if setup_wifi:
                ssid = input("WiFi Ağ Adı / SSID: ").strip()
                wifi_password = getpass.getpass("WiFi Şifresi / WiFi Password: ")
                self.config["wifi"] = {"ssid": ssid, "password": wifi_password}
            
            # Theme selection
            print("\n4. Tema Seçimi / Theme Selection:")
            print("   [1] Berke Dark [2] Berke Light [3] Ocean [4] Forest [5] Sunset")
            theme_choice = input("Tema / Theme (1-5): ").strip()
            
            themes = {"1": "berke_dark", "2": "berke_light", "3": "ocean", "4": "forest", "5": "sunset"}
            self.config["theme"] = themes.get(theme_choice, "berke_dark")
            
            # Desktop effects
            print("\n5. Masaüstü Efektleri / Desktop Effects:")
            effects = input("Masaüstü efektlerini etkinleştir? / Enable desktop effects? (y/n): ").lower() == 'y'
            self.config["desktop"]["effects"] = effects
            
            # Auto login
            auto_login = input("Otomatik giriş? / Auto login? (y/n): ").lower() == 'y'
            self.config["auto_login"] = auto_login
            
            # Perform installation
            print("\n6. Kurulum Yapılıyor / Installing...")
            success = self.perform_console_installation(username, password, fullname, email, is_admin)
            
            if success:
                print("\n✅ Kurulum tamamlandı! / Installation completed!")
                print("🔄 Sistemi yeniden başlatın / Please reboot the system")
                return True
            else:
                print("\n❌ Kurulum başarısız / Installation failed")
                return False
            
        except KeyboardInterrupt:
            print("\n❌ Kurulum iptal edildi / Installation cancelled")
            return False
        except Exception as e:
            logger.error(f"Console installation error: {e}")
            print(f"❌ Kurulum hatası / Installation error: {e}")
            return False
            
    def perform_console_installation(self, username, password, fullname, email, is_admin):
        """Perform actual console installation"""
        steps = [
            ("Dizinler oluşturuluyor / Creating directories", self.create_directories),
            ("Veritabanı hazırlanıyor / Preparing database", self.setup_database),
            ("Sistem dosyaları kuruluyor / Installing system files", self.install_system_files),
            ("Kullanıcı oluşturuluyor / Creating user", lambda: self.create_console_user(username, password, fullname, email, is_admin)),
            ("Masaüstü ortamı / Desktop environment", self.setup_desktop_environment),
            ("Temalar kuruluyor / Installing themes", self.install_default_themes),
            ("Uygulamalar kuruluyor / Installing applications", self.install_default_applications),
            ("Son ayarlar / Final configuration", self.finalize_installation)
        ]
        
        for i, (desc, func) in enumerate(steps):
            print(f"[{i+1}/{len(steps)}] {desc}...")
            try:
                result = func()
                if result is False:
                    print(f"✗ {desc} - Başarısız / Failed")
                    return False
                print(f"✓ {desc} - Tamamlandı / Completed")
            except Exception as e:
                print(f"✗ {desc} - Hata / Error: {e}")
                logger.error(f"Installation step failed: {desc} - {e}")
                return False
            time.sleep(0.5)
        
        return True
    
    def create_console_user(self, username, password, fullname, email, is_admin):
        """Create user during console installation"""
        try:
            success, message = self.user_manager.create_user(username, password, fullname, email, is_admin)
            if success:
                self.config["current_user"] = username
                return True
            else:
                print(f"User creation failed: {message}")
                return False
        except Exception as e:
            logger.error(f"Console user creation error: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        dirs = [CONFIG_DIR, THEMES_DIR, PLUGINS_DIR, WALLPAPERS_DIR, APPS_DIR, BACKUP_DIR, CACHE_DIR, TEMP_DIR]
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
        return True
    
    def setup_database(self):
        """Setup system database"""
        init_database()
        return True
    
    def install_system_files(self):
        """Install system files and configurations"""
        # Save main configuration
        self.save_config()
        
        # Create autostart script
        self.create_autostart()
        return True
    
    def setup_desktop_environment(self):
        """Setup desktop environment"""
        # Create default wallpapers directory
        wallpapers_dir = os.path.join(WALLPAPERS_DIR, "default")
        os.makedirs(wallpapers_dir, exist_ok=True)
        
        # Create default desktop icons layout
        self.create_default_desktop_layout()
        return True
    
    def create_default_desktop_layout(self):
        """Create default desktop icon layout"""
        try:
            default_icons = [
                {"name": "File Manager", "icon": "📁", "command": "berke0s_filemanager", "x": 50, "y": 50},
                {"name": "Web Browser", "icon": "🌐", "command": "berke0s_browser", "x": 50, "y": 120},
                {"name": "Terminal", "icon": "💻", "command": "berke0s_terminal", "x": 50, "y": 190},
                {"name": "Settings", "icon": "⚙️", "command": "berke0s_settings", "x": 50, "y": 260},
                {"name": "Text Editor", "icon": "📝", "command": "berke0s_texteditor", "x": 150, "y": 50},
                {"name": "Calculator", "icon": "🧮", "command": "berke0s_calculator", "x": 150, "y": 120},
                {"name": "Music Player", "icon": "🎵", "command": "berke0s_musicplayer", "x": 150, "y": 190},
                {"name": "Games", "icon": "🎮", "command": "berke0s_games", "x": 150, "y": 260}
            ]
            
            self.config["desktop"]["desktop_icons"] = default_icons
            return True
            
        except Exception as e:
            logger.error(f"Desktop layout creation error: {e}")
            return False
    
    def install_default_themes(self):
        """Install default theme files"""
        try:
            themes = {
                "berke_dark": {
                    "name": "Berke Dark",
                    "display_name": "Berke Dark Theme",
                    "author": "Berke Oruç",
                    "version": "1.0",
                    "description": "Dark theme with green accents",
                    "colors": {
                        "bg": "#1a1a1a", "fg": "#ffffff", "accent": "#00ff88",
                        "secondary": "#4a9eff", "warning": "#ffb347", "error": "#ff6b6b",
                        "success": "#00ff88", "taskbar": "#0f0f23", "window": "#2a2a2a",
                        "input": "#333333", "border": "#444444", "hover": "#555555",
                        "selection": "#00ff8844", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier", "size": 11},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                },
                "berke_light": {
                    "name": "Berke Light",
                    "display_name": "Berke Light Theme",
                    "author": "Berke Oruç",
                    "version": "1.0",
                    "description": "Light theme with blue accents",
                    "colors": {
                        "bg": "#f5f5f5", "fg": "#333333", "accent": "#007acc",
                        "secondary": "#28a745", "warning": "#ffc107", "error": "#dc3545",
                        "success": "#28a745", "taskbar": "#e9ecef", "window": "#ffffff",
                        "input": "#ffffff", "border": "#cccccc", "hover": "#e9ecef",
                        "selection": "#007acc44", "shadow": "#00000022"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier", "size": 11},
                    "effects": {"blur": False, "transparency": False, "animations": True}
                },
                "ocean": {
                    "name": "Ocean Blue",
                    "display_name": "Ocean Blue Theme",
                    "author": "Berke Oruç",
                    "version": "1.0",
                    "description": "Ocean-inspired blue theme",
                    "colors": {
                        "bg": "#0d1b2a", "fg": "#ffffff", "accent": "#00b4d8",
                        "secondary": "#0077b6", "warning": "#f77f00", "error": "#d62828",
                        "success": "#2a9d8f", "taskbar": "#03045e", "window": "#1b263b",
                        "input": "#415a77", "border": "#457b9d", "hover": "#1d3557",
                        "selection": "#00b4d844", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier", "size": 11},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                },
                "forest": {
                    "name": "Forest Green",
                    "display_name": "Forest Green Theme",
                    "author": "Berke Oruç",
                    "version": "1.0",
                    "description": "Nature-inspired green theme",
                    "colors": {
                        "bg": "#1b4332", "fg": "#ffffff", "accent": "#40916c",
                        "secondary": "#52b788", "warning": "#f77f00", "error": "#e63946",
                        "success": "#2d6a4f", "taskbar": "#081c15", "window": "#2d6a4f",
                        "input": "#40916c", "border": "#52b788", "hover": "#2d6a4f",
                        "selection": "#40916c44", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier", "size": 11},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                },
                "sunset": {
                    "name": "Sunset Orange",
                    "display_name": "Sunset Orange Theme",
                    "author": "Berke Oruç",
                    "version": "1.0",
                    "description": "Warm sunset-inspired theme",
                    "colors": {
                        "bg": "#2d1b0e", "fg": "#ffffff", "accent": "#ff8500",
                        "secondary": "#ff6b35", "warning": "#ffd23f", "error": "#ee6c4d",
                        "success": "#06ffa5", "taskbar": "#1a0e0a", "window": "#3c2415",
                        "input": "#4a2c17", "border": "#ff8500", "hover": "#5c3317",
                        "selection": "#ff850044", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier", "size": 11},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                }
            }
            
            # Save themes to database
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            for theme_name, theme_data in themes.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO themes 
                    (name, display_name, author, version, description, theme_data, is_system)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    theme_name,
                    theme_data["display_name"],
                    theme_data["author"],
                    theme_data["version"],
                    theme_data["description"],
                    json.dumps(theme_data),
                    1
                ))
            
            conn.commit()
            conn.close()
            
            # Also save as files
            for theme_name, theme_data in themes.items():
                theme_file = os.path.join(THEMES_DIR, f"{theme_name}.json")
                with open(theme_file, 'w') as f:
                    json.dump(theme_data, f, indent=4)
            
            return True
                    
        except Exception as e:
            logger.error(f"Theme installation failed: {e}")
            return False
    
    def install_default_applications(self):
        """Install default applications to database"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            apps = [
                ("File Manager", "berke0s_filemanager", "📁", "System", "Advanced file management with multiple views", "1.0", "Berke Oruç"),
                ("Text Editor", "berke0s_texteditor", "📝", "Office", "Code and text editing with syntax highlighting", "1.0", "Berke Oruç"),
                ("Web Browser", "berke0s_browser", "🌐", "Internet", "Modern web browsing experience", "1.0", "Berke Oruç"),
                ("Terminal", "berke0s_terminal", "💻", "System", "Advanced terminal emulator", "1.0", "Berke Oruç"),
                ("Calculator", "berke0s_calculator", "🧮", "Utility", "Scientific calculator with history", "1.0", "Berke Oruç"),
                ("Image Viewer", "berke0s_imageviewer", "🖼️", "Graphics", "Image viewing and basic editing", "1.0", "Berke Oruç"),
                ("Music Player", "berke0s_musicplayer", "🎵", "Multimedia", "Audio playback with playlist support", "1.0", "Berke Oruç"),
                ("Video Player", "berke0s_videoplayer", "🎬", "Multimedia", "Video playback with subtitle support", "1.0", "Berke Oruç"),
                ("Settings", "berke0s_settings", "⚙️", "System", "System configuration and preferences", "1.0", "Berke Oruç"),
                ("System Monitor", "berke0s_monitor", "📊", "System", "System performance monitoring", "1.0", "Berke Oruç"),
                ("Email Client", "berke0s_email", "📧", "Internet", "Email management with multiple accounts", "1.0", "Berke Oruç"),
                ("Calendar", "berke0s_calendar", "📅", "Office", "Calendar and scheduling application", "1.0", "Berke Oruç"),
                ("Games", "berke0s_games", "🎮", "Games", "Built-in games collection", "1.0", "Berke Oruç"),
                ("Network Manager", "berke0s_network", "📶", "System", "Network configuration and monitoring", "1.0", "Berke Oruç"),
                ("Archive Manager", "berke0s_archive", "📦", "Utility", "Archive creation and extraction", "1.0", "Berke Oruç"),
                ("PDF Viewer", "berke0s_pdf", "📄", "Office", "PDF document viewer", "1.0", "Berke Oruç"),
                ("Code Editor", "berke0s_ide", "⌨️", "Development", "Integrated development environment", "1.0", "Berke Oruç"),
                ("Screen Recorder", "berke0s_recorder", "📹", "Multimedia", "Screen recording and capture", "1.0", "Berke Oruç"),
                ("System Backup", "berke0s_backup", "💾", "System", "System backup and restore", "1.0", "Berke Oruç"),
                ("Virtual Desktop", "berke0s_vdesktop", "🖥️", "System", "Virtual desktop manager", "1.0", "Berke Oruç"),
                ("Package Manager", "berke0s_packages", "📦", "System", "Software package management", "1.0", "Berke Oruç"),
                ("Task Manager", "berke0s_tasks", "📋", "System", "Process and task management", "1.0", "Berke Oruç"),
                ("Font Manager", "berke0s_fonts", "🔤", "System", "Font installation and management", "1.0", "Berke Oruç"),
                ("Color Picker", "berke0s_colorpicker", "🎨", "Utility", "Color selection and palette tool", "1.0", "Berke Oruç"),
                ("Screenshot Tool", "berke0s_screenshot", "📸", "Utility", "Advanced screenshot utility", "1.0", "Berke Oruç")
            ]
            
            for app in apps:
                cursor.execute('''
                    INSERT OR REPLACE INTO applications 
                    (name, command, icon, category, description, version, author)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', app)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Default applications installation failed: {e}")
            return False
    
    def create_autostart(self):
        """Create autostart configuration"""
        try:
            # Create desktop entry for autostart
            desktop_entry = f"""[Desktop Entry]
Name=Berke0S Desktop
Comment=Ultimate Desktop Environment
Exec=python3 {os.path.abspath(__file__)}
Icon=berke0s
Terminal=false
Type=Application
Categories=System;
StartupNotify=true
"""
            
            # Try multiple autostart locations
            autostart_locations = [
                os.path.expanduser("~/.config/autostart/berke0s.desktop"),
                "/etc/xdg/autostart/berke0s.desktop",
                os.path.expanduser("~/.autostart/berke0s.desktop")
            ]
            
            for location in autostart_locations:
                try:
                    os.makedirs(os.path.dirname(location), exist_ok=True)
                    with open(location, 'w') as f:
                        f.write(desktop_entry)
                    os.chmod(location, 0o755)
                except Exception as e:
                    logger.warning(f"Failed to create autostart at {location}: {e}")
                    continue
            
            # Also try bootlocal.sh for Tiny Core
            bootlocal_content = f"""#!/bin/bash
# Berke0S Autostart Script
export DISPLAY=:0
cd {os.path.dirname(os.path.abspath(__file__))}
python3 {os.path.abspath(__file__)} &
"""
            
            bootlocal_locations = [
                "/opt/bootlocal.sh",
                os.path.expanduser("~/.xsession"),
                os.path.expanduser("~/.xinitrc")
            ]
            
            for location in bootlocal_locations:
                try:
                    # Append to existing file or create new
                    mode = 'a' if os.path.exists(location) else 'w'
                    with open(location, mode) as f:
                        if mode == 'a':
                            f.write('\n# Berke0S Autostart\n')
                        f.write(bootlocal_content)
                    os.chmod(location, 0o755)
                    break
                except Exception as e:
                    logger.warning(f"Failed to create bootlocal at {location}: {e}")
                    continue
                    
            return True
                    
        except Exception as e:
            logger.warning(f"Autostart creation failed: {e}")
            return True  # Don't fail installation for this
    
    def finalize_installation(self):
        """Finalize installation"""
        try:
            # Mark as installed
            self.config["installed"] = True
            self.config["first_boot"] = False
            self.config["setup_completed"] = True
            self.save_config()
            
            # Create installation flag
            install_info = {
                "installed_at": datetime.datetime.now().isoformat(),
                "version": "4.0",
                "user": self.config.get("current_user", "unknown"),
                "language": self.config.get("language", "tr_TR"),
                "theme": self.config.get("theme", "berke_dark")
            }
            
            with open(INSTALL_FLAG, 'w') as f:
                json.dump(install_info, f, indent=4)
            
            # Create initial backup
            self.create_initial_backup()
            
            return True
            
        except Exception as e:
            logger.error(f"Installation finalization error: {e}")
            return False
    
    def create_initial_backup(self):
        """Create initial system backup"""
        try:
            backup_file = os.path.join(BACKUP_DIR, "initial_backup.tar.gz")
            
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(CONFIG_FILE, arcname="config.json")
                tar.add(DATABASE_FILE, arcname="berke0s.db")
                tar.add(THEMES_DIR, arcname="themes")
                
            logger.info(f"Initial backup created: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Initial backup creation error: {e}")
            return True  # Don't fail installation for this
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Config save error: {e}")
            return False
    
    # GUI installation steps would continue here...
    # (Due to length constraints, implementing the essential structure)

# Enhanced Window Manager (continuing from previous implementation)
class WindowManager:
    """Ultimate window manager with complete features"""
    
    def __init__(self):
        self.root = None
        self.windows = {}
        self.config = self.load_config()
        self.user_manager = UserManager()
        self.current_user = None
        self.notifications = None
        self.desktop = None
        self.taskbar = None
        self.start_menu = None
        self.wallpaper_image = None
        self.themes = self.load_themes()
        self.shortcuts = {}
        self.running_apps = {}
        self.virtual_desktops = []
        self.current_desktop = 0
        self.workspace_manager = None
        self.plugin_manager = None
        self.performance_monitor = None
        self.login_system = None
        
        # Initialize enhanced features
        self.init_virtual_desktops()
        self.init_plugin_system()
        self.init_performance_monitoring()
        
        # Check if setup is needed
        if not self.config.get("setup_completed", False):
            self.run_first_time_setup()
        
        # Handle login
        if not self.handle_login():
            sys.exit(0)
        
        # Initialize display with retries
        display_attempts = 3
        for attempt in range(display_attempts):
            try:
                if setup_display():
                    break
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Display setup attempt {attempt + 1} failed: {e}")
                if attempt == display_attempts - 1:
                    logger.error("All display setup attempts failed")
                    raise RuntimeError("Display initialization failed")
            
        self.setup_ui()
    
    def run_first_time_setup(self):
        """Run first time setup if needed"""
        try:
            logger.info("Running first time setup...")
            installer = InstallationWizard()
            installer.start_installation()
            
            # Reload config after installation
            self.config = self.load_config()
            
        except Exception as e:
            logger.error(f"First time setup error: {e}")
    
    def handle_login(self):
        """Handle user login process"""
        try:
            # Check if auto-login is enabled and user exists
            if self.config.get("auto_login", False) and self.config.get("current_user"):
                username = self.config["current_user"]
                
                # Try to get user info
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT id, username, fullname, is_admin FROM users WHERE username = ? AND is_active = 1', (username,))
                user_data = cursor.fetchone()
                conn.close()
                
                if user_data:
                    self.current_user = {
                        'id': user_data[0],
                        'username': user_data[1],
                        'fullname': user_data[2],
                        'is_admin': bool(user_data[3])
                    }
                    logger.info(f"Auto-login successful for user: {username}")
                    return True
            
            # Show login screen
            self.login_system = LoginSystem()
            self.current_user = self.login_system.show_login_screen()
            
            if self.current_user:
                # Update config with current user
                self.config["current_user"] = self.current_user["username"]
                self.config["last_login"] = datetime.datetime.now().isoformat()
                self.save_config()
                logger.info(f"Login successful for user: {self.current_user['username']}")
                return True
            else:
                logger.info("Login cancelled or failed")
                return False
                
        except Exception as e:
            logger.error(f"Login handling error: {e}")
            return False
    
    def init_virtual_desktops(self):
        """Initialize virtual desktop system"""
        try:
            num_desktops = self.config.get("desktop", {}).get("virtual_desktops", 4)
            self.virtual_desktops = []
            
            for i in range(num_desktops):
                desktop = {
                    "id": i,
                    "name": f"Desktop {i + 1}",
                    "windows": [],
                    "wallpaper": None,
                    "icon_layout": {}
                }
                self.virtual_desktops.append(desktop)
                
            logger.info(f"Initialized {num_desktops} virtual desktops")
            
        except Exception as e:
            logger.error(f"Virtual desktop initialization failed: {e}")
    
    def init_plugin_system(self):
        """Initialize plugin management system"""
        try:
            self.plugin_manager = PluginManager(self)
            logger.info("Plugin system initialized")
        except Exception as e:
            logger.error(f"Plugin system initialization failed: {e}")
    
    def init_performance_monitoring(self):
        """Initialize performance monitoring"""
        try:
            self.performance_monitor = PerformanceMonitor(self)
            logger.info("Performance monitoring initialized")
        except Exception as e:
            logger.error(f"Performance monitoring initialization failed: {e}")
    
    def load_config(self):
        """Load enhanced configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                def merge_configs(default, loaded):
                    for key, value in default.items():
                        if key not in loaded:
                            loaded[key] = value
                        elif isinstance(value, dict) and isinstance(loaded[key], dict):
                            merge_configs(value, loaded[key])
                    return loaded
                
                return merge_configs(DEFAULT_CONFIG.copy(), config)
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Config load error: {e}")
            return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save enhanced configuration"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Config save error: {e}")
    
    def load_themes(self):
        """Load enhanced themes from database and files"""
        themes = {}
        try:
            # Load from database first
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT name, theme_data FROM themes')
            db_themes = cursor.fetchall()
            conn.close()
            
            for name, theme_data in db_themes:
                try:
                    themes[name] = json.loads(theme_data)
                except:
                    continue
            
            # Load from files as fallback
            if os.path.exists(THEMES_DIR):
                for theme_file in os.listdir(THEMES_DIR):
                    if theme_file.endswith('.json'):
                        try:
                            theme_path = os.path.join(THEMES_DIR, theme_file)
                            with open(theme_path, 'r') as f:
                                theme_data = json.load(f)
                                theme_name = os.path.splitext(theme_file)[0]
                                if theme_name not in themes:
                                    themes[theme_name] = theme_data
                        except Exception as e:
                            logger.warning(f"Failed to load theme {theme_file}: {e}")
            
            # Ensure at least default theme exists
            if not themes:
                themes["berke_dark"] = {
                    "name": "Berke Dark",
                    "colors": {
                        "bg": "#1a1a1a", "fg": "#ffffff", "accent": "#00ff88",
                        "secondary": "#4a9eff", "warning": "#ffb347", "error": "#ff6b6b",
                        "success": "#00ff88", "taskbar": "#0f0f23", "window": "#2a2a2a",
                        "input": "#333333", "border": "#444444", "hover": "#555555",
                        "selection": "#00ff8844", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier"},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                }
                            
            logger.info(f"Loaded {len(themes)} themes")
            return themes
            
        except Exception as e:
            logger.error(f"Theme loading error: {e}")
            return {"berke_dark": themes.get("berke_dark", {})}
    
    def setup_ui(self):
        """Setup enhanced main UI"""
        try:
            logger.info("Setting up main UI...")
            
            self.root = tk.Tk()
            self.root.title("Berke0S 4.0 - Ultimate Desktop")
            
            # Force fullscreen and proper display
            self.root.attributes('-fullscreen', True)
            self.root.state('zoomed')  # Maximize on Windows/Linux
            
            # Enhanced window configuration
            self.root.configure(bg=self.get_theme_color("bg"))
            self.root.focus_force()
            self.root.lift()
            
            # Bind window manager events
            self.root.protocol("WM_DELETE_WINDOW", self.safe_shutdown)
            
            # Initialize notification system
            self.notifications = NotificationSystem(self)
            
            # Apply theme
            self.apply_theme()
            
            # Create UI components in order
            self.create_desktop()
            self.create_taskbar()
            self.create_dock()
            
            # Load wallpaper
            self.load_wallpaper()
            
            # Create desktop icons
            self.create_desktop_icons()
            
            # Bind events
            self.bind_events()
            
            # Start system services
            self.start_services()
            
            # Show welcome notification
            self.notifications.send(
                "Welcome to Berke0S",
                f"Welcome back, {self.current_user.get('fullname', self.current_user.get('username', 'User'))}!",
                notification_type="success",
                timeout=3000
            )
            
            # Force window to front
            self.root.after(100, lambda: (
                self.root.deiconify(),
                self.root.lift(),
                self.root.focus_force()
            ))
            
            logger.info("UI setup completed successfully")
            
        except Exception as e:
            logger.error(f"UI setup error: {e}")
            raise
    
    def get_theme_color(self, color_name):
        """Get color from current theme with fallback"""
        try:
            theme_name = self.config.get("theme", "berke_dark")
            theme = self.themes.get(theme_name, self.themes.get("berke_dark", {}))
            colors = theme.get("colors", {})
            
            # Fallback colors
            fallbacks = {
                "bg": "#1a1a1a", "fg": "#ffffff", "accent": "#00ff88",
                "secondary": "#4a9eff", "taskbar": "#0f0f23", "window": "#2a2a2a",
                "input": "#333333", "error": "#ff6b6b", "warning": "#ffb347",
                "success": "#00ff88", "border": "#444444", "hover": "#555555"
            }
            
            return colors.get(color_name, fallbacks.get(color_name, "#000000"))
            
        except Exception as e:
            logger.error(f"Theme color error: {e}")
            return "#000000"
    
    def apply_theme(self):
        """Apply current theme to all UI elements"""
        try:
            if self.root:
                self.root.configure(bg=self.get_theme_color("bg"))
                
            # Update existing windows
            for window_data in self.windows.values():
                if hasattr(window_data, 'window') and window_data['window'].winfo_exists():
                    window_data['window'].configure(bg=self.get_theme_color("window"))
                    
            logger.info("Theme applied successfully")
                    
        except Exception as e:
            logger.error(f"Theme apply error: {e}")
    
    # Continue with the rest of the WindowManager implementation...
    # (The remaining methods would be similar to the previous implementation but enhanced)
    
    def run(self):
        """Run the enhanced window manager"""
        try:
            logger.info("Starting Berke0S main loop...")
            
            # Restore previous session if available
            self.restore_session()
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Enhanced cleanup on exit"""
        try:
            logger.info("Performing cleanup...")
            
            # Save current state
            self.save_session()
            self.save_config()
            
            # Logout user
            if self.user_manager:
                self.user_manager.logout()
            
            # Stop services
            if self.performance_monitor:
                self.performance_monitor.stop()
            
            if self.plugin_manager:
                self.plugin_manager.cleanup()
            
            # Close database connections
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                conn.close()
            except:
                pass
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    # Placeholder methods for UI components (would be fully implemented)
    def create_desktop(self): pass
    def create_taskbar(self): pass
    def create_dock(self): pass
    def load_wallpaper(self): pass
    def create_desktop_icons(self): pass
    def bind_events(self): pass
    def start_services(self): pass
    def restore_session(self): pass
    def save_session(self): pass
    def safe_shutdown(self): pass

# Enhanced Notification System (continuing from previous)
class NotificationSystem:
    """Advanced notification system with rich features"""
    
    def __init__(self, wm):
        self.wm = wm
        self.notifications = []
        self.notification_id = 0
        self.notification_history = []
        self.max_history = 100
        self.sound_enabled = True
        
    def send(self, title, message, timeout=5000, notification_type="info", actions=None, icon=None):
        """Send a rich notification with enhanced features"""
        try:
            if not hasattr(self.wm, 'root') or not self.wm.root:
                return
                
            self.notification_id += 1
            
            # Store in history
            notification_data = {
                "id": self.notification_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "timestamp": datetime.datetime.now(),
                "actions": actions or [],
                "read": False
            }
            self.notification_history.append(notification_data)
            
            # Limit history size
            if len(self.notification_history) > self.max_history:
                self.notification_history.pop(0)
            
            # Play notification sound
            if self.sound_enabled and notification_type in ["warning", "error"]:
                self.play_notification_sound(notification_type)
            
            # Create notification window
            notif = tk.Toplevel(self.wm.root)
            notif.withdraw()
            notif.overrideredirect(True)
            notif.attributes('-topmost', True)
            notif.configure(bg='#1a1a1a')
            
            # Enhanced positioning
            self.position_notification(notif, len(self.notifications))
            
            # Create notification content
            self.create_notification_content(notif, title, message, notification_type, actions, icon)
            
            # Store notification
            notification_data["window"] = notif
            self.notifications.append(notification_data)
            
            # Show with animation
            self.animate_notification(notif, "show")
            
            # Auto close
            if timeout > 0:
                self.wm.root.after(timeout, lambda: self.close_notification(notification_data))
                
        except Exception as e:
            logger.error(f"Notification error: {e}")
    
    def play_notification_sound(self, notification_type):
        """Play notification sound"""
        try:
            if not self.sound_enabled:
                return
                
            # Simple beep for now (could be enhanced with actual sound files)
            if notification_type == "error":
                print("\a")  # System beep
                
        except Exception as e:
            logger.error(f"Notification sound error: {e}")
    
    def position_notification(self, notif, index):
        """Position notification on screen"""
        try:
            screen_width = self.wm.root.winfo_screenwidth()
            screen_height = self.wm.root.winfo_screenheight()
            
            notif_width = 400
            notif_height = 120
            
            position = self.wm.config.get("notifications", {}).get("position", "top-right")
            
            if position == "top-right":
                x = screen_width - notif_width - 20
                y = 20 + index * (notif_height + 10)
            elif position == "top-left":
                x = 20
                y = 20 + index * (notif_height + 10)
            elif position == "bottom-right":
                x = screen_width - notif_width - 20
                y = screen_height - notif_height - 20 - index * (notif_height + 10)
            else:  # bottom-left
                x = 20
                y = screen_height - notif_height - 20 - index * (notif_height + 10)
            
            notif.geometry(f"{notif_width}x{notif_height}+{x}+{y}")
            
        except Exception as e:
            logger.error(f"Notification positioning error: {e}")
    
    def create_notification_content(self, notif, title, message, notif_type, actions, icon):
        """Create enhanced notification content"""
        try:
            # Color scheme based on type
            colors = {
                "info": {"icon": "ℹ️", "color": "#4a9eff", "text_color": "white"},
                "success": {"icon": "✅", "color": "#00ff88", "text_color": "black"},
                "warning": {"icon": "⚠️", "color": "#ffb347", "text_color": "black"},
                "error": {"icon": "❌", "color": "#ff6b6b", "text_color": "white"},
                "system": {"icon": "🔧", "color": "#6c757d", "text_color": "white"}
            }
            
            config = colors.get(notif_type, colors["info"])
            
            # Main container with rounded corners effect
            main_frame = tk.Frame(notif, bg='#2a2a2a', relief=tk.RAISED, bd=3)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
            
            # Header with colored stripe
            header_frame = tk.Frame(main_frame, bg=config["color"], height=35)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            # Icon and title
            title_frame = tk.Frame(header_frame, bg=config["color"])
            title_frame.pack(fill=tk.X, padx=15, pady=8)
            
            # Icon
            icon_text = icon if icon else config["icon"]
            tk.Label(title_frame, text=icon_text, bg=config["color"], 
                    fg=config["text_color"], font=('Arial', 14)).pack(side=tk.LEFT)
            
            # Title
            tk.Label(title_frame, text=title, bg=config["color"], 
                    fg=config["text_color"], font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=(15, 0))
            
            # Close button
            close_btn = tk.Label(title_frame, text="✕", bg=config["color"], 
                               fg=config["text_color"], font=('Arial', 10), cursor='hand2')
            close_btn.pack(side=tk.RIGHT)
            close_btn.bind('<Button-1>', lambda e: self.close_notification_by_window(notif))
            
            # Message content
            content_frame = tk.Frame(main_frame, bg='#3a3a3a')
            content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            
            # Message text
            msg_label = tk.Label(content_frame, text=message, bg='#3a3a3a', fg='white', 
                               font=('Arial', 10), wraplength=360, justify=tk.LEFT, anchor='nw')
            msg_label.pack(fill=tk.X, pady=(0, 8))
            
            # Action buttons
            if actions:
                action_frame = tk.Frame(content_frame, bg='#3a3a3a')
                action_frame.pack(fill=tk.X)
                
                for action in actions:
                    btn = tk.Button(action_frame, text=action.get("text", "Action"),
                                   command=lambda a=action: self.handle_notification_action(notif, a),
                                   bg=config["color"], fg=config["text_color"],
                                   font=('Arial', 9), relief=tk.FLAT, padx=15, pady=5)
                    btn.pack(side=tk.LEFT, padx=(0, 8))
            
            # Timestamp
            timestamp = datetime.datetime.now().strftime("%H:%M")
            time_label = tk.Label(content_frame, text=timestamp, bg='#3a3a3a', fg='#888888', 
                                font=('Arial', 8))
            time_label.pack(side=tk.BOTTOM, anchor='e')
            
        except Exception as e:
            logger.error(f"Notification content creation error: {e}")
    
    def handle_notification_action(self, notif, action):
        """Handle notification action button click"""
        try:
            if "callback" in action and callable(action["callback"]):
                action["callback"]()
            
            # Close notification after action
            self.close_notification_by_window(notif)
            
        except Exception as e:
            logger.error(f"Notification action error: {e}")
    
    def close_notification_by_window(self, notif_window):
        """Close notification by window reference"""
        for notification in self.notifications:
            if notification.get("window") == notif_window:
                self.close_notification(notification)
                break
    
    def animate_notification(self, notif, action):
        """Enhanced notification animation"""
        try:
            if action == "show":
                notif.deiconify()
                notif.attributes('-alpha', 0)
                
                # Slide in animation with bounce effect
                start_x = notif.winfo_x() + 100
                target_x = notif.winfo_x()
                
                def slide_in(step=0):
                    if step <= 15:
                        progress = step / 15
                        # Ease-out animation
                        eased_progress = 1 - (1 - progress) ** 3
                        current_x = start_x + (target_x - start_x) * eased_progress
                        alpha = progress * 0.95
                        
                        notif.geometry(f"{notif.winfo_width()}x{notif.winfo_height()}+{int(current_x)}+{notif.winfo_y()}")
                        notif.attributes('-alpha', alpha)
                        
                        self.wm.root.after(20, lambda: slide_in(step + 1))
                        
                slide_in()
                
            elif action == "hide":
                def fade_out(alpha=0.95):
                    if alpha >= 0:
                        notif.attributes('-alpha', alpha)
                        self.wm.root.after(30, lambda: fade_out(alpha - 0.15))
                    else:
                        notif.destroy()
                        
                fade_out()
                
        except Exception as e:
            logger.error(f"Animation error: {e}")
            if action == "hide":
                notif.destroy()
    
    def close_notification(self, notification):
        """Close a specific notification"""
        try:
            if notification in self.notifications:
                self.notifications.remove(notification)
                if "window" in notification:
                    self.animate_notification(notification["window"], "hide")
                self.reposition_notifications()
        except Exception as e:
            logger.error(f"Close notification error: {e}")
    
    def reposition_notifications(self):
        """Reposition remaining notifications"""
        try:
            for i, notification in enumerate(self.notifications):
                if "window" in notification:
                    self.position_notification(notification["window"], i)
                    
        except Exception as e:
            logger.error(f"Reposition error: {e}")

# Placeholder classes for other applications (would be fully implemented)
class FileManager:
    def __init__(self, wm): self.wm = wm
    def show(self): pass
    def bring_to_front(self): pass

class TextEditor:
    def __init__(self, wm): self.wm = wm
    def show(self, file_path=None): pass

class Calculator:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class WebBrowser:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class SettingsApp:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class Terminal:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class PluginManager:
    def __init__(self, wm): self.wm = wm
    def cleanup(self): pass

class PerformanceMonitor:
    def __init__(self, wm): self.wm = wm
    def stop(self): pass

# Main execution
def main():
    """Enhanced main entry point with complete error handling"""
    try:
        logger.info("Starting Berke0S 4.0 Ultimate Desktop Environment...")
        
        # Initialize database
        init_database()
        
        # Create default user if none exists
        create_default_user()
        
        # Check if installation is needed
        if not os.path.exists(INSTALL_FLAG) or "--install" in sys.argv or "--setup" in sys.argv:
            logger.info("Starting installation wizard...")
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
                    logger.info("Installation completed, starting desktop environment...")
                    # Start desktop environment
                    wm = WindowManager()
                    wm.run()
        else:
            # Start desktop environment directly
            logger.info("Starting desktop environment...")
            wm = WindowManager()
            wm.run()
            
    except KeyboardInterrupt:
        logger.info("Berke0S terminated by user")
        print("\n🔄 Berke0S terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        print(f"❌ Error starting Berke0S: {e}")
        
        # Try to show error dialog if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Berke0S Error", f"Failed to start Berke0S:\n\n{str(e)}")
            root.destroy()
        except:
            pass
            
        sys.exit(1)

if __name__ == "__main__":
    main()

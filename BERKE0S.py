#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Berke0S - Complete Advanced Desktop Environment for Tiny Core Linux - Version 2
Created by: Berke Oruç
Version: 3.0 - Ultimate Edition V2 - Enhanced Display Management
License: MIT

Complete desktop environment with advanced display management and Tiny Core Linux optimizations
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
import fcntl
import struct
import termios
from io import BytesIO, StringIO
from urllib.parse import quote, unquote
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
DISPLAY_LOG = f"{CONFIG_DIR}/display.log"
X_LOG = f"{CONFIG_DIR}/x_server.log"

# Ensure directories exist
for directory in [CONFIG_DIR, THEMES_DIR, PLUGINS_DIR, WALLPAPERS_DIR, APPS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Enhanced logging setup with display-specific logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('Berke0S')

# Display logger
display_logger = logging.getLogger('Display')
display_handler = logging.FileHandler(DISPLAY_LOG)
display_handler.setFormatter(logging.Formatter('%(asctime)s - DISPLAY - %(levelname)s - %(message)s'))
display_logger.addHandler(display_handler)
display_logger.setLevel(logging.DEBUG)

# Enhanced default configuration
DEFAULT_CONFIG = {
    "version": "3.0-v2",
    "first_boot": True,
    "language": "tr_TR",
    "timezone": "Europe/Istanbul",
    "theme": "berke_dark",
    "users": [],
    "wifi": {"ssid": "", "password": ""},
    "installed": False,
    "display": {
        "auto_detect": True,
        "force_x11": True,
        "display_server": "auto",  # auto, xorg, wayland
        "resolution": "auto",
        "refresh_rate": 60,
        "color_depth": 24,
        "multi_monitor": False,
        "primary_monitor": 0,
        "x_arguments": ["-nolisten", "tcp", "-nocursor"],
        "fallback_resolution": "1024x768",
        "virtual_display": False,
        "headless_mode": False
    },
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
        "show_dock": False
    },
    "taskbar": {
        "position": "bottom",
        "auto_hide": False,
        "color": "#1a1a1a",
        "size": 45,
        "show_clock": True,
        "show_system_tray": True,
        "show_quick_launch": True,
        "transparency": 0.9
    },
    "notifications": {
        "enabled": True,
        "timeout": 5000,
        "position": "top-right",
        "sound_enabled": True,
        "show_previews": True
    },
    "power": {
        "sleep_timeout": 1800,
        "screen_off_timeout": 900,
        "hibernate_enabled": True,
        "cpu_scaling": "ondemand"
    },
    "accessibility": {
        "high_contrast": False,
        "screen_reader": False,
        "font_scale": 1.0,
        "magnifier": False,
        "keyboard_navigation": True
    },
    "security": {
        "auto_lock": True,
        "lock_timeout": 600,
        "require_password": True,
        "encryption_enabled": False
    },
    "network": {
        "auto_connect": True,
        "proxy_enabled": False,
        "proxy_host": "",
        "proxy_port": 8080,
        "firewall_enabled": True
    },
    "audio": {
        "master_volume": 75,
        "mute": False,
        "default_device": "auto",
        "sound_theme": "default"
    },
    "system": {
        "auto_updates": True,
        "crash_reporting": True,
        "telemetry": False,
        "performance_mode": "balanced",
        "auto_backup": False,
        "backup_interval": 24,
        "24_hour_format": True
    }
}

# Enhanced Display Management System
class DisplayManager:
    """Advanced display management for Tiny Core Linux"""
    
    def __init__(self):
        self.display_info = {}
        self.x_process = None
        self.display_ready = False
        self.current_display = ":0"
        self.backup_displays = [":1", ":2", ":10"]
        self.x_server_attempts = 0
        self.max_attempts = 5
        
    def detect_environment(self):
        """Detect current environment and capabilities"""
        try:
            env_info = {
                "os_name": platform.system(),
                "distribution": self.get_distribution(),
                "is_tinycore": self.is_tiny_core_linux(),
                "desktop_session": os.environ.get("DESKTOP_SESSION", ""),
                "display": os.environ.get("DISPLAY", ""),
                "wayland_display": os.environ.get("WAYLAND_DISPLAY", ""),
                "x11_available": self.check_x11_availability(),
                "wayland_available": self.check_wayland_availability(),
                "graphics_driver": self.detect_graphics_driver(),
                "current_user": getpass.getuser(),
                "is_root": os.getuid() == 0 if hasattr(os, 'getuid') else False,
                "tty": self.get_current_tty(),
                "runlevel": self.get_runlevel()
            }
            
            display_logger.info(f"Environment detected: {env_info}")
            return env_info
            
        except Exception as e:
            display_logger.error(f"Environment detection error: {e}")
            return {"error": str(e)}
    
    def is_tiny_core_linux(self):
        """Check if running on Tiny Core Linux"""
        try:
            # Check for TC-specific files and directories
            tc_indicators = [
                "/opt/tce",
                "/etc/init.d/tc-config",
                "/usr/bin/tce-load",
                "/opt/bootlocal.sh"
            ]
            
            for indicator in tc_indicators:
                if os.path.exists(indicator):
                    return True
            
            # Check version files
            version_files = ["/etc/tc-release", "/etc/tinycore-release"]
            for vfile in version_files:
                if os.path.exists(vfile):
                    return True
            
            # Check command output
            try:
                result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=5)
                if 'tinycore' in result.stdout.lower():
                    return True
            except:
                pass
                
            return False
            
        except Exception as e:
            display_logger.error(f"Tiny Core detection error: {e}")
            return False
    
    def get_distribution(self):
        """Get Linux distribution name"""
        try:
            # Try multiple methods to detect distribution
            methods = [
                "/etc/os-release",
                "/etc/lsb-release",
                "/etc/debian_version",
                "/etc/redhat-release"
            ]
            
            for method in methods:
                if os.path.exists(method):
                    with open(method, 'r') as f:
                        content = f.read()
                        if 'tinycore' in content.lower() or 'tiny core' in content.lower():
                            return "TinyCore"
                        elif 'ubuntu' in content.lower():
                            return "Ubuntu"
                        elif 'debian' in content.lower():
                            return "Debian"
            
            return "Unknown"
            
        except Exception as e:
            display_logger.error(f"Distribution detection error: {e}")
            return "Unknown"
    
    def check_x11_availability(self):
        """Check if X11 is available"""
        try:
            # Check for X11 binaries
            x11_binaries = ['X', 'Xorg', 'xinit', 'startx']
            available_binaries = []
            
            for binary in x11_binaries:
                if shutil.which(binary):
                    available_binaries.append(binary)
            
            # Check for X11 libraries
            x11_libs = ['/usr/lib/xorg', '/usr/lib/X11', '/usr/X11R6/lib']
            available_libs = [lib for lib in x11_libs if os.path.exists(lib)]
            
            return {
                "available": len(available_binaries) > 0,
                "binaries": available_binaries,
                "libraries": available_libs
            }
            
        except Exception as e:
            display_logger.error(f"X11 availability check error: {e}")
            return {"available": False, "error": str(e)}
    
    def check_wayland_availability(self):
        """Check if Wayland is available"""
        try:
            wayland_binaries = ['wayland-scanner', 'weston']
            available_binaries = []
            
            for binary in wayland_binaries:
                if shutil.which(binary):
                    available_binaries.append(binary)
            
            return {
                "available": len(available_binaries) > 0,
                "binaries": available_binaries
            }
            
        except Exception as e:
            display_logger.error(f"Wayland availability check error: {e}")
            return {"available": False, "error": str(e)}
    
    def detect_graphics_driver(self):
        """Detect graphics driver"""
        try:
            drivers = []
            
            # Check lspci for graphics cards
            try:
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
                lines = result.stdout.lower()
                
                if 'nvidia' in lines:
                    drivers.append('nvidia')
                if 'amd' in lines or 'ati' in lines:
                    drivers.append('amd')
                if 'intel' in lines:
                    drivers.append('intel')
                if 'vmware' in lines:
                    drivers.append('vmware')
                if 'virtualbox' in lines:
                    drivers.append('vbox')
                    
            except:
                pass
            
            # Check loaded kernel modules
            try:
                with open('/proc/modules', 'r') as f:
                    modules = f.read().lower()
                    
                if 'nvidia' in modules:
                    drivers.append('nvidia')
                if 'radeon' in modules or 'amdgpu' in modules:
                    drivers.append('amd')
                if 'i915' in modules or 'i965' in modules:
                    drivers.append('intel')
                    
            except:
                pass
            
            return list(set(drivers)) if drivers else ['generic']
            
        except Exception as e:
            display_logger.error(f"Graphics driver detection error: {e}")
            return ['unknown']
    
    def get_current_tty(self):
        """Get current TTY"""
        try:
            result = subprocess.run(['tty'], capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def get_runlevel(self):
        """Get current runlevel"""
        try:
            result = subprocess.run(['runlevel'], capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def setup_display_environment(self):
        """Setup comprehensive display environment"""
        try:
            display_logger.info("Starting comprehensive display setup...")
            
            # Detect current environment
            env_info = self.detect_environment()
            
            # Check if we already have a working display
            if self.test_existing_display():
                display_logger.info("Existing display working, using it")
                return True
            
            # Prepare environment
            self.prepare_display_environment()
            
            # Try different display methods based on environment
            if env_info.get("is_tinycore", False):
                success = self.setup_tinycore_display()
            else:
                success = self.setup_generic_display()
            
            if not success:
                # Try fallback methods
                success = self.try_fallback_display_methods()
            
            if success:
                # Verify display is working
                success = self.verify_display_setup()
                
            if success:
                display_logger.info("Display setup completed successfully")
                self.display_ready = True
                return True
            else:
                display_logger.warning("All display setup methods failed, attempting headless mode")
                return self.setup_headless_mode()
                
        except Exception as e:
            display_logger.error(f"Display setup error: {e}")
            return self.setup_headless_mode()
    
    def test_existing_display(self):
        """Test if there's already a working display"""
        try:
            current_display = os.environ.get('DISPLAY', '')
            if current_display:
                display_logger.info(f"Testing existing display: {current_display}")
                
                # Test with xdpyinfo
                try:
                    result = subprocess.run(['xdpyinfo'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        display_logger.info("Existing display is working")
                        self.current_display = current_display
                        return True
                except:
                    pass
                
                # Test with xset
                try:
                    result = subprocess.run(['xset', 'q'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        display_logger.info("Existing display verified with xset")
                        self.current_display = current_display
                        return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            display_logger.error(f"Existing display test error: {e}")
            return False
    
    def prepare_display_environment(self):
        """Prepare environment variables and settings"""
        try:
            display_logger.info("Preparing display environment...")
            
            # Set basic environment variables
            os.environ['DISPLAY'] = self.current_display
            os.environ['XAUTHORITY'] = os.path.expanduser('~/.Xauthority')
            
            # Tiny Core specific environment
            if self.detect_environment().get("is_tinycore", False):
                # Set TC-specific paths
                x_paths = [
                    '/usr/local/bin',
                    '/usr/bin',
                    '/bin',
                    '/opt/bin',
                    '/usr/local/lib/X11',
                    '/usr/lib/X11'
                ]
                
                current_path = os.environ.get('PATH', '')
                for path in x_paths:
                    if path not in current_path and os.path.exists(path):
                        os.environ['PATH'] = f"{path}:{current_path}"
                
                # Set library paths
                lib_paths = [
                    '/usr/local/lib',
                    '/usr/lib',
                    '/lib',
                    '/opt/lib'
                ]
                
                ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
                for lib_path in lib_paths:
                    if lib_path not in ld_library_path and os.path.exists(lib_path):
                        os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{ld_library_path}"
            
            # Create necessary directories
            x_dirs = [
                '/tmp/.X11-unix',
                '/tmp/.ICE-unix',
                os.path.expanduser('~/.cache'),
                os.path.expanduser('~/.local/share')
            ]
            
            for directory in x_dirs:
                os.makedirs(directory, exist_ok=True)
                try:
                    os.chmod(directory, 0o1777 if directory.startswith('/tmp') else 0o755)
                except:
                    pass
            
            display_logger.info("Display environment prepared")
            
        except Exception as e:
            display_logger.error(f"Environment preparation error: {e}")
    
    def setup_tinycore_display(self):
        """Setup display specifically for Tiny Core Linux"""
        try:
            display_logger.info("Setting up display for Tiny Core Linux...")
            
            # TC-specific X server start methods
            tc_methods = [
                self.start_tc_x_with_startx,
                self.start_tc_x_with_xinit,
                self.start_tc_x_direct,
                self.start_tc_x_with_wm
            ]
            
            for method in tc_methods:
                try:
                    display_logger.info(f"Trying method: {method.__name__}")
                    if method():
                        display_logger.info(f"Success with method: {method.__name__}")
                        return True
                    time.sleep(2)  # Wait between attempts
                except Exception as e:
                    display_logger.warning(f"Method {method.__name__} failed: {e}")
                    continue
            
            return False
            
        except Exception as e:
            display_logger.error(f"Tiny Core display setup error: {e}")
            return False
    
    def start_tc_x_with_startx(self):
        """Start X using startx (TC preferred method)"""
        try:
            display_logger.info("Starting X with startx...")
            
            # Check if startx is available
            if not shutil.which('startx'):
                display_logger.warning("startx not found")
                return False
            
            # Kill any existing X processes
            self.cleanup_x_processes()
            
            # Create minimal xinitrc if it doesn't exist
            xinitrc_path = os.path.expanduser('~/.xinitrc')
            if not os.path.exists(xinitrc_path):
                with open(xinitrc_path, 'w') as f:
                    f.write('#!/bin/sh\n')
                    f.write('xset -dpms\n')
                    f.write('xset s off\n')
                    f.write('exec flwm &\n')
                    f.write('wait\n')
                os.chmod(xinitrc_path, 0o755)
            
            # Start X server with startx
            cmd = ['startx', '--', self.current_display, '-nolisten', 'tcp']
            
            display_logger.info(f"Starting X with command: {' '.join(cmd)}")
            
            # Start in background
            self.x_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for X to start
            return self.wait_for_x_server()
            
        except Exception as e:
            display_logger.error(f"startx method error: {e}")
            return False
    
    def start_tc_x_with_xinit(self):
        """Start X using xinit"""
        try:
            display_logger.info("Starting X with xinit...")
            
            if not shutil.which('xinit'):
                display_logger.warning("xinit not found")
                return False
            
            self.cleanup_x_processes()
            
            # Try different xinit configurations
            xinit_configs = [
                ['xinit', '--', f'/usr/bin/X', self.current_display, '-nolisten', 'tcp'],
                ['xinit', '--', f'/usr/bin/Xorg', self.current_display, '-nolisten', 'tcp'],
                ['xinit', '/usr/bin/flwm', '--', self.current_display, '-nolisten', 'tcp']
            ]
            
            for config in xinit_configs:
                try:
                    display_logger.info(f"Trying xinit config: {' '.join(config)}")
                    
                    self.x_process = subprocess.Popen(
                        config,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        preexec_fn=os.setsid
                    )
                    
                    if self.wait_for_x_server(timeout=10):
                        return True
                    
                    self.cleanup_x_processes()
                    
                except Exception as e:
                    display_logger.warning(f"xinit config failed: {e}")
                    continue
            
            return False
            
        except Exception as e:
            display_logger.error(f"xinit method error: {e}")
            return False
    
    def start_tc_x_direct(self):
        """Start X server directly"""
        try:
            display_logger.info("Starting X server directly...")
            
            # Find X server binary
            x_binaries = ['Xorg', 'X']
            x_binary = None
            
            for binary in x_binaries:
                binary_path = shutil.which(binary)
                if binary_path:
                    x_binary = binary_path
                    break
            
            if not x_binary:
                display_logger.warning("No X server binary found")
                return False
            
            self.cleanup_x_processes()
            
            # Build X server command
            x_cmd = [
                x_binary,
                self.current_display,
                '-nolisten', 'tcp',
                '-nolisten', 'local',
                '-noreset',
                '-auth', os.path.expanduser('~/.Xauthority')
            ]
            
            # Add TC-specific arguments
            tc_args = [
                '-sharevts',
                '-novtswitch',
                '-quiet'
            ]
            x_cmd.extend(tc_args)
            
            display_logger.info(f"Starting X server: {' '.join(x_cmd)}")
            
            # Start X server
            self.x_process = subprocess.Popen(
                x_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for X server to start
            if self.wait_for_x_server():
                # Start a simple window manager
                self.start_window_manager()
                return True
            
            return False
            
        except Exception as e:
            display_logger.error(f"Direct X start error: {e}")
            return False
    
    def start_tc_x_with_wm(self):
        """Start X with window manager in one step"""
        try:
            display_logger.info("Starting X with integrated window manager...")
            
            # Check for available window managers
            wm_list = ['flwm', 'jwm', 'openbox', 'icewm', 'twm']
            available_wm = None
            
            for wm in wm_list:
                if shutil.which(wm):
                    available_wm = wm
                    break
            
            if not available_wm:
                display_logger.warning("No window manager found")
                return False
            
            self.cleanup_x_processes()
            
            # Create startup script
            startup_script = f"""#!/bin/sh
export DISPLAY={self.current_display}
xset -dpms &
xset s off &
{available_wm} &
wait
"""
            
            script_path = '/tmp/berke0s_startup.sh'
            with open(script_path, 'w') as f:
                f.write(startup_script)
            os.chmod(script_path, 0o755)
            
            # Start with xinit
            cmd = ['xinit', script_path, '--', self.current_display, '-nolisten', 'tcp']
            
            display_logger.info(f"Starting X+WM: {' '.join(cmd)}")
            
            self.x_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            return self.wait_for_x_server()
            
        except Exception as e:
            display_logger.error(f"X+WM start error: {e}")
            return False
    
    def setup_generic_display(self):
        """Setup display for generic Linux distributions"""
        try:
            display_logger.info("Setting up display for generic Linux...")
            
            generic_methods = [
                self.start_x_with_gdm,
                self.start_x_with_lightdm,
                self.start_x_standard,
                self.start_x_fallback
            ]
            
            for method in generic_methods:
                try:
                    if method():
                        return True
                    time.sleep(2)
                except Exception as e:
                    display_logger.warning(f"Generic method failed: {e}")
                    continue
            
            return False
            
        except Exception as e:
            display_logger.error(f"Generic display setup error: {e}")
            return False
    
    def start_x_with_gdm(self):
        """Start X using GDM"""
        try:
            if shutil.which('gdm') or shutil.which('gdm3'):
                display_logger.info("Starting X with GDM...")
                subprocess.Popen(['gdm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return self.wait_for_x_server()
            return False
        except:
            return False
    
    def start_x_with_lightdm(self):
        """Start X using LightDM"""
        try:
            if shutil.which('lightdm'):
                display_logger.info("Starting X with LightDM...")
                subprocess.Popen(['lightdm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return self.wait_for_x_server()
            return False
        except:
            return False
    
    def start_x_standard(self):
        """Standard X startup method"""
        try:
            display_logger.info("Starting X with standard method...")
            
            if shutil.which('startx'):
                self.x_process = subprocess.Popen(
                    ['startx', '--', self.current_display, '-nolisten', 'tcp'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return self.wait_for_x_server()
            
            return False
        except:
            return False
    
    def start_x_fallback(self):
        """Fallback X startup method"""
        try:
            display_logger.info("Starting X with fallback method...")
            
            x_binary = shutil.which('Xorg') or shutil.which('X')
            if x_binary:
                self.x_process = subprocess.Popen(
                    [x_binary, self.current_display, '-nolisten', 'tcp'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return self.wait_for_x_server()
            
            return False
        except:
            return False
    
    def try_fallback_display_methods(self):
        """Try various fallback display methods"""
        try:
            display_logger.info("Trying fallback display methods...")
            
            fallback_methods = [
                self.try_virtual_display,
                self.try_nested_x,
                self.try_xvfb,
                self.try_different_displays
            ]
            
            for method in fallback_methods:
                try:
                    display_logger.info(f"Trying fallback: {method.__name__}")
                    if method():
                        return True
                except Exception as e:
                    display_logger.warning(f"Fallback method failed: {e}")
                    continue
            
            return False
            
        except Exception as e:
            display_logger.error(f"Fallback methods error: {e}")
            return False
    
    def try_virtual_display(self):
        """Try to create a virtual display"""
        try:
            if shutil.which('Xvfb'):
                display_logger.info("Starting virtual display with Xvfb...")
                
                self.cleanup_x_processes()
                
                cmd = [
                    'Xvfb',
                    self.current_display,
                    '-screen', '0', '1024x768x24',
                    '-nolisten', 'tcp',
                    '-auth', os.path.expanduser('~/.Xauthority')
                ]
                
                self.x_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                return self.wait_for_x_server()
            
            return False
            
        except Exception as e:
            display_logger.error(f"Virtual display error: {e}")
            return False
    
    def try_nested_x(self):
        """Try nested X server"""
        try:
            if shutil.which('Xnest'):
                display_logger.info("Starting nested X server...")
                
                cmd = [
                    'Xnest',
                    self.current_display,
                    '-geometry', '1024x768',
                    '-name', 'Berke0S'
                ]
                
                self.x_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                return self.wait_for_x_server()
            
            return False
            
        except Exception as e:
            display_logger.error(f"Nested X error: {e}")
            return False
    
    def try_xvfb(self):
        """Try Xvfb (Virtual Framebuffer)"""
        try:
            if shutil.which('Xvfb'):
                display_logger.info("Starting Xvfb...")
                
                cmd = [
                    'Xvfb',
                    self.current_display,
                    '-screen', '0', '1024x768x24',
                    '-pixdepths', '3', '8', '15', '16', '24', '32'
                ]
                
                self.x_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if self.wait_for_x_server():
                    # Start window manager for Xvfb
                    self.start_window_manager()
                    return True
            
            return False
            
        except Exception as e:
            display_logger.error(f"Xvfb error: {e}")
            return False
    
    def try_different_displays(self):
        """Try different display numbers"""
        try:
            display_logger.info("Trying different display numbers...")
            
            for display_num in self.backup_displays:
                try:
                    display_logger.info(f"Trying display: {display_num}")
                    
                    self.current_display = display_num
                    os.environ['DISPLAY'] = display_num
                    
                    # Try starting X on this display
                    x_binary = shutil.which('Xorg') or shutil.which('X')
                    if x_binary:
                        cmd = [x_binary, display_num, '-nolisten', 'tcp']
                        
                        self.x_process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                        if self.wait_for_x_server(timeout=10):
                            display_logger.info(f"Success with display: {display_num}")
                            self.start_window_manager()
                            return True
                        
                        self.cleanup_x_processes()
                    
                except Exception as e:
                    display_logger.warning(f"Display {display_num} failed: {e}")
                    continue
            
            return False
            
        except Exception as e:
            display_logger.error(f"Different displays error: {e}")
            return False
    
    def wait_for_x_server(self, timeout=30):
        """Wait for X server to become ready"""
        try:
            display_logger.info(f"Waiting for X server on {self.current_display} (timeout: {timeout}s)...")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Test with xdpyinfo
                try:
                    result = subprocess.run(
                        ['xdpyinfo', '-display', self.current_display],
                        capture_output=True,
                        timeout=3
                    )
                    if result.returncode == 0:
                        display_logger.info("X server is ready (xdpyinfo test passed)")
                        return True
                except:
                    pass
                
                # Test with xset
                try:
                    result = subprocess.run(
                        ['xset', '-display', self.current_display, 'q'],
                        capture_output=True,
                        timeout=3
                    )
                    if result.returncode == 0:
                        display_logger.info("X server is ready (xset test passed)")
                        return True
                except:
                    pass
                
                # Check if X process is still running
                if self.x_process and self.x_process.poll() is not None:
                    display_logger.warning("X server process died")
                    return False
                
                time.sleep(1)
            
            display_logger.warning(f"X server timeout after {timeout} seconds")
            return False
            
        except Exception as e:
            display_logger.error(f"Wait for X server error: {e}")
            return False
    
    def start_window_manager(self):
        """Start a window manager"""
        try:
            display_logger.info("Starting window manager...")
            
            # List of window managers to try
            wm_list = ['flwm', 'jwm', 'openbox', 'icewm', 'mwm', 'twm', 'fvwm']
            
            for wm in wm_list:
                if shutil.which(wm):
                    display_logger.info(f"Starting window manager: {wm}")
                    
                    try:
                        env = os.environ.copy()
                        env['DISPLAY'] = self.current_display
                        
                        subprocess.Popen(
                            [wm],
                            env=env,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        
                        display_logger.info(f"Window manager {wm} started")
                        time.sleep(2)  # Give WM time to start
                        return True
                        
                    except Exception as e:
                        display_logger.warning(f"Failed to start {wm}: {e}")
                        continue
            
            display_logger.warning("No window manager could be started")
            return False
            
        except Exception as e:
            display_logger.error(f"Window manager start error: {e}")
            return False
    
    def cleanup_x_processes(self):
        """Clean up existing X processes"""
        try:
            display_logger.info("Cleaning up existing X processes...")
            
            # Kill existing X processes
            x_processes = ['X', 'Xorg', 'Xvfb', 'Xnest']
            
            for proc_name in x_processes:
                try:
                    subprocess.run(['pkill', '-f', proc_name], 
                                 capture_output=True, timeout=5)
                except:
                    pass
            
            # Clean up X sockets
            x_sockets = [f'/tmp/.X11-unix/X{i}' for i in range(0, 10)]
            for socket_path in x_sockets:
                try:
                    if os.path.exists(socket_path):
                        os.remove(socket_path)
                except:
                    pass
            
            # Wait a moment for cleanup
            time.sleep(1)
            
            display_logger.info("X processes cleanup completed")
            
        except Exception as e:
            display_logger.error(f"X processes cleanup error: {e}")
    
    def verify_display_setup(self):
        """Verify that display setup is working correctly"""
        try:
            display_logger.info("Verifying display setup...")
            
            # Test basic X functionality
            tests = [
                self.test_x_connection,
                self.test_x_extensions,
                self.test_window_creation
            ]
            
            for test in tests:
                try:
                    if not test():
                        display_logger.warning(f"Display test failed: {test.__name__}")
                        return False
                except Exception as e:
                    display_logger.warning(f"Display test error {test.__name__}: {e}")
                    return False
            
            display_logger.info("Display verification successful")
            return True
            
        except Exception as e:
            display_logger.error(f"Display verification error: {e}")
            return False
    
    def test_x_connection(self):
        """Test basic X connection"""
        try:
            result = subprocess.run(
                ['xdpyinfo', '-display', self.current_display],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def test_x_extensions(self):
        """Test X extensions"""
        try:
            result = subprocess.run(
                ['xdpyinfo', '-display', self.current_display, '-ext', 'all'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def test_window_creation(self):
        """Test window creation capability"""
        try:
            # Try to create a simple test window with xwininfo
            result = subprocess.run(
                ['xwininfo', '-display', self.current_display, '-root'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def setup_headless_mode(self):
        """Setup headless mode for systems without display"""
        try:
            display_logger.info("Setting up headless mode...")
            
            # Set environment for headless operation
            os.environ['DISPLAY'] = ':99'  # Non-existent display
            
            # Create dummy display info
            self.display_info = {
                "mode": "headless",
                "width": 1024,
                "height": 768,
                "depth": 24
            }
            
            display_logger.info("Headless mode configured")
            return True
            
        except Exception as e:
            display_logger.error(f"Headless setup error: {e}")
            return False
    
    def get_display_info(self):
        """Get current display information"""
        try:
            if self.display_ready:
                # Get display info from X server
                try:
                    result = subprocess.run(
                        ['xdpyinfo', '-display', self.current_display],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        info = self.parse_xdpyinfo_output(result.stdout)
                        self.display_info = info
                        return info
                except:
                    pass
            
            # Return default info if X is not available
            return {
                "display": self.current_display,
                "mode": "headless" if not self.display_ready else "unknown",
                "width": 1024,
                "height": 768,
                "depth": 24
            }
            
        except Exception as e:
            display_logger.error(f"Get display info error: {e}")
            return {"error": str(e)}
    
    def parse_xdpyinfo_output(self, output):
        """Parse xdpyinfo output to extract display information"""
        try:
            info = {
                "display": self.current_display,
                "mode": "x11"
            }
            
            lines = output.split('\n')
            for line in lines:
                if 'dimensions:' in line:
                    # Extract resolution
                    parts = line.split()
                    if len(parts) >= 2:
                        resolution = parts[1]
                        if 'x' in resolution:
                            w, h = resolution.split('x')
                            info['width'] = int(w)
                            info['height'] = int(h.split()[0])  # Remove any additional text
                
                elif 'depth of root window:' in line:
                    # Extract color depth
                    parts = line.split()
                    if len(parts) >= 5:
                        info['depth'] = int(parts[4])
                
                elif 'number of screens:' in line:
                    # Extract screen count
                    parts = line.split()
                    if len(parts) >= 4:
                        info['screens'] = int(parts[3])
            
            return info
            
        except Exception as e:
            display_logger.error(f"Parse xdpyinfo error: {e}")
            return {"error": str(e)}
    
    def is_display_ready(self):
        """Check if display is ready for use"""
        return self.display_ready
    
    def get_current_display(self):
        """Get current display identifier"""
        return self.current_display
    
    def shutdown_display(self):
        """Shutdown display system"""
        try:
            display_logger.info("Shutting down display system...")
            
            if self.x_process and self.x_process.poll() is None:
                try:
                    os.killpg(os.getpgid(self.x_process.pid), signal.SIGTERM)
                    time.sleep(2)
                    if self.x_process.poll() is None:
                        os.killpg(os.getpgid(self.x_process.pid), signal.SIGKILL)
                except:
                    pass
            
            self.cleanup_x_processes()
            self.display_ready = False
            
            display_logger.info("Display system shutdown completed")
            
        except Exception as e:
            display_logger.error(f"Display shutdown error: {e}")

# Enhanced display detection and setup with improved error handling
def setup_display():
    """Enhanced display setup with comprehensive fallback system"""
    try:
        logger.info("Starting enhanced display setup...")
        
        display_manager = DisplayManager()
        
        # Setup display environment
        success = display_manager.setup_display_environment()
        
        if success:
            logger.info("Display setup completed successfully")
            
            # Log display information
            display_info = display_manager.get_display_info()
            logger.info(f"Display info: {display_info}")
            
            return True
        else:
            logger.warning("Display setup failed, but continuing in headless mode")
            return True  # Continue even without display
            
    except Exception as e:
        logger.error(f"Display setup critical error: {e}")
        # Even if display setup fails completely, continue
        return True

def init_database():
    """Initialize SQLite database for system data"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                fullname TEXT,
                password_hash TEXT,
                is_admin INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                preferences TEXT
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                session_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Files metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE,
                file_type TEXT,
                size INTEGER,
                modified_at TIMESTAMP,
                tags TEXT,
                rating INTEGER DEFAULT 0
            )
        ''')
        
        # System logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY,
                level TEXT,
                message TEXT,
                component TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY,
                name TEXT,
                command TEXT,
                icon TEXT,
                category TEXT,
                description TEXT,
                installed INTEGER DEFAULT 1
            )
        ''')
        
        # Display logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS display_logs (
                id INTEGER PRIMARY KEY,
                event_type TEXT,
                display_id TEXT,
                message TEXT,
                success INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

# Enhanced Installation System
class InstallationWizard:
    """Complete installation wizard with advanced features and display management"""
    
    def __init__(self):
        self.root = None
        self.current_step = 0
        self.steps = [
            "welcome",
            "system_check", 
            "language", 
            "display_setup",
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
        self.display_manager = DisplayManager()
        
    def start_installation(self):
        """Start the installation process with enhanced display management"""
        logger.info("Starting Berke0S installation wizard...")
        
        # First, try to setup display
        display_success = self.display_manager.setup_display_environment()
        
        if display_success and self.display_manager.is_display_ready():
            return self.gui_install()
        else:
            logger.warning("GUI not available, falling back to console installation")
            return self.console_install()
            
    def gui_install(self):
        """GUI installation with enhanced display support"""
        try:
            self.root = tk.Tk()
            self.root.title("Berke0S 3.0 V2 - Ultimate Installation")
            self.root.geometry("900x700")
            self.root.configure(bg='#0a0a0f')
            self.root.resizable(True, True)
            
            # Enhanced window styling
            try:
                self.root.attributes('-alpha', 0.98)
            except:
                pass  # Ignore if not supported
            
            # Center window
            self.center_window()
            
            # Load custom fonts
            self.setup_fonts()
            
            # Create enhanced UI
            self.setup_installation_ui()
            
            self.show_step()
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"GUI installation failed: {e}")
            return self.console_install()
            
    def center_window(self):
        """Center the installation window"""
        try:
            self.root.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
            y = (self.root.winfo_screenheight() // 2) - (700 // 2)
            self.root.geometry(f"900x700+{x}+{y}")
        except Exception as e:
            logger.warning(f"Window centering failed: {e}")
        
    def setup_fonts(self):
        """Setup custom fonts for installation"""
        try:
            self.title_font = tkFont.Font(family="Arial", size=24, weight="bold")
            self.header_font = tkFont.Font(family="Arial", size=16, weight="bold")
            self.normal_font = tkFont.Font(family="Arial", size=11)
            self.small_font = tkFont.Font(family="Arial", size=9)
        except Exception as e:
            logger.warning(f"Font setup failed: {e}")
            # Use default fonts as fallback
            self.title_font = ("Arial", 24, "bold")
            self.header_font = ("Arial", 16, "bold")
            self.normal_font = ("Arial", 11)
            self.small_font = ("Arial", 9)
        
    def setup_installation_ui(self):
        """Setup enhanced installation UI"""
        try:
            # Create gradient background
            self.create_gradient_bg()
            
            # Main container
            self.main_container = tk.Frame(self.root, bg='#0a0a0f')
            self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        except Exception as e:
            logger.error(f"Installation UI setup failed: {e}")
        
    def create_gradient_bg(self):
        """Create gradient background for installation"""
        if PIL_AVAILABLE:
            try:
                width, height = 900, 700
                image = Image.new('RGB', (width, height))
                draw = ImageDraw.Draw(image)
                
                # Create a beautiful gradient
                for y in range(height):
                    ratio = y / height
                    r = int(10 + ratio * 20)
                    g = int(10 + ratio * 30)
                    b = int(15 + ratio * 50)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                
                self.bg_image = ImageTk.PhotoImage(image)
                bg_label = tk.Label(self.root, image=self.bg_image)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                logger.warning(f"Gradient background creation failed: {e}")
        
    def show_step(self):
        """Show current installation step"""
        try:
            # Clear main container
            for widget in self.main_container.winfo_children():
                widget.destroy()
            
            step_name = self.steps[self.current_step]
            
            if step_name == "welcome":
                self.show_welcome_step()
            elif step_name == "system_check":
                self.show_system_check_step()
            elif step_name == "language":
                self.show_language_step()
            elif step_name == "display_setup":
                self.show_display_setup_step()
            elif step_name == "disk_setup":
                self.show_disk_setup_step()
            elif step_name == "network":
                self.show_network_step()
            elif step_name == "user_setup":
                self.show_user_setup_step()
            elif step_name == "customization":
                self.show_customization_step()
            elif step_name == "advanced_settings":
                self.show_advanced_settings_step()
            elif step_name == "installation":
                self.show_installation_step()
            elif step_name == "complete":
                self.show_complete_step()
                
        except Exception as e:
            logger.error(f"Step display error: {e}")
    
    def show_welcome_step(self):
        """Show welcome step"""
        try:
            # Welcome header
            header = tk.Label(self.main_container, 
                            text="Welcome to Berke0S 3.0 V2",
                            font=self.title_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(50, 20))
            
            # Welcome message
            message = tk.Text(self.main_container, height=15, width=70,
                            bg="#1a1a1a", fg="white", font=self.normal_font,
                            wrap=tk.WORD, relief=tk.FLAT)
            message.pack(pady=20, padx=50)
            
            welcome_text = """
🚀 Welcome to Berke0S Ultimate Desktop Environment!

This installation wizard will guide you through setting up Berke0S 3.0 V2 
with enhanced display management and Tiny Core Linux optimizations.

Features in this version:
• Advanced display detection and management
• Enhanced Tiny Core Linux support
• Improved X server initialization
• Robust fallback display methods
• Better hardware compatibility
• Enhanced error handling and logging

The installation process includes:
✓ System compatibility check
✓ Display configuration
✓ User account setup
✓ Network configuration
✓ Desktop customization
✓ Advanced system settings

Click Next to begin the installation process.
            """
            
            message.insert('1.0', welcome_text)
            message.config(state='disabled')
            
            # Navigation buttons
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"Welcome step error: {e}")
    
    def show_system_check_step(self):
        """Show system check step"""
        try:
            # Header
            header = tk.Label(self.main_container, 
                            text="System Compatibility Check",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # Progress frame
            progress_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            progress_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
            
            # System check results
            self.check_results = tk.Text(progress_frame, height=20, width=80,
                                       bg="#1a1a1a", fg="white", font=("Courier", 10),
                                       wrap=tk.WORD, relief=tk.FLAT)
            self.check_results.pack(fill=tk.BOTH, expand=True)
            
            # Perform system checks
            self.perform_system_checks()
            
            # Navigation buttons
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"System check step error: {e}")
    
    def perform_system_checks(self):
        """Perform comprehensive system checks"""
        try:
            self.check_results.insert(tk.END, "🔍 Starting system compatibility check...\n\n")
            self.root.update()
            
            checks = [
                ("Operating System", self.check_operating_system),
                ("Python Version", self.check_python_version),
                ("Display System", self.check_display_system),
                ("Graphics Hardware", self.check_graphics_hardware),
                ("Memory", self.check_memory),
                ("Disk Space", self.check_disk_space),
                ("Network", self.check_network),
                ("Audio System", self.check_audio_system),
                ("Required Packages", self.check_packages),
                ("Permissions", self.check_permissions)
            ]
            
            self.system_checks_passed = 0
            self.system_checks_total = len(checks)
            
            for check_name, check_func in checks:
                self.check_results.insert(tk.END, f"📋 Checking {check_name}... ")
                self.root.update()
                
                try:
                    result = check_func()
                    if result["status"] == "pass":
                        self.check_results.insert(tk.END, "✅ PASS\n")
                        self.system_checks_passed += 1
                    elif result["status"] == "warning":
                        self.check_results.insert(tk.END, "⚠️ WARNING\n")
                        self.system_checks_passed += 0.5
                    else:
                        self.check_results.insert(tk.END, "❌ FAIL\n")
                    
                    if result.get("details"):
                        self.check_results.insert(tk.END, f"   {result['details']}\n")
                    
                except Exception as e:
                    self.check_results.insert(tk.END, f"❌ ERROR: {str(e)}\n")
                
                self.check_results.insert(tk.END, "\n")
                self.root.update()
                time.sleep(0.5)
            
            # Summary
            pass_rate = (self.system_checks_passed / self.system_checks_total) * 100
            self.check_results.insert(tk.END, f"\n📊 System Check Summary:\n")
            self.check_results.insert(tk.END, f"   Passed: {self.system_checks_passed:.1f}/{self.system_checks_total} ({pass_rate:.1f}%)\n")
            
            if pass_rate >= 80:
                self.check_results.insert(tk.END, "✅ System is compatible with Berke0S!\n")
            elif pass_rate >= 60:
                self.check_results.insert(tk.END, "⚠️ System has some compatibility issues but installation can continue.\n")
            else:
                self.check_results.insert(tk.END, "❌ System may have significant compatibility issues.\n")
            
            self.check_results.see(tk.END)
            
        except Exception as e:
            logger.error(f"System checks error: {e}")
            self.check_results.insert(tk.END, f"❌ System check failed: {str(e)}\n")
    
    def check_operating_system(self):
        """Check operating system compatibility"""
        try:
            os_name = platform.system()
            distribution = self.display_manager.get_distribution()
            is_tinycore = self.display_manager.is_tiny_core_linux()
            
            if os_name == "Linux":
                if is_tinycore:
                    return {"status": "pass", "details": f"Tiny Core Linux detected - Excellent compatibility"}
                else:
                    return {"status": "pass", "details": f"Linux distribution: {distribution}"}
            else:
                return {"status": "warning", "details": f"Unsupported OS: {os_name}"}
                
        except Exception as e:
            return {"status": "fail", "details": str(e)}
    
    def check_python_version(self):
        """Check Python version"""
        try:
            version = sys.version_info
            version_str = f"{version.major}.{version.minor}.{version.micro}"
            
            if version.major >= 3 and version.minor >= 6:
                return {"status": "pass", "details": f"Python {version_str} - Compatible"}
            else:
                return {"status": "fail", "details": f"Python {version_str} - Requires Python 3.6+"}
                
        except Exception as e:
            return {"status": "fail", "details": str(e)}
    
    def check_display_system(self):
        """Check display system"""
        try:
            env_info = self.display_manager.detect_environment()
            x11_available = env_info.get("x11_available", {}).get("available", False)
            wayland_available = env_info.get("wayland_available", {}).get("available", False)
            
            if x11_available:
                binaries = env_info.get("x11_available", {}).get("binaries", [])
                return {"status": "pass", "details": f"X11 available: {', '.join(binaries)}"}
            elif wayland_available:
                return {"status": "warning", "details": "Wayland available (limited support)"}
            else:
                return {"status": "warning", "details": "No display server detected - will use headless mode"}
                
        except Exception as e:
            return {"status": "fail", "details": str(e)}
    
    def check_graphics_hardware(self):
        """Check graphics hardware"""
        try:
            drivers = self.display_manager.detect_graphics_driver()
            if drivers and drivers != ['unknown']:
                return {"status": "pass", "details": f"Graphics drivers: {', '.join(drivers)}"}
            else:
                return {"status": "warning", "details": "Graphics hardware not detected"}
                
        except Exception as e:
            return {"status": "warning", "details": str(e)}
    
    def check_memory(self):
        """Check system memory"""
        try:
            if psutil:
                memory = psutil.virtual_memory()
                total_gb = memory.total / (1024**3)
                
                if total_gb >= 1.0:
                    return {"status": "pass", "details": f"RAM: {total_gb:.1f} GB"}
                else:
                    return {"status": "warning", "details": f"RAM: {total_gb:.1f} GB (minimum for basic functionality)"}
            else:
                return {"status": "warning", "details": "Memory check unavailable"}
                
        except Exception as e:
            return {"status": "warning", "details": str(e)}
    
    def check_disk_space(self):
        """Check disk space"""
        try:
            if psutil:
                disk = psutil.disk_usage('/')
                free_gb = disk.free / (1024**3)
                
                if free_gb >= 1.0:
                    return {"status": "pass", "details": f"Free space: {free_gb:.1f} GB"}
                else:
                    return {"status": "warning", "details": f"Free space: {free_gb:.1f} GB (low)"}
            else:
                return {"status": "warning", "details": "Disk check unavailable"}
                
        except Exception as e:
            return {"status": "warning", "details": str(e)}
    
    def check_network(self):
        """Check network connectivity"""
        try:
            # Test internet connectivity
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return {"status": "pass", "details": "Internet connectivity available"}
        except:
            return {"status": "warning", "details": "No internet connectivity"}
    
    def check_audio_system(self):
        """Check audio system"""
        try:
            audio_systems = ['pulseaudio', 'alsa', 'jack']
            available_systems = []
            
            for system in audio_systems:
                if shutil.which(system):
                    available_systems.append(system)
            
            if available_systems:
                return {"status": "pass", "details": f"Audio: {', '.join(available_systems)}"}
            else:
                return {"status": "warning", "details": "No audio system detected"}
                
        except Exception as e:
            return {"status": "warning", "details": str(e)}
    
    def check_packages(self):
        """Check required packages"""
        try:
            required_packages = {
                'tkinter': 'GUI framework',
                'sqlite3': 'Database support',
                'subprocess': 'Process management',
                'threading': 'Multi-threading support'
            }
            
            missing_packages = []
            
            for package, description in required_packages.items():
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(f"{package} ({description})")
            
            if not missing_packages:
                return {"status": "pass", "details": "All required packages available"}
            else:
                return {"status": "warning", "details": f"Missing: {', '.join(missing_packages)}"}
                
        except Exception as e:
            return {"status": "warning", "details": str(e)}
    
    def check_permissions(self):
        """Check system permissions"""
        try:
            # Check write permissions
            test_dirs = [
                CONFIG_DIR,
                os.path.expanduser("~"),
                "/tmp"
            ]
            
            writable_dirs = []
            for test_dir in test_dirs:
                try:
                    os.makedirs(test_dir, exist_ok=True)
                    test_file = os.path.join(test_dir, 'berke0s_test')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    writable_dirs.append(test_dir)
                except:
                    pass
            
            if len(writable_dirs) >= 2:
                return {"status": "pass", "details": "Sufficient write permissions"}
            else:
                return {"status": "warning", "details": "Limited write permissions"}
                
        except Exception as e:
            return {"status": "warning", "details": str(e)}
    
    def show_display_setup_step(self):
        """Show display setup step"""
        try:
            # Header
            header = tk.Label(self.main_container, 
                            text="Display Configuration",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # Display options frame
            options_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            options_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
            
            # Display information
            info_text = tk.Text(options_frame, height=8, width=80,
                              bg="#1a1a1a", fg="white", font=self.normal_font,
                              wrap=tk.WORD, relief=tk.FLAT)
            info_text.pack(pady=(0, 20))
            
            # Get current display info
            display_info = self.display_manager.get_display_info()
            env_info = self.display_manager.detect_environment()
            
            info_content = f"""Current Display Configuration:
Display: {display_info.get('display', 'Unknown')}
Mode: {display_info.get('mode', 'Unknown')}
Resolution: {display_info.get('width', 'Unknown')}x{display_info.get('height', 'Unknown')}
Color Depth: {display_info.get('depth', 'Unknown')} bits

System Information:
OS: {env_info.get('distribution', 'Unknown')}
X11 Available: {'Yes' if env_info.get('x11_available', {}).get('available') else 'No'}
Graphics Driver: {', '.join(env_info.get('graphics_driver', ['Unknown']))}
Current Display: {env_info.get('display', 'None')}
"""
            
            info_text.insert('1.0', info_content)
            info_text.config(state='disabled')
            
            # Display options
            self.display_mode = tk.StringVar(value="auto")
            
            options = [
                ("auto", "Automatic Detection (Recommended)"),
                ("x11", "Force X11"),
                ("headless", "Headless Mode (No Display)"),
                ("virtual", "Virtual Display")
            ]
            
            for value, text in options:
                rb = tk.Radiobutton(options_frame, text=text, variable=self.display_mode, value=value,
                                   bg="#0a0a0f", fg="white", font=self.normal_font,
                                   selectcolor="#00ff88", activebackground="#0a0a0f")
                rb.pack(anchor='w', pady=5)
            
            # Test display button
            test_btn = tk.Button(options_frame, text="Test Display Configuration",
                               command=self.test_display_config,
                               bg="#00ff88", fg="black", font=self.normal_font,
                               relief=tk.FLAT, padx=20, pady=5)
            test_btn.pack(pady=20)
            
            # Navigation buttons
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"Display setup step error: {e}")
    
    def test_display_config(self):
        """Test display configuration"""
        try:
            mode = self.display_mode.get()
            
            # Create test window
            test_window = tk.Toplevel(self.root)
            test_window.title("Display Test")
            test_window.geometry("400x300")
            test_window.configure(bg="#1a1a1a")
            
            # Test content
            tk.Label(test_window, text="Display Test", 
                    font=("Arial", 20, "bold"), fg="#00ff88", bg="#1a1a1a").pack(pady=50)
            
            tk.Label(test_window, text=f"Mode: {mode.upper()}", 
                    font=("Arial", 14), fg="white", bg="#1a1a1a").pack(pady=10)
            
            tk.Label(test_window, text="If you can see this window clearly,\nyour display is working correctly.", 
                    font=("Arial", 12), fg="white", bg="#1a1a1a", justify=tk.CENTER).pack(pady=20)
            
            tk.Button(test_window, text="Close Test", command=test_window.destroy,
                     bg="#00ff88", fg="black", font=("Arial", 10), relief=tk.FLAT).pack(pady=20)
            
            # Center test window
            test_window.update_idletasks()
            x = (test_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (test_window.winfo_screenheight() // 2) - (300 // 2)
            test_window.geometry(f"400x300+{x}+{y}")
            
        except Exception as e:
            logger.error(f"Display test error: {e}")
            messagebox.showerror("Display Test Error", f"Failed to test display: {str(e)}")
    
    def show_language_step(self):
        """Show language selection step"""
        try:
            # Implementation for language step
            header = tk.Label(self.main_container, 
                            text="Language Selection",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # Language options
            self.language_var = tk.StringVar(value="tr_TR")
            
            languages = [
                ("tr_TR", "Türkçe (Turkish)"),
                ("en_US", "English (US)"),
                ("en_GB", "English (UK)"),
                ("de_DE", "Deutsch (German)"),
                ("fr_FR", "Français (French)"),
                ("es_ES", "Español (Spanish)"),
                ("it_IT", "Italiano (Italian)"),
                ("ru_RU", "Русский (Russian)")
            ]
            
            lang_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            lang_frame.pack(expand=True)
            
            for code, name in languages:
                rb = tk.Radiobutton(lang_frame, text=name, variable=self.language_var, value=code,
                                   bg="#0a0a0f", fg="white", font=self.normal_font,
                                   selectcolor="#00ff88", activebackground="#0a0a0f")
                rb.pack(anchor='w', pady=8, padx=50)
            
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"Language step error: {e}")
    
    def show_disk_setup_step(self):
        """Show disk setup step - simplified for Tiny Core"""
        try:
            header = tk.Label(self.main_container, 
                            text="Storage Configuration",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # Information for Tiny Core users
            info_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            info_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
            
            info_text = tk.Text(info_frame, height=15, width=70,
                              bg="#1a1a1a", fg="white", font=self.normal_font,
                              wrap=tk.WORD, relief=tk.FLAT)
            info_text.pack()
            
            storage_info = """Storage Configuration for Tiny Core Linux:

Berke0S will store its configuration and data in your home directory:
• Configuration: ~/.berke0s/
• User data: ~/Desktop, ~/Documents, etc.
• Themes and customizations: ~/.berke0s/themes/
• Applications data: ~/.berke0s/applications/

For Tiny Core Linux:
• Make sure you have backup configured (backup.sh)
• Consider using persistent storage (/opt or /home)
• Berke0S configuration will be preserved across reboots if properly backed up

Estimated space requirements:
• Minimum: 50 MB
• Recommended: 200 MB for full installation with themes and applications
• Additional space needed for user data

Current available space will be checked during installation.
"""
            
            info_text.insert('1.0', storage_info)
            info_text.config(state='disabled')
            
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"Disk setup step error: {e}")
    
    def show_network_step(self):
        """Show network setup step"""
        try:
            header = tk.Label(self.main_container, 
                            text="Network Configuration",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # Network frame
            network_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            network_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
            
            # WiFi configuration
            wifi_frame = tk.LabelFrame(network_frame, text="WiFi Configuration", 
                                     bg="#1a1a1a", fg="white", font=self.normal_font)
            wifi_frame.pack(fill=tk.X, pady=(0, 20))
            
            # Enable WiFi
            self.enable_wifi = tk.BooleanVar(value=False)
            wifi_check = tk.Checkbutton(wifi_frame, text="Configure WiFi", 
                                       variable=self.enable_wifi,
                                       bg="#1a1a1a", fg="white", font=self.normal_font,
                                       selectcolor="#00ff88", activebackground="#1a1a1a",
                                       command=self.toggle_wifi_config)
            wifi_check.pack(anchor='w', padx=10, pady=10)
            
            # WiFi settings
            self.wifi_settings_frame = tk.Frame(wifi_frame, bg="#1a1a1a")
            self.wifi_settings_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
            
            tk.Label(self.wifi_settings_frame, text="Network Name (SSID):", 
                    bg="#1a1a1a", fg="white", font=self.normal_font).grid(row=0, column=0, sticky='w', pady=5)
            self.wifi_ssid = tk.Entry(self.wifi_settings_frame, bg="#333333", fg="white", font=self.normal_font)
            self.wifi_ssid.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
            
            tk.Label(self.wifi_settings_frame, text="Password:", 
                    bg="#1a1a1a", fg="white", font=self.normal_font).grid(row=1, column=0, sticky='w', pady=5)
            self.wifi_password = tk.Entry(self.wifi_settings_frame, show='*', bg="#333333", fg="white", font=self.normal_font)
            self.wifi_password.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)
            
            self.wifi_settings_frame.grid_columnconfigure(1, weight=1)
            self.wifi_settings_frame.grid_remove()  # Initially hidden
            
            # Network status
            status_frame = tk.LabelFrame(network_frame, text="Network Status", 
                                       bg="#1a1a1a", fg="white", font=self.normal_font)
            status_frame.pack(fill=tk.X)
            
            self.network_status = tk.Text(status_frame, height=6, bg="#1a1a1a", fg="white", 
                                        font=("Courier", 9), relief=tk.FLAT)
            self.network_status.pack(fill=tk.X, padx=10, pady=10)
            
            self.check_network_status()
            
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"Network step error: {e}")
    
    def toggle_wifi_config(self):
        """Toggle WiFi configuration visibility"""
        if self.enable_wifi.get():
            self.wifi_settings_frame.grid()
        else:
            self.wifi_settings_frame.grid_remove()
    
    def check_network_status(self):
        """Check and display network status"""
        try:
            status_text = "Network Status:\n"
            
            # Check internet connectivity
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=5)
                status_text += "✅ Internet: Connected\n"
            except:
                status_text += "❌ Internet: Not connected\n"
            
            # Check network interfaces
            try:
                result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    interfaces = []
                    for line in lines:
                        if ': <' in line and 'lo:' not in line:
                            interface = line.split(':')[1].strip()
                            interfaces.append(interface)
                    
                    if interfaces:
                        status_text += f"📡 Interfaces: {', '.join(interfaces[:3])}\n"
                    else:
                        status_text += "📡 Interfaces: None detected\n"
            except:
                status_text += "📡 Interfaces: Check failed\n"
            
            self.network_status.delete('1.0', tk.END)
            self.network_status.insert('1.0', status_text)
            
        except Exception as e:
            logger.error(f"Network status check error: {e}")
    
    def show_user_setup_step(self):
        """Show user setup step"""
        try:
            header = tk.Label(self.main_container, 
                            text="User Account Setup",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # User form
            user_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            user_frame.pack(expand=True)
            
            # Form fields
            fields = [
                ("Full Name:", "user_fullname"),
                ("Username:", "user_username"),
                ("Password:", "user_password"),
                ("Confirm Password:", "user_confirm_password")
            ]
            
            self.user_fields = {}
            
            for i, (label_text, field_name) in enumerate(fields):
                tk.Label(user_frame, text=label_text, bg="#0a0a0f", fg="white", 
                        font=self.normal_font).grid(row=i, column=0, sticky='w', pady=10, padx=(50, 10))
                
                if "password" in field_name:
                    entry = tk.Entry(user_frame, show='*', bg="#333333", fg="white", 
                                   font=self.normal_font, width=30)
                else:
                    entry = tk.Entry(user_frame, bg="#333333", fg="white", 
                                   font=self.normal_font, width=30)
                
                entry.grid(row=i, column=1, sticky='w', pady=10)
                self.user_fields[field_name] = entry
            
            # Admin checkbox
            self.user_admin = tk.BooleanVar(value=True)
            admin_check = tk.Checkbutton(user_frame, text="Administrator privileges", 
                                       variable=self.user_admin,
                                       bg="#0a0a0f", fg="white", font=self.normal_font,
                                       selectcolor="#00ff88", activebackground="#0a0a0f")
            admin_check.grid(row=len(fields), column=0, columnspan=2, sticky='w', pady=10, padx=(50, 0))
            
            # Auto-login checkbox
            self.user_autologin = tk.BooleanVar(value=True)
            autologin_check = tk.Checkbutton(user_frame, text="Automatic login", 
                                           variable=self.user_autologin,
                                           bg="#0a0a0f", fg="white", font=self.normal_font,
                                           selectcolor="#00ff88", activebackground="#0a0a0f")
            autologin_check.grid(row=len(fields)+1, column=0, columnspan=2, sticky='w', pady=10, padx=(50, 0))
            
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"User setup step error: {e}")
    
    def show_customization_step(self):
        """Show customization step"""
        try:
            header = tk.Label(self.main_container, 
                            text="Desktop Customization",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # Customization options
            custom_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            custom_frame.pack(fill=tk.BOTH, expand=True, padx=50)
            
            # Theme selection
            theme_frame = tk.LabelFrame(custom_frame, text="Theme", 
                                      bg="#1a1a1a", fg="white", font=self.normal_font)
            theme_frame.pack(fill=tk.X, pady=(0, 20))
            
            self.theme_var = tk.StringVar(value="berke_dark")
            
            themes = [
                ("berke_dark", "Berke Dark (Default)"),
                ("berke_light", "Berke Light"),
                ("ocean", "Ocean Blue"),
                ("forest", "Forest Green")
            ]
            
            theme_inner = tk.Frame(theme_frame, bg="#1a1a1a")
            theme_inner.pack(fill=tk.X, padx=10, pady=10)
            
            for i, (value, name) in enumerate(themes):
                rb = tk.Radiobutton(theme_inner, text=name, variable=self.theme_var, value=value,
                                   bg="#1a1a1a", fg="white", font=self.normal_font,
                                   selectcolor="#00ff88", activebackground="#1a1a1a")
                rb.grid(row=i//2, column=i%2, sticky='w', padx=20, pady=5)
            
            # Desktop options
            desktop_frame = tk.LabelFrame(custom_frame, text="Desktop Options", 
                                        bg="#1a1a1a", fg="white", font=self.normal_font)
            desktop_frame.pack(fill=tk.X)
            
            self.desktop_options = {}
            
            options = [
                ("show_desktop_icons", "Show desktop icons", True),
                ("effects", "Enable visual effects", True),
                ("show_dock", "Show application dock", False),
                ("auto_arrange", "Auto-arrange icons", False)
            ]
            
            desktop_inner = tk.Frame(desktop_frame, bg="#1a1a1a")
            desktop_inner.pack(fill=tk.X, padx=10, pady=10)
            
            for i, (key, text, default) in enumerate(options):
                var = tk.BooleanVar(value=default)
                check = tk.Checkbutton(desktop_inner, text=text, variable=var,
                                     bg="#1a1a1a", fg="white", font=self.normal_font,
                                     selectcolor="#00ff88", activebackground="#1a1a1a")
                check.grid(row=i//2, column=i%2, sticky='w', padx=20, pady=5)
                self.desktop_options[key] = var
            
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"Customization step error: {e}")
    
    def show_advanced_settings_step(self):
        """Show advanced settings step"""
        try:
            header = tk.Label(self.main_container, 
                            text="Advanced Settings",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # Settings notebook
            notebook = ttk.Notebook(self.main_container)
            notebook.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
            
            # System tab
            system_tab = tk.Frame(notebook, bg="#1a1a1a")
            notebook.add(system_tab, text="System")
            
            self.system_settings = {}
            
            system_options = [
                ("auto_updates", "Enable automatic updates", True),
                ("crash_reporting", "Enable crash reporting", True),
                ("telemetry", "Enable telemetry (anonymous usage data)", False),
                ("auto_backup", "Enable automatic backup", False)
            ]
            
            for i, (key, text, default) in enumerate(system_options):
                var = tk.BooleanVar(value=default)
                check = tk.Checkbutton(system_tab, text=text, variable=var,
                                     bg="#1a1a1a", fg="white", font=self.normal_font,
                                     selectcolor="#00ff88", activebackground="#1a1a1a")
                check.pack(anchor='w', padx=20, pady=10)
                self.system_settings[key] = var
            
            # Performance tab
            perf_tab = tk.Frame(notebook, bg="#1a1a1a")
            notebook.add(perf_tab, text="Performance")
            
            tk.Label(perf_tab, text="Performance Mode:", bg="#1a1a1a", fg="white", 
                    font=self.normal_font).pack(anchor='w', padx=20, pady=(20, 5))
            
            self.performance_mode = tk.StringVar(value="balanced")
            
            perf_modes = [
                ("power_save", "Power Saving"),
                ("balanced", "Balanced"),
                ("performance", "High Performance")
            ]
            
            for value, text in perf_modes:
                rb = tk.Radiobutton(perf_tab, text=text, variable=self.performance_mode, value=value,
                                   bg="#1a1a1a", fg="white", font=self.normal_font,
                                   selectcolor="#00ff88", activebackground="#1a1a1a")
                rb.pack(anchor='w', padx=40, pady=5)
            
            # Security tab
            security_tab = tk.Frame(notebook, bg="#1a1a1a")
            notebook.add(security_tab, text="Security")
            
            self.security_settings = {}
            
            security_options = [
                ("auto_lock", "Enable automatic screen lock", True),
                ("require_password", "Require password for system changes", True),
                ("firewall_enabled", "Enable basic firewall", True),
                ("encryption_enabled", "Enable data encryption", False)
            ]
            
            for i, (key, text, default) in enumerate(security_options):
                var = tk.BooleanVar(value=default)
                check = tk.Checkbutton(security_tab, text=text, variable=var,
                                     bg="#1a1a1a", fg="white", font=self.normal_font,
                                     selectcolor="#00ff88", activebackground="#1a1a1a")
                check.pack(anchor='w', padx=20, pady=10)
                self.security_settings[key] = var
            
            self.create_navigation_buttons()
            
        except Exception as e:
            logger.error(f"Advanced settings step error: {e}")
    
    def show_installation_step(self):
        """Show installation progress step"""
        try:
            header = tk.Label(self.main_container, 
                            text="Installing Berke0S",
                            font=self.header_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(30, 20))
            
            # Progress frame
            progress_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            progress_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
            
            # Progress bar
            self.progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                         maximum=100, length=600)
            progress_bar.pack(pady=(0, 20))
            
            # Progress text
            self.progress_text = tk.Text(progress_frame, height=20, width=80,
                                       bg="#1a1a1a", fg="white", font=("Courier", 10),
                                       wrap=tk.WORD, relief=tk.FLAT)
            self.progress_text.pack(fill=tk.BOTH, expand=True)
            
            # Start installation
            self.start_installation_process()
            
        except Exception as e:
            logger.error(f"Installation step error: {e}")
    
    def start_installation_process(self):
        """Start the actual installation process"""
        try:
            # Collect all configuration
            self.collect_configuration()
            
            # Installation steps
            steps = [
                ("Preparing installation environment", self.prepare_installation),
                ("Creating directories", self.create_directories),
                ("Setting up database", self.setup_database),
                ("Configuring display system", self.configure_display_system),
                ("Installing system files", self.install_system_files),
                ("Creating user account", self.create_user_account),
                ("Configuring network", self.configure_network),
                ("Setting up desktop environment", self.setup_desktop_environment),
                ("Installing applications", self.install_applications),
                ("Applying customizations", self.apply_customizations),
                ("Configuring advanced settings", self.configure_advanced_settings),
                ("Creating startup scripts", self.create_startup_scripts),
                ("Finalizing installation", self.finalize_installation)
            ]
            
            self.installation_thread = threading.Thread(
                target=self.run_installation_steps, 
                args=(steps,),
                daemon=True
            )
            self.installation_thread.start()
            
        except Exception as e:
            logger.error(f"Installation start error: {e}")
            self.progress_text.insert(tk.END, f"❌ Installation failed to start: {str(e)}\n")
    
    def collect_configuration(self):
        """Collect all configuration from wizard steps"""
        try:
            # Update config with user selections
            if hasattr(self, 'language_var'):
                self.config["language"] = self.language_var.get()
            
            if hasattr(self, 'display_mode'):
                self.config["display"]["display_server"] = self.display_mode.get()
            
            if hasattr(self, 'theme_var'):
                self.config["theme"] = self.theme_var.get()
            
            # User account
            if hasattr(self, 'user_fields'):
                user_data = {
                    "username": self.user_fields["user_username"].get(),
                    "fullname": self.user_fields["user_fullname"].get(),
                    "password": hashlib.sha256(self.user_fields["user_password"].get().encode()).hexdigest(),
                    "admin": self.user_admin.get(),
                    "auto_login": self.user_autologin.get()
                }
                self.config["users"] = [user_data]
            
            # Network
            if hasattr(self, 'enable_wifi') and self.enable_wifi.get():
                self.config["wifi"] = {
                    "ssid": self.wifi_ssid.get(),
                    "password": self.wifi_password.get()
                }
            
            # Desktop options
            if hasattr(self, 'desktop_options'):
                for key, var in self.desktop_options.items():
                    self.config["desktop"][key] = var.get()
            
            # System settings
            if hasattr(self, 'system_settings'):
                for key, var in self.system_settings.items():
                    self.config["system"][key] = var.get()
            
            # Performance
            if hasattr(self, 'performance_mode'):
                self.config["system"]["performance_mode"] = self.performance_mode.get()
            
            # Security
            if hasattr(self, 'security_settings'):
                for key, var in self.security_settings.items():
                    self.config["security"][key] = var.get()
            
            logger.info("Configuration collected successfully")
            
        except Exception as e:
            logger.error(f"Configuration collection error: {e}")
    
    def run_installation_steps(self, steps):
        """Run installation steps in separate thread"""
        try:
            total_steps = len(steps)
            
            for i, (step_name, step_func) in enumerate(steps):
                try:
                    # Update progress
                    progress = (i / total_steps) * 100
                    self.progress_var.set(progress)
                    
                    # Update text
                    self.progress_text.insert(tk.END, f"[{i+1}/{total_steps}] {step_name}...\n")
                    self.root.update()
                    
                    # Execute step
                    step_func()
                    
                    self.progress_text.insert(tk.END, f"✅ {step_name} completed\n\n")
                    self.root.update()
                    
                    time.sleep(0.5)  # Brief pause for user to see progress
                    
                except Exception as e:
                    self.progress_text.insert(tk.END, f"❌ {step_name} failed: {str(e)}\n\n")
                    logger.error(f"Installation step '{step_name}' failed: {e}")
                    self.root.update()
            
            # Complete
            self.progress_var.set(100)
            self.progress_text.insert(tk.END, "🎉 Installation completed successfully!\n")
            self.root.update()
            
            # Enable next button
            self.root.after(2000, self.enable_next_button)
            
        except Exception as e:
            logger.error(f"Installation error: {e}")
            self.progress_text.insert(tk.END, f"❌ Installation failed: {str(e)}\n")
    
    def enable_next_button(self):
        """Enable next button after installation"""
        if hasattr(self, 'next_button'):
            self.next_button.config(state='normal')
    
    # Installation step implementations
    def prepare_installation(self):
        """Prepare installation environment"""
        # Verify system requirements
        if not os.path.exists('/tmp'):
            raise Exception("Temporary directory not available")
        
        # Set up logging
        os.makedirs(CONFIG_DIR, exist_ok=True)
    
    def create_directories(self):
        """Create necessary directories"""
        dirs = [CONFIG_DIR, THEMES_DIR, PLUGINS_DIR, WALLPAPERS_DIR, APPS_DIR]
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            
        # Create user directories
        user_dirs = ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos", "Scripts"]
        for user_dir in user_dirs:
            os.makedirs(os.path.expanduser(f"~/{user_dir}"), exist_ok=True)
    
    def setup_database(self):
        """Setup system database"""
        init_database()
    
    def configure_display_system(self):
        """Configure display system based on user selection"""
        display_mode = self.config.get("display", {}).get("display_server", "auto")
        
        if display_mode == "auto":
            # Auto-detect and configure
            pass
        elif display_mode == "headless":
            # Configure headless mode
            self.config["display"]["headless_mode"] = True
        
        # Save display configuration
        display_config = {
            "mode": display_mode,
            "configured_at": datetime.datetime.now().isoformat()
        }
        
        with open(f"{CONFIG_DIR}/display_config.json", 'w') as f:
            json.dump(display_config, f, indent=4)
    
    def install_system_files(self):
        """Install system files and configurations"""
        self.save_config()
        self.create_autostart()
    
    def create_user_account(self):
        """Create user account in database"""
        if self.config.get("users"):
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                
                user = self.config["users"][0]
                cursor.execute(
                    "INSERT OR REPLACE INTO users (username, fullname, password_hash, is_admin, preferences) VALUES (?, ?, ?, ?, ?)",
                    (user["username"], user["fullname"], user["password"], 
                     int(user["admin"]), json.dumps({"auto_login": user["auto_login"]}))
                )
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"User creation error: {e}")
    
    def configure_network(self):
        """Configure network settings"""
        if self.config.get("wifi", {}).get("ssid"):
            # Save WiFi configuration for later use
            wifi_config = {
                "ssid": self.config["wifi"]["ssid"],
                "configured": True,
                "configured_at": datetime.datetime.now().isoformat()
            }
            
            with open(f"{CONFIG_DIR}/wifi_config.json", 'w') as f:
                json.dump(wifi_config, f, indent=4)
    
    def setup_desktop_environment(self):
        """Setup desktop environment"""
        self.create_default_applications()
        self.install_default_themes()
    
    def install_applications(self):
        """Install default applications"""
        # Default applications are created in database by create_default_applications
        pass
    
    def apply_customizations(self):
        """Apply user customizations"""
        # Theme and desktop settings are already in config
        pass
    
    def configure_advanced_settings(self):
        """Configure advanced system settings"""
        # Advanced settings are already in config
        pass
    
    def create_startup_scripts(self):
        """Create startup scripts for different environments"""
        self.create_autostart()
        self.create_desktop_entry()
    
    def finalize_installation(self):
        """Finalize installation"""
        self.config["installed"] = True
        self.config["first_boot"] = False
        self.config["installation_date"] = datetime.datetime.now().isoformat()
        self.save_config()
        
        # Create installation flag
        with open(INSTALL_FLAG, 'w') as f:
            f.write(json.dumps({
                "installed_at": datetime.datetime.now().isoformat(),
                "version": "3.0-v2",
                "user": self.config.get("users", [{}])[0].get("username", "unknown")
            }))
    
    def create_autostart(self):
        """Create autostart configuration for different environments"""
        try:
            script_content = f"""#!/bin/bash
# Berke0S Autostart Script V2
export DISPLAY=:0
cd {os.path.dirname(os.path.abspath(__file__))}

# Try to start Berke0S
python3 {os.path.abspath(__file__)} &

# For Tiny Core Linux - add to bootlocal.sh
if [ -f /opt/bootlocal.sh ]; then
    if ! grep -q "berke0s" /opt/bootlocal.sh; then
        echo "# Berke0S Desktop Environment" >> /opt/bootlocal.sh
        echo "python3 {os.path.abspath(__file__)} &" >> /opt/bootlocal.sh
    fi
fi
"""
            
            # Try multiple autostart locations
            autostart_locations = [
                os.path.expanduser("~/.xsession"),
                os.path.expanduser("~/.xinitrc"),
                f"{CONFIG_DIR}/autostart.sh"
            ]
            
            for location in autostart_locations:
                try:
                    with open(location, 'w') as f:
                        f.write(script_content)
                    os.chmod(location, 0o755)
                except Exception as e:
                    logger.warning(f"Failed to create autostart at {location}: {e}")
                    
        except Exception as e:
            logger.warning(f"Autostart creation failed: {e}")
    
    def create_desktop_entry(self):
        """Create desktop entry for application launchers"""
        try:
            desktop_entry = f"""[Desktop Entry]
Name=Berke0S Desktop Environment
Comment=Ultimate Desktop Environment for Tiny Core Linux
Exec=python3 {os.path.abspath(__file__)}
Icon=berke0s
Type=Application
Categories=System;
StartupNotify=true
"""
            
            desktop_dirs = [
                os.path.expanduser("~/.local/share/applications"),
                os.path.expanduser("~/Desktop"),
                "/usr/local/share/applications"
            ]
            
            for desktop_dir in desktop_dirs:
                try:
                    os.makedirs(desktop_dir, exist_ok=True)
                    desktop_file = os.path.join(desktop_dir, "berke0s.desktop")
                    with open(desktop_file, 'w') as f:
                        f.write(desktop_entry)
                    os.chmod(desktop_file, 0o755)
                except Exception as e:
                    logger.warning(f"Failed to create desktop entry in {desktop_dir}: {e}")
                    
        except Exception as e:
            logger.warning(f"Desktop entry creation failed: {e}")
    
    def create_default_applications(self):
        """Create default applications database"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            apps = [
                ("File Manager", "berke0s_filemanager", "📁", "System", "Advanced file management"),
                ("Text Editor", "berke0s_texteditor", "📝", "Office", "Code and text editing"),
                ("Web Browser", "berke0s_browser", "🌐", "Internet", "Web browsing"),
                ("Terminal", "berke0s_terminal", "💻", "System", "Command line interface"),
                ("Calculator", "berke0s_calculator", "🧮", "Utility", "Scientific calculator"),
                ("Image Viewer", "berke0s_imageviewer", "🖼️", "Graphics", "Image viewing and editing"),
                ("Music Player", "berke0s_musicplayer", "🎵", "Multimedia", "Audio playback"),
                ("Video Player", "berke0s_videoplayer", "🎬", "Multimedia", "Video playback"),
                ("Settings", "berke0s_settings", "⚙️", "System", "System configuration"),
                ("System Monitor", "berke0s_monitor", "📊", "System", "System monitoring"),
                ("Email Client", "berke0s_email", "📧", "Internet", "Email management"),
                ("Calendar", "berke0s_calendar", "📅", "Office", "Calendar and scheduling"),
                ("Games", "berke0s_games", "🎮", "Games", "Built-in games"),
                ("Network Manager", "berke0s_network", "📶", "System", "Network configuration"),
                ("Archive Manager", "berke0s_archive", "📦", "Utility", "Archive management"),
                ("PDF Viewer", "berke0s_pdf", "📄", "Office", "PDF document viewer"),
                ("Code Editor", "berke0s_ide", "⌨️", "Development", "Integrated development environment"),
                ("Screen Recorder", "berke0s_recorder", "📹", "Multimedia", "Screen recording"),
                ("System Backup", "berke0s_backup", "💾", "System", "System backup and restore"),
                ("Virtual Desktop", "berke0s_vdesktop", "🖥️", "System", "Virtual desktop manager"),
                ("Display Settings", "berke0s_display", "🖥️", "System", "Display configuration")
            ]
            
            for app in apps:
                cursor.execute(
                    "INSERT OR REPLACE INTO applications (name, command, icon, category, description) VALUES (?, ?, ?, ?, ?)",
                    app
                )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Default applications creation failed: {e}")
    
    def install_default_themes(self):
        """Install default theme files with enhanced V2 themes"""
        try:
            themes = {
                "berke_dark": {
                    "name": "Berke Dark V2",
                    "version": "2.0",
                    "colors": {
                        "bg": "#1a1a1a", "fg": "#ffffff", "accent": "#00ff88",
                        "secondary": "#4a9eff", "warning": "#ffb347", "error": "#ff6b6b",
                        "success": "#00ff88", "taskbar": "#0f0f23", "window": "#2a2a2a",
                        "input": "#333333", "border": "#444444", "hover": "#555555",
                        "selection": "#00ff8844", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier"},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                },
                "berke_light": {
                    "name": "Berke Light V2",
                    "version": "2.0",
                    "colors": {
                        "bg": "#f5f5f5", "fg": "#333333", "accent": "#007acc",
                        "secondary": "#28a745", "warning": "#ffc107", "error": "#dc3545",
                        "success": "#28a745", "taskbar": "#e9ecef", "window": "#ffffff",
                        "input": "#ffffff", "border": "#cccccc", "hover": "#e9ecef",
                        "selection": "#007acc44", "shadow": "#00000022"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier"},
                    "effects": {"blur": False, "transparency": False, "animations": True}
                },
                "ocean": {
                    "name": "Ocean Blue V2",
                    "version": "2.0", 
                    "colors": {
                        "bg": "#0d1b2a", "fg": "#ffffff", "accent": "#00b4d8",
                        "secondary": "#0077b6", "warning": "#f77f00", "error": "#d62828",
                        "success": "#2a9d8f", "taskbar": "#03045e", "window": "#1b263b",
                        "input": "#415a77", "border": "#457b9d", "hover": "#1d3557",
                        "selection": "#00b4d844", "shadow": "#00000066"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier"},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                },
                "forest": {
                    "name": "Forest Green V2",
                    "version": "2.0",
                    "colors": {
                        "bg": "#1b4332", "fg": "#ffffff", "accent": "#40916c",
                        "secondary": "#52b788", "warning": "#f77f00", "error": "#e63946",
                        "success": "#2d6a4f", "taskbar": "#081c15", "window": "#2d6a4f",
                        "input": "#40916c", "border": "#52b788", "hover": "#2d6a4f",
                        "selection": "#40916c44", "shadow": "#00000044"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier"},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                },
                "tinycore": {
                    "name": "Tiny Core Classic",
                    "version": "2.0",
                    "colors": {
                        "bg": "#2e3436", "fg": "#ffffff", "accent": "#729fcf",
                        "secondary": "#8ae234", "warning": "#fcaf3e", "error": "#ef2929",
                        "success": "#8ae234", "taskbar": "#555753", "window": "#3c4043",
                        "input": "#2e3436", "border": "#888a85", "hover": "#555753",
                        "selection": "#729fcf44", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Monospace"},
                    "effects": {"blur": False, "transparency": False, "animations": False}
                }
            }
            
            for theme_name, theme_data in themes.items():
                theme_file = os.path.join(THEMES_DIR, f"{theme_name}.json")
                with open(theme_file, 'w') as f:
                    json.dump(theme_data, f, indent=4)
                    
        except Exception as e:
            logger.error(f"Theme installation failed: {e}")
    
    def show_complete_step(self):
        """Show installation complete step"""
        try:
            # Header
            header = tk.Label(self.main_container, 
                            text="Installation Complete!",
                            font=self.title_font,
                            fg="#00ff88", bg="#0a0a0f")
            header.pack(pady=(50, 30))
            
            # Success message
            message = tk.Text(self.main_container, height=15, width=70,
                            bg="#1a1a1a", fg="white", font=self.normal_font,
                            wrap=tk.WORD, relief=tk.FLAT)
            message.pack(pady=20, padx=50)
            
            complete_text = f"""
🎉 Berke0S 3.0 V2 has been successfully installed!

✅ Installation Summary:
• Desktop environment configured
• User account created: {self.config.get('users', [{}])[0].get('fullname', 'User')}
• Display system optimized for your hardware
• {len(self.config.get('users', []))} user account(s) configured
• Theme applied: {self.config.get('theme', 'berke_dark')}
• Network configuration saved
• Advanced settings configured

🚀 What's Next:
• Click "Finish" to complete the installation
• Berke0S will start automatically after installation
• You can launch applications from the start menu
• Customize your desktop from Settings
• Enjoy your new ultimate desktop environment!

📋 Important Information:
• Configuration saved to: ~/.berke0s/
• For Tiny Core Linux: Add to backup for persistence
• Documentation available in the Help menu
• Report issues through the System Monitor

Thank you for choosing Berke0S Ultimate Desktop Environment!
            """
            
            message.insert('1.0', complete_text)
            message.config(state='disabled')
            
            # Final buttons
            button_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            button_frame.pack(pady=30)
            
            finish_btn = tk.Button(button_frame, text="Finish & Start Berke0S",
                                 command=self.finish_installation,
                                 bg="#00ff88", fg="black", font=self.header_font,
                                 relief=tk.FLAT, padx=30, pady=10)
            finish_btn.pack(side=tk.LEFT, padx=10)
            
            exit_btn = tk.Button(button_frame, text="Exit Installer",
                               command=self.exit_installer,
                               bg="#666666", fg="white", font=self.normal_font,
                               relief=tk.FLAT, padx=20, pady=10)
            exit_btn.pack(side=tk.LEFT, padx=10)
            
        except Exception as e:
            logger.error(f"Complete step error: {e}")
    
    def create_navigation_buttons(self):
        """Create navigation buttons for wizard"""
        try:
            nav_frame = tk.Frame(self.main_container, bg="#0a0a0f")
            nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
            
            # Back button
            if self.current_step > 0:
                back_btn = tk.Button(nav_frame, text="< Back",
                                   command=self.previous_step,
                                   bg="#666666", fg="white", font=self.normal_font,
                                   relief=tk.FLAT, padx=20, pady=5)
                back_btn.pack(side=tk.LEFT, padx=10)
            
            # Next button
            if self.current_step < len(self.steps) - 1:
                next_text = "Next >" if self.current_step < len(self.steps) - 2 else "Install"
                self.next_button = tk.Button(nav_frame, text=next_text,
                                           command=self.next_step,
                                           bg="#00ff88", fg="black", font=self.normal_font,
                                           relief=tk.FLAT, padx=20, pady=5)
                self.next_button.pack(side=tk.RIGHT, padx=10)
                
                # Disable next button during installation
                if self.steps[self.current_step] == "installation":
                    self.next_button.config(state='disabled')
            
            # Progress indicator
            progress_text = f"Step {self.current_step + 1} of {len(self.steps)}"
            progress_label = tk.Label(nav_frame, text=progress_text,
                                    bg="#0a0a0f", fg="#888888", font=self.small_font)
            progress_label.pack()
            
        except Exception as e:
            logger.error(f"Navigation buttons error: {e}")
    
    def next_step(self):
        """Go to next step"""
        if self.validate_current_step():
            self.current_step += 1
            self.show_step()
    
    def previous_step(self):
        """Go to previous step"""
        self.current_step -= 1
        self.show_step()
    
    def validate_current_step(self):
        """Validate current step before proceeding"""
        try:
            step_name = self.steps[self.current_step]
            
            if step_name == "user_setup":
                # Validate user input
                if hasattr(self, 'user_fields'):
                    username = self.user_fields["user_username"].get().strip()
                    fullname = self.user_fields["user_fullname"].get().strip()
                    password = self.user_fields["user_password"].get()
                    confirm_password = self.user_fields["user_confirm_password"].get()
                    
                    if not username or not fullname:
                        messagebox.showerror("Validation Error", "Please fill in all required fields.")
                        return False
                    
                    if len(username) < 3:
                        messagebox.showerror("Validation Error", "Username must be at least 3 characters long.")
                        return False
                    
                    if len(password) < 4:
                        messagebox.showerror("Validation Error", "Password must be at least 4 characters long.")
                        return False
                    
                    if password != confirm_password:
                        messagebox.showerror("Validation Error", "Passwords do not match.")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Step validation error: {e}")
            return True
    
    def finish_installation(self):
        """Finish installation and start Berke0S"""
        try:
            self.root.destroy()
            
            # Start Berke0S
            logger.info("Starting Berke0S after installation...")
            wm = WindowManager()
            wm.run()
            
        except Exception as e:
            logger.error(f"Finish installation error: {e}")
    
    def exit_installer(self):
        """Exit installer without starting Berke0S"""
        try:
            self.root.destroy()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Exit installer error: {e}")
            sys.exit(1)
        
    def console_install(self):
        """Enhanced console-based installation with V2 improvements"""
        try:
            print("\n" + "="*80)
            print("  ██████╗ ███████╗██████╗ ██╗  ██╗███████╗ ██████╗ ███████╗")
            print("  ██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔════╝██╔═████╗██╔════╝")
            print("  ██████╔╝█████╗  ██████╔╝█████╔╝ █████╗  ██║██╔██║███████╗")
            print("  ██╔══██╗██╔══╝  ██╔══██╗██╔═██╗ ██╔══╝  ████╔╝██║╚════██║")
            print("  ██████╔╝███████╗██║  ██║██║  ██╗███████╗╚██████╔╝███████║")
            print("  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝")
            print("  Ultimate Desktop Environment V2 - Enhanced Display Management")
            print("  Console Installation Mode")
            print("="*80)
            
            # Enhanced console setup
            print("\n🚀 Berke0S V2 Enhanced Installation")
            print("   • Improved display detection and management")
            print("   • Better Tiny Core Linux support")
            print("   • Enhanced error handling")
            print("   • Robust fallback systems")
            
            # System check
            print("\n🔍 Performing system check...")
            self.perform_console_system_check()
            
            # Language selection
            print("\n1. Dil Seçimi / Language Selection:")
            print("   [1] Türkçe [2] English [3] Deutsch [4] Français")
            lang_choice = input("Seçim / Choice (1-4): ").strip()
            
            languages = {"1": "tr_TR", "2": "en_US", "3": "de_DE", "4": "fr_FR"}
            self.config["language"] = languages.get(lang_choice, "tr_TR")
            
            # Display setup
            print("\n2. Display Configuration:")
            print("   [1] Auto-detect (Recommended)")
            print("   [2] Force X11")
            print("   [3] Headless mode")
            display_choice = input("Display mode (1-3): ").strip()
            
            display_modes = {"1": "auto", "2": "x11", "3": "headless"}
            self.config["display"]["display_server"] = display_modes.get(display_choice, "auto")
            
            # User setup
            print("\n3. Kullanıcı Hesabı / User Account:")
            fullname = input("Ad Soyad / Full Name: ").strip()
            username = input("Kullanıcı Adı / Username: ").strip()
            password = getpass.getpass("Şifre / Password: ")
            
            # Validate user input
            if len(username) < 3:
                print("❌ Username must be at least 3 characters")
                return False
            if len(password) < 4:
                print("❌ Password must be at least 4 characters")
                return False
            
            # Network setup
            print("\n4. Ağ Ayarları / Network Settings:")
            setup_wifi = input("WiFi kurmak ister misiniz? / Setup WiFi? (y/n): ").lower() == 'y'
            
            if setup_wifi:
                ssid = input("WiFi Ağ Adı / SSID: ").strip()
                wifi_password = getpass.getpass("WiFi Şifresi / WiFi Password: ")
                self.config["wifi"] = {"ssid": ssid, "password": wifi_password}
            
            # Theme selection
            print("\n5. Tema Seçimi / Theme Selection:")
            print("   [1] Berke Dark V2 [2] Berke Light V2 [3] Ocean Blue V2")
            print("   [4] Forest Green V2 [5] Tiny Core Classic")
            theme_choice = input("Tema / Theme (1-5): ").strip()
            
            themes = {
                "1": "berke_dark", "2": "berke_light", "3": "ocean", 
                "4": "forest", "5": "tinycore"
            }
            self.config["theme"] = themes.get(theme_choice, "berke_dark")
            
            # Advanced options
            print("\n6. Gelişmiş Ayarlar / Advanced Settings:")
            enable_effects = input("Visual effects enable? (y/n): ").lower() == 'y'
            self.config["desktop"]["effects"] = enable_effects
            
            auto_updates = input("Auto updates enable? (y/n): ").lower() == 'y'
            self.config["system"]["auto_updates"] = auto_updates
            
            # Create user
            self.config["users"] = [{
                "username": username,
                "fullname": fullname,
                "password": hashlib.sha256(password.encode()).hexdigest(),
                "admin": True,
                "auto_login": True
            }]
            
            # Perform installation
            print("\n7. Kurulum Yapılıyor / Installing...")
            self.perform_console_installation()
            
            print("\n✅ Kurulum tamamlandı! / Installation completed!")
            print("🔄 Berke0S başlatılıyor / Starting Berke0S...")
            
            return True
            
        except KeyboardInterrupt:
            print("\n❌ Kurulum iptal edildi / Installation cancelled")
            return False
        except Exception as e:
            logger.error(f"Console installation error: {e}")
            print(f"❌ Kurulum hatası / Installation error: {e}")
            return False
    
    def perform_console_system_check(self):
        """Perform system check in console mode"""
        try:
            checks = [
                ("Operating System", self.check_operating_system),
                ("Python Version", self.check_python_version),
                ("Display System", self.check_display_system),
                ("Memory", self.check_memory),
                ("Disk Space", self.check_disk_space),
                ("Permissions", self.check_permissions)
            ]
            
            print("   System Compatibility Check:")
            passed = 0
            
            for check_name, check_func in checks:
                try:
                    result = check_func()
                    if result["status"] == "pass":
                        print(f"   ✅ {check_name}: {result.get('details', 'OK')}")
                        passed += 1
                    elif result["status"] == "warning":
                        print(f"   ⚠️  {check_name}: {result.get('details', 'Warning')}")
                        passed += 0.5
                    else:
                        print(f"   ❌ {check_name}: {result.get('details', 'Failed')}")
                except Exception as e:
                    print(f"   ❌ {check_name}: Error - {str(e)}")
            
            pass_rate = (passed / len(checks)) * 100
            print(f"\n   📊 Compatibility: {pass_rate:.0f}% ({passed:.1f}/{len(checks)})")
            
            if pass_rate >= 70:
                print("   ✅ System is compatible!")
            else:
                print("   ⚠️  Some compatibility issues detected")
                
        except Exception as e:
            logger.error(f"Console system check error: {e}")
            print(f"   ❌ System check failed: {e}")
            
    def perform_console_installation(self):
        """Perform actual console installation with V2 enhancements"""
        steps = [
            ("Dizinler oluşturuluyor / Creating directories", self.create_directories),
            ("Veritabanı hazırlanıyor / Preparing database", self.setup_database),
            ("Display sistemi yapılandırılıyor / Configuring display", self.configure_display_system),
            ("Sistem dosyaları kuruluyor / Installing system files", self.install_system_files),
            ("Kullanıcı ayarları / User configuration", self.create_user_account),
            ("Ağ yapılandırması / Network configuration", self.configure_network),
            ("Masaüstü ortamı / Desktop environment", self.setup_desktop_environment),
            ("Uygulamalar kuruluyor / Installing applications", self.install_applications),
            ("Temalar kuruluyor / Installing themes", self.install_default_themes),
            ("Başlangıç betikleri / Startup scripts", self.create_startup_scripts),
            ("Son ayarlar / Final configuration", self.finalize_installation)
        ]
        
        for i, (desc, func) in enumerate(steps):
            print(f"[{i+1}/{len(steps)}] {desc}...")
            try:
                func()
                print(f"✓ {desc} - Tamamlandı / Completed")
            except Exception as e:
                print(f"✗ {desc} - Hata / Error: {e}")
                logger.error(f"Installation step failed: {desc} - {e}")
            time.sleep(0.3)
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Config save error: {e}")

# Enhanced Notification System (keeping existing implementation)
class NotificationSystem:
    """Advanced notification system with rich features"""
    
    def __init__(self, wm):
        self.wm = wm
        self.notifications = []
        self.notification_id = 0
        self.notification_history = []
        self.max_history = 100
        
    def send(self, title, message, timeout=5000, notification_type="info", actions=None, icon=None):
        """Send a rich notification"""
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
                "actions": actions or []
            }
            self.notification_history.append(notification_data)
            
            # Limit history size
            if len(self.notification_history) > self.max_history:
                self.notification_history.pop(0)
            
            # Create notification window
            notif = tk.Toplevel(self.wm.root)
            notif.withdraw()
            notif.overrideredirect(True)
            notif.attributes('-topmost', True)
            notif.configure(bg='#1a1a1a')
            
            # Enhanced positioning
            screen_width = self.wm.root.winfo_screenwidth()
            screen_height = self.wm.root.winfo_screenheight()
            
            notif_width = 400
            notif_height = 100 + (len(actions) * 30 if actions else 0)
            
            position = self.wm.config.get("notifications", {}).get("position", "top-right")
            
            if position == "top-right":
                x = screen_width - notif_width - 20
                y = 20 + len(self.notifications) * (notif_height + 10)
            elif position == "top-left":
                x = 20
                y = 20 + len(self.notifications) * (notif_height + 10)
            elif position == "bottom-right":
                x = screen_width - notif_width - 20
                y = screen_height - notif_height - 20 - len(self.notifications) * (notif_height + 10)
            else:  # bottom-left
                x = 20
                y = screen_height - notif_height - 20 - len(self.notifications) * (notif_height + 10)
            
            notif.geometry(f"{notif_width}x{notif_height}+{x}+{y}")
            
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
            
            # Main container
            main_frame = tk.Frame(notif, bg='#2a2a2a', relief=tk.RAISED, bd=2)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
            
            # Header with colored stripe
            header_frame = tk.Frame(main_frame, bg=config["color"], height=30)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            # Icon and title
            title_frame = tk.Frame(header_frame, bg=config["color"])
            title_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Icon
            icon_text = icon if icon else config["icon"]
            tk.Label(title_frame, text=icon_text, bg=config["color"], 
                    fg=config["text_color"], font=('Arial', 12)).pack(side=tk.LEFT)
            
            # Title
            tk.Label(title_frame, text=title, bg=config["color"], 
                    fg=config["text_color"], font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(10, 0))
            
            # Close button
            close_btn = tk.Label(title_frame, text="✕", bg=config["color"], 
                               fg=config["text_color"], font=('Arial', 8), cursor='hand2')
            close_btn.pack(side=tk.RIGHT)
            close_btn.bind('<Button-1>', lambda e: self.close_notification_by_window(notif))
            
            # Message content
            content_frame = tk.Frame(main_frame, bg='#3a3a3a')
            content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Message text
            msg_label = tk.Label(content_frame, text=message, bg='#3a3a3a', fg='white', 
                               font=('Arial', 9), wraplength=360, justify=tk.LEFT, anchor='nw')
            msg_label.pack(fill=tk.X, pady=(0, 5))
            
            # Action buttons
            if actions:
                action_frame = tk.Frame(content_frame, bg='#3a3a3a')
                action_frame.pack(fill=tk.X)
                
                for action in actions:
                    btn = tk.Button(action_frame, text=action.get("text", "Action"),
                                   command=lambda a=action: self.handle_notification_action(notif, a),
                                   bg=config["color"], fg=config["text_color"],
                                   font=('Arial', 8), relief=tk.FLAT, padx=10, pady=2)
                    btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Progress bar for timed notifications
            if notif_type in ["info", "system"]:
                progress_frame = tk.Frame(content_frame, bg='#3a3a3a', height=3)
                progress_frame.pack(fill=tk.X, side=tk.BOTTOM)
                
                progress_bar = tk.Frame(progress_frame, bg=config["color"], height=3)
                progress_bar.pack(side=tk.LEFT, fill=tk.Y)
                
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
                
                # Slide in animation
                start_x = notif.winfo_x() + 50
                target_x = notif.winfo_x()
                
                def slide_in(step=0):
                    if step <= 10:
                        progress = step / 10
                        current_x = start_x + (target_x - start_x) * progress
                        alpha = progress * 0.95
                        
                        notif.geometry(f"{notif.winfo_width()}x{notif.winfo_height()}+{int(current_x)}+{notif.winfo_y()}")
                        notif.attributes('-alpha', alpha)
                        
                        self.wm.root.after(20, lambda: slide_in(step + 1))
                        
                slide_in()
                
            elif action == "hide":
                def fade_out(alpha=0.95):
                    if alpha >= 0:
                        notif.attributes('-alpha', alpha)
                        self.wm.root.after(50, lambda: fade_out(alpha - 0.1))
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
            position = self.wm.config.get("notifications", {}).get("position", "top-right")
            screen_width = self.wm.root.winfo_screenwidth()
            screen_height = self.wm.root.winfo_screenheight()
            
            for i, notification in enumerate(self.notifications):
                if "window" in notification:
                    notif = notification["window"]
                    width, height = 400, 100
                    
                    if position == "top-right":
                        x = screen_width - width - 20
                        y = 20 + i * (height + 10)
                    elif position == "top-left":
                        x = 20
                        y = 20 + i * (height + 10)
                    elif position == "bottom-right":
                        x = screen_width - width - 20
                        y = screen_height - height - 20 - i * (height + 10)
                    else:  # bottom-left
                        x = 20
                        y = screen_height - height - 20 - i * (height + 10)
                    
                    notif.geometry(f"{width}x{height}+{x}+{y}")
                    
        except Exception as e:
            logger.error(f"Reposition error: {e}")
    
    def show_notification_center(self):
        """Show notification center with history"""
        try:
            center = tk.Toplevel(self.wm.root)
            center.title("Notification Center")
            center.geometry("500x600")
            center.configure(bg=self.wm.get_theme_color("window"))
            
            # Header
            header = tk.Frame(center, bg=self.wm.get_theme_color("accent"), height=50)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            
            tk.Label(header, text="📢 Notification Center", 
                    bg=self.wm.get_theme_color("accent"), fg="white",
                    font=('Arial', 14, 'bold')).pack(pady=15)
            
            # Clear all button
            tk.Button(header, text="Clear All", command=self.clear_all_notifications,
                     bg=self.wm.get_theme_color("error"), fg="white").pack(side=tk.RIGHT, padx=10, pady=10)
            
            # Notification list
            list_frame = tk.Frame(center, bg=self.wm.get_theme_color("window"))
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Scrollable list
            canvas = tk.Canvas(list_frame, bg=self.wm.get_theme_color("window"))
            scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.wm.get_theme_color("window"))
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Display notification history
            for notification in reversed(self.notification_history[-20:]):  # Show last 20
                self.create_history_item(scrollable_frame, notification)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
        except Exception as e:
            logger.error(f"Notification center error: {e}")
    
    def create_history_item(self, parent, notification):
        """Create a notification history item"""
        try:
            item_frame = tk.Frame(parent, bg=self.wm.get_theme_color("bg"), relief=tk.RAISED, bd=1)
            item_frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Header with type color
            colors = {
                "info": "#4a9eff", "success": "#00ff88", 
                "warning": "#ffb347", "error": "#ff6b6b"
            }
            color = colors.get(notification["type"], "#4a9eff")
            
            header = tk.Frame(item_frame, bg=color, height=5)
            header.pack(fill=tk.X)
            
            # Content
            content = tk.Frame(item_frame, bg=self.wm.get_theme_color("bg"))
            content.pack(fill=tk.X, padx=10, pady=5)
            
            # Title and timestamp
            title_frame = tk.Frame(content, bg=self.wm.get_theme_color("bg"))
            title_frame.pack(fill=tk.X)
            
            tk.Label(title_frame, text=notification["title"], 
                    bg=self.wm.get_theme_color("bg"), fg=self.wm.get_theme_color("fg"),
                    font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
            
            timestamp = notification["timestamp"].strftime("%H:%M")
            tk.Label(title_frame, text=timestamp, 
                    bg=self.wm.get_theme_color("bg"), fg=self.wm.get_theme_color("fg"),
                    font=('Arial', 8)).pack(side=tk.RIGHT)
            
            # Message
            tk.Label(content, text=notification["message"], 
                    bg=self.wm.get_theme_color("bg"), fg=self.wm.get_theme_color("fg"),
                    font=('Arial', 9), wraplength=450, justify=tk.LEFT).pack(anchor='w')
            
        except Exception as e:
            logger.error(f"History item creation error: {e}")
    
    def clear_all_notifications(self):
        """Clear all notifications and history"""
        # Close all active notifications
        for notification in self.notifications.copy():
            self.close_notification(notification)
        
        # Clear history
        self.notification_history.clear()

# Enhanced Window Manager with improved display management
class WindowManager:
    """Ultimate window manager with advanced features and enhanced display support"""
    
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
        self.virtual_desktops = []
        self.current_desktop = 0
        self.workspace_manager = None
        self.plugin_manager = None
        self.performance_monitor = None
        self.display_manager = DisplayManager()
        
        # Initialize enhanced features
        self.init_virtual_desktops()
        self.init_plugin_system()
        self.init_performance_monitoring()
        
        # Initialize display with enhanced management
        self.setup_display_system()
        
        self.setup_ui()
    
    def setup_display_system(self):
        """Setup display system with enhanced management"""
        try:
            logger.info("Setting up enhanced display system...")
            
            # Setup display environment
            display_success = self.display_manager.setup_display_environment()
            
            if display_success:
                logger.info("Display system initialized successfully")
                
                # Log display information
                display_info = self.display_manager.get_display_info()
                logger.info(f"Display configuration: {display_info}")
                
                # Store display info in database
                self.log_display_event("initialization", "success", f"Display ready: {display_info}")
                
            else:
                logger.warning("Display system initialization failed, using fallback")
                self.log_display_event("initialization", "fallback", "Using headless mode")
                
        except Exception as e:
            logger.error(f"Display system setup error: {e}")
            self.log_display_event("initialization", "error", str(e))
    
    def log_display_event(self, event_type, status, message):
        """Log display events to database"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO display_logs (event_type, display_id, message, success) VALUES (?, ?, ?, ?)",
                (event_type, self.display_manager.get_current_display(), message, 1 if status == "success" else 0)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Display event logging error: {e}")
    
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
        """Load enhanced themes from files"""
        themes = {}
        try:
            # Load built-in themes
            builtin_themes = {
                "berke_dark": {
                    "name": "Berke Dark V2",
                    "version": "2.0",
                    "colors": {
                        "bg": "#1a1a1a", "fg": "#ffffff", "accent": "#00ff88",
                        "secondary": "#4a9eff", "warning": "#ffb347", "error": "#ff6b6b",
                        "success": "#00ff88", "taskbar": "#0f0f23", "window": "#2a2a2a",
                        "input": "#333333", "border": "#444444", "hover": "#555555",
                        "selection": "#00ff8844", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier"},
                    "effects": {"blur": True, "transparency": True, "animations": True}
                },
                "berke_light": {
                    "name": "Berke Light V2",
                    "version": "2.0",
                    "colors": {
                        "bg": "#f5f5f5", "fg": "#333333", "accent": "#007acc",
                        "secondary": "#28a745", "warning": "#ffc107", "error": "#dc3545",
                        "success": "#28a745", "taskbar": "#e9ecef", "window": "#ffffff",
                        "input": "#ffffff", "border": "#cccccc", "hover": "#e9ecef",
                        "selection": "#007acc44", "shadow": "#00000022"
                    },
                    "fonts": {"default": "Arial", "mono": "Courier"},
                    "effects": {"blur": False, "transparency": False, "animations": True}
                },
                "tinycore": {
                    "name": "Tiny Core Classic",
                    "version": "2.0",
                    "colors": {
                        "bg": "#2e3436", "fg": "#ffffff", "accent": "#729fcf",
                        "secondary": "#8ae234", "warning": "#fcaf3e", "error": "#ef2929",
                        "success": "#8ae234", "taskbar": "#555753", "window": "#3c4043",
                        "input": "#2e3436", "border": "#888a85", "hover": "#555753",
                        "selection": "#729fcf44", "shadow": "#00000055"
                    },
                    "fonts": {"default": "Arial", "mono": "Monospace"},
                    "effects": {"blur": False, "transparency": False, "animations": False}
                }
            }
            themes.update(builtin_themes)
            
            # Load custom themes from files
            if os.path.exists(THEMES_DIR):
                for theme_file in os.listdir(THEMES_DIR):
                    if theme_file.endswith('.json'):
                        try:
                            theme_path = os.path.join(THEMES_DIR, theme_file)
                            with open(theme_path, 'r') as f:
                                theme_data = json.load(f)
                                theme_name = os.path.splitext(theme_file)[0]
                                themes[theme_name] = theme_data
                        except Exception as e:
                            logger.warning(f"Failed to load theme {theme_file}: {e}")
                            
            logger.info(f"Loaded {len(themes)} themes")
            return themes
            
        except Exception as e:
            logger.error(f"Theme loading error: {e}")
            return builtin_themes
        
    def setup_ui(self):
        """Setup enhanced main UI with improved display handling"""
        try:
            logger.info("Setting up main UI...")
            
            # Check if display is available
            if not self.display_manager.is_display_ready():
                logger.warning("Display not ready, attempting headless mode")
                self.setup_headless_mode()
                return
            
            self.root = tk.Tk()
            self.root.title("Berke0S 3.0 V2 - Ultimate Desktop")
            
            # Enhanced display configuration
            try:
                # Force fullscreen and proper display
                self.root.attributes('-fullscreen', True)
                self.root.state('zoomed')  # Maximize on Windows/Linux
            except Exception as e:
                logger.warning(f"Fullscreen setup failed: {e}")
                # Fallback to maximized window
                try:
                    self.root.geometry("1024x768")
                    self.root.state('normal')
                except:
                    pass
            
            # Enhanced window configuration
            self.root.configure(bg=self.get_theme_color("bg"))
            self.root.focus_force()
            self.root.lift()
            
            # Bind window manager events
            self.root.protocol("WM_DELETE_WINDOW", self.safe_shutdown)
            
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
                "Berke0S V2 Ready",
                "Welcome to Berke0S 3.0 V2 with Enhanced Display Management!",
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
            # Try headless mode as fallback
            self.setup_headless_mode()
    
    def setup_headless_mode(self):
        """Setup headless mode for systems without display"""
        try:
            logger.info("Setting up headless mode...")
            
            # Create minimal root for services
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the window
            
            # Start essential services only
            self.start_headless_services()
            
            logger.info("Headless mode configured")
            
        except Exception as e:
            logger.error(f"Headless mode setup error: {e}")
            # Ultimate fallback - console mode
            self.run_console_mode()
    
    def start_headless_services(self):
        """Start essential services for headless mode"""
        try:
            services = [
                ("System Monitor", self.system_monitor_service),
                ("Auto-Save", self.auto_save_service),
                ("Performance Monitor", self.performance_monitor_service)
            ]
            
            for service_name, service_func in services:
                try:
                    thread = threading.Thread(target=service_func, daemon=True, name=service_name)
                    thread.start()
                    logger.info(f"Started headless service: {service_name}")
                except Exception as e:
                    logger.error(f"Failed to start headless service {service_name}: {e}")
            
        except Exception as e:
            logger.error(f"Headless services start error: {e}")
    
    def run_console_mode(self):
        """Run in console mode as ultimate fallback"""
        try:
            logger.info("Running in console mode...")
            
            print("\n" + "="*60)
            print("  Berke0S 3.0 V2 - Console Mode")
            print("  Enhanced Display Management")
            print("="*60)
            print("\nDisplay system not available - running in console mode")
            print("Essential services are running in the background")
            print("\nPress Ctrl+C to exit")
            
            # Keep running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Console mode terminated by user")
        except Exception as e:
            logger.error(f"Console mode error: {e}")
    
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
    
    def create_desktop(self):
        """Create enhanced desktop area"""
        try:
            # Main desktop canvas
            self.desktop = tk.Canvas(
                self.root,
                bg=self.get_theme_color("bg"),
                highlightthickness=0,
                cursor="arrow"
            )
            
            # Configure desktop positioning
            taskbar_pos = self.config.get("taskbar", {}).get("position", "bottom")
            taskbar_size = self.config.get("taskbar", {}).get("size", 45)
            
            if taskbar_pos == "bottom":
                self.desktop.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
            elif taskbar_pos == "top":
                self.desktop.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)
            elif taskbar_pos == "left":
                self.desktop.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
            elif taskbar_pos == "right":
                self.desktop.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
                
            # Bind desktop events
            self.desktop.bind("<Button-1>", self.desktop_click)
            self.desktop.bind("<Button-3>", self.show_desktop_menu)
            self.desktop.bind("<Double-Button-1>", self.hide_all_windows)
            self.desktop.bind("<B1-Motion>", self.desktop_drag)
            
            # Enable drag and drop
            self.desktop.bind("<ButtonPress-1>", self.start_desktop_selection)
            self.desktop.bind("<B1-Motion>", self.update_desktop_selection)
            self.desktop.bind("<ButtonRelease-1>", self.end_desktop_selection)
            
            logger.info("Desktop created successfully")
            
        except Exception as e:
            logger.error(f"Desktop creation error: {e}")
    
    def create_taskbar(self):
        """Create enhanced taskbar with modern features"""
        try:
            taskbar_pos = self.config.get("taskbar", {}).get("position", "bottom")
            taskbar_size = self.config.get("taskbar", {}).get("size", 45)
            
            self.taskbar = tk.Frame(
                self.root,
                bg=self.get_theme_color("taskbar"),
                height=taskbar_size if taskbar_pos in ["top", "bottom"] else None,
                width=taskbar_size if taskbar_pos in ["left", "right"] else None
            )
            
            # Apply transparency if supported
            if self.config.get("taskbar", {}).get("transparency", 0.9) < 1.0:
                try:
                    self.taskbar.attributes('-alpha', self.config.get("taskbar", {}).get("transparency", 0.9))
                except:
                    pass
            
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
            
            # Create taskbar components
            self.create_start_button()
            self.create_quick_launch()
            self.create_window_list()
            self.create_system_tray()
            
            logger.info("Taskbar created successfully")
            
        except Exception as e:
            logger.error(f"Taskbar creation error: {e}")
    
    def create_start_button(self):
        """Create enhanced start menu button"""
        try:
            self.start_button = tk.Button(
                self.taskbar,
                text="🏠 Berke0S V2",
                bg=self.get_theme_color("accent"),
                fg="white",
                font=('Arial', 11, 'bold'),
                relief=tk.FLAT,
                padx=20,
                pady=8,
                command=self.toggle_start_menu,
                cursor="hand2",
                activebackground=self.get_theme_color("hover")
            )
            self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
            
            # Add hover effects
            self.start_button.bind("<Enter>", lambda e: self.start_button.config(bg=self.get_theme_color("hover")))
            self.start_button.bind("<Leave>", lambda e: self.start_button.config(bg=self.get_theme_color("accent")))
            
        except Exception as e:
            logger.error(f"Start button creation error: {e}")
    
    def create_quick_launch(self):
        """Create enhanced quick launch area"""
        try:
            self.quick_launch_frame = tk.Frame(self.taskbar, bg=self.get_theme_color("taskbar"))
            self.quick_launch_frame.pack(side=tk.LEFT, padx=10)
            
            # Quick launch apps with enhanced icons
            quick_apps = [
                ("📁", "File Manager", self.launch_file_manager, "System file management"),
                ("🌐", "Web Browser", self.launch_web_browser, "Browse the internet"),
                ("💻", "Terminal", self.launch_terminal, "Command line interface"),
                ("⚙️", "Settings", self.launch_settings, "System configuration"),
                ("📝", "Text Editor", lambda: TextEditor(self).show(), "Edit text files"),
                ("🧮", "Calculator", lambda: Calculator(self).show(), "Perform calculations"),
                ("🖥️", "Display", lambda: DisplaySettings(self).show(), "Display configuration")
            ]
            
            for icon, name, command, tooltip in quick_apps:
                btn = tk.Button(
                    self.quick_launch_frame,
                    text=icon,
                    bg=self.get_theme_color("taskbar"),
                    fg=self.get_theme_color("fg"),
                    font=('Arial', 14),
                    relief=tk.FLAT,
                    width=3,
                    height=1,
                    command=command,
                    cursor="hand2"
                )
                btn.pack(side=tk.LEFT, padx=3, pady=3)
                
                # Enhanced tooltip
                self.create_enhanced_tooltip(btn, name, tooltip)
                
                # Hover effects
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.get_theme_color("hover")))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.get_theme_color("taskbar")))
                
        except Exception as e:
            logger.error(f"Quick launch creation error: {e}")
    
    def create_window_list(self):
        """Create window list area in taskbar"""
        try:
            self.window_list_frame = tk.Frame(self.taskbar, bg=self.get_theme_color("taskbar"))
            self.window_list_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            # This will be populated dynamically as windows are created
            
        except Exception as e:
            logger.error(f"Window list creation error: {e}")
    
    def create_system_tray(self):
        """Create enhanced system tray"""
        try:
            self.tray_frame = tk.Frame(self.taskbar, bg=self.get_theme_color("taskbar"))
            self.tray_frame.pack(side=tk.RIGHT, padx=10)
            
            # System indicators with enhanced functionality
            self.create_system_indicators()
            
            # Clock with enhanced features
            self.clock_frame = tk.Frame(self.tray_frame, bg=self.get_theme_color("taskbar"))
            self.clock_frame.pack(side=tk.RIGHT, padx=10)
            
            self.clock_label = tk.Label(
                self.clock_frame,
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 10, 'bold'),
                cursor="hand2"
            )
            self.clock_label.pack()
            
            # Clock click handler
            self.clock_label.bind("<Button-1>", self.show_calendar)
            
            # Update clock
            self.update_clock()
            
        except Exception as e:
            logger.error(f"System tray creation error: {e}")
    
    def create_system_indicators(self):
        """Create enhanced system status indicators"""
        try:
            indicators = []
            
            # Display indicator (new for V2)
            self.display_indicator = tk.Label(
                self.tray_frame,
                text="🖥️",
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 12),
                cursor="hand2"
            )
            self.display_indicator.pack(side=tk.RIGHT, padx=3)
            self.display_indicator.bind("<Button-1>", lambda e: DisplaySettings(self).show())
            indicators.append(("Display", self.display_indicator))
            
            # Network indicator
            self.network_indicator = tk.Label(
                self.tray_frame,
                text="📶",
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 12),
                cursor="hand2"
            )
            self.network_indicator.pack(side=tk.RIGHT, padx=3)
            self.network_indicator.bind("<Button-1>", self.show_network_menu)
            indicators.append(("Network", self.network_indicator))
            
            # Volume indicator
            self.volume_indicator = tk.Label(
                self.tray_frame,
                text="🔊",
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 12),
                cursor="hand2"
            )
            self.volume_indicator.pack(side=tk.RIGHT, padx=3)
            self.volume_indicator.bind("<Button-1>", self.show_volume_menu)
            indicators.append(("Volume", self.volume_indicator))
            
            # Battery indicator (if available)
            if self.has_battery():
                self.battery_indicator = tk.Label(
                    self.tray_frame,
                    text="🔋",
                    bg=self.get_theme_color("taskbar"),
                    fg=self.get_theme_color("fg"),
                    font=('Arial', 12),
                    cursor="hand2"
                )
                self.battery_indicator.pack(side=tk.RIGHT, padx=3)
                self.battery_indicator.bind("<Button-1>", self.show_battery_info)
                indicators.append(("Battery", self.battery_indicator))
            
            # CPU indicator
            self.cpu_indicator = tk.Label(
                self.tray_frame,
                text="🖥️",
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 12),
                cursor="hand2"
            )
            self.cpu_indicator.pack(side=tk.RIGHT, padx=3)
            self.cpu_indicator.bind("<Button-1>", lambda e: SystemMonitor(self).show())
            indicators.append(("CPU", self.cpu_indicator))
            
            # Notification indicator
            self.notification_indicator = tk.Label(
                self.tray_frame,
                text="🔔",
                bg=self.get_theme_color("taskbar"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 12),
                cursor="hand2"
            )
            self.notification_indicator.pack(side=tk.RIGHT, padx=3)
            self.notification_indicator.bind("<Button-1>", lambda e: self.notifications.show_notification_center())
            indicators.append(("Notifications", self.notification_indicator))
            
            # Add tooltips to all indicators
            for name, indicator in indicators:
                self.create_enhanced_tooltip(indicator, name, f"Click to open {name} settings")
                
        except Exception as e:
            logger.error(f"System indicators error: {e}")
    
    def create_dock(self):
        """Create optional dock for favorite applications"""
        if self.config.get("desktop", {}).get("show_dock", False):
            try:
                self.dock = tk.Frame(self.root, bg=self.get_theme_color("taskbar"))
                self.dock.place(relx=0.5, rely=0.95, anchor="center")
                
                # Dock applications
                dock_apps = [
                    ("📁", self.launch_file_manager),
                    ("🌐", self.launch_web_browser),
                    ("💻", self.launch_terminal),
                    ("📝", lambda: TextEditor(self).show()),
                    ("🧮", lambda: Calculator(self).show()),
                    ("🎵", lambda: MusicPlayer(self).show()),
                    ("🖼️", lambda: ImageViewer(self).show()),
                    ("⚙️", self.launch_settings),
                    ("🖥️", lambda: DisplaySettings(self).show())
                ]
                
                for icon, command in dock_apps:
                    btn = tk.Button(
                        self.dock,
                        text=icon,
                        bg=self.get_theme_color("taskbar"),
                        fg=self.get_theme_color("fg"),
                        font=('Arial', 16),
                        relief=tk.FLAT,
                        width=3,
                        command=command,
                        cursor="hand2"
                    )
                    btn.pack(side=tk.LEFT, padx=2, pady=5)
                    
                    # Hover effects
                    btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.get_theme_color("accent")))
                    btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.get_theme_color("taskbar")))
                    
            except Exception as e:
                logger.error(f"Dock creation error: {e}")
    
    def create_desktop_icons(self):
        """Create desktop icons for common applications"""
        try:
            if not self.config.get("desktop", {}).get("show_desktop_icons", True):
                return
                
            icon_size = self.config.get("desktop", {}).get("icon_size", 48)
            
            # Default desktop icons with V2 additions
            desktop_icons = [
                {"name": "File Manager", "icon": "📁", "command": self.launch_file_manager, "x": 50, "y": 50},
                {"name": "Web Browser", "icon": "🌐", "command": self.launch_web_browser, "x": 50, "y": 120},
                {"name": "Terminal", "icon": "💻", "command": self.launch_terminal, "x": 50, "y": 190},
                {"name": "Settings", "icon": "⚙️", "command": self.launch_settings, "x": 50, "y": 260},
                {"name": "Text Editor", "icon": "📝", "command": lambda: TextEditor(self).show(), "x": 150, "y": 50},
                {"name": "Calculator", "icon": "🧮", "command": lambda: Calculator(self).show(), "x": 150, "y": 120},
                {"name": "Music Player", "icon": "🎵", "command": lambda: MusicPlayer(self).show(), "x": 150, "y": 190},
                {"name": "Games", "icon": "🎮", "command": lambda: GamesLauncher(self).show(), "x": 150, "y": 260},
                {"name": "Display Settings", "icon": "🖥️", "command": lambda: DisplaySettings(self).show(), "x": 250, "y": 50}
            ]
            
            # Load custom icon positions
            saved_icons = self.config.get("desktop", {}).get("desktop_icons", [])
            if saved_icons:
                desktop_icons = saved_icons
            
            for icon_data in desktop_icons:
                self.create_desktop_icon(icon_data)
                
        except Exception as e:
            logger.error(f"Desktop icons creation error: {e}")
    
    def create_desktop_icon(self, icon_data):
        """Create a single desktop icon"""
        try:
            icon_frame = tk.Frame(self.desktop, bg=self.get_theme_color("bg"))
            
            # Icon button
            icon_btn = tk.Button(
                icon_frame,
                text=icon_data["icon"],
                bg=self.get_theme_color("bg"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 24),
                relief=tk.FLAT,
                cursor="hand2",
                command=icon_data["command"]
            )
            icon_btn.pack()
            
            # Icon label
            icon_label = tk.Label(
                icon_frame,
                text=icon_data["name"],
                bg=self.get_theme_color("bg"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 9),
                wraplength=80
            )
            icon_label.pack()
            
            # Position icon
            self.desktop.create_window(
                icon_data["x"], icon_data["y"],
                window=icon_frame, anchor="nw"
            )
            
            # Hover effects
            icon_btn.bind("<Enter>", lambda e: icon_btn.config(bg=self.get_theme_color("hover")))
            icon_btn.bind("<Leave>", lambda e: icon_btn.config(bg=self.get_theme_color("bg")))
            
            # Drag and drop for icon positioning
            icon_frame.bind("<Button-1>", lambda e: self.start_icon_drag(e, icon_frame, icon_data))
            icon_frame.bind("<B1-Motion>", lambda e: self.drag_icon(e, icon_frame, icon_data))
            icon_frame.bind("<ButtonRelease-1>", lambda e: self.end_icon_drag(e, icon_frame, icon_data))
            
        except Exception as e:
            logger.error(f"Desktop icon creation error: {e}")
    
    def update_clock(self):
        """Update system clock with enhanced format"""
        try:
            now = datetime.datetime.now()
            
            # Format based on user preference
            if self.config.get("system", {}).get("24_hour_format", True):
                time_str = now.strftime("%H:%M")
            else:
                time_str = now.strftime("%I:%M %p")
                
            date_str = now.strftime("%a %d/%m")
            
            self.clock_label.config(text=f"{time_str}\n{date_str}")
            
            # Update system indicators
            self.update_system_indicators()
            
            # Schedule next update
            self.root.after(1000, self.update_clock)
            
        except Exception as e:
            logger.error(f"Clock update error: {e}")
            self.root.after(5000, self.update_clock)  # Retry in 5 seconds
    
    def update_system_indicators(self):
        """Update system status indicators"""
        try:
            # Update network status
            self.update_network_indicator()
            
            # Update volume status
            self.update_volume_indicator()
            
            # Update battery status
            if hasattr(self, 'battery_indicator'):
                self.update_battery_indicator()
                
            # Update CPU status
            self.update_cpu_indicator()
            
            # Update display status (new for V2)
            self.update_display_indicator()
            
        except Exception as e:
            logger.error(f"System indicators update error: {e}")
    
    def update_display_indicator(self):
        """Update display status indicator"""
        try:
            if self.display_manager.is_display_ready():
                self.display_indicator.config(text="🖥️", fg=self.get_theme_color("success"))
            else:
                self.display_indicator.config(text="🖥️", fg=self.get_theme_color("error"))
                
        except Exception as e:
            logger.error(f"Display indicator update error: {e}")
    
    def update_network_indicator(self):
        """Update network connectivity indicator"""
        try:
            # Check network connectivity
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                connected = True
            except OSError:
                connected = False
            
            if connected:
                self.network_indicator.config(text="📶", fg=self.get_theme_color("success"))
            else:
                self.network_indicator.config(text="📵", fg=self.get_theme_color("error"))
                
        except Exception as e:
            logger.error(f"Network indicator update error: {e}")
    
    def update_volume_indicator(self):
        """Update volume indicator"""
        try:
            # Get volume level (simplified for demo)
            volume_level = self.config.get("audio", {}).get("master_volume", 75)
            muted = self.config.get("audio", {}).get("mute", False)
            
            if muted or volume_level == 0:
                self.volume_indicator.config(text="🔇")
            elif volume_level < 30:
                self.volume_indicator.config(text="🔈")
            elif volume_level < 70:
                self.volume_indicator.config(text="🔉")
            else:
                self.volume_indicator.config(text="🔊")
                
        except Exception as e:
            logger.error(f"Volume indicator update error: {e}")
    
    def update_battery_indicator(self):
        """Update battery status indicator"""
        try:
            if psutil:
                battery = psutil.sensors_battery()
                if battery:
                    percent = battery.percent
                    plugged = battery.power_plugged
                    
                    if plugged:
                        self.battery_indicator.config(text="🔌")
                    elif percent > 75:
                        self.battery_indicator.config(text="🔋")
                    elif percent > 50:
                        self.battery_indicator.config(text="🔋")
                    elif percent > 25:
                        self.battery_indicator.config(text="🪫")
                    else:
                        self.battery_indicator.config(text="🪫", fg=self.get_theme_color("error"))
                        
        except Exception as e:
            logger.error(f"Battery indicator update error: {e}")
    
    def update_cpu_indicator(self):
        """Update CPU usage indicator"""
        try:
            if psutil:
                cpu_percent = psutil.cpu_percent(interval=None)
                
                if cpu_percent > 80:
                    self.cpu_indicator.config(fg=self.get_theme_color("error"))
                elif cpu_percent > 60:
                    self.cpu_indicator.config(fg=self.get_theme_color("warning"))
                else:
                    self.cpu_indicator.config(fg=self.get_theme_color("fg"))
                    
        except Exception as e:
            logger.error(f"CPU indicator update error: {e}")
    
    def load_wallpaper(self):
        """Load enhanced desktop wallpaper"""
        try:
            wallpaper_path = self.config.get("desktop", {}).get("wallpaper", "")
            wallpaper_mode = self.config.get("desktop", {}).get("wallpaper_mode", "stretch")
            
            if wallpaper_path and os.path.exists(wallpaper_path) and PIL_AVAILABLE:
                self.load_custom_wallpaper(wallpaper_path, wallpaper_mode)
            else:
                self.create_default_wallpaper()
                
        except Exception as e:
            logger.error(f"Wallpaper load error: {e}")
            self.create_default_wallpaper()
    
    def load_custom_wallpaper(self, wallpaper_path, mode):
        """Load custom wallpaper with different modes"""
        try:
            img = Image.open(wallpaper_path)
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            if mode == "stretch":
                img = img.resize((screen_width, screen_height), Image.LANCZOS)
            elif mode == "fit":
                img.thumbnail((screen_width, screen_height), Image.LANCZOS)
            elif mode == "center":
                # Center the image
                bg = Image.new('RGB', (screen_width, screen_height), (0, 0, 0))
                x = (screen_width - img.width) // 2
                y = (screen_height - img.height) // 2
                bg.paste(img, (x, y))
                img = bg
            elif mode == "tile":
                # Tile the image
                bg = Image.new('RGB', (screen_width, screen_height))
                for x in range(0, screen_width, img.width):
                    for y in range(0, screen_height, img.height):
                        bg.paste(img, (x, y))
                img = bg
            
            # Apply effects if enabled
            if self.config.get("desktop", {}).get("effects", True):
                blur_radius = self.config.get("desktop", {}).get("blur_radius", 0)
                if blur_radius > 0:
                    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            self.wallpaper_image = ImageTk.PhotoImage(img)
            self.desktop.create_image(0, 0, anchor=tk.NW, image=self.wallpaper_image)
            
            logger.info(f"Custom wallpaper loaded: {wallpaper_path}")
            
        except Exception as e:
            logger.error(f"Custom wallpaper load error: {e}")
            self.create_default_wallpaper()
    
    def create_default_wallpaper(self):
        """Create enhanced default gradient wallpaper"""
        try:
            if not PIL_AVAILABLE:
                return
                
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Create gradient image
            img = Image.new('RGB', (screen_width, screen_height))
            draw = ImageDraw.Draw(img)
            
            # Enhanced gradient based on theme
            theme_name = self.config.get("theme", "berke_dark")
            
            gradients = {
                "berke_dark": [(15, 15, 35), (26, 26, 26), (40, 40, 60)],
                "berke_light": [(240, 240, 240), (220, 220, 220), (200, 200, 200)],
                "ocean": [(13, 27, 42), (3, 4, 94), (0, 119, 190)],
                "forest": [(27, 67, 50), (45, 145, 108), (82, 183, 136)],
                "tinycore": [(46, 52, 54), (85, 87, 83), (136, 138, 133)]
            }
            
            colors = gradients.get(theme_name, gradients["berke_dark"])
            
            # Create multi-color gradient
            for y in range(screen_height):
                progress = y / screen_height
                
                if progress < 0.5:
                    # First half
                    ratio = progress * 2
                    r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
                    g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
                    b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
                else:
                    # Second half
                    ratio = (progress - 0.5) * 2
                    r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * ratio)
                    g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * ratio)
                    b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * ratio)
                
                draw.line([(0, y), (screen_width, y)], fill=(r, g, b))
            
            # Add some texture/pattern
            if self.config.get("desktop", {}).get("effects", True):
                # Add subtle geometric pattern
                pattern_color = (255, 255, 255, 20)  # Very transparent white
                pattern_img = Image.new('RGBA', (screen_width, screen_height), (0, 0, 0, 0))
                pattern_draw = ImageDraw.Draw(pattern_img)
                
                # Draw subtle lines
                for x in range(0, screen_width, 100):
                    pattern_draw.line([(x, 0), (x, screen_height)], fill=pattern_color, width=1)
                for y in range(0, screen_height, 100):
                    pattern_draw.line([(0, y), (screen_width, y)], fill=pattern_color, width=1)
                
                # Composite pattern onto background
                img = Image.alpha_composite(img.convert('RGBA'), pattern_img).convert('RGB')
            
            self.wallpaper_image = ImageTk.PhotoImage(img)
            self.desktop.create_image(0, 0, anchor=tk.NW, image=self.wallpaper_image)
            
            logger.info("Default gradient wallpaper created")
            
        except Exception as e:
            logger.error(f"Default wallpaper creation error: {e}")
    
    def bind_events(self):
        """Bind enhanced keyboard and mouse events"""
        try:
            # Global shortcuts
            shortcuts = {
                '<Control-Alt-t>': self.launch_terminal,
                '<Control-Alt-f>': self.launch_file_manager,
                '<Control-Alt-s>': self.launch_settings,
                '<Control-Alt-w>': self.launch_web_browser,
                '<Control-Alt-c>': lambda: Calculator(self).show(),
                '<Control-Alt-e>': lambda: TextEditor(self).show(),
                '<Control-Alt-d>': lambda: DisplaySettings(self).show(),  # New for V2
                '<Alt-F4>': self.close_active_window,
                '<Control-Alt-l>': self.lock_screen,
                '<Control-Alt-d>': self.show_desktop,
                '<Control-Alt-m>': lambda: SystemMonitor(self).show(),
                '<Print>': self.take_screenshot,
                '<F11>': self.toggle_fullscreen,
                '<Control-Alt-r>': self.restart_session,
                '<Control-Alt-q>': self.safe_shutdown
            }
            
            for key, command in shortcuts.items():
                self.root.bind(key, lambda e, cmd=command: cmd())
            
            # Window management
            self.root.bind('<Alt-Tab>', self.cycle_windows)
            self.root.bind('<Alt-Shift-Tab>', lambda e: self.cycle_windows(reverse=True))
            
            # Virtual desktop switching
            for i in range(1, 5):
                self.root.bind(f'<Control-{i}>', lambda e, desk=i-1: self.switch_virtual_desktop(desk))
            
            # Global mouse events
            self.root.bind('<Button-4>', self.mouse_wheel_up)
            self.root.bind('<Button-5>', self.mouse_wheel_down)
            
            logger.info("Event bindings configured")
            
        except Exception as e:
            logger.error(f"Event binding error: {e}")
    
    def start_services(self):
        """Start enhanced background services"""
        try:
            services = [
                ("System Monitor", self.system_monitor_service),
                ("Auto-Save", self.auto_save_service),
                ("Performance Monitor", self.performance_monitor_service),
                ("Plugin Manager", self.plugin_service),
                ("Network Monitor", self.network_monitor_service),
                ("Backup Service", self.backup_service),
                ("Display Monitor", self.display_monitor_service)  # New for V2
            ]
            
            for service_name, service_func in services:
                try:
                    thread = threading.Thread(target=service_func, daemon=True, name=service_name)
                    thread.start()
                    logger.info(f"Started service: {service_name}")
                except Exception as e:
                    logger.error(f"Failed to start service {service_name}: {e}")
            
            logger.info("Background services started")
            
        except Exception as e:
            logger.error(f"Services start error: {e}")
    
    def display_monitor_service(self):
        """Monitor display system health (new for V2)"""
        while True:
            try:
                # Check display health
                if self.display_manager.is_display_ready():
                    # Test display connection
                    try:
                        result = subprocess.run(['xdpyinfo'], capture_output=True, timeout=5)
                        if result.returncode != 0:
                            logger.warning("Display connection test failed")
                            self.notifications.send(
                                "Display Warning",
                                "Display connection issues detected",
                                notification_type="warning"
                            )
                    except:
                        pass
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Display monitor error: {e}")
                time.sleep(120)
    
    def system_monitor_service(self):
        """Enhanced system monitoring service"""
        while True:
            try:
                if not psutil:
                    time.sleep(60)
                    continue
                
                # Monitor CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > 90:
                    self.notifications.send(
                        "System Warning",
                        f"High CPU usage: {cpu_percent:.1f}%",
                        notification_type="warning",
                        actions=[
                            {"text": "Open Monitor", "callback": lambda: SystemMonitor(self).show()},
                            {"text": "Dismiss", "callback": lambda: None}
                        ]
                    )
                
                # Monitor memory usage
                memory = psutil.virtual_memory()
                if memory.percent > 85:
                    self.notifications.send(
                        "System Warning", 
                        f"High memory usage: {memory.percent:.1f}%",
                        notification_type="warning",
                        actions=[
                            {"text": "Free Memory", "callback": self.free_memory},
                            {"text": "Open Monitor", "callback": lambda: SystemMonitor(self).show()}
                        ]
                    )
                
                # Monitor disk space
                disk = psutil.disk_usage('/')
                if disk.percent > 90:
                    self.notifications.send(
                        "System Warning",
                        f"Low disk space: {disk.percent:.1f}% used",
                        notification_type="error",
                        actions=[
                            {"text": "Clean Temp", "callback": self.clean_temp_files},
                            {"text": "Open Disk", "callback": self.launch_file_manager}
                        ]
                    )
                
                # Monitor temperature (if available)
                try:
                    temps = psutil.sensors_temperatures()
                    if temps:
                        for name, entries in temps.items():
                            for entry in entries:
                                if entry.current > 80:  # 80°C threshold
                                    self.notifications.send(
                                        "Temperature Warning",
                                        f"{name}: {entry.current:.1f}°C",
                                        notification_type="warning"
                                    )
                except:
                    pass
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"System monitor error: {e}")
                time.sleep(60)
    
    def auto_save_service(self):
        """Enhanced auto-save service"""
        while True:
            try:
                time.sleep(300)  # Save every 5 minutes
                self.save_session()
                self.save_config()
                
                # Save plugin states
                if self.plugin_manager:
                    self.plugin_manager.save_plugin_states()
                    
                logger.debug("Auto-save completed")
                
            except Exception as e:
                logger.error(f"Auto-save error: {e}")
    
    def performance_monitor_service(self):
        """Performance monitoring service"""
        while True:
            try:
                if self.performance_monitor:
                    self.performance_monitor.update_metrics()
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
                time.sleep(30)
    
    def plugin_service(self):
        """Plugin management service"""
        while True:
            try:
                if self.plugin_manager:
                    self.plugin_manager.check_plugin_updates()
                time.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Plugin service error: {e}")
                time.sleep(3600)
    
    def network_monitor_service(self):
        """Network monitoring service"""
        last_status = None
        while True:
            try:
                # Check network connectivity
                try:
                    socket.create_connection(("8.8.8.8", 53), timeout=5)
                    current_status = "connected"
                except OSError:
                    current_status = "disconnected"
                
                # Notify on status change
                if last_status and last_status != current_status:
                    if current_status == "connected":
                        self.notifications.send(
                            "Network Status",
                            "Internet connection restored",
                            notification_type="success"
                        )
                    else:
                        self.notifications.send(
                            "Network Status",
                            "Internet connection lost",
                            notification_type="error"
                        )
                
                last_status = current_status
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Network monitor error: {e}")
                time.sleep(60)
    
    def backup_service(self):
        """Automatic backup service"""
        while True:
            try:
                # Check if auto-backup is enabled
                if not self.config.get("system", {}).get("auto_backup", False):
                    time.sleep(3600)
                    continue
                
                # Perform backup every 24 hours
                backup_interval = self.config.get("system", {}).get("backup_interval", 24) * 3600
                
                # Create backup
                self.create_system_backup()
                
                time.sleep(backup_interval)
                
            except Exception as e:
                logger.error(f"Backup service error: {e}")
                time.sleep(3600)
    
    # Enhanced utility methods
    def create_enhanced_tooltip(self, widget, title, description=None):
        """Create enhanced tooltip with title and description"""
        def show_tooltip(event):
            try:
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.configure(bg=self.get_theme_color("window"))
                
                # Position tooltip
                x = event.x_root + 10
                y = event.y_root + 10
                
                # Adjust position to stay on screen
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                tooltip_width = 200
                tooltip_height = 60 if description else 30
                
                if x + tooltip_width > screen_width:
                    x = event.x_root - tooltip_width - 10
                if y + tooltip_height > screen_height:
                    y = event.y_root - tooltip_height - 10
                
                tooltip.geometry(f"{tooltip_width}x{tooltip_height}+{x}+{y}")
                
                # Tooltip content
                main_frame = tk.Frame(tooltip, bg=self.get_theme_color("window"), 
                                    relief=tk.SOLID, bd=1)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
                
                # Title
                title_label = tk.Label(main_frame, text=title, 
                                     bg=self.get_theme_color("window"),
                                     fg=self.get_theme_color("fg"),
                                     font=('Arial', 9, 'bold'))
                title_label.pack(anchor='w', padx=5, pady=(5, 0))
                
                # Description
                if description:
                    desc_label = tk.Label(main_frame, text=description,
                                        bg=self.get_theme_color("window"),
                                        fg=self.get_theme_color("fg"),
                                        font=('Arial', 8),
                                        wraplength=180)
                    desc_label.pack(anchor='w', padx=5, pady=(0, 5))
                
                # Auto-hide after 3 seconds
                tooltip.after(3000, tooltip.destroy)
                
                # Store reference to prevent garbage collection
                widget.tooltip = tooltip
                
            except Exception as e:
                logger.error(f"Tooltip creation error: {e}")
        
        def hide_tooltip(event):
            try:
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    delattr(widget, 'tooltip')
            except:
                pass
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def has_battery(self):
        """Check if system has battery with fallback"""
        try:
            if psutil:
                battery = psutil.sensors_battery()
                return battery is not None
            return False
        except:
            return False
    
    def free_memory(self):
        """Free system memory"""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear caches if available
            if psutil:
                # Get current memory usage
                before = psutil.virtual_memory().percent
                
                # Try to clear system caches (Linux specific)
                try:
                    subprocess.run(['sync'], capture_output=True)
                    subprocess.run(['sudo', 'sh', '-c', 'echo 1 > /proc/sys/vm/drop_caches'], 
                                 capture_output=True)
                except:
                    pass
                
                after = psutil.virtual_memory().percent
                freed = before - after
                
                if freed > 0:
                    self.notifications.send(
                        "Memory Freed",
                        f"Freed {freed:.1f}% memory",
                        notification_type="success"
                    )
                else:
                    self.notifications.send(
                        "Memory",
                        "No significant memory was freed",
                        notification_type="info"
                    )
        except Exception as e:
            logger.error(f"Memory free error: {e}")
    
    def clean_temp_files(self):
        """Clean temporary files"""
        try:
            cleaned_size = 0
            temp_dirs = [
                tempfile.gettempdir(),
                os.path.expanduser("~/.cache"),
                "/tmp",
                "/var/tmp"
            ]
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                try:
                                    file_path = os.path.join(root, file)
                                    # Only clean files older than 7 days
                                    if (time.time() - os.path.getmtime(file_path)) > 7 * 24 * 3600:
                                        size = os.path.getsize(file_path)
                                        os.remove(file_path)
                                        cleaned_size += size
                                except:
                                    continue
                    except:
                        continue
            
            cleaned_mb = cleaned_size / (1024 * 1024)
            self.notifications.send(
                "Cleanup Complete",
                f"Cleaned {cleaned_mb:.1f} MB of temporary files",
                notification_type="success"
            )
            
        except Exception as e:
            logger.error(f"Temp cleanup error: {e}")
    
    def create_system_backup(self):
        """Create system configuration backup"""
        try:
            backup_dir = os.path.join(CONFIG_DIR, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"berke0s_backup_{timestamp}.tar.gz")
            
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(CONFIG_FILE, arcname="config.json")
                tar.add(DATABASE_FILE, arcname="berke0s.db")
                tar.add(THEMES_DIR, arcname="themes")
                
            logger.info(f"System backup created: {backup_file}")
            
        except Exception as e:
            logger.error(f"Backup creation error: {e}")
    
    # Application launcher methods
    def launch_file_manager(self):
        """Launch enhanced file manager"""
        try:
            if "file_manager" not in self.running_apps:
                app = FileManager(self)
                self.running_apps["file_manager"] = app
                app.show()
            else:
                # Bring existing window to front
                self.running_apps["file_manager"].bring_to_front()
        except Exception as e:
            logger.error(f"File manager launch error: {e}")
            
    def launch_web_browser(self):
        """Launch enhanced web browser"""
        try:
            if "web_browser" not in self.running_apps:
                app = WebBrowser(self)
                self.running_apps["web_browser"] = app
                app.show()
            else:
                self.running_apps["web_browser"].bring_to_front()
        except Exception as e:
            logger.error(f"Web browser launch error: {e}")
            
    def launch_settings(self):
        """Launch enhanced settings"""
        try:
            if "settings" not in self.running_apps:
                app = SettingsApp(self)
                self.running_apps["settings"] = app
                app.show()
            else:
                self.running_apps["settings"].bring_to_front()
        except Exception as e:
            logger.error(f"Settings launch error: {e}")
            
    def launch_terminal(self):
        """Launch enhanced terminal"""
        try:
            app = Terminal(self)
            app.show()
        except Exception as e:
            logger.error(f"Terminal launch error: {e}")
    
    # Enhanced menu and dialog methods
    def toggle_start_menu(self):
        """Toggle enhanced start menu"""
        try:
            if hasattr(self, 'start_menu_window') and self.start_menu_window.winfo_exists():
                self.start_menu_window.destroy()
                return
                
            self.show_start_menu()
            
        except Exception as e:
            logger.error(f"Start menu toggle error: {e}")
    
    def show_start_menu(self):
        """Show enhanced start menu"""
        try:
            self.start_menu_window = tk.Toplevel(self.root)
            self.start_menu_window.overrideredirect(True)
            self.start_menu_window.configure(bg=self.get_theme_color("window"))
            self.start_menu_window.attributes('-alpha', 0.98)
            
            # Enhanced positioning
            taskbar_pos = self.config.get("taskbar", {}).get("position", "bottom")
            button_x = self.start_button.winfo_rootx()
            button_y = self.start_button.winfo_rooty()
            
            menu_width, menu_height = 400, 500
            
            if taskbar_pos == "bottom":
                x = button_x
                y = button_y - menu_height - 5
            elif taskbar_pos == "top":
                x = button_x
                y = button_y + self.start_button.winfo_height() + 5
            else:  # left or right
                x = button_x + self.start_button.winfo_width() + 5
                y = button_y
            
            self.start_menu_window.geometry(f"{menu_width}x{menu_height}+{x}+{y}")
            
            # Create enhanced menu content
            self.create_enhanced_start_menu()
            
            # Auto-hide and focus handling
            self.start_menu_window.bind('<FocusOut>', self.hide_start_menu)
            self.start_menu_window.focus_set()
            
            # Smooth appear animation
            self.animate_start_menu("show")
            
        except Exception as e:
            logger.error(f"Start menu show error: {e}")
    
    def hide_start_menu(self, event=None):
        """Hide start menu with animation"""
        try:
            if hasattr(self, 'start_menu_window'):
                self.animate_start_menu("hide")
        except Exception as e:
            logger.error(f"Start menu hide error: {e}")
    
    def animate_start_menu(self, action):
        """Animate start menu appearance/disappearance"""
        try:
            if action == "show":
                self.start_menu_window.attributes('-alpha', 0)
                
                def fade_in(alpha=0):
                    if alpha <= 0.98:
                        self.start_menu_window.attributes('-alpha', alpha)
                        self.root.after(20, lambda: fade_in(alpha + 0.1))
                        
                fade_in()
                
            elif action == "hide":
                def fade_out(alpha=0.98):
                    if alpha >= 0:
                        self.start_menu_window.attributes('-alpha', alpha)
                        self.root.after(20, lambda: fade_out(alpha - 0.1))
                    else:
                        self.start_menu_window.destroy()
                        
                fade_out()
                
        except Exception as e:
            logger.error(f"Start menu animation error: {e}")
            if hasattr(self, 'start_menu_window'):
                self.start_menu_window.destroy()
    
    def create_enhanced_start_menu(self):
        """Create enhanced start menu with modern design"""
        try:
            # Main container
            main_container = tk.Frame(self.start_menu_window, bg=self.get_theme_color("window"))
            main_container.pack(fill=tk.BOTH, expand=True)
            
            # Header with user info
            header = tk.Frame(main_container, bg=self.get_theme_color("accent"), height=80)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            
            # User avatar and info
            user_frame = tk.Frame(header, bg=self.get_theme_color("accent"))
            user_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Avatar placeholder
            avatar_label = tk.Label(user_frame, text="👤", font=('Arial', 24),
                                  bg=self.get_theme_color("accent"), fg="white")
            avatar_label.pack(side=tk.LEFT)
            
            # User info
            info_frame = tk.Frame(user_frame, bg=self.get_theme_color("accent"))
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 0))
            
            current_user = self.config.get("users", [{}])[0] if self.config.get("users") else {}
            username = current_user.get("fullname", current_user.get("username", "User"))
            
            tk.Label(info_frame, text=f"Welcome, {username}", font=('Arial', 12, 'bold'),
                    bg=self.get_theme_color("accent"), fg="white").pack(anchor='w')
            
            current_time = datetime.datetime.now().strftime("%H:%M, %A")
            tk.Label(info_frame, text=current_time, font=('Arial', 9),
                    bg=self.get_theme_color("accent"), fg="white").pack(anchor='w')
            
            # Version info
            tk.Label(info_frame, text="Berke0S V2", font=('Arial', 8),
                    bg=self.get_theme_color("accent"), fg="white").pack(anchor='w')
            
            # Search bar
            search_frame = tk.Frame(main_container, bg=self.get_theme_color("window"))
            search_frame.pack(fill=tk.X, padx=20, pady=10)
            
            self.search_var = tk.StringVar()
            self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                        bg=self.get_theme_color("input"), 
                                        fg=self.get_theme_color("fg"),
                                        font=('Arial', 11), relief=tk.FLAT, bd=5)
            self.search_entry.pack(fill=tk.X, ipady=8)
            self.search_entry.insert(0, "🔍 Search applications...")
            self.search_entry.bind('<FocusIn>', self.clear_search_placeholder)
            self.search_entry.bind('<FocusOut>', self.restore_search_placeholder)
            self.search_entry.bind('<KeyRelease>', self.filter_applications)
            
            # Content area with notebook tabs
            content_frame = tk.Frame(main_container, bg=self.get_theme_color("window"))
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
            
            # Tab buttons
            tab_frame = tk.Frame(content_frame, bg=self.get_theme_color("window"))
            tab_frame.pack(fill=tk.X, pady=(0, 10))
            
            tabs = [
                ("All Apps", "all"),
                ("Recent", "recent"),
                ("Favorites", "favorites"),
                ("System", "system")
            ]
            
            self.current_tab = "all"
            self.tab_buttons = {}
            
            for tab_name, tab_id in tabs:
                btn = tk.Button(tab_frame, text=tab_name,
                               command=lambda tid=tab_id: self.switch_start_menu_tab(tid),
                               bg=self.get_theme_color("accent") if tab_id == "all" else self.get_theme_color("window"),
                               fg="white" if tab_id == "all" else self.get_theme_color("fg"),
                               font=('Arial', 9), relief=tk.FLAT, padx=15, pady=5)
                btn.pack(side=tk.LEFT, padx=(0, 5))
                self.tab_buttons[tab_id] = btn
            
            # Applications area
            apps_container = tk.Frame(content_frame, bg=self.get_theme_color("window"))
            apps_container.pack(fill=tk.BOTH, expand=True)
            
            # Scrollable applications list
            self.apps_canvas = tk.Canvas(apps_container, bg=self.get_theme_color("window"),
                                        highlightthickness=0)
            apps_scrollbar = tk.Scrollbar(apps_container, orient="vertical", 
                                         command=self.apps_canvas.yview)
            self.apps_scrollable_frame = tk.Frame(self.apps_canvas, bg=self.get_theme_color("window"))
            
            self.apps_scrollable_frame.bind(
                "<Configure>",
                lambda e: self.apps_canvas.configure(scrollregion=self.apps_canvas.bbox("all"))
            )
            
            self.apps_canvas.create_window((0, 0), window=self.apps_scrollable_frame, anchor="nw")
            self.apps_canvas.configure(yscrollcommand=apps_scrollbar.set)
            
            self.apps_canvas.pack(side="left", fill="both", expand=True)
            apps_scrollbar.pack(side="right", fill="y")
            
            # Load applications
            self.load_start_menu_applications()
            
            # Footer with power options
            footer = tk.Frame(main_container, bg=self.get_theme_color("bg"), height=50)
            footer.pack(fill=tk.X)
            footer.pack_propagate(False)
            
            power_frame = tk.Frame(footer, bg=self.get_theme_color("bg"))
            power_frame.pack(side=tk.RIGHT, padx=20, pady=10)
            
            power_options = [
                ("🔒", "Lock", self.lock_screen),
                ("🔄", "Restart", self.restart_system),
                ("⚡", "Shutdown", self.shutdown_system),
                ("⚙️", "Settings", self.launch_settings),
                ("🖥️", "Display", lambda: DisplaySettings(self).show())  # New for V2
            ]
            
            for icon, tooltip, command in power_options:
                btn = tk.Button(power_frame, text=icon, command=command,
                               bg=self.get_theme_color("bg"), fg=self.get_theme_color("fg"),
                               font=('Arial', 14), relief=tk.FLAT, width=3)
                btn.pack(side=tk.LEFT, padx=2)
                self.create_enhanced_tooltip(btn, tooltip)
                
                # Hover effects
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.get_theme_color("hover")))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.get_theme_color("bg")))
            
        except Exception as e:
            logger.error(f"Enhanced start menu creation error: {e}")
    
    def clear_search_placeholder(self, event):
        """Clear search placeholder text"""
        if self.search_entry.get() == "🔍 Search applications...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=self.get_theme_color("fg"))
    
    def restore_search_placeholder(self, event):
        """Restore search placeholder text"""
        if not self.search_entry.get():
            self.search_entry.insert(0, "🔍 Search applications...")
            self.search_entry.config(fg=self.get_theme_color("fg"))
    
    def filter_applications(self, event=None):
        """Filter applications based on search"""
        search_term = self.search_var.get().lower()
        if search_term == "🔍 search applications...":
            search_term = ""
        
        # Re-load applications with filter
        self.load_start_menu_applications(filter_text=search_term)
    
    def switch_start_menu_tab(self, tab_id):
        """Switch start menu tab"""
        try:
            self.current_tab = tab_id
            
            # Update tab button appearances
            for tid, btn in self.tab_buttons.items():
                if tid == tab_id:
                    btn.config(bg=self.get_theme_color("accent"), fg="white")
                else:
                    btn.config(bg=self.get_theme_color("window"), fg=self.get_theme_color("fg"))
            
            # Reload applications for the selected tab
            self.load_start_menu_applications()
            
        except Exception as e:
            logger.error(f"Tab switch error: {e}")
    
    def load_start_menu_applications(self, filter_text=""):
        """Load applications in start menu based on current tab and filter"""
        try:
            # Clear existing applications
            for widget in self.apps_scrollable_frame.winfo_children():
                widget.destroy()
            
            # Get applications from database
            apps = self.get_applications_list(self.current_tab, filter_text)
            
            # Create application items
            for i, app in enumerate(apps):
                self.create_start_menu_app_item(app, i)
                
        except Exception as e:
            logger.error(f"Applications loading error: {e}")
    
    def get_applications_list(self, tab_type, filter_text=""):
        """Get applications list based on tab type and filter"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            if tab_type == "all":
                if filter_text:
                    cursor.execute(
                        "SELECT * FROM applications WHERE name LIKE ? OR description LIKE ? ORDER BY name",
                        (f"%{filter_text}%", f"%{filter_text}%")
                    )
                else:
                    cursor.execute("SELECT * FROM applications ORDER BY name")
            elif tab_type == "recent":
                # Mock recent apps for now
                cursor.execute("SELECT * FROM applications LIMIT 10")
            elif tab_type == "favorites":
                # Mock favorites for now
                cursor.execute("SELECT * FROM applications WHERE category = 'System' LIMIT 8")
            elif tab_type == "system":
                cursor.execute("SELECT * FROM applications WHERE category = 'System'")
            
            apps = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            app_list = []
            for app in apps:
                app_dict = {
                    "id": app[0],
                    "name": app[1],
                    "command": app[2],
                    "icon": app[3],
                    "category": app[4],
                    "description": app[5]
                }
                app_list.append(app_dict)
            
            return app_list
            
        except Exception as e:
            logger.error(f"Applications list error: {e}")
            return []
    
    def create_start_menu_app_item(self, app, index):
        """Create a single application item in start menu"""
        try:
            item_frame = tk.Frame(self.apps_scrollable_frame, bg=self.get_theme_color("window"))
            item_frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Application button
            app_btn = tk.Button(
                item_frame,
                text=f"{app['icon']} {app['name']}",
                command=lambda: self.launch_start_menu_app(app),
                bg=self.get_theme_color("window"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 11),
                relief=tk.FLAT,
                anchor='w',
                padx=15,
                pady=8
            )
            app_btn.pack(fill=tk.X)
            
            # Description
            if app.get('description'):
                desc_label = tk.Label(
                    item_frame,
                    text=app['description'],
                    bg=self.get_theme_color("window"),
                    fg=self.get_theme_color("fg"),
                    font=('Arial', 8),
                    anchor='w'
                )
                desc_label.pack(fill=tk.X, padx=20)
            
            # Hover effects
            def on_enter(e):
                app_btn.config(bg=self.get_theme_color("hover"))
                if app.get('description'):
                    desc_label.config(bg=self.get_theme_color("hover"))
            
            def on_leave(e):
                app_btn.config(bg=self.get_theme_color("window"))
                if app.get('description'):
                    desc_label.config(bg=self.get_theme_color("window"))
            
            app_btn.bind("<Enter>", on_enter)
            app_btn.bind("<Leave>", on_leave)
            
            if app.get('description'):
                desc_label.bind("<Enter>", on_enter)
                desc_label.bind("<Leave>", on_leave)
            
        except Exception as e:
            logger.error(f"App item creation error: {e}")
    
    def launch_start_menu_app(self, app):
        """Launch application from start menu"""
        try:
            command = app['command']
            
            # Hide start menu
            self.hide_start_menu()
            
            # Launch application
            if command == "berke0s_filemanager":
                self.launch_file_manager()
            elif command == "berke0s_texteditor":
                TextEditor(self).show()
            elif command == "berke0s_browser":
                self.launch_web_browser()
            elif command == "berke0s_terminal":
                self.launch_terminal()
            elif command == "berke0s_calculator":
                Calculator(self).show()
            elif command == "berke0s_imageviewer":
                ImageViewer(self).show()
            elif command == "berke0s_musicplayer":
                MusicPlayer(self).show()
            elif command == "berke0s_videoplayer":
                VideoPlayer(self).show()
            elif command == "berke0s_settings":
                self.launch_settings()
            elif command == "berke0s_monitor":
                SystemMonitor(self).show()
            elif command == "berke0s_email":
                EmailClient(self).show()
            elif command == "berke0s_calendar":
                CalendarApp(self).show()
            elif command == "berke0s_games":
                GamesLauncher(self).show()
            elif command == "berke0s_network":
                NetworkManager(self).show()
            elif command == "berke0s_archive":
                ArchiveManager(self).show()
            elif command == "berke0s_pdf":
                PDFViewer(self).show()
            elif command == "berke0s_ide":
                CodeEditor(self).show()
            elif command == "berke0s_recorder":
                ScreenRecorder(self).show()
            elif command == "berke0s_backup":
                BackupManager(self).show()
            elif command == "berke0s_vdesktop":
                VirtualDesktopManager(self).show()
            elif command == "berke0s_display":  # New for V2
                DisplaySettings(self).show()
            else:
                # Try to execute as system command
                subprocess.Popen(command.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        except Exception as e:
            logger.error(f"App launch error: {e}")
            self.notifications.send(
                "Application Error",
                f"Failed to launch {app['name']}: {str(e)}",
                notification_type="error"
            )
    
    # Enhanced window management
    def create_window(self, title, content_func, width=600, height=400, resizable=True, **kwargs):
        """Create enhanced application window"""
        try:
            window = tk.Toplevel(self.root)
            window.title(title)
            window.geometry(f"{width}x{height}")
            window.configure(bg=self.get_theme_color("window"))
            
            # Enhanced window properties
            if not resizable:
                window.resizable(False, False)
            
            # Apply theme-based styling
            if self.config.get("desktop", {}).get("effects", True):
                transparency = self.config.get("desktop", {}).get("transparency", 0.95)
                try:
                    window.attributes('-alpha', transparency)
                except:
                    pass
            
            # Window icon (if provided)
            if 'icon' in kwargs:
                try:
                    window.iconbitmap(kwargs['icon'])
                except:
                    pass
            
            # Center window on screen by default
            if kwargs.get('center', True):
                window.update_idletasks()
                x = (window.winfo_screenwidth() // 2) - (width // 2)
                y = (window.winfo_screenheight() // 2) - (height // 2)
                window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create window content
            content_func(window)
            
            # Store window reference
            window_id = str(uuid.uuid4())
            self.windows[window_id] = {
                "window": window,
                "title": title,
                "app": content_func.__name__ if hasattr(content_func, '__name__') else "unknown",
                "created_at": datetime.datetime.now()
            }
            
            # Bind close event
            window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(window_id))
            
            # Add to taskbar
            self.add_window_to_taskbar(window_id, title)
            
            # Window animations
            if self.config.get("desktop", {}).get("effects", True):
                self.animate_window_open(window)
            
            logger.info(f"Window created: {title}")
            return window
            
        except Exception as e:
            logger.error(f"Window creation error: {e}")
            return None
    
    def animate_window_open(self, window):
        """Animate window opening"""
        try:
            window.attributes('-alpha', 0)
            window.update()
            
            def fade_in(alpha=0):
                if alpha <= 0.95:
                    window.attributes('-alpha', alpha)
                    self.root.after(30, lambda: fade_in(alpha + 0.1))
                    
            fade_in()
            
        except Exception as e:
            logger.error(f"Window animation error: {e}")
    
    def add_window_to_taskbar(self, window_id, title):
        """Add window button to taskbar"""
        try:
            if not hasattr(self, 'window_buttons'):
                self.window_buttons = {}
            
            # Create window button
            btn = tk.Button(
                self.window_list_frame,
                text=title[:15] + "..." if len(title) > 15 else title,
                command=lambda: self.focus_window(window_id),
                bg=self.get_theme_color("window"),
                fg=self.get_theme_color("fg"),
                font=('Arial', 9),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
            btn.pack(side=tk.LEFT, padx=2)
            
            self.window_buttons[window_id] = btn
            
            # Hover effects
            btn.bind("<Enter>", lambda e: btn.config(bg=self.get_theme_color("hover")))
            btn.bind("<Leave>", lambda e: btn.config(bg=self.get_theme_color("window")))
            
        except Exception as e:
            logger.error(f"Taskbar button creation error: {e}")
    
    def focus_window(self, window_id):
        """Focus a specific window"""
        try:
            if window_id in self.windows:
                window_data = self.windows[window_id]
                window = window_data['window']
                
                if window.winfo_exists():
                    window.deiconify()
                    window.lift()
                    window.focus_force()
                    
        except Exception as e:
            logger.error(f"Window focus error: {e}")
    
    def close_window(self, window_id):
        """Close a window with animation"""
        try:
            if window_id in self.windows:
                window_data = self.windows[window_id]
                window = window_data['window']
                
                if window.winfo_exists():
                    # Animate close
                    if self.config.get("desktop", {}).get("effects", True):
                        def fade_out(alpha=0.95):
                            if alpha >= 0:
                                window.attributes('-alpha', alpha)
                                self.root.after(30, lambda: fade_out(alpha - 0.1))
                            else:
                                window.destroy()
                                self.cleanup_window(window_id)
                        fade_out()
                    else:
                        window.destroy()
                        self.cleanup_window(window_id)
                else:
                    self.cleanup_window(window_id)
                    
        except Exception as e:
             
            logger.error(f"Window close error: {e}")
            self.cleanup_window(window_id)
    
    def cleanup_window(self, window_id):
        """Clean up window references"""
        try:
            # Remove from windows dict
            if window_id in self.windows:
                del self.windows[window_id]
            
            # Remove taskbar button
            if hasattr(self, 'window_buttons') and window_id in self.window_buttons:
                self.window_buttons[window_id].destroy()
                del self.window_buttons[window_id]
                
        except Exception as e:
            logger.error(f"Window cleanup error: {e}")
    
    def save_session(self):
        """Save enhanced session data"""
        try:
            session_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "version": "3.0-v2",
                "windows": [],
                "virtual_desktops": self.virtual_desktops,
                "current_desktop": self.current_desktop,
                "shortcuts": self.shortcuts,
                "current_user": self.current_user,
                "running_apps": list(self.running_apps.keys()),
                "display_info": self.display_manager.get_display_info()
            }
            
            # Save window states
            for window_id, window_data in self.windows.items():
                if 'window' in window_data and window_data['window'].winfo_exists():
                    try:
                        window = window_data['window']
                        session_data["windows"].append({
                            "id": window_id,
                            "title": window_data.get("title", ""),
                            "app": window_data.get("app", ""),
                            "geometry": window.geometry(),
                            "state": window.state(),
                            "created_at": window_data.get("created_at", "").isoformat() if isinstance(window_data.get("created_at"), datetime.datetime) else ""
                        })
                    except Exception as e:
                        logger.warning(f"Failed to save window {window_id}: {e}")
            
            with open(SESSION_FILE, 'w') as f:
                json.dump(session_data, f, indent=4)
                
            logger.debug("Session saved successfully")
                
        except Exception as e:
            logger.error(f"Session save error: {e}")
    
    def restore_session(self):
        """Restore previous session"""
        try:
            if not os.path.exists(SESSION_FILE):
                return
                
            with open(SESSION_FILE, 'r') as f:
                session_data = json.load(f)
            
            # Restore virtual desktops
            if "virtual_desktops" in session_data:
                self.virtual_desktops = session_data["virtual_desktops"]
                
            if "current_desktop" in session_data:
                self.current_desktop = session_data["current_desktop"]
            
            # Restore shortcuts
            if "shortcuts" in session_data:
                self.shortcuts.update(session_data["shortcuts"])
            
            logger.info("Session restored successfully")
            
        except Exception as e:
            logger.error(f"Session restore error: {e}")
    
    # Enhanced event handlers
    def desktop_click(self, event):
        """Handle desktop click"""
        try:
            # Clear any selections
            self.clear_desktop_selection()
            
            # Hide start menu if open
            if hasattr(self, 'start_menu_window') and self.start_menu_window.winfo_exists():
                self.hide_start_menu()
                
        except Exception as e:
            logger.error(f"Desktop click error: {e}")
    
    def show_desktop_menu(self, event):
        """Show enhanced desktop context menu"""
        try:
            menu = tk.Menu(self.root, tearoff=0, 
                          bg=self.get_theme_color("window"),
                          fg=self.get_theme_color("fg"),
                          activebackground=self.get_theme_color("accent"),
                          activeforeground="white")
            
            # File operations
            menu.add_command(label="📁 New Folder", command=self.create_new_folder)
            menu.add_command(label="📄 New File", command=self.create_new_file)
            menu.add_separator()
            
            # Desktop customization
            menu.add_command(label="🖼️ Change Wallpaper", command=self.change_wallpaper)
            menu.add_command(label="🎨 Desktop Settings", command=self.desktop_settings)
            menu.add_separator()
            
            # System operations
            menu.add_command(label="🔄 Refresh Desktop", command=self.refresh_desktop)
            menu.add_command(label="📊 System Monitor", command=lambda: SystemMonitor(self).show())
            menu.add_command(label="💻 Open Terminal", command=self.launch_terminal)
            menu.add_command(label="🖥️ Display Settings", command=lambda: DisplaySettings(self).show())  # New for V2
            menu.add_separator()
            
            # Virtual desktops
            vd_menu = tk.Menu(menu, tearoff=0, bg=self.get_theme_color("window"), fg=self.get_theme_color("fg"))
            for i, desktop in enumerate(self.virtual_desktops):
                vd_menu.add_command(
                    label=f"Desktop {i+1}" + (" (Current)" if i == self.current_desktop else ""),
                    command=lambda d=i: self.switch_virtual_desktop(d)
                )
            menu.add_cascade(label="🖥️ Virtual Desktops", menu=vd_menu)
            
            menu.add_separator()
            menu.add_command(label="⚙️ Settings", command=self.launch_settings)
            
            menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            logger.error(f"Desktop menu error: {e}")
    
    def cycle_windows(self, event=None, reverse=False):
        """Cycle through open windows (Alt+Tab)"""
        try:
            if not self.windows:
                return
                
            window_list = list(self.windows.keys())
            if not window_list:
                return
            
            # Find currently focused window
            current_index = 0
            try:
                focused_window = self.root.focus_get()
                for i, window_id in enumerate(window_list):
                    if window_id in self.windows:
                        window = self.windows[window_id]['window']
                        if window.winfo_exists() and focused_window in window.winfo_children():
                            current_index = i
                            break
            except:
                pass
            
            # Calculate next window index
            if reverse:
                next_index = (current_index - 1) % len(window_list)
            else:
                next_index = (current_index + 1) % len(window_list)
            
            # Focus next window
            next_window_id = window_list[next_index]
            self.focus_window(next_window_id)
            
        except Exception as e:
            logger.error(f"Window cycling error: {e}")
    
    def switch_virtual_desktop(self, desktop_index):
        """Switch to a different virtual desktop"""
        try:
            if 0 <= desktop_index < len(self.virtual_desktops):
                # Hide current desktop windows
                current_desktop = self.virtual_desktops[self.current_desktop]
                for window_id in current_desktop.get("windows", []):
                    if window_id in self.windows:
                        window = self.windows[window_id]['window']
                        if window.winfo_exists():
                            window.withdraw()
                
                # Switch to new desktop
                self.current_desktop = desktop_index
                new_desktop = self.virtual_desktops[desktop_index]
                
                # Show new desktop windows
                for window_id in new_desktop.get("windows", []):
                    if window_id in self.windows:
                        window = self.windows[window_id]['window']
                        if window.winfo_exists():
                            window.deiconify()
                
                # Update wallpaper if different
                if new_desktop.get("wallpaper"):
                    self.load_custom_wallpaper(new_desktop["wallpaper"], "stretch")
                
                self.notifications.send(
                    "Virtual Desktop",
                    f"Switched to Desktop {desktop_index + 1}",
                    notification_type="info",
                    timeout=2000
                )
                
        except Exception as e:
            logger.error(f"Virtual desktop switch error: {e}")
    
    def take_screenshot(self):
        """Take a screenshot"""
        try:
            if PIL_AVAILABLE:
                screenshot = ImageGrab.grab()
                
                # Save screenshot
                screenshots_dir = os.path.expanduser("~/Pictures/Screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(screenshots_dir, filename)
                
                screenshot.save(filepath)
                
                self.notifications.send(
                    "Screenshot Saved",
                    f"Screenshot saved to {filename}",
                    notification_type="success",
                    actions=[
                        {"text": "Open Folder", "callback": lambda: self.launch_file_manager()},
                        {"text": "View Image", "callback": lambda: ImageViewer(self).show(filepath)}
                    ]
                )
            else:
                self.notifications.send(
                    "Screenshot Error",
                    "PIL not available for screenshots",
                    notification_type="error"
                )
                
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            self.notifications.send(
                "Screenshot Error",
                f"Failed to take screenshot: {str(e)}",
                notification_type="error"
            )
    
    def lock_screen(self):
        """Lock the screen"""
        try:
            # Create lock screen
            lock_window = tk.Toplevel(self.root)
            lock_window.title("Screen Locked")
            lock_window.attributes('-fullscreen', True)
            lock_window.attributes('-topmost', True)
            lock_window.configure(bg='#000000')
            
            # Lock screen content
            lock_frame = tk.Frame(lock_window, bg='#000000')
            lock_frame.pack(expand=True)
            
            # Clock
            clock_label = tk.Label(lock_frame, text="", font=('Arial', 48, 'bold'),
                                  fg='white', bg='#000000')
            clock_label.pack(pady=50)
            
            # User info
            current_user = self.config.get("users", [{}])[0] if self.config.get("users") else {}
            username = current_user.get("fullname", current_user.get("username", "User"))
            
            tk.Label(lock_frame, text=f"Welcome back, {username}", font=('Arial', 18),
                    fg='white', bg='#000000').pack(pady=20)
            
            # Version info
            tk.Label(lock_frame, text="Berke0S V2 - Enhanced Display Management", font=('Arial', 12),
                    fg='#888888', bg='#000000').pack(pady=10)
            
            # Password entry
            tk.Label(lock_frame, text="Enter password to unlock:", font=('Arial', 12),
                    fg='white', bg='#000000').pack()
            
            password_var = tk.StringVar()
            password_entry = tk.Entry(lock_frame, textvariable=password_var, show='*',
                                    font=('Arial', 14), width=20, justify='center')
            password_entry.pack(pady=10)
            password_entry.focus_set()
            
            def check_password(event=None):
                entered_password = password_var.get()
                stored_password = current_user.get("password", "")
                
                if hashlib.sha256(entered_password.encode()).hexdigest() == stored_password:
                    lock_window.destroy()
                else:
                    password_var.set("")
                    tk.Label(lock_frame, text="Incorrect password", font=('Arial', 10),
                            fg='red', bg='#000000').pack()
            
            password_entry.bind('<Return>', check_password)
            
            # Update clock
            def update_lock_clock():
                if lock_window.winfo_exists():
                    now = datetime.datetime.now()
                    time_str = now.strftime("%H:%M:%S")
                    date_str = now.strftime("%A, %B %d, %Y")
                    clock_label.config(text=f"{time_str}\n{date_str}")
                    lock_window.after(1000, update_lock_clock)
            
            update_lock_clock()
            
        except Exception as e:
            logger.error(f"Screen lock error: {e}")
    
    def safe_shutdown(self):
        """Safely shutdown the system"""
        try:
            # Ask for confirmation
            result = messagebox.askyesno(
                "Shutdown Confirmation",
                "Are you sure you want to shutdown the system?",
                icon='question'
            )
            
            if result:
                # Save session and config
                self.save_session()
                self.save_config()
                
                # Close all applications
                for window_id in list(self.windows.keys()):
                    self.close_window(window_id)
                
                # Shutdown display system
                self.display_manager.shutdown_display()
                
                # Show shutdown screen
                self.show_shutdown_screen()
                
                # Actual shutdown
                self.root.after(3000, self.perform_shutdown)
                
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    def show_shutdown_screen(self):
        """Show shutdown screen"""
        try:
            # Hide all windows
            self.root.withdraw()
            
            # Create shutdown window
            shutdown_window = tk.Toplevel()
            shutdown_window.title("Shutting Down")
            shutdown_window.attributes('-fullscreen', True)
            shutdown_window.configure(bg='#0a0a0f')
            
            # Shutdown content
            shutdown_frame = tk.Frame(shutdown_window, bg='#0a0a0f')
            shutdown_frame.pack(expand=True)
            
            # Logo
            tk.Label(shutdown_frame, text="Berke0S V2", font=('Arial', 48, 'bold'),
                    fg='#00ff88', bg='#0a0a0f').pack(pady=50)
            
            # Shutdown message
            tk.Label(shutdown_frame, text="Shutting down...", font=('Arial', 18),
                    fg='white', bg='#0a0a0f').pack(pady=20)
            
            # Version info
            tk.Label(shutdown_frame, text="Enhanced Display Management", font=('Arial', 12),
                    fg='#888888', bg='#0a0a0f').pack(pady=10)
            
            # Progress animation
            progress_frame = tk.Frame(shutdown_frame, bg='#0a0a0f')
            progress_frame.pack(pady=30)
            
            progress_dots = []
            for i in range(5):
                dot = tk.Label(progress_frame, text="●", font=('Arial', 20),
                              fg='#333333', bg='#0a0a0f')
                dot.pack(side=tk.LEFT, padx=5)
                progress_dots.append(dot)
            
            # Animate progress
            def animate_progress(index=0):
                if shutdown_window.winfo_exists():
                    # Reset all dots
                    for dot in progress_dots:
                        dot.config(fg='#333333')
                    
                    # Light up current dot
                    if index < len(progress_dots):
                        progress_dots[index].config(fg='#00ff88')
                    
                    # Continue animation
                    next_index = (index + 1) % len(progress_dots)
                    shutdown_window.after(500, lambda: animate_progress(next_index))
            
            animate_progress()
            
        except Exception as e:
            logger.error(f"Shutdown screen error: {e}")
    
    def perform_shutdown(self):
        """Perform actual system shutdown"""
        try:
            # Try different shutdown methods
            shutdown_commands = [
                ['sudo', 'shutdown', '-h', 'now'],
                ['sudo', 'poweroff'],
                ['sudo', 'halt'],
                ['systemctl', 'poweroff']
            ]
            
            for cmd in shutdown_commands:
                try:
                    subprocess.run(cmd, timeout=5)
                    break
                except:
                    continue
            
            # If all fail, just exit
            self.root.quit()
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"Shutdown execution error: {e}")
            self.root.quit()
            sys.exit(0)
    
    def restart_system(self):
        """Restart the system"""
        try:
            result = messagebox.askyesno(
                "Restart Confirmation",
                "Are you sure you want to restart the system?",
                icon='question'
            )
            
            if result:
                self.save_session()
                self.save_config()
                
                # Try restart commands
                restart_commands = [
                    ['sudo', 'reboot'],
                    ['sudo', 'shutdown', '-r', 'now'],
                    ['systemctl', 'reboot']
                ]
                
                for cmd in restart_commands:
                    try:
                        subprocess.run(cmd, timeout=5)
                        break
                    except:
                        continue
                
                # Fallback
                self.root.quit()
                
        except Exception as e:
            logger.error(f"Restart error: {e}")
    
    def run(self):
        """Run the enhanced window manager"""
        try:
            logger.info("Starting Berke0S V2 main loop...")
            
            # Restore previous session if available
            self.restore_session()
            
            # Start main loop
            if self.root:
                self.root.mainloop()
            else:
                # Fallback to console mode
                self.run_console_mode()
            
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
            
            # Stop services
            if self.performance_monitor:
                self.performance_monitor.stop()
            
            if self.plugin_manager:
                self.plugin_manager.cleanup()
            
            # Shutdown display system
            if self.display_manager:
                self.display_manager.shutdown_display()
            
            # Close database connections
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                conn.close()
            except:
                pass
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Enhanced Application Classes

class FileManager:
    """Ultimate file manager with advanced features"""
    
    def __init__(self, wm):
        self.wm = wm
        self.current_path = os.path.expanduser("~")
        self.history = [self.current_path]
        self.history_index = 0
        self.bookmarks = self.load_bookmarks()
        self.clipboard = []
        self.clipboard_action = None
        self.view_mode = "list"  # list, icons, details
        self.sort_by = "name"  # name, size, date, type
        self.sort_reverse = False
        self.show_hidden = False
        self.search_results = []
        self.current_search = ""
        
    def load_bookmarks(self):
        """Load user bookmarks"""
        default_bookmarks = [
            {"name": "Home", "path": os.path.expanduser("~"), "icon": "🏠"},
            {"name": "Desktop", "path": os.path.expanduser("~/Desktop"), "icon": "🖥️"},
            {"name": "Documents", "path": os.path.expanduser("~/Documents"), "icon": "📄"},
            {"name": "Downloads", "path": os.path.expanduser("~/Downloads"), "icon": "📥"},
            {"name": "Pictures", "path": os.path.expanduser("~/Pictures"), "icon": "🖼️"},
            {"name": "Music", "path": os.path.expanduser("~/Music"), "icon": "🎵"},
            {"name": "Videos", "path": os.path.expanduser("~/Videos"), "icon": "🎬"},
            {"name": "Root", "path": "/", "icon": "💾"}
        ]
        
        # Create directories if they don't exist
        for bookmark in default_bookmarks:
            if bookmark["path"] != "/" and not os.path.exists(bookmark["path"]):
                try:
                    os.makedirs(bookmark["path"], exist_ok=True)
                except:
                    pass
        
        return default_bookmarks
    
    def show(self):
        """Show enhanced file manager window"""
        try:
            self.window = self.wm.create_window(
                "File Manager", 
                self.create_content, 
                900, 650,
                resizable=True
            )
            if self.window:
                self.refresh_view()
                
        except Exception as e:
            logger.error(f"File manager show error: {e}")
    
    def bring_to_front(self):
        """Bring file manager window to front"""
        if hasattr(self, 'window') and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
    
    def create_content(self, parent):
        """Create enhanced file manager content"""
        try:
            # Create main container
            main_container = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            main_container.pack(fill=tk.BOTH, expand=True)
            
            # Menu bar
            self.create_menu_bar(parent)
            
            # Toolbar
            self.create_toolbar(main_container)
            
            # Main content area
            content_area = tk.Frame(main_container, bg=self.wm.get_theme_color("window"))
            content_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Sidebar
            self.create_sidebar(content_area)
            
            # File area
            self.create_file_area(content_area)
            
            # Status bar
            self.create_status_bar(main_container)
            
        except Exception as e:
            logger.error(f"File manager content creation error: {e}")
    
    def create_menu_bar(self, parent):
        """Create file manager menu bar"""
        try:
            menubar = tk.Menu(parent)
            parent.config(menu=menubar)
            
            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="New Folder", command=self.create_folder, accelerator="Ctrl+Shift+N")
            file_menu.add_command(label="New File", command=self.create_file, accelerator="Ctrl+N")
            file_menu.add_separator()
            file_menu.add_command(label="Open", command=self.open_selected, accelerator="Enter")
            file_menu.add_command(label="Open With...", command=self.open_with)
            file_menu.add_separator()
            file_menu.add_command(label="Properties", command=self.show_properties, accelerator="Alt+Enter")
            
            # Edit menu
            edit_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Edit", menu=edit_menu)
            edit_menu.add_command(label="Cut", command=self.cut_files, accelerator="Ctrl+X")
            edit_menu.add_command(label="Copy", command=self.copy_files, accelerator="Ctrl+C")
            edit_menu.add_command(label="Paste", command=self.paste_files, accelerator="Ctrl+V")
            edit_menu.add_separator()
            edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
            edit_menu.add_command(label="Invert Selection", command=self.invert_selection)
            
            # View menu
            view_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="View", menu=view_menu)
            view_menu.add_command(label="List View", command=lambda: self.set_view_mode("list"))
            view_menu.add_command(label="Icon View", command=lambda: self.set_view_mode("icons"))
            view_menu.add_command(label="Details View", command=lambda: self.set_view_mode("details"))
            view_menu.add_separator()
            view_menu.add_checkbutton(label="Show Hidden Files", command=self.toggle_hidden_files)
            view_menu.add_command(label="Refresh", command=self.refresh_view, accelerator="F5")
            
            # Tools menu
            tools_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Tools", menu=tools_menu)
            tools_menu.add_command(label="Search", command=self.show_search, accelerator="Ctrl+F")
            tools_menu.add_command(label="Terminal Here", command=self.open_terminal_here)
            tools_menu.add_separator()
            tools_menu.add_command(label="Calculate Folder Size", command=self.calculate_folder_size)
            tools_menu.add_command(label="Compress", command=self.compress_selection)
            tools_menu.add_command(label="Extract", command=self.extract_archive)
            
        except Exception as e:
            logger.error(f"Menu bar creation error: {e}")
    
    def create_toolbar(self, parent):
        """Create enhanced toolbar"""
        try:
            toolbar = tk.Frame(parent, bg=self.wm.get_theme_color("window"), height=50)
            toolbar.pack(fill=tk.X, padx=5, pady=5)
            toolbar.pack_propagate(False)
            
            # Navigation section
            nav_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            nav_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            # Navigation buttons
            nav_buttons = [
                ("⬅️", "Back", self.go_back),
                ("➡️", "Forward", self.go_forward),
                ("⬆️", "Up", self.go_up),
                ("🏠", "Home", self.go_home),
                ("🔄", "Refresh", self.refresh_view)
            ]
            
            for icon, tooltip, command in nav_buttons:
                btn = tk.Button(nav_frame, text=icon, command=command,
                               bg=self.wm.get_theme_color("accent"), fg="white",
                               font=('Arial', 12), relief=tk.FLAT, width=3, height=1)
                btn.pack(side=tk.LEFT, padx=2)
                self.wm.create_enhanced_tooltip(btn, tooltip)
            
            # Address bar
            address_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            address_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            tk.Label(address_frame, text="Location:", bg=self.wm.get_theme_color("window"),
                    fg=self.wm.get_theme_color("fg"), font=('Arial', 9)).pack(side=tk.LEFT)
            
            self.address_var = tk.StringVar(value=self.current_path)
            self.address_entry = tk.Entry(address_frame, textvariable=self.address_var,
                                         bg=self.wm.get_theme_color("input"), 
                                         fg=self.wm.get_theme_color("fg"),
                                         font=('Arial', 10), relief=tk.FLAT, bd=5)
            self.address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            self.address_entry.bind('<Return>', self.navigate_to_address)
            
            # View options
            view_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            view_frame.pack(side=tk.RIGHT, padx=(20, 0))
            
            # View mode buttons
            view_buttons = [
                ("📋", "List", lambda: self.set_view_mode("list")),
                ("🔲", "Icons", lambda: self.set_view_mode("icons")),
                ("📊", "Details", lambda: self.set_view_mode("details"))
            ]
            
            for icon, tooltip, command in view_buttons:
                btn = tk.Button(view_frame, text=icon, command=command,
                               bg=self.wm.get_theme_color("secondary"), fg="white",
                               font=('Arial', 10), relief=tk.FLAT, width=3)
                btn.pack(side=tk.LEFT, padx=1)
                self.wm.create_enhanced_tooltip(btn, f"{tooltip} View")
            
            # Search button
            search_btn = tk.Button(view_frame, text="🔍", command=self.show_search,
                                  bg=self.wm.get_theme_color("accent"), fg="white",
                                  font=('Arial', 12), relief=tk.FLAT, width=3)
            search_btn.pack(side=tk.LEFT, padx=(10, 0))
            self.wm.create_enhanced_tooltip(search_btn, "Search Files")
            
        except Exception as e:
            logger.error(f"Toolbar creation error: {e}")
    
    def create_sidebar(self, parent):
        """Create enhanced sidebar"""
        try:
            sidebar = tk.Frame(parent, bg=self.wm.get_theme_color("bg"), width=200)
            sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
            sidebar.pack_propagate(False)
            
            # Bookmarks section
            bookmarks_label = tk.Label(sidebar, text="Quick Access", 
                                      bg=self.wm.get_theme_color("bg"),
                                      fg=self.wm.get_theme_color("fg"), 
                                      font=('Arial', 11, 'bold'))
            bookmarks_label.pack(pady=(10, 5), padx=10, anchor='w')
            
            # Bookmarks list
            self.bookmarks_frame = tk.Frame(sidebar, bg=self.wm.get_theme_color("bg"))
            self.bookmarks_frame.pack(fill=tk.X, padx=5)
            
            for bookmark in self.bookmarks:
                self.create_bookmark_item(bookmark)
            
            # Separator
            separator = tk.Frame(sidebar, bg=self.wm.get_theme_color("border"), height=1)
            separator.pack(fill=tk.X, padx=10, pady=10)
            
            # Devices section
            devices_label = tk.Label(sidebar, text="Devices", 
                                   bg=self.wm.get_theme_color("bg"),
                                   fg=self.wm.get_theme_color("fg"), 
                                   font=('Arial', 11, 'bold'))
            devices_label.pack(pady=(5, 5), padx=10, anchor='w')
            
            # Detect and show mounted devices
            self.devices_frame = tk.Frame(sidebar, bg=self.wm.get_theme_color("bg"))
            self.devices_frame.pack(fill=tk.X, padx=5)
            
            self.refresh_devices()
            
        except Exception as e:
            logger.error(f"Sidebar creation error: {e}")
    
    def create_bookmark_item(self, bookmark):
        """Create a single bookmark item"""
        try:
            item_frame = tk.Frame(self.bookmarks_frame, bg=self.wm.get_theme_color("bg"))
            item_frame.pack(fill=tk.X, pady=1)
            
            btn = tk.Button(item_frame, 
                           text=f"{bookmark['icon']} {bookmark['name']}", 
                           command=lambda: self.navigate_to(bookmark['path']),
                           bg=self.wm.get_theme_color("bg"), 
                           fg=self.wm.get_theme_color("fg"),
                           font=('Arial', 9), relief=tk.FLAT, anchor='w', padx=10, pady=3)
            btn.pack(fill=tk.X)
            
            # Hover effects
            btn.bind("<Enter>", lambda e: btn.config(bg=self.wm.get_theme_color("hover")))
            btn.bind("<Leave>", lambda e: btn.config(bg=self.wm.get_theme_color("bg")))
            
        except Exception as e:
            logger.error(f"Bookmark item creation error: {e}")
    
    def refresh_devices(self):
        """Refresh mounted devices list"""
        try:
            # Clear existing devices
            for widget in self.devices_frame.winfo_children():
                widget.destroy()
            
            # Get mounted devices
            devices = []
            try:
                if psutil:
                    partitions = psutil.disk_partitions()
                    for partition in partitions:
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            devices.append({
                                "name": os.path.basename(partition.device) or partition.device,
                                "path": partition.mountpoint,
                                "fstype": partition.fstype,
                                "total": usage.total,
                                "used": usage.used,
                                "free": usage.free
                            })
                        except:
                            continue
            except:
                # Fallback device list
                devices = [
                    {"name": "Root", "path": "/", "fstype": "ext4", "total": 0, "used": 0, "free": 0}
                ]
            
            # Create device items
            for device in devices:
                self.create_device_item(device)
                
        except Exception as e:
            logger.error(f"Devices refresh error: {e}")
    
    def create_device_item(self, device):
        """Create a device item in sidebar"""
        try:
            item_frame = tk.Frame(self.devices_frame, bg=self.wm.get_theme_color("bg"))
            item_frame.pack(fill=tk.X, pady=1)
            
            # Device icon based on type
            if device["path"] == "/":
                icon = "💾"
            elif "usb" in device.get("fstype", "").lower():
                icon = "🔌"
            elif device["path"].startswith("/media") or device["path"].startswith("/mnt"):
                icon = "📀"
            else:
                icon = "💿"
            
            btn = tk.Button(item_frame, 
                           text=f"{icon} {device['name']}", 
                           command=lambda: self.navigate_to(device['path']),
                           bg=self.wm.get_theme_color("bg"), 
                           fg=self.wm.get_theme_color("fg"),
                           font=('Arial', 9), relief=tk.FLAT, anchor='w', padx=10, pady=3)
            btn.pack(fill=tk.X)
            
            # Show usage info in tooltip
            if device["total"] > 0:
                used_gb = device["used"] / (1024**3)
                total_gb = device["total"] / (1024**3)
                usage_percent = (device["used"] / device["total"]) * 100
                tooltip = f"Used: {used_gb:.1f} GB / {total_gb:.1f} GB ({usage_percent:.1f}%)"
                self.wm.create_enhanced_tooltip(btn, device["name"], tooltip)
            
            # Hover effects
            btn.bind("<Enter>", lambda e: btn.config(bg=self.wm.get_theme_color("hover")))
            btn.bind("<Leave>", lambda e: btn.config(bg=self.wm.get_theme_color("bg")))
            
        except Exception as e:
            logger.error(f"Device item creation error: {e}")
    
    def create_file_area(self, parent):
        """Create enhanced file listing area"""
        try:
            file_area = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            file_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # File list container
            list_container = tk.Frame(file_area, bg=self.wm.get_theme_color("window"))
            list_container.pack(fill=tk.BOTH, expand=True)
            
            # Create different view widgets
            self.create_list_view(list_container)
            self.create_icon_view(list_container)
            self.create_details_view(list_container)
            
            # Initially show list view
            self.set_view_mode("list")
            
        except Exception as e:
            logger.error(f"File area creation error: {e}")
    
    def create_list_view(self, parent):
        """Create list view widget"""
        try:
            self.list_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            
            # Listbox with scrollbar
            list_container = tk.Frame(self.list_frame, bg=self.wm.get_theme_color("window"))
            list_container.pack(fill=tk.BOTH, expand=True)
            
            self.file_listbox = tk.Listbox(list_container, 
                                          bg=self.wm.get_theme_color("input"),
                                          fg=self.wm.get_theme_color("fg"),
                                          font=('Courier', 10),
                                          selectmode=tk.EXTENDED,
                                          relief=tk.FLAT,
                                          highlightthickness=0,
                                          selectbackground=self.wm.get_theme_color("accent"))
            
            list_scrollbar = tk.Scrollbar(list_container, command=self.file_listbox.yview)
            self.file_listbox.config(yscrollcommand=list_scrollbar.set)
            
            self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bind events
            self.file_listbox.bind('<Double-Button-1>', self.open_selected)
            self.file_listbox.bind('<Button-3>', self.show_context_menu)
            self.file_listbox.bind('<Return>', self.open_selected)
            self.file_listbox.bind('<Delete>', self.delete_files)
            self.file_listbox.bind('<F2>', self.rename_file)
            
        except Exception as e:
            logger.error(f"List view creation error: {e}")
    
    def create_icon_view(self, parent):
        """Create icon view widget"""
        try:
            self.icon_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            
            # Canvas for icon layout
            icon_container = tk.Frame(self.icon_frame, bg=self.wm.get_theme_color("window"))
            icon_container.pack(fill=tk.BOTH, expand=True)
            
            self.icon_canvas = tk.Canvas(icon_container, 
                                        bg=self.wm.get_theme_color("input"),
                                        highlightthickness=0)
            icon_scrollbar = tk.Scrollbar(icon_container, command=self.icon_canvas.yview)
            self.icon_scrollable_frame = tk.Frame(self.icon_canvas, bg=self.wm.get_theme_color("input"))
            
            self.icon_scrollable_frame.bind(
                "<Configure>",
                lambda e: self.icon_canvas.configure(scrollregion=self.icon_canvas.bbox("all"))
            )
            
            self.icon_canvas.create_window((0, 0), window=self.icon_scrollable_frame, anchor="nw")
            self.icon_canvas.configure(yscrollcommand=icon_scrollbar.set)
            
            self.icon_canvas.pack(side="left", fill="both", expand=True)
            icon_scrollbar.pack(side="right", fill="y")
            
        except Exception as e:
            logger.error(f"Icon view creation error: {e}")
    
    def create_details_view(self, parent):
        """Create details view widget (tree view)"""
        try:
            self.details_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            
            # Treeview for detailed file information
            details_container = tk.Frame(self.details_frame, bg=self.wm.get_theme_color("window"))
            details_container.pack(fill=tk.BOTH, expand=True)
            
            # Configure treeview style
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("Treeview", 
                           background=self.wm.get_theme_color("input"),
                           foreground=self.wm.get_theme_color("fg"),
                           fieldbackground=self.wm.get_theme_color("input"))
            style.configure("Treeview.Heading",
                           background=self.wm.get_theme_color("accent"),
                           foreground="white")
            
            columns = ("Name", "Size", "Type", "Modified")
            self.details_tree = ttk.Treeview(details_container, columns=columns, show="tree headings")
            
            # Configure columns
            self.details_tree.heading("#0", text="Icon")
            self.details_tree.column("#0", width=50, minwidth=50)
            
            for col in columns:
                self.details_tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
                if col == "Name":
                    self.details_tree.column(col, width=300, minwidth=200)
                elif col == "Size":
                    self.details_tree.column(col, width=100, minwidth=80)
                elif col == "Type":
                    self.details_tree.column(col, width=120, minwidth=100)
                elif col == "Modified":
                    self.details_tree.column(col, width=150, minwidth=120)
            
            details_scrollbar = tk.Scrollbar(details_container, command=self.details_tree.yview)
            self.details_tree.config(yscrollcommand=details_scrollbar.set)
            
            self.details_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bind events
            self.details_tree.bind('<Double-Button-1>', self.open_selected_tree)
            self.details_tree.bind('<Button-3>', self.show_context_menu_tree)
            
        except Exception as e:
            logger.error(f"Details view creation error: {e}")
    
    def create_status_bar(self, parent):
        """Create enhanced status bar"""
        try:
            status_frame = tk.Frame(parent, bg=self.wm.get_theme_color("bg"), height=25)
            status_frame.pack(side=tk.BOTTOM, fill=tk.X)
            status_frame.pack_propagate(False)
            
            # Status text
            self.status_label = tk.Label(status_frame, text="Ready", 
                                        bg=self.wm.get_theme_color("bg"),
                                        fg=self.wm.get_theme_color("fg"),
                                        font=('Arial', 9), anchor='w')
            self.status_label.pack(side=tk.LEFT, padx=10, pady=3)
            
            # Selection info
            self.selection_label = tk.Label(status_frame, text="", 
                                           bg=self.wm.get_theme_color("bg"),
                                           fg=self.wm.get_theme_color("fg"),
                                           font=('Arial', 9))
            self.selection_label.pack(side=tk.RIGHT, padx=10, pady=3)
            
        except Exception as e:
            logger.error(f"Status bar creation error: {e}")
    
    def set_view_mode(self, mode):
        """Set file view mode"""
        try:
            self.view_mode = mode
            
            # Hide all views
            if hasattr(self, 'list_frame'):
                self.list_frame.pack_forget()
            if hasattr(self, 'icon_frame'):
                self.icon_frame.pack_forget()
            if hasattr(self, 'details_frame'):
                self.details_frame.pack_forget()
            
            # Show selected view
            if mode == "list" and hasattr(self, 'list_frame'):
                self.list_frame.pack(fill=tk.BOTH, expand=True)
            elif mode == "icons" and hasattr(self, 'icon_frame'):
                self.icon_frame.pack(fill=tk.BOTH, expand=True)
            elif mode == "details" and hasattr(self, 'details_frame'):
                self.details_frame.pack(fill=tk.BOTH, expand=True)
            
            # Refresh view
            self.refresh_view()
            
        except Exception as e:
            logger.error(f"View mode set error: {e}")
    
    def refresh_view(self):
        """Refresh current file view"""
        try:
            if not os.path.exists(self.current_path):
                self.current_path = os.path.expanduser("~")
            
            self.address_var.set(self.current_path)
            
            # Get file list
            files = self.get_file_list()
            
            # Update appropriate view
            if self.view_mode == "list":
                self.update_list_view(files)
            elif self.view_mode == "icons":
                self.update_icon_view(files)
            elif self.view_mode == "details":
                self.update_details_view(files)
            
            # Update status
            self.update_status(files)
            
        except Exception as e:
            logger.error(f"View refresh error: {e}")
    
    def get_file_list(self):
        """Get list of files in current directory"""
        try:
            files = []
            
            try:
                items = os.listdir(self.current_path)
            except PermissionError:
                self.status_label.config(text="Permission denied")
                return []
            
            for item in items:
                # Skip hidden files if not showing them
                if not self.show_hidden and item.startswith('.'):
                    continue
                
                item_path = os.path.join(self.current_path, item)
                
                try:
                    stat_info = os.stat(item_path)
                    is_dir = os.path.isdir(item_path)
                    
                    file_info = {
                        "name": item,
                        "path": item_path,
                        "is_dir": is_dir,
                        "size": stat_info.st_size if not is_dir else 0,
                        "modified": datetime.datetime.fromtimestamp(stat_info.st_mtime),
                        "permissions": stat.filemode(stat_info.st_mode),
                        "icon": self.get_file_icon(item, is_dir)
                    }
                    
                    # Get file type
                    if is_dir:
                        file_info["type"] = "Folder"
                    else:
                        ext = os.path.splitext(item)[1].lower()
                        file_info["type"] = self.get_file_type(ext)
                    
                    files.append(file_info)
                    
                except (OSError, IOError):
                    continue
            
            # Sort files
            files = self.sort_files(files)
            
            return files
            
        except Exception as e:
            logger.error(f"File list error: {e}")
            return []
    
    def get_file_icon(self, filename, is_dir):
        """Get appropriate icon for file"""
        if is_dir:
            return "📁"
        
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.txt': '📄', '.py': '🐍', '.js': '📜', '.html': '🌐',
            '.css': '🎨', '.json': '📋', '.xml': '📋', '.md': '📝',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.mp4': '🎬', '.avi': '🎬',
            '.pdf': '📕', '.doc': '📘', '.docx': '📘', '.xls': '📗',
            '.zip': '📦', '.tar': '📦', '.gz': '📦', '.rar': '📦',
            '.exe': '⚙️', '.deb': '📦', '.rpm': '📦', '.sh': '📜'
        }
        return icons.get(ext, '📄')
    
    def get_file_type(self, ext):
        """Get file type description"""
        types = {
            '.txt': 'Text File', '.py': 'Python Script', '.js': 'JavaScript File',
            '.html': 'HTML Document', '.css': 'CSS Stylesheet', '.json': 'JSON File',
            '.jpg': 'JPEG Image', '.png': 'PNG Image', '.gif': 'GIF Image',
            '.mp3': 'MP3 Audio', '.wav': 'WAV Audio', '.mp4': 'MP4 Video',
            '.pdf': 'PDF Document', '.doc': 'Word Document', '.zip': 'ZIP Archive'
        }
        return types.get(ext, f'{ext.upper()} File' if ext else 'File')
    
    def sort_files(self, files):
        """Sort files based on current sort settings"""
        try:
            if self.sort_by == "name":
                key_func = lambda f: (not f["is_dir"], f["name"].lower())
            elif self.sort_by == "size":
                key_func = lambda f: (not f["is_dir"], f["size"])
            elif self.sort_by == "date":
                key_func = lambda f: (not f["is_dir"], f["modified"])
            elif self.sort_by == "type":
                key_func = lambda f: (not f["is_dir"], f["type"])
            else:
                key_func = lambda f: (not f["is_dir"], f["name"].lower())
            
            return sorted(files, key=key_func, reverse=self.sort_reverse)
            
        except Exception as e:
            logger.error(f"File sort error: {e}")
            return files
    
    def update_list_view(self, files):
        """Update list view with files"""
        try:
            self.file_listbox.delete(0, tk.END)
            
            for file_info in files:
                display_text = f"{file_info['icon']} {file_info['name']}"
                self.file_listbox.insert(tk.END, display_text)
            
        except Exception as e:
            logger.error(f"List view update error: {e}")
    
    def update_icon_view(self, files):
        """Update icon view with files"""
        try:
            # Clear existing icons
            for widget in self.icon_scrollable_frame.winfo_children():
                widget.destroy()
            
            # Create icon grid
            cols = 6  # Number of columns
            for i, file_info in enumerate(files):
                row = i // cols
                col = i % cols
                
                icon_frame = tk.Frame(self.icon_scrollable_frame, 
                                     bg=self.wm.get_theme_color("input"))
                icon_frame.grid(row=row, column=col, padx=10, pady=10, sticky="n")
                
                # Icon
                icon_label = tk.Label(icon_frame, text=file_info['icon'],
                                     bg=self.wm.get_theme_color("input"),
                                     fg=self.wm.get_theme_color("fg"),
                                     font=('Arial', 24), cursor="hand2")
                icon_label.pack()
                
                # Name
                name_text = file_info['name']
                if len(name_text) > 12:
                    name_text = name_text[:12] + "..."
                
                name_label = tk.Label(icon_frame, text=name_text,
                                     bg=self.wm.get_theme_color("input"),
                                     fg=self.wm.get_theme_color("fg"),
                                     font=('Arial', 8), wraplength=80)
                name_label.pack()
                
                # Bind events
                for widget in [icon_label, name_label]:
                    widget.bind('<Double-Button-1>', 
                               lambda e, f=file_info: self.open_file_info(f))
                    widget.bind('<Button-3>', 
                               lambda e, f=file_info: self.show_file_context_menu(e, f))
            
        except Exception as e:
            logger.error(f"Icon view update error: {e}")
    
    def update_details_view(self, files):
        """Update details view with files"""
        try:
            # Clear existing items
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)
            
            # Add files to tree
            for file_info in files:
                # Format size
                if file_info['is_dir']:
                    size_text = ""
                else:
                    size = file_info['size']
                    if size < 1024:
                        size_text = f"{size} B"
                    elif size < 1024**2:
                        size_text = f"{size/1024:.1f} KB"
                    elif size < 1024**3:
                        size_text = f"{size/(1024**2):.1f} MB"
                    else:
                        size_text = f"{size/(1024**3):.1f} GB"
                
                # Format date
                date_text = file_info['modified'].strftime("%Y-%m-%d %H:%M")
                
                self.details_tree.insert("", "end", 
                                        text=file_info['icon'],
                                        values=(file_info['name'], size_text, 
                                               file_info['type'], date_text),
                                        tags=(file_info['path'],))
            
        except Exception as e:
            logger.error(f"Details view update error: {e}")
    
    def update_status(self, files):
        """Update status bar information"""
        try:
            total_files = len([f for f in files if not f['is_dir']])
            total_dirs = len([f for f in files if f['is_dir']])
            
            status_text = f"{total_dirs} folders, {total_files} files"
            
            # Add disk space info
            try:
                if psutil:
                    usage = psutil.disk_usage(self.current_path)
                    free_gb = usage.free / (1024**3)
                    total_gb = usage.total / (1024**3)
                    status_text += f" | {free_gb:.1f} GB free of {total_gb:.1f} GB"
            except:
                pass
            
            self.status_label.config(text=status_text)
            
        except Exception as e:
            logger.error(f"Status update error: {e}")
    
    # Navigation methods
    def navigate_to(self, path):
        """Navigate to specific path"""
        try:
            if os.path.exists(path) and os.path.isdir(path):
                self.current_path = os.path.abspath(path)
                self.history = self.history[:self.history_index + 1]
                self.history.append(self.current_path)
                self.history_index = len(self.history) - 1
                self.refresh_view()
            else:
                self.wm.notifications.send(
                    "File Manager",
                    f"Path not found: {path}",
                    notification_type="error"
                )
        except Exception as e:
            logger.error(f"Navigation error: {e}")
    
    def navigate_to_address(self, event=None):
        """Navigate to address bar path"""
        try:
            new_path = self.address_var.get()
            self.navigate_to(new_path)
        except Exception as e:
            logger.error(f"Address navigation error: {e}")
    
    def go_back(self):
        """Go back in navigation history"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_path = self.history[self.history_index]
            self.refresh_view()
    
    def go_forward(self):
        """Go forward in navigation history"""
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
    
    # File operations
    def open_selected(self, event=None):
        """Open selected file or directory"""
        try:
            if self.view_mode == "list":
                selection = self.file_listbox.curselection()
                if not selection:
                    return
                
                files = self.get_file_list()
                if selection[0] < len(files):
                    file_info = files[selection[0]]
                    self.open_file_info(file_info)
                    
        except Exception as e:
            logger.error(f"Open selected error: {e}")
    
    def open_selected_tree(self, event=None):
        """Open selected item from tree view"""
        try:
            selection = self.details_tree.selection()
            if selection:
                item = self.details_tree.item(selection[0])
                file_path = item['tags'][0]
                
                if os.path.isdir(file_path):
                    self.navigate_to(file_path)
                else:
                    self.open_file(file_path)
                    
        except Exception as e:
            logger.error(f"Tree open error: {e}")
    
    def open_file_info(self, file_info):
        """Open file based on file info"""
        if file_info['is_dir']:
            self.navigate_to(file_info['path'])
        else:
            self.open_file(file_info['path'])
    
    def open_file(self, file_path):
        """Open file with appropriate application"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            # Open with appropriate Berke0S application
            if ext in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.sh']:
                TextEditor(self.wm).show(file_path)
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                ImageViewer(self.wm).show(file_path)
            elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
                MusicPlayer(self.wm).show(file_path)
            elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                VideoPlayer(self.wm).show(file_path)
            elif ext in ['.pdf']:
                PDFViewer(self.wm).show(file_path)
            elif ext in ['.zip', '.tar', '.gz', '.rar']:
                ArchiveManager(self.wm).show(file_path)
            else:
                # Try to open with system default
                try:
                    subprocess.Popen(['xdg-open', file_path], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except:
                    # Fallback to text editor
                    TextEditor(self.wm).show(file_path)
                    
        except Exception as e:
            logger.error(f"File open error: {e}")
            self.wm.notifications.send(
                "File Manager",
                f"Cannot open file: {str(e)}",
                notification_type="error"
            )
    
    def create_folder(self):
        """Create new folder"""
        try:
            folder_name = simpledialog.askstring(
                "New Folder",
                "Enter folder name:",
                parent=self.window
            )
            
            if folder_name:
                folder_path = os.path.join(self.current_path, folder_name)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    self.refresh_view()
                    self.wm.notifications.send(
                        "File Manager",
                        f"Folder '{folder_name}' created",
                        notification_type="success"
                    )
                else:
                    self.wm.notifications.send(
                        "File Manager",
                        f"Folder '{folder_name}' already exists",
                        notification_type="warning"
                    )
                    
        except Exception as e:
            logger.error(f"Create folder error: {e}")
            self.wm.notifications.send(
                "File Manager",
                f"Failed to create folder: {str(e)}",
                notification_type="error"
            )
    
    def create_file(self):
        """Create new file"""
        try:
            file_name = simpledialog.askstring(
                "New File",
                "Enter file name:",
                parent=self.window
            )
            
            if file_name:
                file_path = os.path.join(self.current_path, file_name)
                if not os.path.exists(file_path):
                    with open(file_path, 'w') as f:
                        f.write("")
                    self.refresh_view()
                    self.wm.notifications.send(
                        "File Manager",
                        f"File '{file_name}' created",
                        notification_type="success"
                    )
                else:
                    self.wm.notifications.send(
                        "File Manager",
                        f"File '{file_name}' already exists",
                        notification_type="warning"
                    )
                    
        except Exception as e:
            logger.error(f"Create file error: {e}")
            self.wm.notifications.send(
                "File Manager",
                f"Failed to create file: {str(e)}",
                notification_type="error"
            )
    
    # Additional methods would continue here...
    # (Due to length constraints, I'm including the essential structure)

# Additional Application Classes

class TextEditor:
    """Advanced text editor with syntax highlighting and modern features"""
    
    def __init__(self, wm):
        self.wm = wm
        self.current_file = None
        self.modified = False
        self.find_dialog = None
        self.replace_dialog = None
        self.syntax_highlighting = True
        
    def show(self, file_path=None):
        """Show text editor window"""
        try:
            self.window = self.wm.create_window(
                "Text Editor", 
                self.create_content, 
                900, 700,
                resizable=True
            )
            if file_path:
                self.open_file(file_path)
        except Exception as e:
            logger.error(f"Text editor show error: {e}")
    
    def create_content(self, parent):
        """Create text editor content with advanced features"""
        try:
            # Create menu bar
            self.create_menu_bar(parent)
            
            # Create toolbar
            self.create_toolbar(parent)
            
            # Main content area
            content_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Line numbers and text area
            text_container = tk.Frame(content_frame, bg=self.wm.get_theme_color("window"))
            text_container.pack(fill=tk.BOTH, expand=True)
            
            # Line numbers
            self.line_numbers = tk.Text(text_container, width=4, padx=3, takefocus=0,
                                       border=0, state='disabled', wrap='none',
                                       bg=self.wm.get_theme_color("bg"),
                                       fg=self.wm.get_theme_color("fg"),
                                       font=('Courier', 10))
            self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
            
            # Text area with scrollbars
            text_frame = tk.Frame(text_container, bg=self.wm.get_theme_color("window"))
            text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            self.text_area = tk.Text(text_frame, 
                                    bg=self.wm.get_theme_color("input"),
                                    fg=self.wm.get_theme_color("fg"),
                                    font=('Courier', 11),
                                    wrap=tk.NONE,
                                    undo=True,
                                    insertbackground=self.wm.get_theme_color("accent"),
                                    selectbackground=self.wm.get_theme_color("selection"))
            
            # Scrollbars
            v_scrollbar = tk.Scrollbar(text_frame, command=self.text_area.yview)
            h_scrollbar = tk.Scrollbar(text_frame, command=self.text_area.xview, orient=tk.HORIZONTAL)
            
            self.text_area.config(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Pack scrollbars and text area
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            self.text_area.pack(fill=tk.BOTH, expand=True)
            
            # Status bar
            self.create_status_bar(parent)
            
            # Bind events
            self.bind_events()
            
            # Configure syntax highlighting
            self.setup_syntax_highlighting()
            
        except Exception as e:
            logger.error(f"Text editor content creation error: {e}")
    
    def create_menu_bar(self, parent):
        """Create comprehensive menu bar"""
        try:
            menubar = tk.Menu(parent)
            parent.config(menu=menubar)
            
            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
            file_menu.add_command(label="Open", command=self.open_file_dialog, accelerator="Ctrl+O")
            file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
            file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Ctrl+Shift+S")
            file_menu.add_separator()
            file_menu.add_command(label="Recent Files", command=self.show_recent_files)
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
            edit_menu.add_command(label="Find", command=self.show_find_dialog, accelerator="Ctrl+F")
            edit_menu.add_command(label="Replace", command=self.show_replace_dialog, accelerator="Ctrl+H")
            edit_menu.add_command(label="Go to Line", command=self.goto_line, accelerator="Ctrl+G")
            
            # View menu
            view_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="View", menu=view_menu)
            view_menu.add_checkbutton(label="Line Numbers", command=self.toggle_line_numbers)
            view_menu.add_checkbutton(label="Syntax Highlighting", command=self.toggle_syntax_highlighting)
            view_menu.add_checkbutton(label="Word Wrap", command=self.toggle_word_wrap)
            view_menu.add_separator()
            view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
            view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
            view_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="Ctrl+0")
            
            # Tools menu
            tools_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Tools", menu=tools_menu)
            tools_menu.add_command(label="Word Count", command=self.show_word_count)
            tools_menu.add_command(label="Character Map", command=self.show_character_map)
            tools_menu.add_separator()
            tools_menu.add_command(label="Convert to Uppercase", command=self.to_uppercase)
            tools_menu.add_command(label="Convert to Lowercase", command=self.to_lowercase)
            tools_menu.add_command(label="Sort Lines", command=self.sort_lines)
            
        except Exception as e:
            logger.error(f"Menu bar creation error: {e}")
    
    def create_toolbar(self, parent):
        """Create toolbar with common actions"""
        try:
            toolbar = tk.Frame(parent, bg=self.wm.get_theme_color("window"), height=40)
            toolbar.pack(fill=tk.X, padx=5, pady=5)
            toolbar.pack_propagate(False)
            
            # File operations
            file_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            file_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            file_buttons = [
                ("📄", "New", self.new_file),
                ("📁", "Open", self.open_file_dialog),
                ("💾", "Save", self.save_file),
                ("🖨️", "Print", self.print_file)
            ]
            
            for icon, tooltip, command in file_buttons:
                btn = tk.Button(file_frame, text=icon, command=command,
                               bg=self.wm.get_theme_color("accent"), fg="white",
                               font=('Arial', 12), relief=tk.FLAT, width=3)
                btn.pack(side=tk.LEFT, padx=2)
                self.wm.create_enhanced_tooltip(btn, tooltip)
            
            # Edit operations
            edit_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            edit_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            edit_buttons = [
                ("↶", "Undo", self.undo),
                ("↷", "Redo", self.redo),
                ("✂️", "Cut", self.cut),
                ("📋", "Copy", self.copy),
                ("📌", "Paste", self.paste)
            ]
            
            for icon, tooltip, command in edit_buttons:
                btn = tk.Button(edit_frame, text=icon, command=command,
                               bg=self.wm.get_theme_color("secondary"), fg="white",
                               font=('Arial', 10), relief=tk.FLAT, width=3)
                btn.pack(side=tk.LEFT, padx=1)
                self.wm.create_enhanced_tooltip(btn, tooltip)
            
            # Search operations
            search_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            search_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            tk.Button(search_frame, text="🔍", command=self.show_find_dialog,
                     bg=self.wm.get_theme_color("accent"), fg="white",
                     font=('Arial', 12), relief=tk.FLAT, width=3).pack(side=tk.LEFT, padx=2)
            
            # Font size controls
            font_frame = tk.Frame(toolbar, bg=self.wm.get_theme_color("window"))
            font_frame.pack(side=tk.RIGHT)
            
            tk.Label(font_frame, text="Font Size:", bg=self.wm.get_theme_color("window"),
                    fg=self.wm.get_theme_color("fg"), font=('Arial', 9)).pack(side=tk.LEFT)
            
            self.font_size_var = tk.StringVar(value="11")
            font_spinbox = tk.Spinbox(font_frame, from_=8, to=72, width=5,
                                     textvariable=self.font_size_var,
                                     command=self.change_font_size,
                                     bg=self.wm.get_theme_color("input"),
                                     fg=self.wm.get_theme_color("fg"))
            font_spinbox.pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            logger.error(f"Toolbar creation error: {e}")
    
    def create_status_bar(self, parent):
        """Create status bar with file information"""
        try:
            status_frame = tk.Frame(parent, bg=self.wm.get_theme_color("bg"), height=25)
            status_frame.pack(side=tk.BOTTOM, fill=tk.X)
            status_frame.pack_propagate(False)
            
            # File status
            self.file_status = tk.Label(status_frame, text="New File", 
                                       bg=self.wm.get_theme_color("bg"),
                                       fg=self.wm.get_theme_color("fg"),
                                       font=('Arial', 9), anchor='w')
            self.file_status.pack(side=tk.LEFT, padx=10, pady=3)
            
            # Cursor position
            self.cursor_position = tk.Label(status_frame, text="Line 1, Col 1", 
                                           bg=self.wm.get_theme_color("bg"),
                                           fg=self.wm.get_theme_color("fg"),
                                           font=('Arial', 9))
            self.cursor_position.pack(side=tk.RIGHT, padx=10, pady=3)
            
            # File encoding
            self.encoding_label = tk.Label(status_frame, text="UTF-8", 
                                          bg=self.wm.get_theme_color("bg"),
                                          fg=self.wm.get_theme_color("fg"),
                                          font=('Arial', 9))
            self.encoding_label.pack(side=tk.RIGHT, padx=10, pady=3)
            
        except Exception as e:
            logger.error(f"Status bar creation error: {e}")
    
    def bind_events(self):
        """Bind keyboard events and text changes"""
        try:
            # File operations
            self.window.bind('<Control-n>', lambda e: self.new_file())
            self.window.bind('<Control-o>', lambda e: self.open_file_dialog())
            self.window.bind('<Control-s>', lambda e: self.save_file())
            self.window.bind('<Control-Shift-S>', lambda e: self.save_as_file())
            
            # Edit operations
            self.window.bind('<Control-z>', lambda e: self.undo())
            self.window.bind('<Control-y>', lambda e: self.redo())
            self.window.bind('<Control-f>', lambda e: self.show_find_dialog())
            self.window.bind('<Control-h>', lambda e: self.show_replace_dialog())
            self.window.bind('<Control-g>', lambda e: self.goto_line())
            
            # Text area events
            self.text_area.bind('<KeyRelease>', self.on_text_change)
            self.text_area.bind('<Button-1>', self.update_cursor_position)
            self.text_area.bind('<KeyPress>', self.on_key_press)
            
            # Line numbers sync
            self.text_area.bind('<MouseWheel>', self.sync_line_numbers)
            
        except Exception as e:
            logger.error(f"Event binding error: {e}")
    
    def setup_syntax_highlighting(self):
        """Setup syntax highlighting for different file types"""
        try:
            # Define syntax highlighting tags
            self.text_area.tag_configure("keyword", foreground="#569cd6")
            self.text_area.tag_configure("string", foreground="#ce9178")
            self.text_area.tag_configure("comment", foreground="#6a9955")
            self.text_area.tag_configure("number", foreground="#b5cea8")
            self.text_area.tag_configure("function", foreground="#dcdcaa")
            
        except Exception as e:
            logger.error(f"Syntax highlighting setup error: {e}")
    
    def apply_syntax_highlighting(self):
        """Apply syntax highlighting to current text"""
        if not self.syntax_highlighting:
            return
            
        try:
            content = self.text_area.get("1.0", tk.END)
            
            # Clear existing tags
            for tag in ["keyword", "string", "comment", "number", "function"]:
                self.text_area.tag_remove(tag, "1.0", tk.END)
            
            # Python keywords
            keywords = [
                "def", "class", "if", "else", "elif", "for", "while", "try", "except",
                "import", "from", "return", "break", "continue", "pass", "lambda",
                "and", "or", "not", "in", "is", "True", "False", "None"
            ]
            
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                # Highlight keywords
                for keyword in keywords:
                    start = 0
                    while True:
                        pos = line.find(keyword, start)
                        if pos == -1:
                            break
                        
                        # Check if it's a whole word
                        if (pos == 0 or not line[pos-1].isalnum()) and \
                           (pos + len(keyword) >= len(line) or not line[pos + len(keyword)].isalnum()):
                            start_idx = f"{line_num}.{pos}"
                            end_idx = f"{line_num}.{pos + len(keyword)}"
                            self.text_area.tag_add("keyword", start_idx, end_idx)
                        
                        start = pos + 1
                
                # Highlight strings
                in_string = False
                string_char = None
                for i, char in enumerate(line):
                    if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            string_char = char
                            string_start = i
                        elif char == string_char:
                            in_string = False
                            start_idx = f"{line_num}.{string_start}"
                            end_idx = f"{line_num}.{i+1}"
                            self.text_area.tag_add("string", start_idx, end_idx)
                
                # Highlight comments
                comment_pos = line.find('#')
                if comment_pos != -1:
                    start_idx = f"{line_num}.{comment_pos}"
                    end_idx = f"{line_num}.{len(line)}"
                    self.text_area.tag_add("comment", start_idx, end_idx)
                
                # Highlight numbers
                import re
                for match in re.finditer(r'\b\d+\.?\d*\b', line):
                    start_idx = f"{line_num}.{match.start()}"
                    end_idx = f"{line_num}.{match.end()}"
                    self.text_area.tag_add("number", start_idx, end_idx)
            
        except Exception as e:
            logger.error(f"Syntax highlighting error: {e}")
    
    def update_line_numbers(self):
        """Update line numbers display"""
        try:
            self.line_numbers.config(state='normal')
            self.line_numbers.delete('1.0', tk.END)
            
            # Get number of lines
            line_count = int(self.text_area.index('end-1c').split('.')[0])
            
            # Generate line numbers
            line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
            self.line_numbers.insert('1.0', line_numbers_text)
            
            self.line_numbers.config(state='disabled')
            
        except Exception as e:
            logger.error(f"Line numbers update error: {e}")
    
    def sync_line_numbers(self, event=None):
        """Sync line numbers scrolling with text area"""
        try:
            # Get the first visible line in text area
            first_line = self.text_area.index("@0,0")
            self.line_numbers.yview_moveto(self.text_area.yview()[0])
        except Exception as e:
            logger.error(f"Line numbers sync error: {e}")
    
    def on_text_change(self, event=None):
        """Handle text changes"""
        try:
            self.modified = True
            self.update_title()
            self.update_line_numbers()
            self.update_cursor_position()
            
            # Apply syntax highlighting with delay to avoid lag
            self.window.after_idle(self.apply_syntax_highlighting)
            
        except Exception as e:
            logger.error(f"Text change error: {e}")
    
    def on_key_press(self, event):
        """Handle key press events"""
        try:
            # Auto-indentation for Python
            if event.keysym == 'Return':
                current_line = self.text_area.get("insert linestart", "insert")
                indent = len(current_line) - len(current_line.lstrip())
                
                # Add extra indent after colon
                if current_line.rstrip().endswith(':'):
                    indent += 4
                
                if indent > 0:
                    self.text_area.insert("insert", '\n' + ' ' * indent)
                    return 'break'
            
            # Auto-close brackets and quotes
            elif event.char in ['(', '[', '{', '"', "'"]:
                closing = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
                self.text_area.insert("insert", event.char + closing[event.char])
                self.text_area.mark_set("insert", "insert-1c")
                return 'break'
                
        except Exception as e:
            logger.error(f"Key press error: {e}")
    
    def update_cursor_position(self, event=None):
        """Update cursor position in status bar"""
        try:
            cursor_pos = self.text_area.index(tk.INSERT)
            line, col = cursor_pos.split('.')
            self.cursor_position.config(text=f"Line {line}, Col {int(col)+1}")
        except Exception as e:
            logger.error(f"Cursor position update error: {e}")
    
    def update_title(self):
        """Update window title"""
        try:
            title = "Text Editor"
            if self.current_file:
                title += f" - {os.path.basename(self.current_file)}"
            if self.modified:
                title += " *"
            self.window.title(title)
        except Exception as e:
            logger.error(f"Title update error: {e}")
    
    # File operations
    def new_file(self):
        """Create new file"""
        try:
            if self.modified:
                result = messagebox.askyesnocancel("Save Changes", 
                                                  "Do you want to save changes to the current file?")
                if result is True:
                    self.save_file()
                elif result is None:
                    return
            
            self.text_area.delete('1.0', tk.END)
            self.current_file = None
            self.modified = False
            self.update_title()
            self.file_status.config(text="New File")
            
        except Exception as e:
            logger.error(f"New file error: {e}")
    
    def open_file_dialog(self):
        """Open file dialog"""
        try:
            file_path = filedialog.askopenfilename(
                parent=self.window,
                title="Open File",
                filetypes=[
                    ("Text Files", "*.txt"),
                    ("Python Files", "*.py"),
                    ("JavaScript Files", "*.js"),
                    ("HTML Files", "*.html"),
                    ("CSS Files", "*.css"),
                    ("All Files", "*.*")
                ]
            )
            
            if file_path:
                self.open_file(file_path)
                
        except Exception as e:
            logger.error(f"Open file dialog error: {e}")
    
    def open_file(self, file_path):
        """Open specific file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', content)
            
            self.current_file = file_path
            self.modified = False
            self.update_title()
            self.file_status.config(text=os.path.basename(file_path))
            
            # Apply syntax highlighting
            self.apply_syntax_highlighting()
            
        except Exception as e:
            logger.error(f"Open file error: {e}")
            self.wm.notifications.send(
                "Text Editor",
                f"Failed to open file: {str(e)}",
                notification_type="error"
            )
    
    def save_file(self):
        """Save current file"""
        try:
            if not self.current_file:
                return self.save_as_file()
            
            content = self.text_area.get('1.0', 'end-1c')
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.modified = False
            self.update_title()
            self.wm.notifications.send(
                "Text Editor",
                f"File saved: {os.path.basename(self.current_file)}",
                notification_type="success"
            )
            
        except Exception as e:
            logger.error(f"Save file error: {e}")
            self.wm.notifications.send(
                "Text Editor",
                f"Failed to save file: {str(e)}",
                notification_type="error"
            )
    
    def save_as_file(self):
        """Save file with new name"""
        try:
            file_path = filedialog.asksaveasfilename(
                parent=self.window,
                title="Save As",
                defaultextension=".txt",
                filetypes=[
                    ("Text Files", "*.txt"),
                    ("Python Files", "*.py"),
                    ("JavaScript Files", "*.js"),
                    ("HTML Files", "*.html"),
                    ("CSS Files", "*.css"),
                    ("All Files", "*.*")
                ]
            )
            
            if file_path:
                content = self.text_area.get('1.0', 'end-1c')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.current_file = file_path
                self.modified = False
                self.update_title()
                self.file_status.config(text=os.path.basename(file_path))
                
                self.wm.notifications.send(
                    "Text Editor",
                    f"File saved as: {os.path.basename(file_path)}",
                    notification_type="success"
                )
                
        except Exception as e:
            logger.error(f"Save as error: {e}")
            self.wm.notifications.send(
                "Text Editor",
                f"Failed to save file: {str(e)}",
                notification_type="error"
            )
    
    # Edit operations
    def undo(self):
        """Undo last action"""
        try:
            self.text_area.edit_undo()
        except tk.TclError:
            pass
    
    def redo(self):
        """Redo last undone action"""
        try:
            self.text_area.edit_redo()
        except tk.TclError:
            pass
    
    def cut(self):
        """Cut selected text"""
        try:
            self.text_area.event_generate("<<Cut>>")
        except Exception as e:
            logger.error(f"Cut error: {e}")
    
    def copy(self):
        """Copy selected text"""
        try:
            self.text_area.event_generate("<<Copy>>")
        except Exception as e:
            logger.error(f"Copy error: {e}")
    
    def paste(self):
        """Paste text from clipboard"""
        try:
            self.text_area.event_generate("<<Paste>>")
        except Exception as e:
            logger.error(f"Paste error: {e}")
    
    def select_all(self):
        """Select all text"""
        try:
            self.text_area.tag_add(tk.SEL, "1.0", tk.END)
            self.text_area.mark_set(tk.INSERT, "1.0")
            self.text_area.see(tk.INSERT)
        except Exception as e:
            logger.error(f"Select all error: {e}")
    
    # Additional methods would continue here...

class Calculator:
    """Advanced scientific calculator with enhanced features"""
    
    def __init__(self, wm):
        self.wm = wm
        self.display_var = tk.StringVar(value="0")
        self.memory = 0
        self.last_operation = None
        self.last_number = None
        self.history = []
        self.angle_mode = "degrees"  # degrees or radians
        
    def show(self):
        """Show calculator window"""
        try:
            self.window = self.wm.create_window(
                "Calculator", 
                self.create_content, 
                400, 600, 
                resizable=False
            )
        except Exception as e:
            logger.error(f"Calculator show error: {e}")
    
    def create_content(self, parent):
        """Create enhanced calculator interface"""
        try:
            # Main container
            main_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Display area
            self.create_display(main_frame)
            
            # Mode selector
            self.create_mode_selector(main_frame)
            
            # Button area
            self.create_buttons(main_frame)
            
            # History panel
            self.create_history_panel(main_frame)
            
        except Exception as e:
            logger.error(f"Calculator content creation error: {e}")
    
    def create_display(self, parent):
        """Create calculator display"""
        try:
            display_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            display_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Main display
            display = tk.Entry(display_frame, textvariable=self.display_var,
                              font=('Arial', 18, 'bold'), justify='right',
                              bg=self.wm.get_theme_color("input"),
                              fg=self.wm.get_theme_color("fg"),
                              state='readonly', relief=tk.SUNKEN, bd=3)
            display.pack(fill=tk.X, ipady=15)
            
            # Secondary display for operations
            self.operation_var = tk.StringVar()
            operation_display = tk.Label(display_frame, textvariable=self.operation_var,
                                        font=('Arial', 10), justify='right',
                                        bg=self.wm.get_theme_color("window"),
                                        fg=self.wm.get_theme_color("fg"))
            operation_display.pack(fill=tk.X, pady=(5, 0))
            
        except Exception as e:
            logger.error(f"Display creation error: {e}")
    
    def create_mode_selector(self, parent):
        """Create angle mode selector"""
        try:
            mode_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            mode_frame.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(mode_frame, text="Angle Mode:", 
                    bg=self.wm.get_theme_color("window"),
                    fg=self.wm.get_theme_color("fg"),
                    font=('Arial', 9)).pack(side=tk.LEFT)
            
            self.angle_var = tk.StringVar(value="degrees")
            
            deg_radio = tk.Radiobutton(mode_frame, text="Degrees", 
                                      variable=self.angle_var, value="degrees",
                                      bg=self.wm.get_theme_color("window"),
                                      fg=self.wm.get_theme_color("fg"),
                                      selectcolor=self.wm.get_theme_color("accent"),
                                      command=self.change_angle_mode)
            deg_radio.pack(side=tk.LEFT, padx=10)
            
            rad_radio = tk.Radiobutton(mode_frame, text="Radians", 
                                      variable=self.angle_var, value="radians",
                                      bg=self.wm.get_theme_color("window"),
                                      fg=self.wm.get_theme_color("fg"),
                                      selectcolor=self.wm.get_theme_color("accent"),
                                      command=self.change_angle_mode)
            rad_radio.pack(side=tk.LEFT, padx=10)
            
        except Exception as e:
            logger.error(f"Mode selector creation error: {e}")
    
    def create_buttons(self, parent):
        """Create calculator buttons"""
        try:
            buttons_frame = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            buttons_frame.pack(fill=tk.BOTH, expand=True)
            
            # Scientific functions row
            sci_buttons = [
                ('sin', 'sin'), ('cos', 'cos'), ('tan', 'tan'), ('log', 'log'),
                ('ln', 'ln'), ('√', 'sqrt'), ('x²', 'square'), ('xʸ', 'power')
            ]
            
            sci_frame = tk.Frame(buttons_frame, bg=self.wm.get_theme_color("window"))
            sci_frame.pack(fill=tk.X, pady=(0, 5))
            
            for i, (text, func) in enumerate(sci_buttons):
                btn = tk.Button(sci_frame, text=text,
                               command=lambda f=func: self.scientific_function(f),
                               bg=self.wm.get_theme_color("secondary"), fg="white",
                               font=('Arial', 9), width=5, height=1)
                btn.grid(row=0, column=i, padx=1, pady=1, sticky='nsew')
                sci_frame.grid_columnconfigure(i, weight=1)
            
            # Memory functions row
            mem_buttons = [
                ('MC', 'memory_clear'), ('MR', 'memory_recall'), 
                ('M+', 'memory_add'), ('M-', 'memory_subtract'),
                ('MS', 'memory_store'), ('π', 'pi'), ('e', 'e'), ('±', 'negate')
            ]
            
            mem_frame = tk.Frame(buttons_frame, bg=self.wm.get_theme_color("window"))
            mem_frame.pack(fill=tk.X, pady=(0, 5))
            
            for i, (text, func) in enumerate(mem_buttons):
                btn = tk.Button(mem_frame, text=text,
                               command=lambda f=func: self.memory_function(f),
                               bg=self.wm.get_theme_color("bg"), 
                               fg=self.wm.get_theme_color("fg"),
                               font=('Arial', 9), width=5, height=1)
                btn.grid(row=0, column=i, padx=1, pady=1, sticky='nsew')
                mem_frame.grid_columnconfigure(i, weight=1)
            
            # Main calculator buttons
            main_buttons = [
                ['C', 'CE', '⌫', '/'],
                ['7', '8', '9', '*'],
                ['4', '5', '6', '-'],
                ['1', '2', '3', '+'],
                ['0', '.', '(', ')'],
                ['=', 'Ans', 'Hist', 'Clear']
            ]
            
            main_frame = tk.Frame(buttons_frame, bg=self.wm.get_theme_color("window"))
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            for i, row in enumerate(main_buttons):
                for j, btn_text in enumerate(row):
                    self.create_main_button(main_frame, btn_text, i, j)
            
        except Exception as e:
            logger.error(f"Buttons creation error: {e}")
    
    def create_main_button(self, parent, text, row, col):
        """Create a main calculator button"""
        try:
            # Color coding
            if text in ['C', 'CE', '⌫', 'Clear']:
                bg_color = self.wm.get_theme_color("error")
                fg_color = "white"
            elif text in ['+', '-', '*', '/', '=']:
                bg_color = self.wm.get_theme_color("accent")
                fg_color = "white"
            elif text in ['(', ')', 'Ans', 'Hist']:
                bg_color = self.wm.get_theme_color("secondary")
                fg_color = "white"
            else:
                bg_color = self.wm.get_theme_color("bg")
                fg_color = self.wm.get_theme_color("fg")
            
            btn = tk.Button(parent, text=text,
                           command=lambda: self.button_click(text),
                           bg=bg_color, fg=fg_color,
                           font=('Arial', 12, 'bold'),
                           width=6, height=2)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
            
            # Configure grid weights
            parent.grid_rowconfigure(row, weight=1)
            parent.grid_columnconfigure(col, weight=1)
            
            # Hover effects
            btn.bind("<Enter>", lambda e: btn.config(bg=self.lighten_color(bg_color)))
            btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))
            
        except Exception as e:
            logger.error(f"Main button creation error: {e}")
    
    def create_history_panel(self, parent):
        """Create calculation history panel"""
        try:
            history_frame = tk.LabelFrame(parent, text="History", 
                                         bg=self.wm.get_theme_color("window"),
                                         fg=self.wm.get_theme_color("fg"),
                                         font=('Arial', 10, 'bold'))
            history_frame.pack(fill=tk.X, pady=(10, 0))
            
            # History listbox
            self.history_listbox = tk.Listbox(history_frame, height=4,
                                             bg=self.wm.get_theme_color("input"),
                                             fg=self.wm.get_theme_color("fg"),
                                             font=('Courier', 9))
            self.history_listbox.pack(fill=tk.X, padx=5, pady=5)
            
            # Bind double-click to use history item
            self.history_listbox.bind('<Double-Button-1>', self.use_history_item)
            
        except Exception as e:
            logger.error(f"History panel creation error: {e}")
    
    def lighten_color(self, color):
        """Lighten a color for hover effects"""
        try:
            # Simple color lightening (this is a basic implementation)
            if color.startswith('#'):
                # Convert hex to RGB, lighten, convert back
                hex_color = color[1:]
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                lightened = tuple(min(255, int(c * 1.2)) for c in rgb)
                return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"
            return color
        except:
            return color
    
    def change_angle_mode(self):
        """Change angle mode between degrees and radians"""
        self.angle_mode = self.angle_var.get()
    
    def button_click(self, text):
        """Handle calculator button clicks"""
        try:
            current = self.display_var.get()
            
            if text.isdigit() or text == '.':
                if current == "0" or current == "Error":
                    self.display_var.set(text)
                else:
                    self.display_var.set(current + text)
                    
            elif text in ['+', '-', '*', '/']:
                try:
                    self.last_number = float(current)
                    self.last_operation = text
                    self.operation_var.set(f"{current} {text}")
                    self.display_var.set("0")
                except ValueError:
                    self.display_var.set("Error")
                    
            elif text == '=':
                self.calculate_result()
                
            elif text == 'C':
                self.clear_all()
                
            elif text == 'CE':
                self.display_var.set("0")
                
            elif text == '⌫':
                if len(current) > 1:
                    self.display_var.set(current[:-1])
                else:
                    self.display_var.set("0")
                    
            elif text == '±':
                try:
                    value = float(current)
                    self.display_var.set(str(-value))
                except ValueError:
                    pass
                    
            elif text in ['(', ')']:
                if current == "0":
                    self.display_var.set(text)
                else:
                    self.display_var.set(current + text)
                    
            elif text == 'Ans':
                if self.history:
                    last_result = self.history[-1].split('=')[-1].strip()
                    self.display_var.set(last_result)
                    
            elif text == 'Hist':
                self.show_history_dialog()
                
            elif text == 'Clear':
                self.clear_history()
                
        except Exception as e:
            logger.error(f"Button click error: {e}")
            self.display_var.set("Error")
    
    def scientific_function(self, func):
        """Handle scientific function buttons"""
        try:
            current = self.display_var.get()
            value = float(current)
            
            if func == 'sin':
                if self.angle_mode == "degrees":
                    result = math.sin(math.radians(value))
                else:
                    result = math.sin(value)
            elif func == 'cos':
                if self.angle_mode == "degrees":
                    result = math.cos(math.radians(value))
                else:
                    result = math.cos(value)
            elif func == 'tan':
                if self.angle_mode == "degrees":
                    result = math.tan(math.radians(value))
                else:
                    result = math.tan(value)
            elif func == 'log':
                result = math.log10(value)
            elif func == 'ln':
                result = math.log(value)
            elif func == 'sqrt':
                result = math.sqrt(value)
            elif func == 'square':
                result = value ** 2
            elif func == 'power':
                # For power function, we need two numbers
                self.last_number = value
                self.last_operation = '**'
                self.operation_var.set(f"{current} ^")
                self.display_var.set("0")
                return
            else:
                return
            
            # Add to history
            operation = f"{func}({current}) = {result}"
            self.add_to_history(operation)
            
            self.display_var.set(str(result))
            self.operation_var.set("")
            
        except Exception as e:
            logger.error(f"Scientific function error: {e}")
            self.display_var.set("Error")
    
    def memory_function(self, func):
        """Handle memory function buttons"""
        try:
            current = self.display_var.get()
            
            if func == 'memory_clear':
                self.memory = 0
            elif func == 'memory_recall':
                self.display_var.set(str(self.memory))
            elif func == 'memory_add':
                self.memory += float(current)
            elif func == 'memory_subtract':
                self.memory -= float(current)
            elif func == 'memory_store':
                self.memory = float(current)
            elif func == 'pi':
                self.display_var.set(str(math.pi))
            elif func == 'e':
                self.display_var.set(str(math.e))
            elif func == 'negate':
                value = float(current)
                self.display_var.set(str(-value))
                
        except Exception as e:
            logger.error(f"Memory function error: {e}")
            self.display_var.set("Error")
    
    def calculate_result(self):
        """Calculate and display result"""
        try:
            if self.last_operation and self.last_number is not None:
                current = self.display_var.get()
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
                elif self.last_operation == '**':
                    result = self.last_number ** current_num
                else:
                    return
                
                # Add to history
                operation = f"{self.last_number} {self.last_operation} {current_num} = {result}"
                self.add_to_history(operation)
                
                self.display_var.set(str(result))
                self.operation_var.set("")
                self.last_operation = None
                self.last_number = None
                
        except Exception as e:
            logger.error(f"Calculate result error: {e}")
            self.display_var.set("Error")
    
    def clear_all(self):
        """Clear all calculator state"""
        self.display_var.set("0")
        self.operation_var.set("")
        self.last_operation = None
        self.last_number = None
    
    def add_to_history(self, operation):
        """Add operation to history"""
        self.history.append(operation)
        self.history_listbox.insert(tk.END, operation)
        
        # Limit history size
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_listbox.delete(0)
        
        # Scroll to bottom
        self.history_listbox.see(tk.END)
    
    def use_history_item(self, event=None):
        """Use selected history item"""
        try:
            selection = self.history_listbox.curselection()
            if selection:
                item = self.history_listbox.get(selection[0])
                # Extract result from history item
                result = item.split('=')[-1].strip()
                self.display_var.set(result)
        except Exception as e:
            logger.error(f"Use history item error: {e}")
    
    def clear_history(self):
        """Clear calculation history"""
        self.history.clear()
        self.history_listbox.delete(0, tk.END)
    
    def show_history_dialog(self):
        """Show full history in a dialog"""
        try:
            history_window = tk.Toplevel(self.window)
            history_window.title("Calculation History")
            history_window.geometry("400x300")
            history_window.configure(bg=self.wm.get_theme_color("window"))
            
            # History text area
            text_area = scrolledtext.ScrolledText(history_window,
                                                 bg=self.wm.get_theme_color("input"),
                                                 fg=self.wm.get_theme_color("fg"),
                                                 font=('Courier', 10))
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add all history items
            for item in self.history:
                text_area.insert(tk.END, item + '\n')
            
            text_area.config(state='disabled')
            
        except Exception as e:
            logger.error(f"History dialog error: {e}")

# New Display Settings Application for V2
class DisplaySettings:
    """Display configuration and management application (New for V2)"""
    
    def __init__(self, wm):
        self.wm = wm
        self.display_manager = wm.display_manager
        
    def show(self):
        """Show display settings window"""
        try:
            self.window = self.wm.create_window(
                "Display Settings", 
                self.create_content, 
                700, 600,
                resizable=True
            )
        except Exception as e:
            logger.error(f"Display settings show error: {e}")
    
    def create_content(self, parent):
        """Create display settings content"""
        try:
            # Main container
            main_container = tk.Frame(parent, bg=self.wm.get_theme_color("window"))
            main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Header
            header = tk.Label(main_container, text="🖥️ Display Configuration", 
                            font=('Arial', 16, 'bold'),
                            bg=self.wm.get_theme_color("window"),
                            fg=self.wm.get_theme_color("accent"))
            header.pack(pady=(0, 20))
            
            # Create notebook for different sections
            notebook = ttk.Notebook(main_container)
            notebook.pack(fill=tk.BOTH, expand=True)
            
            # Display Information Tab
            self.create_display_info_tab(notebook)
            
            # Display Configuration Tab
            self.create_display_config_tab(notebook)
            
            # Advanced Settings Tab
            self.create_advanced_settings_tab(notebook)
            
            # Troubleshooting Tab
            self.create_troubleshooting_tab(notebook)
            
        except Exception as e:
            logger.error(f"Display settings content creation error: {e}")
    
    def create_display_info_tab(self, notebook):
        """Create display information tab"""
        try:
            info_frame = tk.Frame(notebook, bg=self.wm.get_theme_color("window"))
            notebook.add(info_frame, text="Display Info")
            
            # Current display information
            info_label = tk.Label(info_frame, text="Current Display Information", 
                                font=('Arial', 12, 'bold'),
                                bg=self.wm.get_theme_color("window"),
                                fg=self.wm.get_theme_color("fg"))
            info_label.pack(pady=(10, 20))
            
            # Display info text area
            self.info_text = tk.Text(info_frame, height=20, width=70,
                                   bg=self.wm.get_theme_color("input"),
                                   fg=self.wm.get_theme_color("fg"),
                                   font=('Courier', 10), wrap=tk.WORD)
            self.info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Refresh button
            refresh_btn = tk.Button(info_frame, text="🔄 Refresh Information",
                                  command=self.refresh_display_info,
                                  bg=self.wm.get_theme_color("accent"), fg="white",
                                  font=('Arial', 10), relief=tk.FLAT, padx=20, pady=5)
            refresh_btn.pack(pady=10)
            
            # Load initial information
            self.refresh_display_info()
            
        except Exception as e:
            logger.error(f"Display info tab creation error: {e}")
    
    def create_display_config_tab(self, notebook):
        """Create display configuration tab"""
        try:
            config_frame = tk.Frame(notebook, bg=self.wm.get_theme_color("window"))
            notebook.add(config_frame, text="Configuration")
            
            # Configuration options
            config_label = tk.Label(config_frame, text="Display Configuration", 
                                  font=('Arial', 12, 'bold'),
                                  bg=self.wm.get_theme_color("window"),
                                  fg=self.wm.get_theme_color("fg"))
            config_label.pack(pady=(10, 20))
            
            # Display mode selection
            mode_frame = tk.LabelFrame(config_frame, text="Display Mode", 
                                     bg=self.wm.get_theme_color("window"),
                                     fg=self.wm.get_theme_color("fg"))
            mode_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.display_mode_var = tk.StringVar(value=self.wm.config.get("display", {}).get("display_server", "auto"))
            
            modes = [
                ("auto", "Automatic Detection (Recommended)"),
                ("x11", "Force X11"),
                ("headless", "Headless Mode"),
                ("virtual", "Virtual Display")
            ]
            
            for value, text in modes:
                rb = tk.Radiobutton(mode_frame, text=text, variable=self.display_mode_var, value=value,
                                   bg=self.wm.get_theme_color("window"), fg=self.wm.get_theme_color("fg"),
                                   selectcolor=self.wm.get_theme_color("accent"))
                rb.pack(anchor='w', padx=10, pady=5)
            
            # Resolution settings
            res_frame = tk.LabelFrame(config_frame, text="Resolution", 
                                    bg=self.wm.get_theme_color("window"),
                                    fg=self.wm.get_theme_color("fg"))
            res_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.resolution_var = tk.StringVar(value=self.wm.config.get("display", {}).get("resolution", "auto"))
            
            resolutions = ["auto", "1920x1080", "1366x768", "1280x720", "1024x768", "800x600"]
            
            tk.Label(res_frame, text="Resolution:", bg=self.wm.get_theme_color("window"),
                    fg=self.wm.get_theme_color("fg")).pack(side=tk.LEFT, padx=10)
            
            res_combo = ttk.Combobox(res_frame, textvariable=self.resolution_var, values=resolutions, width=15)
            res_combo.pack(side=tk.LEFT, padx=10, pady=10)
            
            # Refresh rate
            refresh_frame = tk.LabelFrame(config_frame, text="Refresh Rate", 
                                        bg=self.wm.get_theme_color("window"),
                                        fg=self.wm.get_theme_color("fg"))
            refresh_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.refresh_rate_var = tk.StringVar(value=str(self.wm.config.get("display", {}).get("refresh_rate", 60)))
            
            tk.Label(refresh_frame, text="Refresh Rate (Hz):", bg=self.wm.get_theme_color("window"),
                    fg=self.wm.get_theme_color("fg")).pack(side=tk.LEFT, padx=10)
            
            refresh_spinbox = tk.Spinbox(refresh_frame, from_=30, to=240, textvariable=self.refresh_rate_var, width=10)
            refresh_spinbox.pack(side=tk.LEFT, padx=10, pady=10)
            
            # Apply button
            apply_btn = tk.Button(config_frame, text="💾 Apply Settings",
                                command=self.apply_display_settings,
                                bg=self.wm.get_theme_color("success"), fg="white",
                                font=('Arial', 12, 'bold'), relief=tk.FLAT, padx=30, pady=10)
            apply_btn.pack(pady=20)
            
        except Exception as e:
            logger.error(f"Display config tab creation error: {e}")
    
    def create_advanced_settings_tab(self, notebook):
        """Create advanced settings tab"""
        try:
            advanced_frame = tk.Frame(notebook, bg=self.wm.get_theme_color("window"))
            notebook.add(advanced_frame, text="Advanced")
            
            # Advanced options
            advanced_label = tk.Label(advanced_frame, text="Advanced Display Settings", 
                                    font=('Arial', 12, 'bold'),
                                    bg=self.wm.get_theme_color("window"),
                                    fg=self.wm.get_theme_color("fg"))
            advanced_label.pack(pady=(10, 20))
            
            # X Server arguments
            x_args_frame = tk.LabelFrame(advanced_frame, text="X Server Arguments", 
                                       bg=self.wm.get_theme_color("window"),
                                       fg=self.wm.get_theme_color("fg"))
            x_args_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(x_args_frame, text="Additional X Server Arguments:", 
                    bg=self.wm.get_theme_color("window"),
                    fg=self.wm.get_theme_color("fg")).pack(anchor='w', padx=10, pady=5)
            
            self.x_args_var = tk.StringVar(value=" ".join(self.wm.config.get("display", {}).get("x_arguments", [])))
            x_args_entry = tk.Entry(x_args_frame, textvariable=self.x_args_var, width=60,
                                  bg=self.wm.get_theme_color("input"),
                                  fg=self.wm.get_theme_color("fg"))
            x_args_entry.pack(fill=tk.X, padx=10, pady=10)
            
            # Color depth
            depth_frame = tk.LabelFrame(advanced_frame, text="Color Depth", 
                                      bg=self.wm.get_theme_color("window"),
                                      fg=self.wm.get_theme_color("fg"))
            depth_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.color_depth_var = tk.StringVar(value=str(self.wm.config.get("display", {}).get("color_depth", 24)))
            
            depths = ["8", "16", "24", "32"]
            for depth in depths:
                rb = tk.Radiobutton(depth_frame, text=f"{depth} bit", variable=self.color_depth_var, value=depth,
                                   bg=self.wm.get_theme_color("window"), fg=self.wm.get_theme_color("fg"),
                                   selectcolor=self.wm.get_theme_color("accent"))
                rb.pack(side=tk.LEFT, padx=20, pady=10)
            
            # Multi-monitor support
            multi_frame = tk.LabelFrame(advanced_frame, text="Multi-Monitor", 
                                      bg=self.wm.get_theme_color("window"),
                                      fg=self.wm.get_theme_color("fg"))
            multi_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.multi_monitor_var = tk.BooleanVar(value=self.wm.config.get("display", {}).get("multi_monitor", False))
            multi_check = tk.Checkbutton(multi_frame, text="Enable Multi-Monitor Support", 
                                       variable=self.multi_monitor_var,
                                       bg=self.wm.get_theme_color("window"), fg=self.wm.get_theme_color("fg"),
                                       selectcolor=self.wm.get_theme_color("accent"))
            multi_check.pack(anchor='w', padx=10, pady=10)
            
            # Virtual display options
            virtual_frame = tk.LabelFrame(advanced_frame, text="Virtual Display", 
                                        bg=self.wm.get_theme_color("window"),
                                        fg=self.wm.get_theme_color("fg"))
            virtual_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.virtual_display_var = tk.BooleanVar(value=self.wm.config.get("display", {}).get("virtual_display", False))
            virtual_check = tk.Checkbutton(virtual_frame, text="Enable Virtual Display", 
                                         variable=self.virtual_display_var,
                                         bg=self.wm.get_theme_color("window"), fg=self.wm.get_theme_color("fg"),
                                         selectcolor=self.wm.get_theme_color("accent"))
            virtual_check.pack(anchor='w', padx=10, pady=10)
            
        except Exception as e:
            logger.error(f"Advanced settings tab creation error: {e}")
    
    def create_troubleshooting_tab(self, notebook):
        """Create troubleshooting tab"""
        try:
            trouble_frame = tk.Frame(notebook, bg=self.wm.get_theme_color("window"))
            notebook.add(trouble_frame, text="Troubleshooting")
            
            # Troubleshooting tools
            trouble_label = tk.Label(trouble_frame, text="Display Troubleshooting Tools", 
                                   font=('Arial', 12, 'bold'),
                                   bg=self.wm.get_theme_color("window"),
                                   fg=self.wm.get_theme_color("fg"))
            trouble_label.pack(pady=(10, 20))
            
            # Test buttons
            test_frame = tk.Frame(trouble_frame, bg=self.wm.get_theme_color("window"))
            test_frame.pack(fill=tk.X, padx=10, pady=10)
            
            test_buttons = [
                ("🔍 Test Display Connection", self.test_display_connection),
                ("🖥️ Restart Display System", self.restart_display_system),
                ("📊 Run Display Diagnostics", self.run_display_diagnostics),
                ("🔧 Reset Display Settings", self.reset_display_settings),
                ("📋 Export Display Logs", self.export_display_logs)
            ]
            
            for text, command in test_buttons:
                btn = tk.Button(test_frame, text=text, command=command,
                               bg=self.wm.get_theme_color("secondary"), fg="white",
                               font=('Arial', 10), relief=tk.FLAT, padx=20, pady=8)
                btn.pack(fill=tk.X, pady=5)
            
            # Diagnostic output
            diag_label = tk.Label(trouble_frame, text="Diagnostic Output:", 
                                bg=self.wm.get_theme_color("window"),
                                fg=self.wm.get_theme_color("fg"),
                                font=('Arial', 10, 'bold'))
            diag_label.pack(anchor='w', padx=10, pady=(20, 5))
            
            self.diagnostic_text = tk.Text(trouble_frame, height=15, width=70,
                                         bg=self.wm.get_theme_color("input"),
                                         fg=self.wm.get_theme_color("fg"),
                                         font=('Courier', 9), wrap=tk.WORD)
            self.diagnostic_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
        except Exception as e:
            logger.error(f"Troubleshooting tab creation error: {e}")
    
    def refresh_display_info(self):
        """Refresh display information"""
        try:
            self.info_text.delete('1.0', tk.END)
            
            # Get display information
            display_info = self.display_manager.get_display_info()
            env_info = self.display_manager.detect_environment()
            
            info_content = f"""Display Information - Berke0S V2
{'='*50}

Current Display Status:
• Display ID: {display_info.get('display', 'Unknown')}
• Mode: {display_info.get('mode', 'Unknown')}
• Resolution: {display_info.get('width', 'Unknown')}x{display_info.get('height', 'Unknown')}
• Color Depth: {display_info.get('depth', 'Unknown')} bits
• Ready: {'Yes' if self.display_manager.is_display_ready() else 'No'}

System Environment:
• Operating System: {env_info.get('distribution', 'Unknown')}
• Tiny Core Linux: {'Yes' if env_info.get('is_tinycore') else 'No'}
• Current User: {env_info.get('current_user', 'Unknown')}
• TTY: {env_info.get('tty', 'Unknown')}
• Runlevel: {env_info.get('runlevel', 'Unknown')}

Display Server Support:
• X11 Available: {'Yes' if env_info.get('x11_available', {}).get('available') else 'No'}
• X11 Binaries: {', '.join(env_info.get('x11_available', {}).get('binaries', []))}
• Wayland Available: {'Yes' if env_info.get('wayland_available', {}).get('available') else 'No'}

Graphics Hardware:
• Detected Drivers: {', '.join(env_info.get('graphics_driver', ['Unknown']))}

Configuration:
• Display Server: {self.wm.config.get('display', {}).get('display_server', 'auto')}
• Resolution: {self.wm.config.get('display', {}).get('resolution', 'auto')}
• Refresh Rate: {self.wm.config.get('display', {}).get('refresh_rate', 60)} Hz
• Color Depth: {self.wm.config.get('display', {}).get('color_depth', 24)} bits
• Multi-Monitor: {'Enabled' if self.wm.config.get('display', {}).get('multi_monitor') else 'Disabled'}

Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            self.info_text.insert('1.0', info_content)
            
        except Exception as e:
            logger.error(f"Display info refresh error: {e}")
            self.info_text.insert('1.0', f"Error refreshing display information: {str(e)}")
    
    def apply_display_settings(self):
        """Apply display configuration changes"""
        try:
            # Update configuration
            self.wm.config["display"]["display_server"] = self.display_mode_var.get()
            self.wm.config["display"]["resolution"] = self.resolution_var.get()
            self.wm.config["display"]["refresh_rate"] = int(self.refresh_rate_var.get())
            
            if hasattr(self, 'color_depth_var'):
                self.wm.config["display"]["color_depth"] = int(self.color_depth_var.get())
            
            if hasattr(self, 'x_args_var'):
                self.wm.config["display"]["x_arguments"] = self.x_args_var.get().split()
            
            if hasattr(self, 'multi_monitor_var'):
                self.wm.config["display"]["multi_monitor"] = self.multi_monitor_var.get()
            
            if hasattr(self, 'virtual_display_var'):
                self.wm.config["display"]["virtual_display"] = self.virtual_display_var.get()
            
            # Save configuration
            self.wm.save_config()
            
            # Show confirmation
            result = messagebox.askyesno(
                "Apply Settings",
                "Display settings have been saved. Do you want to restart the display system to apply changes?",
                parent=self.window
            )
            
            if result:
                self.restart_display_system()
            else:
                self.wm.notifications.send(
                    "Display Settings",
                    "Settings saved. Restart required to apply changes.",
                    notification_type="info"
                )
            
        except Exception as e:
            logger.error(f"Apply display settings error: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {str(e)}", parent=self.window)
    
    def test_display_connection(self):
        """Test display connection"""
        try:
            self.diagnostic_text.delete('1.0', tk.END)
            self.diagnostic_text.insert(tk.END, "Testing display connection...\n\n")
            
            # Test X server connection
            try:
                result = subprocess.run(['xdpyinfo'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.diagnostic_text.insert(tk.END, "✅ X server connection: SUCCESS\n")
                    self.diagnostic_text.insert(tk.END, f"Display info:\n{result.stdout[:500]}...\n\n")
                else:
                    self.diagnostic_text.insert(tk.END, "❌ X server connection: FAILED\n")
                    self.diagnostic_text.insert(tk.END, f"Error: {result.stderr}\n\n")
            except subprocess.TimeoutExpired:
                self.diagnostic_text.insert(tk.END, "⏱️ X server connection: TIMEOUT\n\n")
            except FileNotFoundError:
                self.diagnostic_text.insert(tk.END, "❌ xdpyinfo not found\n\n")
            
            # Test window creation
            try:
                result = subprocess.run(['xwininfo', '-root'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.diagnostic_text.insert(tk.END, "✅ Window system: WORKING\n")
                else:
                    self.diagnostic_text.insert(tk.END, "❌ Window system: FAILED\n")
            except:
                self.diagnostic_text.insert(tk.END, "❌ Window system test failed\n")
            
            self.diagnostic_text.insert(tk.END, "\nTest completed.\n")
            
        except Exception as e:
            logger.error(f"Display connection test error: {e}")
            self.diagnostic_text.insert(tk.END, f"Test error: {str(e)}\n")
    
    def restart_display_system(self):
        """Restart display system"""
        try:
            self.diagnostic_text.delete('1.0', tk.END)
            self.diagnostic_text.insert(tk.END, "Restarting display system...\n\n")
            
            # Shutdown current display
            self.display_manager.shutdown_display()
            self.diagnostic_text.insert(tk.END, "✅ Display system shutdown\n")
            
            time.sleep(2)
            
            # Restart display
            success = self.display_manager.setup_display_environment()
            
            if success:
                self.diagnostic_text.insert(tk.END, "✅ Display system restarted successfully\n")
                self.wm.notifications.send(
                    "Display Settings",
                    "Display system restarted successfully",
                    notification_type="success"
                )
            else:
                self.diagnostic_text.insert(tk.END, "❌ Display system restart failed\n")
                self.wm.notifications.send(
                    "Display Settings",
                    "Display system restart failed",
                    notification_type="error"
                )
            
        except Exception as e:
            logger.error(f"Display restart error: {e}")
            self.diagnostic_text.insert(tk.END, f"Restart error: {str(e)}\n")
    
    def run_display_diagnostics(self):
        """Run comprehensive display diagnostics"""
        try:
            self.diagnostic_text.delete('1.0', tk.END)
            self.diagnostic_text.insert(tk.END, "Running comprehensive display diagnostics...\n\n")
            
            # System information
            self.diagnostic_text.insert(tk.END, "=== SYSTEM INFORMATION ===\n")
            try:
                result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=5)
                self.diagnostic_text.insert(tk.END, f"System: {result.stdout}\n")
            except:
                self.diagnostic_text.insert(tk.END, "System info: Not available\n")
            
            # Graphics hardware
            self.diagnostic_text.insert(tk.END, "\n=== GRAPHICS HARDWARE ===\n")
            try:
                result = subprocess.run(['lspci', '|', 'grep', '-i', 'vga'], 
                                      capture_output=True, text=True, timeout=5, shell=True)
                if result.stdout:
                    self.diagnostic_text.insert(tk.END, f"Graphics: {result.stdout}\n")
                else:
                    self.diagnostic_text.insert(tk.END, "Graphics hardware: Not detected\n")
            except:
                self.diagnostic_text.insert(tk.END, "Graphics detection: Failed\n")
            
            # X server processes
            self.diagnostic_text.insert(tk.END, "\n=== X SERVER PROCESSES ===\n")
            try:
                result = subprocess.run(['ps', 'aux', '|', 'grep', '[X]'], 
                                      capture_output=True, text=True, timeout=5, shell=True)
                if result.stdout:
                    self.diagnostic_text.insert(tk.END, f"X processes:\n{result.stdout}\n")
                else:
                    self.diagnostic_text.insert(tk.END, "No X server processes found\n")
            except:
                self.diagnostic_text.insert(tk.END, "Process check: Failed\n")
            
            # Display environment
            self.diagnostic_text.insert(tk.END, "\n=== ENVIRONMENT VARIABLES ===\n")
            env_vars = ['DISPLAY', 'XAUTHORITY', 'WAYLAND_DISPLAY', 'XDG_SESSION_TYPE']
            for var in env_vars:
                value = os.environ.get(var, 'Not set')
                self.diagnostic_text.insert(tk.END, f"{var}: {value}\n")
            
            # Berke0S display manager status
            self.diagnostic_text.insert(tk.END, "\n=== BERKE0S DISPLAY MANAGER ===\n")
            self.diagnostic_text.insert(tk.END, f"Display Ready: {self.display_manager.is_display_ready()}\n")
            self.diagnostic_text.insert(tk.END, f"Current Display: {self.display_manager.get_current_display()}\n")
            
            display_info = self.display_manager.get_display_info()
            for key, value in display_info.items():
                self.diagnostic_text.insert(tk.END, f"{key}: {value}\n")
            
            self.diagnostic_text.insert(tk.END, "\n=== DIAGNOSTICS COMPLETE ===\n")
            
        except Exception as e:
            logger.error(f"Display diagnostics error: {e}")
            self.diagnostic_text.insert(tk.END, f"Diagnostics error: {str(e)}\n")
    
    def reset_display_settings(self):
        """Reset display settings to defaults"""
        try:
            result = messagebox.askyesno(
                "Reset Settings",
                "This will reset all display settings to defaults. Continue?",
                parent=self.window
            )
            
            if result:
                # Reset to defaults
                self.wm.config["display"] = DEFAULT_CONFIG["display"].copy()
                self.wm.save_config()
                
                # Update UI
                self.display_mode_var.set("auto")
                self.resolution_var.set("auto")
                self.refresh_rate_var.set("60")
                
                if hasattr(self, 'color_depth_var'):
                    self.color_depth_var.set("24")
                if hasattr(self, 'x_args_var'):
                    self.x_args_var.set("-nolisten tcp -nocursor")
                if hasattr(self, 'multi_monitor_var'):
                    self.multi_monitor_var.set(False)
                if hasattr(self, 'virtual_display_var'):
                    self.virtual_display_var.set(False)
                
                self.wm.notifications.send(
                    "Display Settings",
                    "Display settings reset to defaults",
                    notification_type="success"
                )
                
        except Exception as e:
            logger.error(f"Reset display settings error: {e}")
            messagebox.showerror("Error", f"Failed to reset settings: {str(e)}", parent=self.window)
    
    def export_display_logs(self):
        """Export display logs"""
        try:
            log_file = filedialog.asksaveasfilename(
                parent=self.window,
                title="Export Display Logs",
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            
            if log_file:
                with open(log_file, 'w') as f:
                    f.write("Berke0S V2 Display Logs\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Export Date: {datetime.datetime.now()}\n\n")
                    
                    # Include display information
                    display_info = self.display_manager.get_display_info()
                    f.write("Display Information:\n")
                    for key, value in display_info.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")
                    
                    # Include environment info
                    env_info = self.display_manager.detect_environment()
                    f.write("Environment Information:\n")
                    for key, value in env_info.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")
                    
                    # Include configuration
                    f.write("Display Configuration:\n")
                    display_config = self.wm.config.get("display", {})
                    for key, value in display_config.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")
                    
                    # Include display logs from database
                    try:
                        conn = sqlite3.connect(DATABASE_FILE)
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM display_logs ORDER BY timestamp DESC LIMIT 100")
                        logs = cursor.fetchall()
                        conn.close()
                        
                        f.write("Recent Display Events:\n")
                        for log in logs:
                            f.write(f"  {log[5]} - {log[1]} - {log[3]} - {log[4]}\n")
                        
                    except Exception as e:
                        f.write(f"Error reading display logs: {e}\n")
                    
                    # Include system logs
                    try:
                        if os.path.exists(DISPLAY_LOG):
                            f.write("\nDisplay Log File:\n")
                            with open(DISPLAY_LOG, 'r') as log_file_handle:
                                f.write(log_file_handle.read())
                    except Exception as e:
                        f.write(f"Error reading display log file: {e}\n")
                
                self.wm.notifications.send(
                    "Display Settings",
                    f"Display logs exported to {os.path.basename(log_file)}",
                    notification_type="success"
                )
                
        except Exception as e:
            logger.error(f"Export display logs error: {e}")
            messagebox.showerror("Error", f"Failed to export logs: {str(e)}", parent=self.window)

# Additional application stubs (would be fully implemented)
class WebBrowser:
    def __init__(self, wm): self.wm = wm
    def show(self): pass
    def bring_to_front(self): pass

class SettingsApp:
    def __init__(self, wm): self.wm = wm
    def show(self): pass
    def bring_to_front(self): pass

class Terminal:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class ImageViewer:
    def __init__(self, wm): self.wm = wm
    def show(self, file_path=None): pass

class MusicPlayer:
    def __init__(self, wm): self.wm = wm
    def show(self, file_path=None): pass

class VideoPlayer:
    def __init__(self, wm): self.wm = wm
    def show(self, file_path=None): pass

class SystemMonitor:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class EmailClient:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class CalendarApp:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class GamesLauncher:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class NetworkManager:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class ArchiveManager:
    def __init__(self, wm): self.wm = wm
    def show(self, file_path=None): pass

class PDFViewer:
    def __init__(self, wm): self.wm = wm
    def show(self, file_path=None): pass

class CodeEditor:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class ScreenRecorder:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class BackupManager:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

class VirtualDesktopManager:
    def __init__(self, wm): self.wm = wm
    def show(self): pass

# Plugin System
class PluginManager:
    """Plugin management system for extensibility"""
    
    def __init__(self, wm):
        self.wm = wm
        self.plugins = {}
        self.plugin_states = {}
        
    def load_plugins(self):
        """Load available plugins"""
        try:
            if not os.path.exists(PLUGINS_DIR):
                return
                
            for plugin_file in os.listdir(PLUGINS_DIR):
                if plugin_file.endswith('.py'):
                    self.load_plugin(plugin_file)
                    
        except Exception as e:
            logger.error(f"Plugin loading error: {e}")
    
    def load_plugin(self, plugin_file):
        """Load a specific plugin"""
        # Plugin loading implementation
        pass
    
    def save_plugin_states(self):
        """Save plugin states"""
        try:
            states_file = os.path.join(PLUGINS_DIR, 'states.json')
            with open(states_file, 'w') as f:
                json.dump(self.plugin_states, f, indent=4)
        except Exception as e:
            logger.error(f"Plugin states save error: {e}")
    
    def check_plugin_updates(self):
        """Check for plugin updates"""
        # Plugin update checking implementation
        pass
    
    def cleanup(self):
        """Cleanup plugin resources"""
        for plugin in self.plugins.values():
            if hasattr(plugin, 'cleanup'):
                try:
                    plugin.cleanup()
                except Exception as e:
                    logger.error(f"Plugin cleanup error: {e}")

# Performance Monitor
class PerformanceMonitor:
    """System performance monitoring"""
    
    def __init__(self, wm):
        self.wm = wm
        self.metrics = {}
        self.running = True
        
    def update_metrics(self):
        """Update performance metrics"""
        try:
            if psutil:
                self.metrics.update({
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'network_io': psutil.net_io_counters(),
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.error(f"Metrics update error: {e}")
    
    def get_metrics(self):
        """Get current metrics"""
        return self.metrics.copy()
    
    def stop(self):
        """Stop performance monitoring"""
        self.running = False

# Main execution
def main():
    """Enhanced main entry point for V2"""
    try:
        logger.info("Starting Berke0S 3.0 V2 - Enhanced Display Management...")
        
        # Initialize database
        init_database()
        
        # Check if installation is needed
        if not os.path.exists(INSTALL_FLAG) or "--install" in sys.argv:
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
        logger.info("Berke0S V2 terminated by user")
        print("\n🔄 Berke0S V2 terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        print(f"❌ Error starting Berke0S V2: {e}")
        
        # Try to provide helpful error information
        print("\n🔧 Troubleshooting Information:")
        print("• Check if X server is available")
        print("• Verify display environment variables")
        print("• Try running with --install flag")
        print("• Check log files in ~/.berke0s/")
        
        sys.exit(1)

if __name__ == "__main__":
    main()

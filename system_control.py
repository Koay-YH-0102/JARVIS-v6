"""
system_control.py - JARVIS v6 System Control Module
Application management, file ops, system monitoring, automation
100% FREE using psutil and Windows APIs
"""

import psutil
import json
import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# Application Management
# ─────────────────────────────────────────────────────────────

class ApplicationManager:
    """Open, close, and control applications"""
    
    def __init__(self):
        self.process_map = {}
        self._update_processes()
    
    def _update_processes(self):
        """Update list of running processes"""
        self.process_map = {}
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                self.process_map[proc.info['name']] = proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    def open_application(self, app_name: str):
        import os
        import subprocess
        import shutil

        print(f"[DEBUG] open_application called with app_name: {app_name}")

        # Normalize app name
        app_lower = app_name.lower().strip()

        # ── Common app paths ──────────────────────────────────────────
        app_map = {
            "microsoft teams": r"C:\Program Files\WindowsApps\MSTeams_26225.1806.5074.1452_x64__8wekyb3d8bbwe\ms-teams.exe",
            "teams": r"C:\Program Files\WindowsApps\MSTeams_26225.1806.5074.1452_x64__8wekyb3d8bbwe\ms-teams.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            "outlook": r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            "vs code": r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
            "vscode": r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
            "code": r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
            "spotify": r"%APPDATA%\Spotify\Spotify.exe",
            "discord": r"%LOCALAPPDATA%\Discord\app-*\Discord.exe",  # wildcard – handle below
        }

        # Expand environment variables
        def expand_path(path):
            return os.path.expandvars(path)

        # Check if app is in PATH
        which_path = shutil.which(app_name)
        if which_path:
            try:
                subprocess.Popen(which_path, shell=False)
                return {"ok": True, "message": f"Opened {app_name}"}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        # Check mapping
        if app_lower in app_map:
            exe_path = expand_path(app_map[app_lower])
            # Handle wildcard for Discord (app-*)
            if '*' in exe_path:
                import glob
                matches = glob.glob(exe_path)
                if matches:
                    exe_path = matches[0]
                else:
                    return {"ok": False, "error": f"Could not find {app_name}"}
            try:
                subprocess.Popen(exe_path, shell=False)
                return {"ok": True, "message": f"Opened {app_name}"}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        # Fallback: try with shell=True (works for apps in PATH with no spaces)
        try:
            subprocess.Popen(app_name, shell=True)
            return {"ok": True, "message": f"Opened {app_name}"}
        except Exception as e:
            # Last resort: try `start` command with quotes
            try:
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                return {"ok": True, "message": f"Opened {app_name}"}
            except Exception as e2:
                return {"ok": False, "error": f"Could not open {app_name}: {e2}"}
    
    def close_application(self, app_name: str):
        """Close application by name"""
        try:
            self._update_processes()
            
            if app_name not in self.process_map:
                return {"ok": False, "error": f"Application not running: {app_name}"}
            
            pid = self.process_map[app_name]
            proc = psutil.Process(pid)
            proc.terminate()
            
            return {"ok": True, "message": f"Closed {app_name}"}
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def list_running_apps(self):
        """List all running applications"""
        self._update_processes()
        apps = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                apps.append({
                    "name": proc.info['name'],
                    "pid": proc.info['pid'],
                    "memory_mb": round(proc.info['memory_percent'] * psutil.virtual_memory().total / 100 / 1024 / 1024, 2),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return {
            "ok": True,
            "apps": sorted(apps, key=lambda x: x['memory_mb'], reverse=True)[:20],
            "total": len(apps),
        }
    
    def get_app_status(self, app_name: str):
        """Get status of specific application"""
        self._update_processes()
        
        if app_name in self.process_map:
            try:
                proc = psutil.Process(self.process_map[app_name])
                return {
                    "ok": True,
                    "running": True,
                    "pid": proc.pid,
                    "memory_mb": round(proc.memory_info().rss / 1024 / 1024, 2),
                    "cpu_percent": round(proc.cpu_percent(interval=0.1), 2),
                }
            except:
                pass
        
        return {"ok": True, "running": False, "app": app_name}


# ─────────────────────────────────────────────────────────────
# File Operations
# ─────────────────────────────────────────────────────────────

class FileManager:
    """File and folder management"""
    
    @staticmethod
    def create_folder(path: str):
        """Create a folder"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return {"ok": True, "message": f"Folder created: {path}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    @staticmethod
    def delete_file(path: str):
        """Delete a file"""
        try:
            if os.path.exists(path):
                os.remove(path)
                return {"ok": True, "message": f"File deleted: {path}"}
            return {"ok": False, "error": "File not found"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    @staticmethod
    def copy_file(src: str, dst: str):
        """Copy file"""
        try:
            shutil.copy(src, dst)
            return {"ok": True, "message": f"File copied from {src} to {dst}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    @staticmethod
    def move_file(src: str, dst: str):
        """Move file"""
        try:
            shutil.move(src, dst)
            return {"ok": True, "message": f"File moved from {src} to {dst}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    @staticmethod
    def list_files(path: str, limit: int = 50):
        """List files in directory"""
        try:
            files = []
            for item in Path(path).iterdir():
                files.append({
                    "name": item.name,
                    "type": "folder" if item.is_dir() else "file",
                    "size_mb": round(item.stat().st_size / 1024 / 1024, 2) if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                })
            
            return {
                "ok": True,
                "files": files[:limit],
                "total": len(files),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────
# System Monitoring
# ─────────────────────────────────────────────────────────────

class SystemMonitor:
    """Monitor CPU, memory, disk, network"""
    
    @staticmethod
    def get_cpu_info():
        """Get CPU information and usage"""
        return {
            "ok": True,
            "usage_percent": psutil.cpu_percent(interval=1),
            "cores": psutil.cpu_count(),
            "freq_ghz": round(psutil.cpu_freq().current / 1000, 2),
        }
    
    @staticmethod
    def get_memory_info():
        """Get memory information"""
        mem = psutil.virtual_memory()
        return {
            "ok": True,
            "total_gb": round(mem.total / 1024**3, 2),
            "available_gb": round(mem.available / 1024**3, 2),
            "used_percent": mem.percent,
            "swap_gb": round(psutil.swap_memory().total / 1024**3, 2),
        }
    
    @staticmethod
    def get_disk_info():
        """Get disk information"""
        disk = psutil.disk_usage('/')
        return {
            "ok": True,
            "total_gb": round(disk.total / 1024**3, 2),
            "free_gb": round(disk.free / 1024**3, 2),
            "used_percent": disk.percent,
        }
    
    @staticmethod
    def get_network_info():
        """Get network information"""
        net = psutil.net_if_stats()
        interfaces = []
        
        for name, stat in net.items():
            interfaces.append({
                "name": name,
                "is_up": stat.isup,
                "speed_mbps": stat.speed,
            })
        
        return {
            "ok": True,
            "interfaces": interfaces,
        }
    
    @staticmethod
    def get_system_stats():
        """Get comprehensive system stats"""
        return {
            "ok": True,
            "cpu": SystemMonitor.get_cpu_info(),
            "memory": SystemMonitor.get_memory_info(),
            "disk": SystemMonitor.get_disk_info(),
            "network": SystemMonitor.get_network_info(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        }


# ─────────────────────────────────────────────────────────────
# Automation & Scheduling
# ─────────────────────────────────────────────────────────────

class TaskScheduler:
    """Schedule tasks and reminders"""
    
    def __init__(self):
        self.tasks = []
        self.task_file = Path(__file__).parent / "scheduled_tasks.json"
        self._load_tasks()
    
    def _load_tasks(self):
        """Load scheduled tasks from file"""
        if self.task_file.exists():
            with open(self.task_file, 'r') as f:
                self.tasks = json.load(f)
    
    def _save_tasks(self):
        """Save tasks to file"""
        with open(self.task_file, 'w') as f:
            json.dump(self.tasks, f, indent=2)
    
    def schedule_task(self, name: str, command: str, interval_minutes: int = 60):
        """Schedule a task"""
        task = {
            "id": len(self.tasks) + 1,
            "name": name,
            "command": command,
            "interval_minutes": interval_minutes,
            "created_at": datetime.now().isoformat(),
            "enabled": True,
        }
        self.tasks.append(task)
        self._save_tasks()
        
        return {
            "ok": True,
            "message": f"Task scheduled: {name}",
            "task_id": task["id"],
        }
    
    def create_reminder(self, reminder_text: str, minutes_from_now: int = 15):
        """Create a reminder"""
        reminder_time = datetime.now().timestamp() + (minutes_from_now * 60)
        
        reminder = {
            "id": len(self.tasks) + 1,
            "type": "reminder",
            "text": reminder_text,
            "time": reminder_time,
            "created_at": datetime.now().isoformat(),
        }
        self.tasks.append(reminder)
        self._save_tasks()
        
        return {
            "ok": True,
            "message": f"Reminder created for {minutes_from_now} minutes from now",
            "reminder_id": reminder["id"],
        }
    
    def get_tasks(self):
        """Get all scheduled tasks"""
        return {
            "ok": True,
            "tasks": self.tasks,
            "count": len(self.tasks),
        }


# ─────────────────────────────────────────────────────────────
# Tool Schemas for JARVIS
# ─────────────────────────────────────────────────────────────

SYSTEM_CONTROL_TOOLS = [
    {"type": "function", "function": {
        "name": "open_app",
        "description": "Open an application",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Application name to open"},
            },
            "required": ["app_name"],
        },
    }},
    {"type": "function", "function": {
        "name": "close_app",
        "description": "Close a running application",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Application name to close"},
            },
            "required": ["app_name"],
        },
    }},
    {"type": "function", "function": {
        "name": "list_running_apps",
        "description": "List all running applications",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_system_stats",
        "description": "Get CPU, memory, disk, and network stats",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "schedule_task",
        "description": "Schedule a task or reminder",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Task name"},
                "command": {"type": "string", "description": "Command to execute"},
                "interval_minutes": {"type": "integer", "description": "Interval in minutes"},
            },
            "required": ["name"],
        },
    }},
]

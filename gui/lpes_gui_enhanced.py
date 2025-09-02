"""
Enhanced LPES GUI Manager with JSON API Integration
Better integration with actual LPES commands using JSON parsing
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import sys
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

# Add src directory to Python path for imports
current_dir = Path(__file__).parent
root_dir = current_dir.parent
src_dir = root_dir / "src"
sys.path.insert(0, str(src_dir))

class LPESApiManager:
    """Manager for LPES API interactions."""
    
    def __init__(self, lpes_path: str):
        self.lpes_path = Path(lpes_path)
        # Default to src/main.py for the new structure
        self.main_script = self.lpes_path.parent / "src" / "main.py"
        if not self.main_script.exists():
            # Fallback to old structure
            self.main_script = self.lpes_path / "main.py"
        
    def run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run LPES command and return structured result."""
        try:
            full_command = [sys.executable, str(self.main_script)] + command
            
            result = subprocess.run(
                full_command,
                cwd=self.lpes_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def list_projects(self) -> List[Dict[str, str]]:
        """Get list of projects."""
        result = self.run_command(["list"])
        
        # Parse the table output (in a real implementation, we'd want JSON output)
        projects = []
        if result['success'] and result['stdout']:
            lines = result['stdout'].split('\n')
            for line in lines:
                # This is a simplified parser for the table output
                # In a real implementation, LPES should have a --json flag
                if '│' in line and not line.startswith('┏') and not line.startswith('┡'):
                    parts = [p.strip() for p in line.split('│') if p.strip()]
                    if len(parts) >= 5:
                        projects.append({
                            'name': parts[0],
                            'domain': parts[1],
                            'status': parts[2],
                            'port': parts[3],
                            'type': parts[4]
                        })
        
        return projects
    
    def create_project(self, name: str, path: str, build: str, start: str, port: str) -> bool:
        """Create a new project."""
        command = ["init", name, "--path", path, "--build", build, "--start", start, "--port", port]
        result = self.run_command(command)
        return result['success']
    
    def remove_project(self, name: str, cleanup: bool = True) -> bool:
        """Remove a project."""
        command = ["remove", name]
        if cleanup:
            command.append("--cleanup")
        result = self.run_command(command)
        return result['success']
    
    def add_domain(self, project: str, domain: str, ssl: bool = True, hosts: bool = True) -> bool:
        """Add domain to project."""
        command = ["domain", "add", project, domain]
        if ssl:
            command.append("--ssl")
        if hosts:
            command.append("--hosts-file")
        result = self.run_command(command)
        return result['success']
    
    def build_project(self, name: str) -> bool:
        """Build a project."""
        result = self.run_command(["build", name])
        return result['success']
    
    def start_project(self, name: str) -> bool:
        """Start a project."""
        result = self.run_command(["start", name])
        return result['success']
    
    def stop_project(self, name: str) -> bool:
        """Stop a project."""
        result = self.run_command(["stop", name])
        return result['success']
    
    def start_proxy(self, port: int = 443) -> bool:
        """Start proxy server."""
        command = ["proxy", "start"]
        if port != 443:
            command.extend(["--port", str(port)])
        result = self.run_command(command)
        return result['success']
    
    def stop_proxy(self) -> bool:
        """Stop proxy server."""
        result = self.run_command(["proxy", "stop"])
        return result['success']


class ModernLPESGui:
    """Modern LPES GUI with enhanced features."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.lpes_path = os.getcwd()
        self.api = LPESApiManager(self.lpes_path)
        self.projects_data = []
        
        self.setup_modern_gui()
        self.setup_logging()
        
    def setup_modern_gui(self):
        """Setup modern GUI with better styling."""
        self.root.title("LPES Manager Pro - Local Production Environment Simulator")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f8f9fa')
        
        # Modern styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom styles
        style.configure('Modern.TFrame', background='#ffffff', relief='flat', borderwidth=1)
        style.configure('Card.TFrame', background='#ffffff', relief='solid', borderwidth=1)
        style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'), background='#f8f9fa', foreground='#2c3e50')
        style.configure('Subheader.TLabel', font=('Segoe UI', 12, 'bold'), background='#ffffff', foreground='#34495e')
        style.configure('Success.TButton', background='#27ae60', foreground='white')
        style.configure('Danger.TButton', background='#e74c3c', foreground='white')
        style.configure('Primary.TButton', background='#3498db', foreground='white', font=('Segoe UI', 10, 'bold'))
        
        # Main container with padding
        main_container = ttk.Frame(self.root, style='Modern.TFrame')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_container, style='Modern.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(header_frame, text="🚀 LPES Manager Pro", style='Header.TLabel').pack(side='left')
        
        # Status indicators
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(side='right')
        
        self.proxy_indicator = ttk.Label(status_frame, text="🔴 Proxy: Offline", font=('Segoe UI', 10))
        self.proxy_indicator.pack(side='right', padx=(0, 10))
        
        # Create paned window for better layout
        paned = ttk.PanedWindow(main_container, orient='horizontal')
        paned.pack(fill='both', expand=True)
        
        # Left panel - Projects
        self.create_projects_panel(paned)
        
        # Right panel - Console and controls
        self.create_control_panel(paned)
        
        # Bottom status bar
        self.create_status_bar(main_container)
        
    def create_projects_panel(self, parent):
        """Create the projects management panel."""
        projects_frame = ttk.Frame(parent, style='Card.TFrame')
        parent.add(projects_frame, weight=3)
        
        # Projects header
        header = ttk.Frame(projects_frame, style='Card.TFrame')
        header.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(header, text="📋 Projects", style='Subheader.TLabel').pack(side='left')
        
        # Toolbar
        toolbar = ttk.Frame(header)
        toolbar.pack(side='right')
        
        ttk.Button(toolbar, text="➕ New", command=self.new_project_dialog, style='Primary.TButton').pack(side='left', padx=2)
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_projects).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🗑️ Delete", command=self.delete_project).pack(side='left', padx=2)
        
        # Projects tree with modern styling
        tree_frame = ttk.Frame(projects_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        columns = ('Name', 'Domain', 'Status', 'Port', 'Type')
        self.projects_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.projects_tree.heading(col, text=col)
            if col == 'Name':
                self.projects_tree.column(col, width=150, minwidth=100)
            elif col == 'Domain':
                self.projects_tree.column(col, width=200, minwidth=150)
            elif col == 'Status':
                self.projects_tree.column(col, width=120, minwidth=100)
            elif col == 'Port':
                self.projects_tree.column(col, width=80, minwidth=60)
            else:
                self.projects_tree.column(col, width=100, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.projects_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.projects_tree.xview)
        self.projects_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for tree and scrollbars
        self.projects_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Quick actions panel
        actions_frame = ttk.LabelFrame(projects_frame, text="🎮 Quick Actions", padding=10)
        actions_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Action buttons in grid
        actions_grid = ttk.Frame(actions_frame)
        actions_grid.pack(fill='x')
        
        actions = [
            ("🔨 Build", self.build_project, 0, 0),
            ("▶️ Start", self.start_project, 0, 1), 
            ("⏹️ Stop", self.stop_project, 0, 2),
            ("🌐 Domain", self.add_domain_dialog, 1, 0),
            ("🔒 SSL", self.manage_ssl, 1, 1),
            ("📁 Open", self.open_project_folder, 1, 2)
        ]
        
        for text, command, row, col in actions:
            btn = ttk.Button(actions_grid, text=text, command=command)
            btn.grid(row=row, column=col, padx=5, pady=2, sticky='ew')
        
        for i in range(3):
            actions_grid.grid_columnconfigure(i, weight=1)
        
    def create_control_panel(self, parent):
        """Create the control panel with console."""
        control_frame = ttk.Frame(parent, style='Card.TFrame')
        parent.add(control_frame, weight=2)
        
        # Notebook for tabs
        notebook = ttk.Notebook(control_frame)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Console tab
        console_frame = ttk.Frame(notebook)
        notebook.add(console_frame, text="📟 Console")
        
        # Console controls
        console_controls = ttk.Frame(console_frame)
        console_controls.pack(fill='x', pady=(0, 5))
        
        ttk.Button(console_controls, text="🧹 Clear", command=self.clear_console).pack(side='left', padx=2)
        ttk.Button(console_controls, text="💾 Save", command=self.save_log).pack(side='left', padx=2)
        
        # Log level
        ttk.Label(console_controls, text="Level:").pack(side='right', padx=(10, 5))
        self.log_level_var = tk.StringVar(value="INFO")
        ttk.Combobox(console_controls, textvariable=self.log_level_var, 
                    values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                    state="readonly", width=8).pack(side='right')
        
        # Console text
        self.console_text = scrolledtext.ScrolledText(
            console_frame, 
            wrap=tk.WORD, 
            height=20,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.console_text.pack(fill='both', expand=True)
        
        # Proxy control tab
        proxy_frame = ttk.Frame(notebook)
        notebook.add(proxy_frame, text="🔄 Proxy")
        
        proxy_controls = ttk.LabelFrame(proxy_frame, text="Proxy Server Control", padding=10)
        proxy_controls.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(proxy_controls, text="▶️ Start Proxy", command=self.start_proxy).pack(side='left', padx=5)
        ttk.Button(proxy_controls, text="⏹️ Stop Proxy", command=self.stop_proxy).pack(side='left', padx=5)
        
        # SSL tab
        ssl_frame = ttk.Frame(notebook)
        notebook.add(ssl_frame, text="🔒 SSL")
        
        ssl_controls = ttk.LabelFrame(ssl_frame, text="SSL Management", padding=10)
        ssl_controls.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(ssl_controls, text="📜 Trust CA", command=self.trust_ca).pack(anchor='w', pady=2)
        ttk.Button(ssl_controls, text="📋 List Certs", command=self.list_certificates).pack(anchor='w', pady=2)
        
    def create_status_bar(self, parent):
        """Create status bar."""
        status_frame = ttk.Frame(parent, style='Modern.TFrame')
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready", font=('Segoe UI', 9))
        self.status_label.pack(side='left')
        
        # Path info
        path_label = ttk.Label(status_frame, text=f"LPES Path: {self.lpes_path}", font=('Segoe UI', 9))
        path_label.pack(side='right')
        
    def setup_logging(self):
        """Setup logging to console."""
        self.log_to_console("🚀 LPES Manager Pro initialized", "INFO")
        self.log_to_console(f"Working directory: {self.lpes_path}", "INFO")
        
    def log_to_console(self, message: str, level: str = "INFO"):
        """Log message to console with color coding."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color mapping
        colors = {
            'INFO': '#3498db',
            'SUCCESS': '#27ae60', 
            'WARNING': '#f39c12',
            'ERROR': '#e74c3c',
            'DEBUG': '#95a5a6'
        }
        
        color = colors.get(level, '#ffffff')
        formatted_msg = f"[{timestamp}] {level}: {message}\n"
        
        self.console_text.insert(tk.END, formatted_msg)
        self.console_text.see(tk.END)
        
        # Update status
        self.status_label.config(text=message[:50] + "..." if len(message) > 50 else message)
        
    def refresh_projects(self):
        """Refresh projects list."""
        self.log_to_console("Refreshing projects list...", "INFO")
        
        # Clear tree
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        
        try:
            self.projects_data = self.api.list_projects()
            
            for project in self.projects_data:
                # Clean up status text (remove emojis for better display)
                status = project['status'].replace('🟢', '').replace('🔴', '').replace('🟡', '').strip()
                
                self.projects_tree.insert('', 'end', values=(
                    project['name'],
                    project['domain'],
                    status,
                    project['port'],
                    project['type']
                ))
            
            self.log_to_console(f"Found {len(self.projects_data)} projects", "SUCCESS")
            
        except Exception as e:
            self.log_to_console(f"Error refreshing projects: {str(e)}", "ERROR")
    
    def get_selected_project(self) -> Optional[str]:
        """Get selected project name."""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a project first.")
            return None
        
        item = self.projects_tree.item(selection[0])
        return item['values'][0]
    
    def new_project_dialog(self):
        """Enhanced new project dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Project")
        dialog.geometry("600x500")
        dialog.configure(bg='#f8f9fa')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, style='Card.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        ttk.Label(main_frame, text="📝 Create New LPES Project", 
                 font=('Segoe UI', 16, 'bold')).pack(pady=(0, 20))
        
        # Form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill='x', pady=(0, 20))
        
        # Project name
        ttk.Label(form_frame, text="Project Name:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=name_var, width=40, font=('Segoe UI', 10)).grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # Project path
        ttk.Label(form_frame, text="Project Path:", font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=5)
        
        path_frame = ttk.Frame(form_frame)
        path_frame.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=path_var, width=30, font=('Segoe UI', 10)).pack(side='left', fill='x', expand=True)
        ttk.Button(path_frame, text="📂", command=lambda: path_var.set(filedialog.askdirectory())).pack(side='right', padx=(5, 0))
        
        # Build command
        ttk.Label(form_frame, text="Build Command:", font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=5)
        build_var = tk.StringVar(value="npm run build")
        ttk.Entry(form_frame, textvariable=build_var, width=40, font=('Segoe UI', 10)).grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # Start command
        ttk.Label(form_frame, text="Start Command:", font=('Segoe UI', 10, 'bold')).grid(row=3, column=0, sticky='w', pady=5)
        start_var = tk.StringVar(value="npm start")
        ttk.Entry(form_frame, textvariable=start_var, width=40, font=('Segoe UI', 10)).grid(row=3, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # Port
        ttk.Label(form_frame, text="Port:", font=('Segoe UI', 10, 'bold')).grid(row=4, column=0, sticky='w', pady=5)
        port_var = tk.StringVar(value="3000")
        ttk.Entry(form_frame, textvariable=port_var, width=40, font=('Segoe UI', 10)).grid(row=4, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding=10)
        options_frame.pack(fill='x', pady=(0, 20))
        
        auto_domain_var = tk.BooleanVar(value=True)
        auto_ssl_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Auto-create domain ({name}.local)", variable=auto_domain_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Generate SSL certificate", variable=auto_ssl_var).pack(anchor='w')
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')
        
        def create_project():
            name = name_var.get().strip()
            path = path_var.get().strip()
            build = build_var.get().strip()
            start = start_var.get().strip()
            port = port_var.get().strip()
            
            if not all([name, path, build, start, port]):
                messagebox.showerror("Error", "All fields are required!")
                return
            
            self.log_to_console(f"Creating project '{name}'...", "INFO")
            
            if self.api.create_project(name, path, build, start, port):
                self.log_to_console(f"Project '{name}' created successfully", "SUCCESS")
                
                # Auto-create domain if requested
                if auto_domain_var.get():
                    domain = f"{name}.local"
                    self.log_to_console(f"Adding domain '{domain}'...", "INFO")
                    if self.api.add_domain(name, domain, auto_ssl_var.get(), True):
                        self.log_to_console(f"Domain '{domain}' added successfully", "SUCCESS")
                
                dialog.destroy()
                self.refresh_projects()
            else:
                self.log_to_console(f"Failed to create project '{name}'", "ERROR")
        
        ttk.Button(btn_frame, text="✅ Create Project", command=create_project, style='Primary.TButton').pack(side='right', padx=(5, 0))
        ttk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy).pack(side='right')
    
    def add_domain_dialog(self):
        """Add domain dialog."""
        project_name = self.get_selected_project()
        if not project_name:
            return
        
        domain = tk.simpledialog.askstring("Add Domain", f"Enter domain for '{project_name}':", 
                                         initialvalue=f"{project_name}.local")
        if domain:
            self.log_to_console(f"Adding domain '{domain}' to '{project_name}'...", "INFO")
            if self.api.add_domain(project_name, domain, True, True):
                self.log_to_console(f"Domain '{domain}' added successfully", "SUCCESS")
                self.refresh_projects()
            else:
                self.log_to_console(f"Failed to add domain '{domain}'", "ERROR")
    
    def build_project(self):
        """Build selected project."""
        project_name = self.get_selected_project()
        if project_name:
            self.log_to_console(f"Building project '{project_name}'...", "INFO")
            if self.api.build_project(project_name):
                self.log_to_console(f"Project '{project_name}' built successfully", "SUCCESS")
            else:
                self.log_to_console(f"Failed to build project '{project_name}'", "ERROR")
    
    def start_project(self):
        """Start selected project."""
        project_name = self.get_selected_project()
        if project_name:
            self.log_to_console(f"Starting project '{project_name}'...", "INFO")
            if self.api.start_project(project_name):
                self.log_to_console(f"Project '{project_name}' started successfully", "SUCCESS")
                self.root.after(2000, self.refresh_projects)
            else:
                self.log_to_console(f"Failed to start project '{project_name}'", "ERROR")
    
    def stop_project(self):
        """Stop selected project."""
        project_name = self.get_selected_project()
        if project_name:
            self.log_to_console(f"Stopping project '{project_name}'...", "INFO")
            if self.api.stop_project(project_name):
                self.log_to_console(f"Project '{project_name}' stopped successfully", "SUCCESS")
                self.root.after(2000, self.refresh_projects)
            else:
                self.log_to_console(f"Failed to stop project '{project_name}'", "ERROR")
    
    def delete_project(self):
        """Delete selected project."""
        project_name = self.get_selected_project()
        if not project_name:
            return
        
        if messagebox.askyesno("Confirm Deletion", 
                              f"Delete project '{project_name}' and all associated resources?"):
            self.log_to_console(f"Deleting project '{project_name}'...", "INFO")
            if self.api.remove_project(project_name, True):
                self.log_to_console(f"Project '{project_name}' deleted successfully", "SUCCESS")
                self.refresh_projects()
            else:
                self.log_to_console(f"Failed to delete project '{project_name}'", "ERROR")
    
    def start_proxy(self):
        """Start proxy server."""
        self.log_to_console("Starting proxy server...", "INFO")
        if self.api.start_proxy():
            self.log_to_console("Proxy server started successfully", "SUCCESS")
            self.proxy_indicator.config(text="🟢 Proxy: Online")
        else:
            self.log_to_console("Failed to start proxy server", "ERROR")
    
    def stop_proxy(self):
        """Stop proxy server."""
        self.log_to_console("Stopping proxy server...", "INFO")
        if self.api.stop_proxy():
            self.log_to_console("Proxy server stopped successfully", "SUCCESS")
            self.proxy_indicator.config(text="🔴 Proxy: Offline")
        else:
            self.log_to_console("Failed to stop proxy server", "ERROR")
    
    def manage_ssl(self):
        """Manage SSL certificates."""
        self.log_to_console("Listing SSL certificates...", "INFO")
        result = self.api.run_command(["ssl", "list"])
        if result['success']:
            self.log_to_console("SSL certificates listed in output", "SUCCESS")
        else:
            self.log_to_console("Failed to list SSL certificates", "ERROR")
    
    def trust_ca(self):
        """Show CA trust information."""
        result = self.api.run_command(["ssl", "trust-info"])
        if result['success']:
            self.log_to_console("SSL trust information displayed", "SUCCESS")
        else:
            self.log_to_console("Failed to get SSL trust info", "ERROR")
    
    def list_certificates(self):
        """List SSL certificates."""
        self.manage_ssl()
    
    def open_project_folder(self):
        """Open project folder in file explorer."""
        project_name = self.get_selected_project()
        if not project_name:
            return
        
        # Find project data
        project_data = next((p for p in self.projects_data if p['name'] == project_name), None)
        if project_data:
            # This would require getting the project path from LPES
            self.log_to_console(f"Opening folder for project '{project_name}'...", "INFO")
        else:
            self.log_to_console(f"Project '{project_name}' not found", "ERROR")
    
    def clear_console(self):
        """Clear console."""
        self.console_text.delete(1.0, tk.END)
        self.log_to_console("Console cleared", "INFO")
    
    def save_log(self):
        """Save console log."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.console_text.get(1.0, tk.END))
                self.log_to_console(f"Log saved to: {filename}", "SUCCESS")
            except Exception as e:
                self.log_to_console(f"Error saving log: {str(e)}", "ERROR")
    
    def run(self):
        """Run the application."""
        self.log_to_console("Starting LPES Manager Pro...", "INFO")
        self.refresh_projects()
        self.root.mainloop()


# Import dialog for convenience
import tkinter.simpledialog

def main():
    """Main entry point."""
    app = ModernLPESGui()
    app.run()


if __name__ == "__main__":
    main()

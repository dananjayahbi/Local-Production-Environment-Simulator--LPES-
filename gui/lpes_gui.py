"""
LPES GUI Manager
A modern tkinter-based GUI for managing LPES projects with integrated console.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import asyncio
import threading
import subprocess
import sys
import os
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List

# Add src directory to Python path for imports
current_dir = Path(__file__).parent
root_dir = current_dir.parent
src_dir = root_dir / "src"
sys.path.insert(0, str(src_dir))

# Modern UI styling
COLORS = {
    'primary': '#2c3e50',
    'secondary': '#34495e',
    'accent': '#3498db',
    'success': '#27ae60',
    'warning': '#f39c12',
    'error': '#e74c3c',
    'bg': '#ecf0f1',
    'card': '#ffffff',
    'text': '#2c3e50',
    'muted': '#7f8c8d'
}

class ConsoleHandler(logging.Handler):
    """Custom logging handler that redirects to GUI console."""
    
    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget
        
    def emit(self, record):
        msg = self.format(record)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on log level
        if record.levelno >= logging.ERROR:
            color = 'red'
        elif record.levelno >= logging.WARNING:
            color = 'orange'
        elif record.levelno >= logging.INFO:
            color = 'blue'
        else:
            color = 'gray'
            
        # Thread-safe GUI update
        self.console_widget.after(0, self._append_to_console, f"[{timestamp}] {msg}", color)
    
    def _append_to_console(self, message, color):
        self.console_widget.config(state='normal')
        self.console_widget.insert(tk.END, f"{message}\n")
        # Auto-scroll to bottom
        self.console_widget.see(tk.END)
        self.console_widget.config(state='disabled')


class LPESGuiManager:
    """Main GUI application for LPES management."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.projects = {}
        self.setup_gui()
        self.setup_logging()
        self.load_projects()
        
    def setup_gui(self):
        """Setup the main GUI interface."""
        self.root.title("LPES Manager - Local Production Environment Simulator")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLORS['bg'])
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), background=COLORS['bg'])
        style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'), background=COLORS['bg'])
        style.configure('Card.TFrame', background=COLORS['card'], relief='solid', borderwidth=1)
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'))
        
        # Main container
        main_frame = ttk.Frame(self.root, style='Card.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🚀 LPES Manager", style='Title.TLabel')
        title_label.pack(pady=(10, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True, padx=10)
        
        # Create tabs
        self.create_projects_tab()
        self.create_console_tab()
        self.create_settings_tab()
        
    def create_projects_tab(self):
        """Create the projects management tab."""
        projects_frame = ttk.Frame(self.notebook)
        self.notebook.add(projects_frame, text="📋 Projects")
        
        # Top toolbar
        toolbar = ttk.Frame(projects_frame)
        toolbar.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(toolbar, text="➕ New Project", command=self.new_project_dialog, style='Primary.TButton').pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_projects).pack(side='left', padx=5)
        ttk.Button(toolbar, text="🗑️ Delete Selected", command=self.delete_selected_project).pack(side='left', padx=5)
        
        # Projects list
        list_frame = ttk.Frame(projects_frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for projects
        columns = ('Name', 'Domain', 'Status', 'Port', 'Type')
        self.projects_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.projects_tree.heading(col, text=col)
            self.projects_tree.column(col, width=120)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=scrollbar.set)
        
        self.projects_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Project actions frame
        actions_frame = ttk.LabelFrame(projects_frame, text="📱 Project Actions", padding=10)
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        # Action buttons
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="🔨 Build", command=self.build_project).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="▶️ Start", command=self.start_project).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_project).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🌐 Add Domain", command=self.add_domain_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔒 SSL Manage", command=self.manage_ssl).pack(side='left', padx=5)
        
        # Proxy controls
        proxy_frame = ttk.LabelFrame(projects_frame, text="🔄 Proxy Server", padding=10)
        proxy_frame.pack(fill='x', padx=10, pady=5)
        
        proxy_btn_frame = ttk.Frame(proxy_frame)
        proxy_btn_frame.pack(fill='x')
        
        ttk.Button(proxy_btn_frame, text="▶️ Start Proxy", command=self.start_proxy).pack(side='left', padx=5)
        ttk.Button(proxy_btn_frame, text="⏹️ Stop Proxy", command=self.stop_proxy).pack(side='left', padx=5)
        
        # Status labels
        self.proxy_status_label = ttk.Label(proxy_btn_frame, text="Status: Unknown")
        self.proxy_status_label.pack(side='right', padx=10)
        
    def create_console_tab(self):
        """Create the integrated console tab."""
        console_frame = ttk.Frame(self.notebook)
        self.notebook.add(console_frame, text="📟 Console")
        
        # Console controls
        controls_frame = ttk.Frame(console_frame)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(controls_frame, text="🧹 Clear Console", command=self.clear_console).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="💾 Save Log", command=self.save_console_log).pack(side='left', padx=5)
        
        # Log level selector
        ttk.Label(controls_frame, text="Log Level:").pack(side='right', padx=(10, 5))
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(controls_frame, textvariable=self.log_level_var, 
                                     values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                     state="readonly", width=10)
        log_level_combo.pack(side='right', padx=5)
        log_level_combo.bind('<<ComboboxSelected>>', self.change_log_level)
        
        # Console text widget
        console_container = ttk.Frame(console_frame)
        console_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.console_text = scrolledtext.ScrolledText(console_container, 
                                                    wrap=tk.WORD, 
                                                    state='disabled',
                                                    height=20,
                                                    font=('Consolas', 10))
        self.console_text.pack(fill='both', expand=True)
        
        # Add welcome message
        self.log_message("🚀 LPES GUI Manager started successfully!", "INFO")
        self.log_message("Ready to manage your Local Production Environment projects.", "INFO")
        
    def create_settings_tab(self):
        """Create the settings tab."""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # LPES Path Settings
        path_frame = ttk.LabelFrame(settings_frame, text="📁 LPES Configuration", padding=10)
        path_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(path_frame, text="LPES Directory:").pack(anchor='w')
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill='x', pady=5)
        
        self.lpes_path_var = tk.StringVar(value=os.getcwd())
        path_entry = ttk.Entry(path_entry_frame, textvariable=self.lpes_path_var, width=60)
        path_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(path_entry_frame, text="📂 Browse", command=self.browse_lpes_path).pack(side='right', padx=(5, 0))
        
        # SSL Settings
        ssl_frame = ttk.LabelFrame(settings_frame, text="🔒 SSL Configuration", padding=10)
        ssl_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(ssl_frame, text="📜 Trust CA Certificate", command=self.show_ssl_trust_info).pack(anchor='w', pady=2)
        ttk.Button(ssl_frame, text="📋 List SSL Certificates", command=self.list_ssl_certificates).pack(anchor='w', pady=2)
        
        # About
        about_frame = ttk.LabelFrame(settings_frame, text="ℹ️ About", padding=10)
        about_frame.pack(fill='x', padx=10, pady=5)
        
        about_text = """
        LPES GUI Manager v1.0
        Local Production Environment Simulator
        
        A modern GUI interface for managing NextJS and other web applications
        in a production-like environment with SSL certificates and custom domains.
        
        Features:
        • Project lifecycle management
        • SSL certificate generation
        • Custom domain configuration
        • Reverse proxy server
        • Build monitoring
        • Integrated console logging
        """
        
        ttk.Label(about_frame, text=about_text, justify='left').pack(anchor='w')
        
    def setup_logging(self):
        """Setup logging to redirect to GUI console."""
        # Create console handler
        self.console_handler = ConsoleHandler(self.console_text)
        self.console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        
        # Setup root logger
        logging.basicConfig(level=logging.INFO, handlers=[self.console_handler])
        
        # Also capture LPES logs
        lpes_logger = logging.getLogger('lpes')
        lpes_logger.addHandler(self.console_handler)
        lpes_logger.setLevel(logging.INFO)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message to the console."""
        logger = logging.getLogger("LPES-GUI")
        getattr(logger, level.lower())(message)
        
    def run_lpes_command(self, command: List[str], description: str = "") -> bool:
        """Run an LPES command and capture output."""
        try:
            if description:
                self.log_message(f"🔄 {description}", "INFO")
            
            full_command = [sys.executable, str(root_dir / "src" / "main.py")] + command
            self.log_message(f"Executing: {' '.join(full_command)}", "DEBUG")
            
            # Change to root directory for execution
            cwd = root_dir
            
            result = subprocess.run(
                full_command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                self.log_message(f"Output: {result.stdout.strip()}", "INFO")
            
            if result.stderr:
                self.log_message(f"Error: {result.stderr.strip()}", "ERROR")
                
            if result.returncode == 0:
                self.log_message(f"✅ {description or 'Command'} completed successfully", "INFO")
                return True
            else:
                self.log_message(f"❌ {description or 'Command'} failed with code {result.returncode}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message(f"⏰ Command timed out: {description}", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"💥 Exception running command: {str(e)}", "ERROR")
            return False
    
    def load_projects(self):
        """Load and display current projects."""
        if self.run_lpes_command(["list"], "Loading projects"):
            self.refresh_projects()
    
    def refresh_projects(self):
        """Refresh the projects list."""
        self.log_message("🔄 Refreshing projects list...", "INFO")
        
        # Clear current items
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        
        # Get projects data (this would ideally parse JSON output)
        # For now, we'll add some mock data for demonstration
        try:
            # In a real implementation, this would parse the LPES list command output
            mock_projects = [
                ("my-app", "simpleapp.local", "🔴 Stopped", "3000", "nextjs"),
                ("simpleapp", "simpleapp.local", "🔴 Stopped", "3000", "nextjs")
            ]
            
            for project in mock_projects:
                self.projects_tree.insert('', 'end', values=project)
                
        except Exception as e:
            self.log_message(f"Error refreshing projects: {str(e)}", "ERROR")
    
    def get_selected_project(self) -> Optional[str]:
        """Get the currently selected project name."""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a project first.")
            return None
        
        item = self.projects_tree.item(selection[0])
        return item['values'][0]  # Project name is first column
    
    def new_project_dialog(self):
        """Show dialog to create new project."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Project")
        dialog.geometry("500x400")
        dialog.configure(bg=COLORS['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Form fields
        ttk.Label(dialog, text="📝 Create New LPES Project", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Project name
        ttk.Label(dialog, text="Project Name:").pack(anchor='w', padx=20, pady=(10, 5))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=50).pack(padx=20, pady=(0, 10))
        
        # Project path
        ttk.Label(dialog, text="Project Path:").pack(anchor='w', padx=20, pady=(0, 5))
        path_frame = ttk.Frame(dialog)
        path_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=path_var, width=40).pack(side='left', fill='x', expand=True)
        ttk.Button(path_frame, text="📂 Browse", 
                  command=lambda: path_var.set(filedialog.askdirectory())).pack(side='right', padx=(5, 0))
        
        # Build command
        ttk.Label(dialog, text="Build Command:").pack(anchor='w', padx=20, pady=(0, 5))
        build_var = tk.StringVar(value="npm run build")
        ttk.Entry(dialog, textvariable=build_var, width=50).pack(padx=20, pady=(0, 10))
        
        # Start command
        ttk.Label(dialog, text="Start Command:").pack(anchor='w', padx=20, pady=(0, 5))
        start_var = tk.StringVar(value="npm start")
        ttk.Entry(dialog, textvariable=start_var, width=50).pack(padx=20, pady=(0, 10))
        
        # Port
        ttk.Label(dialog, text="Port:").pack(anchor='w', padx=20, pady=(0, 5))
        port_var = tk.StringVar(value="3000")
        ttk.Entry(dialog, textvariable=port_var, width=50).pack(padx=20, pady=(0, 10))
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def create_project():
            name = name_var.get().strip()
            path = path_var.get().strip()
            build = build_var.get().strip()
            start = start_var.get().strip()
            port = port_var.get().strip()
            
            if not all([name, path, build, start, port]):
                messagebox.showerror("Error", "All fields are required!")
                return
            
            command = ["init", name, "--path", path, "--build", build, "--start", start, "--port", port]
            if self.run_lpes_command(command, f"Creating project '{name}'"):
                dialog.destroy()
                self.refresh_projects()
            
        ttk.Button(btn_frame, text="✅ Create Project", command=create_project, style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy).pack(side='left', padx=5)
    
    def add_domain_dialog(self):
        """Show dialog to add domain to project."""
        project_name = self.get_selected_project()
        if not project_name:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add Domain to {project_name}")
        dialog.geometry("400x250")
        dialog.configure(bg=COLORS['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"🌐 Add Domain to '{project_name}'", font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        ttk.Label(dialog, text="Domain Name:").pack(anchor='w', padx=20, pady=(10, 5))
        domain_var = tk.StringVar(value=f"{project_name}.local")
        ttk.Entry(dialog, textvariable=domain_var, width=40).pack(padx=20, pady=(0, 10))
        
        # Options
        ssl_var = tk.BooleanVar(value=True)
        hosts_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(dialog, text="Generate SSL Certificate", variable=ssl_var).pack(anchor='w', padx=20, pady=5)
        ttk.Checkbutton(dialog, text="Add to Hosts File", variable=hosts_var).pack(anchor='w', padx=20, pady=5)
        
        def add_domain():
            domain = domain_var.get().strip()
            if not domain:
                messagebox.showerror("Error", "Domain name is required!")
                return
            
            command = ["domain", "add", project_name, domain]
            if ssl_var.get():
                command.append("--ssl")
            if hosts_var.get():
                command.append("--hosts-file")
            
            if self.run_lpes_command(command, f"Adding domain '{domain}' to '{project_name}'"):
                dialog.destroy()
                self.refresh_projects()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="✅ Add Domain", command=add_domain, style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy).pack(side='left', padx=5)
    
    def build_project(self):
        """Build selected project."""
        project_name = self.get_selected_project()
        if project_name:
            self.run_lpes_command(["build", project_name], f"Building project '{project_name}'")
    
    def start_project(self):
        """Start selected project."""
        project_name = self.get_selected_project()
        if project_name:
            self.run_lpes_command(["start", project_name], f"Starting project '{project_name}'")
            # Refresh to update status
            self.root.after(2000, self.refresh_projects)
    
    def stop_project(self):
        """Stop selected project."""
        project_name = self.get_selected_project()
        if project_name:
            self.run_lpes_command(["stop", project_name], f"Stopping project '{project_name}'")
            # Refresh to update status
            self.root.after(2000, self.refresh_projects)
    
    def delete_selected_project(self):
        """Delete selected project with confirmation."""
        project_name = self.get_selected_project()
        if not project_name:
            return
        
        if messagebox.askyesno("Confirm Deletion", 
                              f"Are you sure you want to delete project '{project_name}'?\n\n"
                              "This will also clean up SSL certificates and domains."):
            if self.run_lpes_command(["remove", project_name, "--cleanup"], f"Deleting project '{project_name}'"):
                self.refresh_projects()
    
    def start_proxy(self):
        """Start LPES proxy server."""
        self.run_lpes_command(["proxy", "start"], "Starting proxy server")
        self.proxy_status_label.config(text="Status: Starting...")
        self.root.after(3000, lambda: self.proxy_status_label.config(text="Status: Running ✅"))
    
    def stop_proxy(self):
        """Stop LPES proxy server."""
        self.run_lpes_command(["proxy", "stop"], "Stopping proxy server")
        self.proxy_status_label.config(text="Status: Stopped ⏹️")
    
    def manage_ssl(self):
        """Open SSL management dialog."""
        project_name = self.get_selected_project()
        if not project_name:
            return
        
        self.run_lpes_command(["ssl", "list"], "Listing SSL certificates")
    
    def show_ssl_trust_info(self):
        """Show SSL trust information."""
        self.run_lpes_command(["ssl", "trust-info"], "Getting SSL trust information")
    
    def list_ssl_certificates(self):
        """List SSL certificates."""
        self.run_lpes_command(["ssl", "list"], "Listing SSL certificates")
    
    def clear_console(self):
        """Clear the console output."""
        self.console_text.config(state='normal')
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state='disabled')
        self.log_message("Console cleared", "INFO")
    
    def save_console_log(self):
        """Save console log to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.console_text.get(1.0, tk.END))
                self.log_message(f"Console log saved to: {filename}", "INFO")
            except Exception as e:
                self.log_message(f"Error saving log: {str(e)}", "ERROR")
    
    def change_log_level(self, event=None):
        """Change the logging level."""
        level = self.log_level_var.get()
        logging.getLogger().setLevel(getattr(logging, level))
        self.log_message(f"Log level changed to: {level}", "INFO")
    
    def browse_lpes_path(self):
        """Browse for LPES directory."""
        path = filedialog.askdirectory(initialdir=self.lpes_path_var.get())
        if path:
            self.lpes_path_var.set(path)
            self.log_message(f"LPES path changed to: {path}", "INFO")
    
    def run(self):
        """Start the GUI application."""
        try:
            self.log_message("🚀 Starting LPES GUI Manager...", "INFO")
            self.refresh_projects()
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("👋 Shutting down LPES GUI Manager...", "INFO")
        except Exception as e:
            self.log_message(f"💥 Fatal error: {str(e)}", "ERROR")


def main():
    """Main entry point."""
    app = LPESGuiManager()
    app.run()


if __name__ == "__main__":
    main()

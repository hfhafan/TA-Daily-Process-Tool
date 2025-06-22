#!/usr/bin/env python3
"""
TA Daily Process Tool - GUI dengan tkinter
Tool untuk memproses data TA (Timing Advance) daily dari file CSV Ericsson

Author: Hadi Fauzan Hanif
Email: hadifauzanhanif@gmail.com
Version: 1.0
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, simpledialog
import os
import threading
from datetime import datetime, timedelta
import sys
import ctypes

# Import modul TA processing
try:
    from TA_daily_process_module import (
        process_ta_data, 
        process_ta_data_test, 
        DEFAULT_OUTPUT_PATH, 
        create_db_connection,
        create_admin_db_connection,
        DB_ADMIN_CONFIG
    )
    from sqlalchemy import text
except ImportError as e:
    print(f"Error importing TA module: {e}")
    sys.exit(1)

# Import modul auth
try:
    from auth import check_credentials, check_user_allowed
    from registry import save_login_info, read_login_info
    from spreadsheet import log_latest_login
    from device_id import get_device_id
except ImportError as e:
    print(f"Error importing auth modules: {e}")
    sys.exit(1)

def get_resource_path(relative_path):
    """Get absolute path to resource, works for development, PyInstaller, and Nuitka."""
    try:
        # PyInstaller (onefile) uses a temp folder
        base_path = sys._MEIPASS
    except AttributeError:
        # Nuitka or onedir PyInstaller or dev
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Get icon path
icon_hd = get_resource_path('HFH.ico')

def login_menu():
    """Display login dialog and return username, password"""
    # Create root window for login (hidden)
    temp_root = tk.Tk()
    temp_root.withdraw()  # Hide the root window
    
    login_window = tk.Toplevel(temp_root)
    login_window.title("Login - TA Daily Process Tool")
    login_window.geometry("400x300")
    login_window.resizable(False, False)
    login_window.transient(temp_root)
    login_window.grab_set()
    
    # Set icon for login window
    if os.path.exists(icon_hd):
        try:
            login_window.iconbitmap(icon_hd)
        except:
            pass
    
    # Center the window
    login_window.update_idletasks()
    x = (login_window.winfo_screenwidth() // 2) - (400 // 2)
    y = (login_window.winfo_screenheight() // 2) - (300 // 2)
    login_window.geometry(f"400x300+{x}+{y}")
    
    result = {'username': None, 'password': None}
    
    # Header
    header_frame = tk.Frame(login_window, bg="#FF6B35", height=60)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)
    
    title_label = tk.Label(header_frame, text="🔐 Login Required", 
                          font=("Arial", 16, "bold"), 
                          bg="#FF6B35", fg="white")
    title_label.pack(pady=15)
    
    # Login form
    form_frame = tk.Frame(login_window, padx=40, pady=30)
    form_frame.pack(fill=tk.BOTH, expand=True)
    
    tk.Label(form_frame, text="Username:", font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 5))
    username_entry = tk.Entry(form_frame, font=("Arial", 10), width=30)
    username_entry.pack(fill=tk.X, pady=(0, 15))
    
    tk.Label(form_frame, text="Password:", font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 5))
    password_entry = tk.Entry(form_frame, font=("Arial", 10), width=30, show="*")
    password_entry.pack(fill=tk.X, pady=(0, 20))
    
    def on_login():
        result['username'] = username_entry.get()
        result['password'] = password_entry.get()
        login_window.destroy()
        temp_root.quit()  # Exit the mainloop
    
    def on_cancel():
        login_window.destroy()
        temp_root.quit()  # Exit the mainloop
    
    # Buttons
    button_frame = tk.Frame(form_frame)
    button_frame.pack(fill=tk.X)
    
    tk.Button(button_frame, text="Login", command=on_login,
             bg="#A3BE8C", fg="white", font=("Arial", 10, "bold"),
             width=10).pack(side=tk.LEFT, padx=(0, 10))
    tk.Button(button_frame, text="Cancel", command=on_cancel,
             bg="#BF616A", fg="white", font=("Arial", 10),
             width=10).pack(side=tk.LEFT)
    
    # Bind Enter key
    def on_enter(event):
        on_login()
    
    login_window.bind('<Return>', on_enter)
    username_entry.focus()
    
    # Handle window close button
    def on_window_close():
        temp_root.quit()
    
    login_window.protocol("WM_DELETE_WINDOW", on_window_close)
    
    # Run the login dialog
    temp_root.mainloop()
    
    # Cleanup
    temp_root.destroy()
    
    return result['username'], result['password']

class TAProcessorGUI:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title("TA Daily Process Tool - Telkomsel")
        self.root.geometry("700x900")
        self.root.resizable(True, True)
        
        # Center the main window
        self.center_window()
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_folder = tk.StringVar(value=DEFAULT_OUTPUT_PATH)
        self.upload_to_db = tk.BooleanVar(value=True)
        self.is_processing = False
        
        self.setup_ui()
    
    def center_window(self):
        """Center the main window on screen with consistent positioning"""
        self.root.update_idletasks()
        width = 700
        height = 900
        
        # Calculate center position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # Adjust Y position slightly up to account for taskbar and ensure visibility
        y = max(0, y - 50)
        
        # Ensure window doesn't go off-screen
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Force window to be on top initially
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
    def setup_ui(self):
        """Setup user interface"""
        # Header - Reduced height
        header_frame = tk.Frame(self.root, bg="#FF6B35", height=70)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        # Configure grid for header layout
        header_frame.grid_columnconfigure(0, weight=1)  # Left space
        header_frame.grid_columnconfigure(1, weight=0)  # Center content
        header_frame.grid_columnconfigure(2, weight=1)  # Right space
        header_frame.grid_rowconfigure(0, weight=0)     # Buttons row
        header_frame.grid_rowconfigure(1, weight=1)     # Title row
        header_frame.grid_rowconfigure(2, weight=0)     # User row
        
        # Top buttons (About and Help) - positioned at top right
        button_frame = tk.Frame(header_frame, bg="#FF6B35")
        button_frame.grid(row=0, column=2, sticky="ne", padx=5, pady=2)
        
        tk.Button(button_frame, text="Help", command=self.show_help,
                 bg="#E5C07B", fg="#2E3440", font=("Arial", 8), width=8).pack(side=tk.RIGHT, padx=2)
        tk.Button(button_frame, text="About", command=self.show_about,
                 bg="#E5C07B", fg="#2E3440", font=("Arial", 8), width=8).pack(side=tk.RIGHT, padx=2)
        
        # Title section - centered in middle column
        title_section = tk.Frame(header_frame, bg="#FF6B35")
        title_section.grid(row=1, column=1, sticky="")
        
        title_label = tk.Label(title_section, text="📊 TA Daily Process Tool", 
                              font=("Arial", 16, "bold"), 
                              bg="#FF6B35", fg="white")
        title_label.pack()
        
        subtitle_label = tk.Label(title_section, text="Proses data TA (Timing Advance) daily dari file CSV Ericsson", 
                                 font=("Arial", 10), 
                                 bg="#FF6B35", fg="#FFE5DB")
        subtitle_label.pack()
        
        # User info - positioned at bottom left
        user_label = tk.Label(header_frame, text=f"User: {self.username}", 
                             font=("Arial", 8), 
                             bg="#FF6B35", fg="#FFE5DB")
        user_label.grid(row=2, column=0, sticky="sw", padx=5, pady=2)
        
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Input section
        input_frame = tk.LabelFrame(main_frame, text="📁 Input Data", 
                                   font=("Arial", 11, "bold"), padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        # Source file/folder
        tk.Label(input_frame, text="File CSV atau Folder berisi file CSV:", 
                font=("Arial", 10)).pack(anchor=tk.W)
        
        input_desc = tk.Label(input_frame, 
                             text="• Single file: Pilih satu file CSV data TA\n• Multiple files: Pilih folder yang berisi beberapa file CSV", 
                             font=("Arial", 9), fg="#666666")
        input_desc.pack(anchor=tk.W, pady=(0, 5))
        
        source_frame = tk.Frame(input_frame)
        source_frame.pack(fill=tk.X, pady=5)
        
        tk.Entry(source_frame, textvariable=self.input_path, 
                font=("Arial", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        button_frame = tk.Frame(source_frame)
        button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        tk.Button(button_frame, text="File CSV", command=self.browse_csv_file,
                 bg="#5E81AC", fg="white", font=("Arial", 9), width=8).pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(button_frame, text="Folder", command=self.browse_folder,
                 bg="#5E81AC", fg="white", font=("Arial", 9), width=8).pack(side=tk.LEFT)
        
        # Processing options
        options_frame = tk.LabelFrame(main_frame, text="⚙️ Opsi Pemrosesan", 
                                     font=("Arial", 11, "bold"), padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=5)
        
        # Database upload option
        db_frame = tk.Frame(options_frame)
        db_frame.pack(anchor=tk.W, pady=5)
        
        tk.Checkbutton(db_frame, text="Upload hasil ke Database (MariaDB)", 
                      variable=self.upload_to_db,
                      font=("Arial", 10)).pack(side=tk.LEFT)
        
        # Clear database button
        clear_btn = tk.Button(db_frame, text="🗑️ Clear Database", command=self.safe_show_clear_database_menu,
                 bg="#BF616A", fg="white", font=("Arial", 9))
        clear_btn.pack(side=tk.RIGHT)
        
        # Info about database
        db_info = tk.Label(options_frame, 
                          text="✓ Upload: Hasil akan disimpan ke database + file CSV\n"
                               "✗ Test Mode: Hasil hanya disimpan ke file CSV saja", 
                          font=("Arial", 9), fg="#666666")
        db_info.pack(anchor=tk.W, pady=(0, 5))
        
        # Output section
        output_frame = tk.LabelFrame(main_frame, text="📦 Output", 
                                    font=("Arial", 11, "bold"), padx=10, pady=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(output_frame, text="Folder Output:", font=("Arial", 10)).pack(anchor=tk.W)
        
        output_dir_frame = tk.Frame(output_frame)
        output_dir_frame.pack(fill=tk.X, pady=5)
        
        tk.Entry(output_dir_frame, textvariable=self.output_folder, 
                font=("Arial", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(output_dir_frame, text="Browse", command=self.browse_output_folder,
                 bg="#5E81AC", fg="white", font=("Arial", 9)).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Process button
        process_frame = tk.Frame(main_frame)
        process_frame.pack(fill=tk.X, pady=15)
        
        self.process_button = tk.Button(process_frame, text="🚀 PROSES DATA TA", 
                                       command=self.start_processing,
                                       bg="#A3BE8C", fg="white", 
                                       font=("Arial", 14, "bold"), 
                                       height=2)
        self.process_button.pack(fill=tk.X)
        
        # Progress bar
        progress_frame = tk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X)
        
        # Log section
        log_frame = tk.LabelFrame(main_frame, text="📋 Log Pemrosesan", 
                                 font=("Arial", 11, "bold"), padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, 
                                                 font=("Consolas", 9),
                                                 bg="#F8F8F8")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Siap memproses data TA daily")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W,
                             bg="#ECEFF4", font=("Arial", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Auto-detect if sample files exist
        self.auto_detect_files()
        
        # Welcome message
        self.log(f"🎯 Selamat datang, {self.username}!")
        self.log("💡 Pilih file CSV atau folder yang berisi file CSV data TA Ericsson")
        
    def show_about(self):
        """Show About dialog with GitHub link"""
        # Create custom about dialog
        about_window = tk.Toplevel(self.root)
        about_window.title("About - TA Daily Process Tool")
        about_window.geometry("450x400")  # Tinggi diperbesar untuk memastikan tombol terlihat
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Set icon
        if os.path.exists(icon_hd):
            try:
                about_window.iconbitmap(icon_hd)
            except:
                pass
        
        # Center window
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (225)
        y = (about_window.winfo_screenheight() // 2) - (200)  # Adjust untuk tinggi baru
        about_window.geometry(f"450x400+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(about_window, bg="#FF6B35", height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="📊 About TA Daily Process Tool", 
                              font=("Arial", 10, "bold"), 
                              bg="#FF6B35", fg="white")
        title_label.pack(pady=15)
        
        # Content
        content_frame = tk.Frame(about_window, padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        about_text = """TA Daily Process Tool - Telkomsel
Version 1.0

Dibuat oleh:
Hadi Fauzan Hanif
Email: hadifauzanhanif@gmail.com

Tool untuk memproses data TA (Timing Advance) 
daily dari file CSV Ericsson dengan GUI yang 
user-friendly dan database integration.

⚠️ PENTING: Gunakan file .exe dari download link
karena source code memerlukan lisensi khusus.

© 2025 - Hadi Fauzan Hanif"""
        
        tk.Label(content_frame, text=about_text, 
                font=("Arial", 9), justify=tk.LEFT).pack(pady=(0, 15))
        
        # GitHub link button
        def open_github():
            import webbrowser
            webbrowser.open("https://github.com/hfhafan/TA-Daily-Process-Tool")
        
        github_btn = tk.Button(content_frame, text="🔗 GitHub Repository", 
                              command=open_github,
                              bg="#5E81AC", fg="white", 
                              font=("Arial", 10, "bold"),
                              cursor="hand2")
        github_btn.pack(pady=5)
        
        # Download link button  
        def open_download():
            import webbrowser
            webbrowser.open("http://bit.ly/3GanRLq")
        
        download_btn = tk.Button(content_frame, text="⬇️ Download Latest .exe", 
                                command=open_download,
                                bg="#A3BE8C", fg="white", 
                                font=("Arial", 10, "bold"),
                                cursor="hand2")
        download_btn.pack(pady=5)
        
        # Close button
        tk.Button(content_frame, text="Close", command=about_window.destroy,
                 bg="#BF616A", fg="white", font=("Arial", 10),
                 width=10).pack(pady=15)
        
    def show_help(self):
        """Show Help dialog"""
        help_text = """
CARA PENGGUNAAN:

1. INPUT DATA
   • Pilih file CSV atau folder berisi file CSV
   • File harus berisi kolom: DATE_ID, ERBS, EUtranCellFDD, 
     pmTaInit2Distr_00 sampai pmTaInit2Distr_34

2. OPSI PEMROSESAN
   • Centang "Upload ke Database" untuk simpan ke MariaDB
   • Atau gunakan Test Mode untuk output CSV saja

3. PROSES DATA
   • Klik tombol "PROSES DATA TA"
   • Monitor progress di log area
   • Hasil akan disimpan di folder output

4. CLEAR DATABASE
   • Gunakan tombol "Clear Database" untuk membersihkan data
   • Pilihan: Clear All, By Date Range, atau By Site ID

SUPPORT:
Email: hadifauzanhanif@gmail.com
        """
        messagebox.showinfo("Help", help_text.strip())
        
    def safe_show_clear_database_menu(self):
        """Safe wrapper for show_clear_database_menu with error handling"""
        try:
            self.log("🖱️ Tombol Clear Database diklik")
            self.show_clear_database_menu()
        except Exception as e:
            self.log(f"❌ Error saat buka Clear Database: {str(e)}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Gagal membuka Clear Database:\n{str(e)}")
        
    def show_clear_database_menu(self):
        """Show Clear Database menu dialog - Complete version"""
        try:
            self.log("🔍 DEBUG: Masuk ke show_clear_database_menu")
            
            # Konfirmasi akses
            confirm_access = messagebox.askyesno("Konfirmasi Akses", 
                                               f"Anda akan mengakses menu Clear Database.\n\n"
                                               f"User: {self.username}\n"
                                               f"Database: {DB_ADMIN_CONFIG['database']}.{DB_ADMIN_CONFIG['table']}\n\n"
                                               f"Lanjutkan?")
            if not confirm_access:
                self.log("❌ User membatalkan akses clear database")
                return
                
            # Create clear database window
            clear_window = tk.Toplevel(self.root)
            clear_window.title("Clear Database - TA Daily Process Tool")
            clear_window.resizable(False, True)  # Width resizable, height fixed
            clear_window.transient(self.root)
            clear_window.grab_set()
            
            # Set initial geometry and center the window
            window_width = 600
            window_height = 650
            clear_window.update_idletasks()
            x = (clear_window.winfo_screenwidth() // 2) - (window_width // 2)
            y = (clear_window.winfo_screenheight() // 2) - (window_height // 2)
            clear_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Set minimum size to ensure all content is visible
            clear_window.minsize(550, 600)
            
            # Header
            header_frame = tk.Frame(clear_window, bg="#BF616A", height=60)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            title_label = tk.Label(header_frame, text="🗑️ Clear Database", 
                                  font=("Arial", 16, "bold"), 
                                  bg="#BF616A", fg="white")
            title_label.pack(pady=15)
            
            # Main content frame
            main_frame = tk.Frame(clear_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # User info frame
            info_frame = tk.LabelFrame(main_frame, text="Connection Info", font=("Arial", 10, "bold"))
            info_frame.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(info_frame, text=f"Login User: {self.username}", 
                    font=("Arial", 9, "bold")).pack(anchor=tk.W, padx=10, pady=2)
            tk.Label(info_frame, text=f"Database: {DB_ADMIN_CONFIG['database']}.{DB_ADMIN_CONFIG['table']}", 
                    font=("Arial", 9), fg="#666666").pack(anchor=tk.W, padx=10, pady=2)
            
            # Options frame
            options_frame = tk.LabelFrame(main_frame, text="Clear Options", font=("Arial", 10, "bold"))
            options_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Clear option variable
            clear_option = tk.StringVar(value="all")
            
            # Clear All option
            tk.Radiobutton(options_frame, text="Clear All Data", 
                          variable=clear_option, value="all",
                          font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=10, pady=5)
            tk.Label(options_frame, text="Hapus semua data dari tabel tainit_cell_day", 
                    font=("Arial", 9), fg="#666666").pack(anchor=tk.W, padx=25, pady=(0, 10))
            
            # Clear by Date Range option
            tk.Radiobutton(options_frame, text="Clear by Date Range", 
                          variable=clear_option, value="date",
                          font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=10, pady=5)
            tk.Label(options_frame, text="Hapus data berdasarkan rentang tanggal", 
                    font=("Arial", 9), fg="#666666").pack(anchor=tk.W, padx=25)
            
            date_frame = tk.Frame(options_frame)
            date_frame.pack(anchor=tk.W, padx=25, pady=(5, 10))
            
            tk.Label(date_frame, text="From:", font=("Arial", 9)).pack(side=tk.LEFT)
            from_date = tk.Entry(date_frame, font=("Arial", 9), width=12)
            from_date.pack(side=tk.LEFT, padx=(5, 10))
            from_date.insert(0, "2024-01-01")
            
            tk.Label(date_frame, text="To:", font=("Arial", 9)).pack(side=tk.LEFT)
            to_date = tk.Entry(date_frame, font=("Arial", 9), width=12)
            to_date.pack(side=tk.LEFT, padx=(5, 0))
            to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
            # Clear by Site ID option
            tk.Radiobutton(options_frame, text="Clear by Site ID", 
                          variable=clear_option, value="site",
                          font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=10, pady=5)
            tk.Label(options_frame, text="Hapus data berdasarkan Site ID tertentu", 
                    font=("Arial", 9), fg="#666666").pack(anchor=tk.W, padx=25)
            
            site_frame = tk.Frame(options_frame)
            site_frame.pack(anchor=tk.W, padx=25, pady=(5, 10))
            
            tk.Label(site_frame, text="Site ID:", font=("Arial", 9)).pack(side=tk.LEFT)
            site_id = tk.Entry(site_frame, font=("Arial", 9), width=20)
            site_id.pack(side=tk.LEFT, padx=(5, 0))
            site_id.insert(0, "BTM443")
            
            # Warning frame
            warning_frame = tk.LabelFrame(main_frame, text="⚠️ PERINGATAN", 
                                        font=("Arial", 10, "bold"), fg="#BF616A")
            warning_frame.pack(fill=tk.X, pady=(0, 10))
            
            warning_text = tk.Label(warning_frame, 
                                  text="Operasi ini akan menghapus data secara permanen!\n"
                                       "Pastikan Anda memiliki backup data sebelum melanjutkan.\n"
                                       "Tidak ada cara untuk mengembalikan data yang sudah dihapus.", 
                                  font=("Arial", 9), fg="#BF616A", justify=tk.LEFT)
            warning_text.pack(anchor=tk.W, padx=10, pady=10)
            
            # Buttons frame - Fixed position at bottom
            button_frame = tk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=20)
            
            def execute_clear():
                option = clear_option.get()
                
                # Get values before showing confirmation dialog
                from_date_value = from_date.get()
                to_date_value = to_date.get()
                site_id_value = site_id.get()
                
                # Confirmation dialog
                if option == "all":
                    confirm_text = "Yakin ingin menghapus SEMUA data dari database?"
                elif option == "date":
                    confirm_text = f"Yakin ingin menghapus data dari {from_date_value} sampai {to_date_value}?"
                else:
                    confirm_text = f"Yakin ingin menghapus data untuk Site ID: {site_id_value}?"
                
                if messagebox.askyesno("Konfirmasi Final", confirm_text):
                    clear_window.destroy()
                    self.execute_database_clear(option, from_date_value, to_date_value, site_id_value)
                    
            def cancel_clear():
                self.log("❌ User membatalkan clear database")
                clear_window.destroy()
            
            # Buttons with better spacing
            tk.Button(button_frame, text="🗑️ EXECUTE CLEAR", command=execute_clear,
                     bg="#BF616A", fg="white", font=("Arial", 8, "bold"),
                     height=2, width=20).pack(side=tk.LEFT, padx=(0, 10))
            tk.Button(button_frame, text="❌ CANCEL", command=cancel_clear,
                     bg="#4C566A", fg="white", font=("Arial", 8),
                     height=2, width=10).pack(side=tk.LEFT)
            
            self.log("✅ Dialog Clear Database ditampilkan lengkap")
                
        except Exception as e:
            self.log(f"❌ ERROR di show_clear_database_menu: {str(e)}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error dalam show_clear_database_menu:\n{str(e)}")
        
    def execute_database_clear(self, option, from_date, to_date, site_id):
        """Execute database clear operation"""
        try:
            self.log("="*50)
            self.log("🗑️ MEMULAI OPERASI CLEAR DATABASE")
            self.log(f"🗄️ Database: {DB_ADMIN_CONFIG['database']}.{DB_ADMIN_CONFIG['table']}")
            
            engine = create_admin_db_connection()
            if engine is None:
                self.log("❌ Gagal koneksi ke database dengan user admin")
                messagebox.showerror("Error", "Gagal koneksi ke database dengan user admin")
                return
            
            # Build query based on option
            table_name = DB_ADMIN_CONFIG['table']
            if option == "all":
                query = f"DELETE FROM {table_name}"
                self.log("🗑️ Menghapus SEMUA data...")
            elif option == "date":
                query = f"DELETE FROM {table_name} WHERE DateId BETWEEN %s AND %s"
                self.log(f"🗑️ Menghapus data dari {from_date} sampai {to_date}...")
            else:  # site
                query = f"DELETE FROM {table_name} WHERE SiteId = %s"
                self.log(f"🗑️ Menghapus data untuk Site ID: {site_id}...")
            
            # Execute query
            with engine.begin() as conn:
                if option == "all":
                    result = conn.execute(text(query))
                elif option == "date":
                    result = conn.execute(text(query), (from_date, to_date))
                else:  # site
                    result = conn.execute(text(query), (site_id,))
                
                rows_affected = result.rowcount
                
            self.log(f"✅ Berhasil menghapus {rows_affected} baris data")
            self.log("="*50)
            
            messagebox.showinfo("Success", f"Berhasil menghapus {rows_affected} baris data dari database\n\nDatabase: {DB_ADMIN_CONFIG['database']}.{DB_ADMIN_CONFIG['table']}")
            
        except Exception as e:
            self.log(f"❌ Error saat clear database: {str(e)}")
            messagebox.showerror("Error", f"Gagal clear database:\n{str(e)}")
        
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_status(self, status):
        """Update status bar"""
        self.status_var.set(status)
        self.root.update_idletasks()
        
    def auto_detect_files(self):
        """Auto-detect sample files in current directory"""
        current_dir = os.getcwd()
        
        # Look for common TA file patterns
        sample_files = []
        for file in os.listdir(current_dir):
            if file.lower().endswith('.csv') and any(keyword in file.lower() for keyword in ['ta', 'cell', 'daily', '4g']):
                sample_files.append(file)
        
        if sample_files:
            # Use the first detected file
            detected_file = os.path.join(current_dir, sample_files[0])
            self.input_path.set(detected_file)
            self.log(f"✅ Auto-detected: {sample_files[0]}")
            if len(sample_files) > 1:
                self.log(f"💡 {len(sample_files)} file CSV ditemukan. Gunakan opsi 'Folder' untuk memproses semua.")
        
    def browse_csv_file(self):
        """Browse for single CSV file"""
        file_path = filedialog.askopenfilename(
            title="Pilih File CSV Data TA",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.input_path.set(file_path)
            self.log(f"📄 File dipilih: {os.path.basename(file_path)}")
            
    def browse_folder(self):
        """Browse for folder containing CSV files"""
        folder_path = filedialog.askdirectory(title="Pilih Folder Berisi File CSV")
        if folder_path:
            self.input_path.set(folder_path)
            
            # Count CSV files in folder
            csv_count = len([f for f in os.listdir(folder_path) 
                           if f.lower().endswith('.csv')])
            
            self.log(f"📁 Folder dipilih: {os.path.basename(folder_path)}")
            self.log(f"📊 Ditemukan {csv_count} file CSV di dalam folder")
            
    def browse_output_folder(self):
        """Browse for output folder"""
        folder_path = filedialog.askdirectory(title="Pilih Folder Output")
        if folder_path:
            self.output_folder.set(folder_path)
            self.log(f"📁 Output folder: {os.path.basename(folder_path)}")
            
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.input_path.get():
            messagebox.showerror("Error", "Pilih file CSV atau folder input!")
            return False
            
        input_path = self.input_path.get()
        if not os.path.exists(input_path):
            messagebox.showerror("Error", "File atau folder input tidak ditemukan!")
            return False
            
        # Check if it's a file or folder
        if os.path.isfile(input_path):
            if not input_path.lower().endswith('.csv'):
                messagebox.showerror("Error", "File harus berformat CSV!")
                return False
        else:
            # Check if folder contains CSV files
            csv_files = [f for f in os.listdir(input_path) if f.lower().endswith('.csv')]
            if not csv_files:
                messagebox.showerror("Error", "Folder tidak berisi file CSV!")
                return False
                
        if not self.output_folder.get():
            messagebox.showerror("Error", "Pilih folder output!")
            return False
            
        return True
        
    def processing_thread(self):
        """Run processing in separate thread"""
        try:
            self.is_processing = True
            self.process_button.config(state='disabled')
            self.progress.start()
            
            self.log("="*60)
            self.log("🚀 MEMULAI PEMROSESAN DATA TA")
            self.log("="*60)
            
            input_path = self.input_path.get()
            upload_db = self.upload_to_db.get()
            
            # Log configuration
            self.log(f"📄 Input: {os.path.basename(input_path)}")
            self.log(f"📁 Output: {self.output_folder.get()}")
            self.log(f"🗄️ Upload DB: {'Ya' if upload_db else 'Tidak (Test Mode)'}")
            
            self.update_status("Memproses data TA...")
            
            # Call processing function
            if upload_db:
                success = process_ta_data(input_path, upload_to_db=True)
            else:
                success = process_ta_data_test(input_path)
                
            if success:
                self.log("="*60)
                self.log("🎉 PEMROSESAN DATA TA BERHASIL!")
                self.log("="*60)
                self.log("📋 RINGKASAN:")
                self.log("✅ Data berhasil diproses dan disimpan")
                if upload_db:
                    self.log("✅ Data berhasil diupload ke database")
                else:
                    self.log("ℹ️ Mode test - tidak upload ke database")
                self.log(f"📁 Hasil tersimpan di: {self.output_folder.get()}")
                
                self.update_status("✅ Pemrosesan berhasil!")
                
                # Show success message
                mode_text = "dengan upload database" if upload_db else "mode test"
                messagebox.showinfo("Berhasil!", 
                    f"Pemrosesan data TA berhasil {mode_text}!\n\n"
                    f"Hasil tersimpan di:\n{self.output_folder.get()}\n\n"
                    f"Silakan cek file output dan log untuk detail.")
                    
            else:
                self.log("❌ PEMROSESAN GAGAL!")
                self.log("💡 Periksa log error di atas untuk detail masalah")
                self.update_status("❌ Pemrosesan gagal!")
                messagebox.showerror("Error", 
                    "Pemrosesan data TA gagal!\n\n"
                    "Silakan periksa log untuk detail error.")
                    
        except Exception as e:
            self.log(f"❌ Error tidak terduga: {str(e)}")
            self.update_status("❌ Error terjadi!")
            messagebox.showerror("Error", f"Terjadi error:\n{str(e)}")
            
        finally:
            self.is_processing = False
            self.progress.stop()
            self.process_button.config(state='normal')
            
    def start_processing(self):
        """Start processing in background thread"""
        if self.is_processing:
            messagebox.showwarning("Warning", "Pemrosesan sedang berjalan!")
            return
            
        if not self.validate_inputs():
            return
            
        # Confirmation dialog
        input_type = "file" if os.path.isfile(self.input_path.get()) else "folder"
        mode_text = "dengan upload ke database" if self.upload_to_db.get() else "mode test (tanpa upload DB)"
        
        result = messagebox.askyesno("Konfirmasi", 
            f"Mulai pemrosesan data TA?\n\n"
            f"Input: {input_type} - {os.path.basename(self.input_path.get())}\n"
            f"Mode: {mode_text}\n"
            f"Output: {os.path.basename(self.output_folder.get())}")
            
        if not result:
            return
            
        # Run processing in separate thread
        thread = threading.Thread(target=self.processing_thread)
        thread.daemon = True
        thread.start()
        
    def on_closing(self):
        """Handle window closing"""
        if self.is_processing:
            result = messagebox.askyesno("Konfirmasi", 
                "Pemrosesan sedang berjalan!\n"
                "Yakin ingin keluar dan menghentikan proses?")
            if not result:
                return
                
        self.root.destroy()

def main():
    """Main entry point with login handling"""
    try:
        # ========== Login handling ==========
        device_id = get_device_id()
        stored_username, stored_password = read_login_info()
        login_successful = False
        username = None
        
        # Cek jika ada kredensial tersimpan
        if stored_username and stored_password:
            # Auto-login dari registry
            status = check_credentials(stored_username, stored_password, device_id)
            print(f"[DEBUG] Auto-login status untuk {stored_username}: {status}")
            
            if status == "success":
                username = stored_username
                login_successful = True
                print(f"[INFO] Auto-login berhasil untuk user: {username}")
            elif status == "device_mismatch":
                print(f"[WARNING] Auto-login gagal: device mismatch untuk {stored_username}")
                ctypes.windll.user32.MessageBoxW(0, "Username telah terpakai pada device lain", "Login Error", 0)
                sys.exit(0)
            elif status == "invalid_credentials":
                print(f"[WARNING] Kredensial tersimpan tidak valid untuk {stored_username}")
                # Hapus kredensial yang tidak valid dan minta login ulang
                stored_username, stored_password = None, None
        
        # Jika perlu login
        while not login_successful:
            username, password = login_menu()
            if not username or not password:
                print("Login dibatalkan")
                sys.exit(0)
                
            status = check_credentials(username, password, device_id)
            print(f"[DEBUG] Manual-login attempt untuk {username}: {status}")
            
            if status == "success":
                save_login_info(username, password)
                login_successful = True
                print(f"[INFO] Login berhasil untuk user: {username}")
            elif status == "device_mismatch":
                ctypes.windll.user32.MessageBoxW(0, "Username telah terpakai pada device lain", "Login Error", 0)
                sys.exit(0)
            elif status == "invalid_credentials":
                retry = ctypes.windll.user32.MessageBoxW(0, "Username atau password salah.\nCoba lagi?", "Login Error", 0x00000004)  # MB_YESNO
                if retry != 6:  # IDYES = 6
                    print("Login dibatalkan")
                    sys.exit(0)
            else:
                ctypes.windll.user32.MessageBoxW(0, "Terjadi kesalahan saat memeriksa kredensial.", "Login Error", 0)
                sys.exit(0)
        
        if login_successful:
            print(f"[SYSTEM] User {username} berhasil login")
            print("[INFO] Membuka TA Daily Process Tool GUI...")
            
            # Log latest login
            try:
                log_latest_login(username)
            except Exception as e:
                print(f"[WARNING] Gagal log login: {e}")
            
            # Jalankan aplikasi GUI setelah login berhasil
            root = tk.Tk()
            
            # Set window icon if available
            if os.path.exists(icon_hd):
                try:
                    root.iconbitmap(icon_hd)
                except Exception as e:
                    print(f"[WARNING] Gagal set icon: {e}")
            else:
                print(f"[WARNING] Icon file tidak ditemukan: {icon_hd}")
            
            app = TAProcessorGUI(root, username)
            
            # Handle window closing
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            
            root.mainloop()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
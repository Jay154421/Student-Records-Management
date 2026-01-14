
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import hashlib
import os
import sys
import json
import shutil
from datetime import datetime
from PIL import Image, ImageTk
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import tempfile

class ModernLoginSystem:
    def __init__(self):
        # Colors for modern theme
        self.colors = {
            'primary': '#4361ee',
            'secondary': '#3a0ca3',
            'accent': '#7209b7',
            'light': '#f8f9fa',
            'dark': '#212529',
            'success': '#4cc9f0',
            'danger': '#f72585',
            'warning': '#f8961e',
            'info': '#4895ef',
            'background': '#ffffff',
            'card_bg': '#f8f9fa',
            'text': '#2b2d42',
            'transparent': '#ffffff00'
        }
        
        # Create attachments directory if it doesn't exist
        self.attachments_dir = 'student_attachments'
        if not os.path.exists(self.attachments_dir):
            os.makedirs(self.attachments_dir)
        
        self.root = tk.Tk()
        self.root.title("Student Records Management System")
        self.root.geometry("1200x700")
        self.root.configure(bg=self.colors['background'])
        
        # Current user information
        self.current_user = None
        self.current_role = None
        
        # Set window icon (optional)
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Initialize database
        self.init_database()
        
        # Create login screen
        self.create_login_screen()
        
        # Center the window
        self.center_window()
        
        # Run the application
        self.root.mainloop()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def init_database(self):
        """Initialize database and create default admin"""
        self.conn = sqlite3.connect('modern_users.db')
        self.cursor = self.conn.cursor()
        
        # Create users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                email TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Create credentials table (now for student records)
        # UPDATED: Added all required columns including attachments and graduate-specific fields
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                username TEXT NOT NULL,  -- Will store ID Number
                password TEXT NOT NULL,  -- Will store First Name
                attachments TEXT,        -- Will store JSON list of attachment paths
                category TEXT DEFAULT 'Student',
                first_name TEXT,
                middle_name TEXT,
                last_name TEXT,
                owner_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                -- Graduate-specific fields
                last_school_year TEXT,
                contact_number TEXT,
                so_number TEXT,
                date_issued TEXT,
                series_year TEXT,
                FOREIGN KEY (owner_id) REFERENCES users (id)
            )
        ''')
        
        # Check if attachments column exists, if not add it
        try:
            self.cursor.execute("SELECT attachments FROM credentials LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            self.cursor.execute('ALTER TABLE credentials ADD COLUMN attachments TEXT')
            print("✓ Added 'attachments' column to credentials table")
        
        # Check for other missing columns and add them if needed
        columns_to_check = [
            'first_name', 'middle_name', 'last_name',
            'last_school_year', 'contact_number', 'so_number', 
            'date_issued', 'series_year'
        ]
        for column in columns_to_check:
            try:
                self.cursor.execute(f"SELECT {column} FROM credentials LIMIT 1")
            except sqlite3.OperationalError:
                self.cursor.execute(f'ALTER TABLE credentials ADD COLUMN {column} TEXT')
                print(f"✓ Added '{column}' column to credentials table")
        
        # Create default admin user if not exists
        default_admin_username = "admin"
        default_admin_password = self.hash_password("Admin@123")
        
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (default_admin_username,))
        admin_exists = self.cursor.fetchone()
        
        if not admin_exists:
            self.cursor.execute('''
                INSERT INTO users (username, password, role, email, full_name) 
                VALUES (?, ?, ?, ?, ?)
            ''', (default_admin_username, default_admin_password, 'admin', 
                  'admin@system.com', 'System Administrator'))
            
            # Add some sample student records for admin
            admin_id = self.cursor.lastrowid
            sample_students = [
                ('John Smith (S001)', 'S001', 'John', '[]', 'Undergraduate', 'John', '', 'Smith', admin_id, '', '', '', '', ''),
                ('Jane Doe (S002)', 'S002', 'Jane', '[]', 'Undergraduate', 'Jane', '', 'Doe', admin_id, '', '', '', '', ''),
                ('Robert Johnson (S003)', 'S003', 'Robert', '[]', 'Graduate', 'Robert', 'James', 'Johnson', admin_id, '', '', '', '', ''),
            ]
            
            for student in sample_students:
                self.cursor.execute('''
                    INSERT INTO credentials (title, username, password, attachments, category, first_name, middle_name, last_name, owner_id, last_school_year, contact_number, so_number, date_issued, series_year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', student)
            
            self.conn.commit()
            print("✓ Default admin created: username='admin', password='Admin@123'")
        
        self.conn.commit()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_login_screen(self):
        """Create modern login screen"""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel with gradient
        left_panel = tk.Frame(main_container, bg=self.colors['primary'], width=500)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_panel.pack_propagate(False)
        
        # Content on left panel
        content_frame = tk.Frame(left_panel, bg=self.colors['primary'])
        content_frame.place(relx=0.5, rely=0.5, anchor='center')

        # App logo/name
        app_name = tk.Label(
            content_frame, 
            text="ArchiveX", 
            font=('Arial', 48, 'bold'),
            fg='white',
            bg=self.colors['primary']
        )
        app_name.pack(pady=(0, 10))
        
        app_tagline = tk.Label(
            content_frame,
            text="ST. PETERS COLLEGE",
            font=('Arial', 14),
            fg='white',
            bg=self.colors['primary']
        )
        app_tagline.pack()
        
        # Right panel - Login form
        right_panel = tk.Frame(main_container, bg=self.colors['background'], width=600)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        right_panel.pack_propagate(False)
        
        # Login form container
        form_container = tk.Frame(right_panel, bg=self.colors['background'], padx=80, pady=100)
        form_container.pack(expand=True, fill=tk.BOTH)
        
        # Welcome back text
        welcome_label = tk.Label(
            form_container,
            text="Welcome Back",
            font=('Arial', 32, 'bold'),
            fg=self.colors['dark'],
            bg=self.colors['background']
        )
        welcome_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(
            form_container,
            text="Sign in to access your account",
            font=('Arial', 14),
            fg=self.colors['text'],
            bg=self.colors['background']
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Username field
        tk.Label(
            form_container,
            text="USERNAME",
            font=('Arial', 10, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(anchor='w', pady=(10, 5))
        
        username_frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=45)
        username_frame.pack(fill=tk.X, pady=(0, 20))
        username_frame.pack_propagate(False)
        
        # Username icon
        icon_label = tk.Label(
            username_frame,
            text="👤",
            font=('Arial', 14),
            bg=self.colors['card_bg']
        )
        icon_label.pack(side=tk.LEFT, padx=15)
        
        self.username_entry = tk.Entry(
            username_frame,
            font=('Arial', 12),
            bd=0,
            bg=self.colors['card_bg'],
            fg=self.colors['dark']
        )
        self.username_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        self.username_entry.insert(0, "admin")
        self.username_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(username_frame))
        self.username_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(username_frame))
        
        # Password field
        tk.Label(
            form_container,
            text="PASSWORD",
            font=('Arial', 10, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(anchor='w', pady=(10, 5))
        
        password_frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=45)
        password_frame.pack(fill=tk.X, pady=(0, 20))
        password_frame.pack_propagate(False)
        
        # Password icon
        icon_label = tk.Label(
            password_frame,
            text="🔒",
            font=('Arial', 14),
            bg=self.colors['card_bg']
        )
        icon_label.pack(side=tk.LEFT, padx=15)
        
        self.password_entry = tk.Entry(
            password_frame,
            font=('Arial', 12),
            bd=0,
            bg=self.colors['card_bg'],
            fg=self.colors['dark'],
            show="•"
        )
        self.password_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        self.password_entry.insert(0, "Admin@123")
        self.password_entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(password_frame))
        self.password_entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(password_frame))
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar()
        show_password_check = tk.Checkbutton(
            form_container,
            text="Show Password",
            variable=self.show_password_var,
            command=self.toggle_password_visibility,
            font=('Arial', 10),
            fg=self.colors['text'],
            bg=self.colors['background'],
            selectcolor=self.colors['background'],
            activebackground=self.colors['background']
        )
        show_password_check.pack(anchor='w', pady=(0, 30))
        
        # Login button
        self.login_button = tk.Button(
            form_container,
            text="SIGN IN",
            command=self.login,
            font=('Arial', 12, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            bd=0,
            padx=40,
            pady=12,
            cursor='hand2'
        )
        self.login_button.pack(pady=(10, 20))
        self.login_button.bind('<Enter>', lambda e: self.on_button_hover(e, self.colors['secondary']))
        self.login_button.bind('<Leave>', lambda e: self.on_button_leave(e, self.colors['primary']))
        
        # Forgot password
        forgot_link = tk.Label(
            form_container,
            text="Forgot Password?",
            font=('Arial', 10, 'bold'),
            fg=self.colors['info'],
            bg=self.colors['background'],
            cursor='hand2'
        )
        forgot_link.pack(pady=20)
        forgot_link.bind('<Button-1>', lambda e: self.forgot_password())
        forgot_link.bind('<Enter>', lambda e: forgot_link.config(fg=self.colors['primary']))
        forgot_link.bind('<Leave>', lambda e: forgot_link.config(fg=self.colors['info']))
        
        # Bind Enter key
        self.root.bind('<Return>', lambda event: self.login())
    
    def on_entry_focus_in(self, frame):
        """Highlight entry field on focus"""
        frame.config(bg=self.colors['primary'])
        for widget in frame.winfo_children():
            widget.config(bg=self.colors['primary'])
    
    def on_entry_focus_out(self, frame):
        """Remove highlight from entry field"""
        frame.config(bg=self.colors['card_bg'])
        for widget in frame.winfo_children():
            widget.config(bg=self.colors['card_bg'])
    
    def on_button_hover(self, event, color):
        """Button hover effect"""
        event.widget.config(bg=color)
    
    def on_button_leave(self, event, color):
        """Button leave effect"""
        event.widget.config(bg=color)
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="•")
    
    def login(self):
        """Handle login process"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        # Animate login button
        self.login_button.config(text="SIGNING IN...", state='disabled')
        self.root.update()
        
        # Hash the entered password
        hashed_password = self.hash_password(password)
        
        # Check credentials
        self.cursor.execute('''
            SELECT * FROM users 
            WHERE username = ? AND password = ?
        ''', (username, hashed_password))
        
        user = self.cursor.fetchone()
        
        if user:
            # Update last login
            self.cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP 
                WHERE username = ?
            ''', (username,))
            self.conn.commit()
            
            user_id, username, _, role, email, full_name, created_at, last_login = user
            self.current_user = user_id
            self.current_role = role
            self.show_dashboard(full_name, role, email)
        else:
            self.login_button.config(text="SIGN IN", state='normal')
            messagebox.showerror("Access Denied", "Invalid username or password")
    
    def show_dashboard(self, full_name, role, email):
        """Show modern dashboard after successful login"""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Dashboard container
        self.dashboard_frame = tk.Frame(self.root, bg=self.colors['background'])
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top navbar
        navbar = tk.Frame(self.dashboard_frame, bg='white', height=70)
        navbar.pack(fill=tk.X)
        navbar.pack_propagate(False)
        
        # App logo
        tk.Label(
            navbar,
            text="Student Records System",
            font=('Arial', 24, 'bold'),
            fg=self.colors['primary'],
            bg='white'
        ).pack(side=tk.LEFT, padx=30)
        
        # User info on right
        user_info_frame = tk.Frame(navbar, bg='white')
        user_info_frame.pack(side=tk.RIGHT, padx=30)
        
        tk.Label(
            user_info_frame,
            text=full_name,
            font=('Arial', 12, 'bold'),
            fg=self.colors['dark'],
            bg='white'
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        # User avatar
        avatar_label = tk.Label(
            user_info_frame,
            text="👤",
            font=('Arial', 20),
            bg=self.colors['primary'],
            fg='white',
            width=3,
            height=1
        )
        avatar_label.pack(side=tk.RIGHT)
        
        # Sidebar
        sidebar = tk.Frame(self.dashboard_frame, bg='white', width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Sidebar menu items
        self.menu_items = [
            ("📊", "Dashboard", self.show_main_dashboard),
            ("📋", "Student Records", self.show_credentials),  
            ("⚙️", "Settings", self.show_settings),
            ("🆘", "Help & Support", self.show_help)
        ]
        
        tk.Frame(sidebar, bg=self.colors['light'], height=2).pack(fill=tk.X, pady=(20, 10))
        
        for icon, text, command in self.menu_items:
            item_frame = tk.Frame(sidebar, bg='white', height=50)
            item_frame.pack(fill=tk.X, padx=20, pady=5)
            item_frame.pack_propagate(False)
            
            tk.Label(
                item_frame,
                text=icon,
                font=('Arial', 14),
                bg='white',
                fg=self.colors['text']
            ).pack(side=tk.LEFT, padx=(10, 15))
            
            tk.Label(
                item_frame,
                text=text,
                font=('Arial', 12),
                bg='white',
                fg=self.colors['text']
            ).pack(side=tk.LEFT)
            
            # Make the entire frame clickable
            item_frame.bind('<Button-1>', lambda e, cmd=command: cmd())
            for child in item_frame.winfo_children():
                child.bind('<Button-1>', lambda e, cmd=command: cmd())
            
            # Hover effect
            item_frame.bind('<Enter>', lambda e, f=item_frame: f.config(bg=self.colors['light']))
            item_frame.bind('<Leave>', lambda e, f=item_frame: f.config(bg='white'))
            
            for child in item_frame.winfo_children():
                child.bind('<Enter>', lambda e, f=item_frame: f.config(bg=self.colors['light']))
                child.bind('<Leave>', lambda e, f=item_frame: f.config(bg='white'))
        
        # Main content area
        self.main_content = tk.Frame(self.dashboard_frame, bg=self.colors['light'])
        self.main_content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Show main dashboard by default
        self.show_main_dashboard(full_name, role, email)
    
    def show_main_dashboard(self, full_name=None, role=None, email=None):
        """Show main dashboard content"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        if not full_name:
            # Get user info from database
            self.cursor.execute('SELECT full_name, role, email FROM users WHERE id = ?', (self.current_user,))
            user_info = self.cursor.fetchone()
            if user_info:
                full_name, role, email = user_info
        
        # Welcome message
        welcome_card = tk.Frame(self.main_content, bg='white')
        welcome_card.pack(fill=tk.X, padx=30, pady=30)
        
        tk.Label(
            welcome_card,
            text=f"Welcome back, {full_name}! 👋",
            font=('Arial', 24, 'bold'),
            fg=self.colors['dark'],
            bg='white'
        ).pack(anchor='w', padx=30, pady=(30, 10))
        
        tk.Label(
            welcome_card,
            text=f"Role: {role.upper()} | Email: {email}",
            font=('Arial', 12),
            fg=self.colors['text'],
            bg='white'
        ).pack(anchor='w', padx=30, pady=(0, 30))
        
        # Statistics cards
        stats_frame = tk.Frame(self.main_content, bg=self.colors['light'])
        stats_frame.pack(fill=tk.X, padx=30, pady=(0, 30))
        
        # Get user's student records count
        self.cursor.execute('SELECT COUNT(*) FROM credentials WHERE owner_id = ?', (self.current_user,))
        cred_count = self.cursor.fetchone()[0]
        
        stats_data = [
            ("Student Records", str(cred_count), self.colors['primary'], "👨‍🎓"),
            ("Active Sessions", "1", self.colors['success'], "👥"),
        ]
        
        for title, value, color, icon in stats_data:
            card = tk.Frame(stats_frame, bg='white', width=200, height=120)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
            card.pack_propagate(False)
            
            tk.Label(
                card,
                text=icon,
                font=('Arial', 24),
                bg='white',
                fg=color
            ).pack(anchor='w', padx=20, pady=(20, 5))
            
            tk.Label(
                card,
                text=value,
                font=('Arial', 28, 'bold'),
                bg='white',
                fg=self.colors['dark']
            ).pack(anchor='w', padx=20)
            
            tk.Label(
                card,
                text=title,
                font=('Arial', 10),
                bg='white',
                fg=self.colors['text']
            ).pack(anchor='w', padx=20, pady=(0, 20))
        
        # Logout button at bottom
        logout_btn = tk.Button(
            self.main_content,
            text="🚪 Logout",
            command=self.logout,
            font=('Arial', 10),
            bg=self.colors['danger'],
            fg='white',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        logout_btn.pack(side=tk.RIGHT, padx=30, pady=20)
        logout_btn.bind('<Enter>', lambda e: logout_btn.config(bg='#d90429'))
        logout_btn.bind('<Leave>', lambda e: logout_btn.config(bg=self.colors['danger']))
    
    def show_credentials(self):
        """Show student records management screen"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # Create a main container with scrollbar
        main_container = tk.Frame(self.main_content, bg=self.colors['light'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create a canvas for scrolling
        canvas = tk.Canvas(main_container, bg=self.colors['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['light'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Student records header
        header_frame = tk.Frame(scrollable_frame, bg=self.colors['light'])
        header_frame.pack(fill=tk.X, padx=30, pady=(30, 20))
        
        tk.Label(
            header_frame,
            text="👨‍🎓 Student Records Management",
            font=('Arial', 24, 'bold'),
            bg=self.colors['light'],
            fg=self.colors['dark']
        ).pack(side=tk.LEFT)
        
        # Add New button
        add_btn = tk.Button(
            header_frame,
            text="➕ Add New Student",
            command=self.add_new_credential,
            font=('Arial', 11, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        add_btn.pack(side=tk.RIGHT)
        add_btn.bind('<Enter>', lambda e: add_btn.config(bg=self.colors['secondary']))
        add_btn.bind('<Leave>', lambda e: add_btn.config(bg=self.colors['primary']))
        
        # Search and filter frame
        filter_frame = tk.Frame(scrollable_frame, bg=self.colors['light'])
        filter_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        # Search box
        search_frame = tk.Frame(filter_frame, bg='white', height=40)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_frame.pack_propagate(False)
        
        tk.Label(
            search_frame,
            text="🔍",
            font=('Arial', 14),
            bg='white'
        ).pack(side=tk.LEFT, padx=15)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Arial', 11),
            bd=0,
            bg='white',
            fg=self.colors['dark'],
            relief='flat'
        )
        search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        search_entry.insert(0, "Search student records...")
        search_entry.bind('<FocusIn>', lambda e: search_entry.delete(0, tk.END) if search_entry.get() == "Search student records..." else None)
        search_entry.bind('<FocusOut>', lambda e: search_entry.insert(0, "Search student records...") if not search_entry.get() else None)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_credentials())
        
        # Category filter
        categories = ['All', 'Graduate', 'Undergraduate']
        self.category_var = tk.StringVar(value='All')
        
        category_label = tk.Label(
            filter_frame,
            text="Category:",
            font=('Arial', 11),
            bg=self.colors['light'],
            fg=self.colors['dark']
        )
        category_label.pack(side=tk.LEFT, padx=(30, 10))
        
        category_menu = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=categories,
            font=('Arial', 10),
            state='readonly',
            width=15
        )
        category_menu.pack(side=tk.LEFT)
        category_menu.bind('<<ComboboxSelected>>', lambda e: self.filter_credentials())
        
        # Student records list frame
        list_frame = tk.Frame(scrollable_frame, bg=self.colors['light'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))
        list_frame.pack_propagate(True)
        
        # Create treeview for student records
        columns = ('ID', 'ID Number', 'First Name', 'Last Name', 'Category', 'Attachments', 'Last Updated')
        self.cred_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            selectmode='browse',
            height=15
        )
        
        # Define column headings
        self.cred_tree.heading('ID', text='NO.', anchor='w')
        self.cred_tree.heading('ID Number', text='ID Number', anchor='w')
        self.cred_tree.heading('First Name', text='First Name', anchor='w')
        self.cred_tree.heading('Last Name', text='Last Name', anchor='w')
        self.cred_tree.heading('Category', text='Category', anchor='w')
        self.cred_tree.heading('Attachments', text='Attachments', anchor='w')
        self.cred_tree.heading('Last Updated', text='Last Updated', anchor='w')
        
        # Define column widths
        self.cred_tree.column('ID', width=50)
        self.cred_tree.column('ID Number', width=100)
        self.cred_tree.column('First Name', width=120)
        self.cred_tree.column('Last Name', width=120)
        self.cred_tree.column('Category', width=100)
        self.cred_tree.column('Attachments', width=150)
        self.cred_tree.column('Last Updated', width=150)
        
        # Add scrollbar to treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.cred_tree.yview)
        self.cred_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.cred_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons frame
        action_frame = tk.Frame(scrollable_frame, bg=self.colors['light'])
        action_frame.pack(fill=tk.X, padx=30, pady=(0, 30))
        
        action_buttons = [
            ("👁️ View", self.view_credential),
            ("✏️ Edit", self.edit_credential),
            ("🗑️ Delete", self.delete_credential),
            ("📁 Open Attachments", self.open_attachments),
            ("📤 Export", self.export_options)  # Changed to show export options
        ]
        
        for btn_text, command in action_buttons:
            btn = tk.Button(
                action_frame,
                text=btn_text,
                command=command,
                font=('Arial', 10),
                bg='white',
                fg=self.colors['dark'],
                bd=1,
                padx=15,
                pady=6,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=(0, 10))
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.colors['light']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg='white'))
        
        # Add back to dashboard button
        back_btn = tk.Button(
            scrollable_frame,
            text="⬅ Back to Dashboard",
            command=self.show_main_dashboard,
            font=('Arial', 10),
            bg=self.colors['info'],
            fg='white',
            bd=0,
            padx=15,
            pady=6,
            cursor='hand2'
        )
        back_btn.pack(side=tk.LEFT, padx=30, pady=(0, 30))
        back_btn.bind('<Enter>', lambda e: back_btn.config(bg=self.colors['primary']))
        back_btn.bind('<Leave>', lambda e: back_btn.config(bg=self.colors['info']))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Load student records
        self.load_credentials()
        
        # Bind double click to view record
        self.cred_tree.bind('<Double-1>', lambda e: self.view_credential())
    
    def load_credentials(self, search_text="", category="All"):
        """Load student records from database"""
        # Clear existing items
        for item in self.cred_tree.get_children():
            self.cred_tree.delete(item)
        
        # Build query
        query = '''
            SELECT id, username, password, last_name, category, attachments, updated_at 
            FROM credentials 
            WHERE owner_id = ?
        '''
        params = [self.current_user]
        
        if search_text and search_text != "Search student records...":
            query += " AND (title LIKE ? OR username LIKE ? OR password LIKE ? OR last_name LIKE ? OR first_name LIKE ? OR middle_name LIKE ?)"
            search_pattern = f"%{search_text}%"
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern, 
                          search_pattern, search_pattern])
        
        if category != "All":
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY updated_at DESC"
        
        # Execute query
        self.cursor.execute(query, params)
        credentials = self.cursor.fetchall()
        
        # Add to treeview
        for cred in credentials:
            cred_id, id_number, first_name, last_name, category, attachments_json, updated_at = cred
            
            # Parse attachments JSON
            try:
                attachments = json.loads(attachments_json) if attachments_json else []
            except:
                attachments = []
            
            # Display attachment count
            if attachments:
                display_attachments = f"{len(attachments)} file(s)"
            else:
                display_attachments = "No attachments"
            
            self.cred_tree.insert('', 'end', values=(cred_id, id_number, first_name, last_name, category, display_attachments, updated_at))
    
    def filter_credentials(self):
        """Filter student records based on search and category"""
        search_text = self.search_var.get()
        category = self.category_var.get()
        self.load_credentials(search_text, category)
    
    def export_options(self):
        """Show export options dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Options")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f'400x300+{x}+{y}')
        
        tk.Label(
            dialog,
            text="📤 Export Options",
            font=('Arial', 20, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=(30, 20))
        
        # Export options
        options = [
            ("📋 Export All Records (PDF)", self.export_all_to_pdf),
            ("📄 Export Selected Record (PDF)", self.export_selected_to_pdf),
            ("📊 Export Statistics (PDF)", self.export_statistics_to_pdf),
            ("📁 Export with Images (PDF)", self.export_with_images_to_pdf)
        ]
        
        for btn_text, command in options:
            btn = tk.Button(
                dialog,
                text=btn_text,
                command=lambda cmd=command: self.execute_export(cmd, dialog),
                font=('Arial', 11),
                bg=self.colors['primary'],
                fg='white',
                bd=0,
                padx=20,
                pady=10,
                cursor='hand2',
                width=30
            )
            btn.pack(pady=5)
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.colors['secondary']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=self.colors['primary']))
        
        # Close button
        close_btn = tk.Button(
            dialog,
            text="Close",
            command=dialog.destroy,
            font=('Arial', 10),
            bg=self.colors['danger'],
            fg='white',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        close_btn.pack(pady=20)
        close_btn.bind('<Enter>', lambda e: close_btn.config(bg='#d90429'))
        close_btn.bind('<Leave>', lambda e: close_btn.config(bg=self.colors['danger']))
    
    def execute_export(self, export_function, dialog):
        """Execute export function and close dialog"""
        dialog.destroy()
        export_function()
    
    def export_all_to_pdf(self):
        """Export all student records to PDF"""
        try:
            # Get all student records
            self.cursor.execute('''
                SELECT id, username, password, last_name, category, first_name, middle_name, last_name, created_at, updated_at 
                FROM credentials 
                WHERE owner_id = ?
                ORDER BY last_name, first_name
            ''', (self.current_user,))
            
            students = self.cursor.fetchall()
            
            if not students:
                messagebox.showwarning("No Data", "No student records to export")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"student_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not file_path:
                return
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#4361ee'),
                spaceAfter=30
            )
            
            title = Paragraph("Student Records Report", title_style)
            elements.append(title)
            
            # Subtitle
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#666666'),
                spaceAfter=20
            )
            
            subtitle = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Total Records: {len(students)}", subtitle_style)
            elements.append(subtitle)
            
            elements.append(Spacer(1, 20))
            
            # Create table data
            table_data = [['ID', 'ID Number', 'Full Name', 'Category', 'Created', 'Updated']]
            
            for student in students:
                cred_id, id_number, first_name, last_name, category, fname, mname, lname, created_at, updated_at = student
                
                # Format name
                full_name = f"{first_name} {mname + ' ' if mname else ''}{last_name}".strip()
                
                # Format dates
                created_date = created_at[:10] if created_at else "N/A"
                updated_date = updated_at[:10] if updated_at else "N/A"
                
                table_data.append([str(cred_id), id_number, full_name, category, created_date, updated_date])
            
            # Create table
            table = Table(table_data, colWidths=[0.5*inch, 1*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 30))
            
            # Add summary
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#333333'),
                spaceAfter=10
            )
            
            # Count by category
            categories = {}
            for student in students:
                category = student[4]
                categories[category] = categories.get(category, 0) + 1
            
            summary_text = "Summary by Category:<br/>"
            for category, count in categories.items():
                summary_text += f"• {category}: {count} student(s)<br/>"
            
            summary = Paragraph(summary_text, summary_style)
            elements.append(summary)
            
            # Build PDF
            doc.build(elements)
            
            messagebox.showinfo("Success", f"PDF exported successfully!\nSaved to: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_selected_to_pdf(self):
        """Export selected student record to PDF"""
        selection = self.cred_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a student record to export")
            return
        
        item = self.cred_tree.item(selection[0])
        cred_id = item['values'][0]
        
        # Get student record details
        self.cursor.execute('''
            SELECT title, username, password, attachments, category, first_name, middle_name, last_name, created_at, updated_at, 
                   last_school_year, contact_number, so_number, date_issued, series_year
            FROM credentials 
            WHERE id = ? AND owner_id = ?
        ''', (cred_id, self.current_user))
        
        student = self.cursor.fetchone()
        
        if not student:
            messagebox.showerror("Error", "Student record not found")
            return
        
        title, id_number, first_name, attachments_json, category, fname, mname, lname, created_at, updated_at, last_school_year, contact_number, so_number, date_issued, series_year = student
        
        try:
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"student_{id_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
            
            if not file_path:
                return
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#4361ee'),
                spaceAfter=30
            )
            
            pdf_title = Paragraph(f"Student Record: {title}", title_style)
            elements.append(pdf_title)
            
            # Subtitle
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#666666'),
                spaceAfter=20
            )
            
            subtitle = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style)
            elements.append(subtitle)
            
            elements.append(Spacer(1, 30))
            
            # Student Information Table
            info_data = [
                ['Field', 'Value'],
                ['ID Number', id_number],
                ['First Name', first_name],
                ['Middle Name', mname if mname else 'N/A'],
                ['Last Name', lname],
                ['Category', category],
                ['Created Date', created_at[:10] if created_at else 'N/A'],
                ['Last Updated', updated_at[:10] if updated_at else 'N/A']
            ]
            
            # Add graduate-specific fields if category is Graduate
            if category == 'Graduate':
                info_data.extend([
                    ['Last School Year Attended', last_school_year if last_school_year else 'N/A'],
                    ['Contact Number', contact_number if contact_number else 'N/A'],
                    ['SO Number', so_number if so_number else 'N/A'],
                    ['Date Issued', date_issued if date_issued else 'N/A'],
                    ['Series of Year', series_year if series_year else 'N/A']
                ])
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(info_table)
            elements.append(Spacer(1, 30))
            
            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#999999'),
                alignment=1
            )
            
            footer = Paragraph(f"Confidential Student Record - St. Peter's College Student Records System", footer_style)
            elements.append(footer)
            
            # Build PDF
            doc.build(elements)
            
            messagebox.showinfo("Success", f"Student record exported successfully!\nSaved to: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_statistics_to_pdf(self):
        """Export system statistics to PDF"""
        try:
            # Get statistics
            self.cursor.execute('SELECT COUNT(*) FROM credentials WHERE owner_id = ?', (self.current_user,))
            total_students = self.cursor.fetchone()[0]
            
            self.cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM credentials 
                WHERE owner_id = ?
                GROUP BY category 
                ORDER BY count DESC
            ''', (self.current_user,))
            
            category_stats = self.cursor.fetchall()
            
            self.cursor.execute('''
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
                FROM credentials 
                WHERE owner_id = ?
                GROUP BY month
                ORDER BY month DESC
                LIMIT 6
            ''', (self.current_user,))
            
            monthly_stats = self.cursor.fetchall()
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"student_statistics_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
            
            if not file_path:
                return
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#4361ee'),
                spaceAfter=30
            )
            
            title = Paragraph("Student Records Statistics Report", title_style)
            elements.append(title)
            
            # Subtitle
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#666666'),
                spaceAfter=20
            )
            
            subtitle = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style)
            elements.append(subtitle)
            
            elements.append(Spacer(1, 30))
            
            # Summary Statistics
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#333333'),
                spaceAfter=15
            )
            
            summary = Paragraph(f"Total Students: {total_students}", summary_style)
            elements.append(summary)
            elements.append(Spacer(1, 20))
            
            # Category Distribution Table
            if category_stats:
                cat_title_style = ParagraphStyle(
                    'CategoryTitle',
                    parent=styles['Heading3'],
                    fontSize=14,
                    textColor=colors.HexColor('#555555'),
                    spaceAfter=10
                )
                
                cat_title = Paragraph("Distribution by Category:", cat_title_style)
                elements.append(cat_title)
                
                cat_data = [['Category', 'Number of Students', 'Percentage']]
                for category, count in category_stats:
                    percentage = (count / total_students * 100) if total_students > 0 else 0
                    cat_data.append([category, str(count), f"{percentage:.1f}%"])
                
                cat_table = Table(cat_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                cat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))
                
                elements.append(cat_table)
                elements.append(Spacer(1, 30))
            
            # Monthly Statistics
            if monthly_stats:
                month_title_style = ParagraphStyle(
                    'MonthTitle',
                    parent=styles['Heading3'],
                    fontSize=14,
                    textColor=colors.HexColor('#555555'),
                    spaceAfter=10
                )
                
                month_title = Paragraph("Monthly Registration (Last 6 Months):", month_title_style)
                elements.append(month_title)
                
                month_data = [['Month', 'New Registrations']]
                for month, count in monthly_stats:
                    month_data.append([month, str(count)])
                
                month_table = Table(month_data, colWidths=[2*inch, 2*inch])
                month_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7209b7')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))
                
                elements.append(month_table)
                elements.append(Spacer(1, 30))
            
            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#999999'),
                alignment=1
            )
            
            footer = Paragraph(f"St. Peter's College - Student Records Management System", footer_style)
            elements.append(footer)
            
            # Build PDF
            doc.build(elements)
            
            messagebox.showinfo("Success", f"Statistics exported successfully!\nSaved to: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
    
    def export_with_images_to_pdf(self):
        """Export student records with embedded images to PDF"""
        selection = self.cred_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a student record with images to export")
            return
        
        item = self.cred_tree.item(selection[0])
        cred_id = item['values'][0]
        
        # Get student record details with attachments
        self.cursor.execute('''
            SELECT title, username, password, attachments, category, first_name, middle_name, last_name, created_at, updated_at 
            FROM credentials 
            WHERE id = ? AND owner_id = ?
        ''', (cred_id, self.current_user))
        
        student = self.cursor.fetchone()
        
        if not student:
            messagebox.showerror("Error", "Student record not found")
            return
        
        title, id_number, first_name, attachments_json, category, fname, mname, lname, created_at, updated_at = student
        
        # Parse attachments
        try:
            attachments = json.loads(attachments_json) if attachments_json else []
        except:
            attachments = []
        
        if not attachments:
            messagebox.showwarning("No Images", "This student record has no attachments/images to export")
            return
        
        try:
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"student_with_images_{id_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
            
            if not file_path:
                return
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#4361ee'),
                spaceAfter=30
            )
            
            pdf_title = Paragraph(f"Student Record with Images: {title}", title_style)
            elements.append(pdf_title)
            
            # Subtitle
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#666666'),
                spaceAfter=20
            )
            
            subtitle = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Attachments: {len(attachments)}", subtitle_style)
            elements.append(subtitle)
            
            elements.append(Spacer(1, 30))
            
            # Student Information
            info_style = ParagraphStyle(
                'Info',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#333333'),
                spaceAfter=5
            )
            
            info_text = f"""
            <b>ID Number:</b> {id_number}<br/>
            <b>Full Name:</b> {first_name} {mname + ' ' if mname else ''}{lname}<br/>
            <b>Category:</b> {category}<br/>
            <b>Created:</b> {created_at[:10] if created_at else 'N/A'}<br/>
            <b>Last Updated:</b> {updated_at[:10] if updated_at else 'N/A'}<br/>
            """
            
            info_paragraph = Paragraph(info_text, info_style)
            elements.append(info_paragraph)
            elements.append(Spacer(1, 20))
            
            # Attachments section
            attachments_title_style = ParagraphStyle(
                'AttachmentsTitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#333333'),
                spaceAfter=20
            )
            
            attachments_title = Paragraph(f"Attachments ({len(attachments)}):", attachments_title_style)
            elements.append(attachments_title)
            
            # Process and add images
            image_count = 0
            for attachment_path in attachments:
                if os.path.exists(attachment_path) and attachment_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    try:
                        # Add image filename
                        filename_style = ParagraphStyle(
                            'Filename',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.HexColor('#666666'),
                            spaceAfter=5
                        )
                        
                        filename = os.path.basename(attachment_path)
                        filename_para = Paragraph(f"Image: {filename}", filename_style)
                        elements.append(filename_para)
                        
                        # Add the image
                        img = RLImage(attachment_path, width=4*inch, height=3*inch)
                        elements.append(img)
                        elements.append(Spacer(1, 20))
                        
                        image_count += 1
                        
                        # Add page break after every 2 images
                        if image_count % 2 == 0:
                            elements.append(Spacer(1, 50))
                            
                    except Exception as e:
                        print(f"Failed to add image {attachment_path}: {e}")
                        continue
            
            if image_count == 0:
                no_images_style = ParagraphStyle(
                    'NoImages',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.HexColor('#ff0000'),
                    spaceAfter=20
                )
                
                no_images = Paragraph("No valid images found in attachments.", no_images_style)
                elements.append(no_images)
            
            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#999999'),
                alignment=1
            )
            
            footer = Paragraph(f"Confidential Document - Contains {image_count} image(s)", footer_style)
            elements.append(footer)
            
            # Build PDF
            doc.build(elements)
            
            messagebox.showinfo("Success", f"Student record with images exported successfully!\nSaved to: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF with images: {str(e)}")
    
    def add_new_credential(self):
        """Open dialog to add new student record"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Student Record")
        dialog.geometry("500x750")  # Increased height for graduate fields
        dialog.configure(bg=self.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f'500x750+{x}+{y}')
        
        # Create a scrollable frame for the dialog
        canvas = tk.Canvas(dialog, bg=self.colors['background'])
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['background'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        def center_scrollable_content(event=None):
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(window_id, width=canvas_width)
            canvas.coords(window_id, canvas_width // 2, 0)

        canvas.bind("<Configure>", center_scrollable_content)
        
        # Title - CENTERED
        tk.Label(
            scrollable_frame,
            text="➕ Add New Student Record",
            font=('Arial', 20, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=(30, 20), anchor='center', expand=True, fill='x')
        
        # Form fields container
        form_container = tk.Frame(scrollable_frame, bg=self.colors['background'])
        form_container.pack(fill=tk.BOTH, expand=True, padx=50)
        
        # Form fields
        fields = [
            ("ID Number", "Enter student ID number"),
            ("First Name", "Enter first name"),
            ("Middle Name", "Enter middle name (optional)"),
            ("Last Name", "Enter last name"),
        ]
        
        entries = {}
        
        for i, (label_text, placeholder) in enumerate(fields):
            tk.Label(
                form_container,
                text=label_text,
                font=('Arial', 10, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['background']
            ).pack(anchor='w', pady=(10, 5))
            
            frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=40)
            frame.pack(fill=tk.X, pady=(0, 10))
            frame.pack_propagate(False)
            
            entry = tk.Entry(frame, font=('Arial', 11), bd=0, bg=self.colors['card_bg'])
            entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
            entry.insert(0, placeholder)
            entry.bind('<FocusIn>', lambda e, w=entry, p=placeholder: w.delete(0, tk.END) if w.get() == p else None)
            entry.bind('<FocusOut>', lambda e, w=entry, p=placeholder: w.insert(0, p) if not w.get() else None)
            
            entries[label_text] = entry
        
        # Category field
        tk.Label(
            form_container,
            text="Category",
            font=('Arial', 10, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(anchor='w', pady=(10, 5))
        
        category_frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=40)
        category_frame.pack(fill=tk.X, pady=(0, 10))
        category_frame.pack_propagate(False)
        
        category_var = tk.StringVar(value="Undergraduate")
        
        def on_category_change(*args):
            """Show/hide graduate fields based on category selection"""
            category = category_var.get()
            if category == "Graduate":
                for field_name, entry in graduate_entries.items():
                    entry['label'].pack(anchor='w', pady=(10, 5))
                    entry['frame'].pack(fill=tk.X, pady=(0, 10))
            else:
                for field_name, entry in graduate_entries.items():
                    entry['label'].pack_forget()
                    entry['frame'].pack_forget()
            
            # Update scrollable area
            scrollable_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        category_var.trace_add('write', on_category_change)
        
        category_menu = ttk.Combobox(
            category_frame,
            textvariable=category_var,
            values=['Graduate', 'Undergraduate'],
            font=('Arial', 11),
            state='readonly'
        )
        category_menu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
        
        entries['Category'] = category_var
        
        # Graduate-specific fields (initially hidden)
        graduate_fields = [
            ("Last School Year Attended", "Enter last school year attended"),
            ("Contact Number", "Enter contact number"),
            ("SO Number", "Enter SO number"),
            ("Date Issued", "Enter date issued (YYYY-MM-DD)"),
            ("Series of Year", "Enter series of year")
        ]
        
        graduate_entries = {}

        for label_text, placeholder in graduate_fields:
            # ✅ Label (same style)
            label = tk.Label(
                form_container,
                text=label_text,
                font=('Arial', 10, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['background']
            )

            # ✅ Frame (same as First Name)
            frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=40)
            frame.pack_propagate(False)

            # ✅ Entry (same padding)
            entry = tk.Entry(frame, font=('Arial', 11), bd=0, bg=self.colors['card_bg'])
            entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
            entry.insert(0, placeholder)

            entry.bind('<FocusIn>', lambda e, w=entry, p=placeholder: w.delete(0, tk.END) if w.get() == p else None)
            entry.bind('<FocusOut>', lambda e, w=entry, p=placeholder: w.insert(0, p) if not w.get() else None)

            graduate_entries[label_text] = {
                "label": label,
                "frame": frame,
                "widget": entry
            }

        
        # Attachments section
        tk.Label(
            form_container,
            text="Attachments",
            font=('Arial', 10, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(anchor='w', pady=(10, 5))
        
        attachments_frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=150)
        attachments_frame.pack(fill=tk.X, pady=(0, 10))
        attachments_frame.pack_propagate(False)
        
        # Listbox for attachments
        attachments_listbox_frame = tk.Frame(attachments_frame, bg=self.colors['card_bg'])
        attachments_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Scrollbar for listbox
        listbox_scrollbar = ttk.Scrollbar(attachments_listbox_frame)
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        attachments_listbox = tk.Listbox(
            attachments_listbox_frame,
            yscrollcommand=listbox_scrollbar.set,
            font=('Arial', 10),
            bg='white',
            height=4
        )
        attachments_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        listbox_scrollbar.config(command=attachments_listbox.yview)
        
        # Buttons for attachments
        attachments_buttons_frame = tk.Frame(attachments_frame, bg=self.colors['card_bg'])
        attachments_buttons_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        selected_files = []  # Store file paths
        
        def add_attachments():
            filetypes = [
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PDF files", "*.pdf"),
                ("Document files", "*.doc *.docx *.txt"),
                ("All files", "*.*")
            ]
            files = filedialog.askopenfilenames(
                title="Select attachments",
                filetypes=filetypes
            )
            if files:
                for file in files:
                    if file not in selected_files:
                        selected_files.append(file)
                        attachments_listbox.insert(tk.END, os.path.basename(file))
        
        def remove_selected_attachment():
            selection = attachments_listbox.curselection()
            if selection:
                index = selection[0]
                selected_files.pop(index)
                attachments_listbox.delete(index)
        
        add_btn = tk.Button(
            attachments_buttons_frame,
            text="➕ Add Files",
            command=add_attachments,
            font=('Arial', 9),
            bg=self.colors['info'],
            fg='white',
            bd=0,
            padx=10,
            pady=5,
            cursor='hand2'
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
        add_btn.bind('<Enter>', lambda e: add_btn.config(bg=self.colors['primary']))
        add_btn.bind('<Leave>', lambda e: add_btn.config(bg=self.colors['info']))
        
        remove_btn = tk.Button(
            attachments_buttons_frame,
            text="🗑️ Remove Selected",
            command=remove_selected_attachment,
            font=('Arial', 9),
            bg=self.colors['danger'],
            fg='white',
            bd=0,
            padx=10,
            pady=5,
            cursor='hand2'
        )
        remove_btn.pack(side=tk.LEFT)
        remove_btn.bind('<Enter>', lambda e: remove_btn.config(bg='#d90429'))
        remove_btn.bind('<Leave>', lambda e: remove_btn.config(bg=self.colors['danger']))
        
        def save_credential():
            """Save new student record to database"""
            try:
                # Get values
                id_number = entries['ID Number'].get() if hasattr(entries['ID Number'], 'get') else entries['ID Number']
                first_name = entries['First Name'].get() if hasattr(entries['First Name'], 'get') else entries['First Name']
                middle_name = entries['Middle Name'].get() if hasattr(entries['Middle Name'], 'get') else entries['Middle Name']
                last_name = entries['Last Name'].get() if hasattr(entries['Last Name'], 'get') else entries['Last Name']
                category = entries['Category'].get() if hasattr(entries['Category'], 'get') else entries['Category']
                
                # Validate required fields
                if not id_number or id_number == "Enter student ID number":
                    messagebox.showerror("Error", "ID Number is required")
                    return
                
                if not first_name or first_name == "Enter first name":
                    messagebox.showerror("Error", "First Name is required")
                    return
                
                if not last_name or last_name == "Enter last name":
                    messagebox.showerror("Error", "Last Name is required")
                    return
                
                # Clean up optional fields
                if middle_name == "Enter middle name (optional)":
                    middle_name = ""
                
                # Get graduate-specific fields if category is Graduate
                last_school_year = ""
                contact_number = ""
                so_number = ""
                date_issued = ""
                series_year = ""
                
                if category == "Graduate":
                    last_school_year = graduate_entries["Last School Year Attended"]['widget'].get()
                    if last_school_year == "Enter last school year attended":
                        last_school_year = ""
                    
                    contact_number = graduate_entries["Contact Number"]['widget'].get()
                    if contact_number == "Enter contact number":
                        contact_number = ""
                    
                    so_number = graduate_entries["SO Number"]['widget'].get()
                    if so_number == "Enter SO number":
                        so_number = ""
                    
                    date_issued = graduate_entries["Date Issued"]['widget'].get()
                    if date_issued == "Enter date issued (YYYY-MM-DD)":
                        date_issued = ""
                    
                    series_year = graduate_entries["Series of Year"]['widget'].get()
                    if series_year == "Enter series of year":
                        series_year = ""
                
                # Create title from name
                title = f"{first_name} {last_name} ({id_number})"
                
                # Handle attachments - copy files to attachments directory
                saved_attachments = []
                if selected_files:
                    # Create student-specific directory
                    student_dir = os.path.join(self.attachments_dir, f"student_{id_number}")
                    if not os.path.exists(student_dir):
                        os.makedirs(student_dir)
                    
                    for file_path in selected_files:
                        if os.path.exists(file_path):
                            # Generate unique filename
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{timestamp}_{os.path.basename(file_path)}"
                            dest_path = os.path.join(student_dir, filename)
                            
                            # Copy file to attachments directory
                            shutil.copy2(file_path, dest_path)
                            saved_attachments.append(dest_path)
                
                # Insert into database
                self.cursor.execute('''
                    INSERT INTO credentials (title, username, password, attachments, category, first_name, middle_name, last_name, owner_id, last_school_year, contact_number, so_number, date_issued, series_year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, id_number, first_name, json.dumps(saved_attachments), category, first_name, middle_name, last_name, self.current_user, last_school_year, contact_number, so_number, date_issued, series_year))
                self.conn.commit()
                
                messagebox.showinfo("Success", f"Student record saved successfully!\n{len(saved_attachments)} attachment(s) added.")
                dialog.destroy()
                self.show_credentials()  # Refresh the student records list
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save student record: {str(e)}")
        
        # Button container
        button_container = tk.Frame(scrollable_frame, bg=self.colors['background'])
        button_container.pack(fill=tk.X, pady=30)
        
        # Save button
        save_btn = tk.Button(
            button_container,
            text="💾 Save Student Record",
            command=save_credential,
            font=('Arial', 12, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        save_btn.pack(pady=10)
        save_btn.bind('<Enter>', lambda e: save_btn.config(bg=self.colors['secondary']))
        save_btn.bind('<Leave>', lambda e: save_btn.config(bg=self.colors['primary']))
        
        # Cancel button
        cancel_btn = tk.Button(
            button_container,
            text="Cancel",
            command=dialog.destroy,
            font=('Arial', 10),
            bg=self.colors['danger'],
            fg='white',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        cancel_btn.pack(pady=5)
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.config(bg='#d90429'))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.config(bg=self.colors['danger']))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def edit_credential(self):
        """Edit selected student record"""
        selection = self.cred_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a student record to edit")
            return
        
        item = self.cred_tree.item(selection[0])
        cred_id = item['values'][0]
        
        # Get current student record details
        self.cursor.execute('SELECT * FROM credentials WHERE id = ? AND owner_id = ?', 
                          (cred_id, self.current_user))
        cred = self.cursor.fetchone()
        
        if not cred:
            messagebox.showerror("Error", "Student record not found")
            return
        
        # Unpack the record
        (cred_id_db, title, id_number, first_name, attachments_json, category, 
         fname, mname, lname, owner_id, created_at, updated_at, last_school_year, 
         contact_number, so_number, date_issued, series_year) = cred
        
        # Parse attachments
        try:
            attachments = json.loads(attachments_json) if attachments_json else []
        except:
            attachments = []
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Student Record: {title}")
        dialog.geometry("500x750")
        dialog.configure(bg=self.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f'500x750+{x}+{y}')
        
        # Create a scrollable frame for the dialog
        canvas = tk.Canvas(dialog, bg=self.colors['background'])
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['background'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        def center_scrollable_content(event=None):
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(window_id, width=canvas_width)
            canvas.coords(window_id, canvas_width // 2, 0)

        canvas.bind("<Configure>", center_scrollable_content)
        
        # Title - CENTERED
        tk.Label(
            scrollable_frame,
            text="✏️ Edit Student Record",
            font=('Arial', 20, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=(30, 20), anchor='center', expand=True, fill='x')
        
        # Form fields container
        form_container = tk.Frame(scrollable_frame, bg=self.colors['background'])
        form_container.pack(fill=tk.BOTH, expand=True, padx=50)
        
        # Form fields
        fields = [
            ("ID Number", id_number),
            ("First Name", first_name),
            ("Middle Name", mname if mname else ""),
            ("Last Name", lname),
        ]
        
        entries = {}
        
        for i, (label_text, default_value) in enumerate(fields):
            tk.Label(
                form_container,
                text=label_text,
                font=('Arial', 10, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['background']
            ).pack(anchor='w', pady=(10, 5))
            
            frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=40)
            frame.pack(fill=tk.X, pady=(0, 10))
            frame.pack_propagate(False)
            
            entry = tk.Entry(frame, font=('Arial', 11), bd=0, bg=self.colors['card_bg'])
            entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
            entry.insert(0, default_value)
            
            entries[label_text] = entry
        
        # Category field
        tk.Label(
            form_container,
            text="Category",
            font=('Arial', 10, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(anchor='w', pady=(10, 5))
        
        category_frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=40)
        category_frame.pack(fill=tk.X, pady=(0, 10))
        category_frame.pack_propagate(False)
        
        category_var = tk.StringVar(value=category)
        
        def on_category_change(*args):
            """Show/hide graduate fields based on category selection"""
            cat = category_var.get()
            if cat == "Graduate":
                # Show graduate fields
                for field_name, entry in graduate_entries.items():
                    entry_frame = entry['frame']
                    entry_widget = entry['widget']
                    entry_frame.pack(fill=tk.X, pady=(0, 10))
                    entry_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
            else:
                # Hide graduate fields
                for field_name, entry in graduate_entries.items():
                    entry_frame = entry['frame']
                    entry_widget = entry['widget']
                    entry_frame.pack_forget()
                    entry_widget.pack_forget()
            
            # Update scrollable area
            scrollable_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        category_var.trace_add('write', on_category_change)
        
        category_menu = ttk.Combobox(
            category_frame,
            textvariable=category_var,
            values=['Graduate', 'Undergraduate'],
            font=('Arial', 11),
            state='readonly'
        )
        category_menu.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
        
        entries['Category'] = category_var
        
        # Graduate-specific fields
        graduate_fields = [
            ("Last School Year Attended", last_school_year if last_school_year else "Enter last school year attended"),
            ("Contact Number", contact_number if contact_number else "Enter contact number"),
            ("SO Number", so_number if so_number else "Enter SO number"),
            ("Date Issued", date_issued if date_issued else "Enter date issued (YYYY-MM-DD)"),
            ("Series of Year", series_year if series_year else "Enter series of year")
        ]
        
        graduate_entries = {}
        
        for i, (label_text, default_value) in enumerate(graduate_fields):
            # Create the label
            label = tk.Label(
                form_container,
                text=label_text,
                font=('Arial', 10, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['background']
            )
            
            # Create the frame
            frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=40)
            
            # Create the entry widget
            entry = tk.Entry(frame, font=('Arial', 11), bd=0, bg=self.colors['card_bg'])
            entry.insert(0, default_value)
            entry.bind('<FocusIn>', lambda e, w=entry, d=default_value: w.delete(0, tk.END) if w.get() == d else None)
            entry.bind('<FocusOut>', lambda e, w=entry, d=default_value: w.insert(0, d) if not w.get() else None)
            
            # Store references
            graduate_entries[label_text] = {
                'label': label,
                'frame': frame,
                'widget': entry
            }
        
        # Show graduate fields if category is Graduate
        if category == "Graduate":
            for field_name, entry in graduate_entries.items():
                entry['label'].pack(anchor='w', pady=(10, 5))
                entry['frame'].pack(fill=tk.X, pady=(0, 10))
                entry['widget'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
        
        # Attachments section
        tk.Label(
            form_container,
            text=f"Attachments ({len(attachments)})",
            font=('Arial', 10, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(anchor='w', pady=(10, 5))
        
        attachments_frame = tk.Frame(form_container, bg=self.colors['card_bg'], height=150)
        attachments_frame.pack(fill=tk.X, pady=(0, 10))
        attachments_frame.pack_propagate(False)
        
        # Listbox for attachments
        attachments_listbox_frame = tk.Frame(attachments_frame, bg=self.colors['card_bg'])
        attachments_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Scrollbar for listbox
        listbox_scrollbar = ttk.Scrollbar(attachments_listbox_frame)
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        attachments_listbox = tk.Listbox(
            attachments_listbox_frame,
            yscrollcommand=listbox_scrollbar.set,
            font=('Arial', 10),
            bg='white',
            height=4
        )
        attachments_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        listbox_scrollbar.config(command=attachments_listbox.yview)
        
        # Load existing attachments
        selected_files = []  # Store file paths
        for attachment in attachments:
            if os.path.exists(attachment):
                selected_files.append(attachment)
                attachments_listbox.insert(tk.END, os.path.basename(attachment))
        
        # Buttons for attachments
        attachments_buttons_frame = tk.Frame(attachments_frame, bg=self.colors['card_bg'])
        attachments_buttons_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        def add_attachments():
            filetypes = [
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PDF files", "*.pdf"),
                ("Document files", "*.doc *.docx *.txt"),
                ("All files", "*.*")
            ]
            files = filedialog.askopenfilenames(
                title="Select attachments",
                filetypes=filetypes
            )
            if files:
                for file in files:
                    if file not in selected_files:
                        selected_files.append(file)
                        attachments_listbox.insert(tk.END, os.path.basename(file))
        
        def remove_selected_attachment():
            selection = attachments_listbox.curselection()
            if selection:
                index = selection[0]
                selected_files.pop(index)
                attachments_listbox.delete(index)
        
        add_btn = tk.Button(
            attachments_buttons_frame,
            text="➕ Add Files",
            command=add_attachments,
            font=('Arial', 9),
            bg=self.colors['info'],
            fg='white',
            bd=0,
            padx=10,
            pady=5,
            cursor='hand2'
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
        add_btn.bind('<Enter>', lambda e: add_btn.config(bg=self.colors['primary']))
        add_btn.bind('<Leave>', lambda e: add_btn.config(bg=self.colors['info']))
        
        remove_btn = tk.Button(
            attachments_buttons_frame,
            text="🗑️ Remove Selected",
            command=remove_selected_attachment,
            font=('Arial', 9),
            bg=self.colors['danger'],
            fg='white',
            bd=0,
            padx=10,
            pady=5,
            cursor='hand2'
        )
        remove_btn.pack(side=tk.LEFT)
        remove_btn.bind('<Enter>', lambda e: remove_btn.config(bg='#d90429'))
        remove_btn.bind('<Leave>', lambda e: remove_btn.config(bg=self.colors['danger']))
        
        def update_credential():
            """Update student record in database"""
            try:
                # Get values
                id_number = entries['ID Number'].get()
                first_name = entries['First Name'].get()
                middle_name = entries['Middle Name'].get()
                last_name = entries['Last Name'].get()
                category = entries['Category'].get()
                
                # Validate required fields
                if not id_number:
                    messagebox.showerror("Error", "ID Number is required")
                    return
                
                if not first_name:
                    messagebox.showerror("Error", "First Name is required")
                    return
                
                if not last_name:
                    messagebox.showerror("Error", "Last Name is required")
                    return
                
                # Get graduate-specific fields if category is Graduate
                last_school_year = ""
                contact_number = ""
                so_number = ""
                date_issued = ""
                series_year = ""
                
                if category == "Graduate":
                    last_school_year = graduate_entries["Last School Year Attended"]['widget'].get()
                    if last_school_year == "Enter last school year attended":
                        last_school_year = ""
                    
                    contact_number = graduate_entries["Contact Number"]['widget'].get()
                    if contact_number == "Enter contact number":
                        contact_number = ""
                    
                    so_number = graduate_entries["SO Number"]['widget'].get()
                    if so_number == "Enter SO number":
                        so_number = ""
                    
                    date_issued = graduate_entries["Date Issued"]['widget'].get()
                    if date_issued == "Enter date issued (YYYY-MM-DD)":
                        date_issued = ""
                    
                    series_year = graduate_entries["Series of Year"]['widget'].get()
                    if series_year == "Enter series of year":
                        series_year = ""
                
                # Create title from name
                title = f"{first_name} {last_name} ({id_number})"
                
                # Handle attachments - copy new files to attachments directory
                saved_attachments = []
                student_dir = os.path.join(self.attachments_dir, f"student_{id_number}")
                
                # Clean up old attachments that are no longer selected
                old_attachments = attachments
                for old_attachment in old_attachments:
                    if old_attachment not in selected_files and os.path.exists(old_attachment):
                        try:
                            os.remove(old_attachment)
                        except:
                            pass
                
                # Process selected files
                for file_path in selected_files:
                    if os.path.exists(file_path):
                        # If file is already in the attachments directory, keep it
                        if file_path.startswith(self.attachments_dir):
                            saved_attachments.append(file_path)
                        else:
                            # Copy new file to attachments directory
                            if not os.path.exists(student_dir):
                                os.makedirs(student_dir)
                            
                            # Generate unique filename
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{timestamp}_{os.path.basename(file_path)}"
                            dest_path = os.path.join(student_dir, filename)
                            
                            # Copy file to attachments directory
                            shutil.copy2(file_path, dest_path)
                            saved_attachments.append(dest_path)
                
                # Update database
                self.cursor.execute('''
                    UPDATE credentials 
                    SET title = ?, username = ?, password = ?, attachments = ?, 
                        category = ?, first_name = ?, middle_name = ?, 
                        last_name = ?, last_school_year = ?, contact_number = ?,
                        so_number = ?, date_issued = ?, series_year = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND owner_id = ?
                ''', (title, id_number, first_name, json.dumps(saved_attachments), 
                      category, first_name, middle_name, last_name,
                      last_school_year, contact_number, so_number, date_issued, series_year,
                      cred_id_db, self.current_user))
                self.conn.commit()
                
                messagebox.showinfo("Success", f"Student record updated successfully!\n{len(saved_attachments)} attachment(s) saved.")
                dialog.destroy()
                self.show_credentials()  # Refresh the student records list
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update student record: {str(e)}")
        
        # Button container
        button_container = tk.Frame(scrollable_frame, bg=self.colors['background'])
        button_container.pack(fill=tk.X, pady=30)
        
        # Update button
        update_btn = tk.Button(
            button_container,
            text="💾 Update Student Record",
            command=update_credential,
            font=('Arial', 12, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        update_btn.pack(pady=10)
        update_btn.bind('<Enter>', lambda e: update_btn.config(bg=self.colors['secondary']))
        update_btn.bind('<Leave>', lambda e: update_btn.config(bg=self.colors['primary']))
        
        # Cancel button
        cancel_btn = tk.Button(
            button_container,
            text="Cancel",
            command=dialog.destroy,
            font=('Arial', 10),
            bg=self.colors['danger'],
            fg='white',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        cancel_btn.pack(pady=5)
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.config(bg='#d90429'))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.config(bg=self.colors['danger']))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def view_credential(self):
        """View selected student record details with image display"""
        selection = self.cred_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a student record to view")
            return
        
        item = self.cred_tree.item(selection[0])
        cred_id = item['values'][0]
        
        # Get student record details from database
        self.cursor.execute('''
            SELECT title, username, password, attachments, category, first_name, middle_name, last_name, created_at, updated_at, 
                   last_school_year, contact_number, so_number, date_issued, series_year
            FROM credentials 
            WHERE id = ? AND owner_id = ?
        ''', (cred_id, self.current_user))
        
        cred = self.cursor.fetchone()
        if not cred:
            messagebox.showerror("Error", "Student record not found")
            return
        
        title, id_number, first_name, attachments_json, category, fname, mname, lname, created_at, updated_at, last_school_year, contact_number, so_number, date_issued, series_year = cred
        
        # Parse attachments
        try:
            attachments = json.loads(attachments_json) if attachments_json else []
        except:
            attachments = []
        
        # Create view dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Student Record: {title}")
        dialog.geometry("800x750")  # Adjusted size
        dialog.configure(bg=self.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f'800x750+{x}+{y}')
        
        # Create a scrollable canvas
        canvas = tk.Canvas(dialog, bg=self.colors['background'])
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['background'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title - CENTERED
        tk.Label(
            scrollable_frame,
            text=f"👨‍🎓 {title}",
            font=('Arial', 20, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=(20, 5), anchor='center', expand=True, fill='x')
        
        tk.Label(
            scrollable_frame,
            text=f"Category: {category} | Attachments: {len(attachments)}",
            font=('Arial', 11),
            fg=self.colors['text'],
            bg=self.colors['background']
        ).pack(anchor='center')
        
        # Details frame
        details_frame = tk.Frame(scrollable_frame, bg=self.colors['card_bg'], padx=20, pady=20)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Display attachments if they exist
        if attachments:
            # Create a frame for attachments
            attachments_frame = tk.Frame(details_frame, bg=self.colors['card_bg'])
            attachments_frame.pack(fill=tk.X, pady=(0, 20))
            
            tk.Label(
                attachments_frame,
                text=f"📁 Attachments ({len(attachments)}):",
                font=('Arial', 12, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['card_bg']
            ).pack(anchor='center', pady=(0, 10))
            
            # Create a canvas for horizontal scrolling of images
            images_canvas = tk.Canvas(attachments_frame, bg=self.colors['card_bg'], height=220)
            images_scrollbar = ttk.Scrollbar(attachments_frame, orient="horizontal", command=images_canvas.xview)
            images_inner_frame = tk.Frame(images_canvas, bg=self.colors['card_bg'])
            
            images_canvas.create_window((0, 0), window=images_inner_frame, anchor="nw")
            images_canvas.configure(xscrollcommand=images_scrollbar.set)
            
            # Function to configure canvas
            def configure_images_canvas(e):
                images_canvas.configure(scrollregion=images_canvas.bbox("all"))
            
            images_inner_frame.bind("<Configure>", configure_images_canvas)
            
            # Load and display images
            image_widgets = []
            image_paths = []
            
            for i, attachment_path in enumerate(attachments):
                if os.path.exists(attachment_path):
                    # Create frame for each image
                    img_frame = tk.Frame(images_inner_frame, bg=self.colors['card_bg'], relief='solid', bd=1)
                    img_frame.grid(row=0, column=i, padx=10, pady=5, sticky='nw')
                    
                    # Check if it's an image file
                    if attachment_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        try:
                            # Open and resize the image
                            img = Image.open(attachment_path)
                            
                            # Calculate new dimensions (max 200x200 while maintaining aspect ratio)
                            max_size = (200, 200)
                            img.thumbnail(max_size, Image.Resampling.LANCZOS)
                            
                            # Convert to PhotoImage
                            photo = ImageTk.PhotoImage(img)
                            
                            # Display image in a label
                            img_label = tk.Label(
                                img_frame,
                                image=photo,
                                bg='white'
                            )
                            img_label.image = photo  # Keep a reference
                            img_label.pack(pady=5)
                            
                            image_widgets.append(photo)
                            
                        except Exception as e:
                            # If PIL fails, show file icon
                            img_label = tk.Label(
                                img_frame,
                                text="📄",
                                font=('Arial', 48),
                                bg='white'
                            )
                            img_label.pack(pady=5)
                    else:
                        # For non-image files, show file icon
                        img_label = tk.Label(
                            img_frame,
                            text="📄",
                            font=('Arial', 48),
                            bg='white'
                        )
                        img_label.pack(pady=5)
                    
                    # File name label
                    filename = os.path.basename(attachment_path)
                    if len(filename) > 20:
                        filename = filename[:17] + "..."
                    
                    tk.Label(
                        img_frame,
                        text=filename,
                        font=('Arial', 9),
                        bg=self.colors['card_bg'],
                        wraplength=180
                    ).pack(pady=(0, 5))
                    
                    # Open button
                    open_btn = tk.Button(
                        img_frame,
                        text="Open",
                        command=lambda path=attachment_path: self.open_file(path),
                        font=('Arial', 8),
                        bg=self.colors['info'],
                        fg='white',
                        bd=0,
                        padx=10,
                        pady=2,
                        cursor='hand2'
                    )
                    open_btn.pack(pady=(0, 5))
                    open_btn.bind('<Enter>', lambda e, b=open_btn: b.config(bg=self.colors['primary']))
                    open_btn.bind('<Leave>', lambda e, b=open_btn: b.config(bg=self.colors['info']))
                    
                    image_paths.append(attachment_path)
                else:
                    # File doesn't exist
                    tk.Label(
                        images_inner_frame,
                        text=f"⚠️ File not found: {os.path.basename(attachment_path)}",
                        font=('Arial', 9),
                        fg=self.colors['warning'],
                        bg=self.colors['card_bg']
                    ).grid(row=0, column=i, padx=10, pady=5, sticky='w')
            
            if image_paths:
                images_canvas.pack(fill=tk.X, expand=True)
                images_scrollbar.pack(fill=tk.X)
        else:
            # No attachments
            tk.Label(
                details_frame,
                text="📁 No attachments",
                font=('Arial', 10),
                fg=self.colors['text'],
                bg=self.colors['card_bg']
            ).pack(pady=(0, 20), anchor='center')
        
        # Student information in a grid layout
        info_frame = tk.Frame(details_frame, bg=self.colors['card_bg'])
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Basic fields
        fields = [
            ("🆔 ID Number:", id_number),
            ("👤 First Name:", first_name),
            ("👥 Middle Name:", mname if mname else "N/A"),
            ("👤 Last Name:", lname),
            ("📅 Created:", created_at),
            ("🔄 Updated:", updated_at)
        ]
        
        # Add graduate-specific fields if category is Graduate
        if category == "Graduate":
            fields.extend([
                ("🎓 Last School Year Attended:", last_school_year if last_school_year else "N/A"),
                ("📱 Contact Number:", contact_number if contact_number else "N/A"),
                ("📋 SO Number:", so_number if so_number else "N/A"),
                ("📅 Date Issued:", date_issued if date_issued else "N/A"),
                ("📊 Series of Year:", series_year if series_year else "N/A")
            ])
        
        for i, (label_text, value) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            
            # Label
            tk.Label(
                info_frame,
                text=label_text,
                font=('Arial', 10, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['card_bg'],
                anchor='w'
            ).grid(row=row, column=col, sticky='w', padx=(0, 10), pady=5)
            
            # Value
            tk.Label(
                info_frame,
                text=value,
                font=('Arial', 11),
                fg=self.colors['text'],
                bg=self.colors['card_bg'],
                anchor='w'
            ).grid(row=row, column=col+1, sticky='w', pady=5)
        
        # Action buttons frame
        button_frame = tk.Frame(scrollable_frame, bg=self.colors['background'])
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        action_buttons = [
            ("📋 Copy ID", lambda: self.copy_to_clipboard(id_number)),
            ("✏️ Edit", lambda: self.edit_credential()),
            ("📤 Export PDF", lambda: self.export_selected_to_pdf()),
            ("Close", dialog.destroy)
        ]
        
        for btn_text, command in action_buttons:
            btn = tk.Button(
                button_frame,
                text=btn_text,
                command=command,
                font=('Arial', 10),
                bg=self.colors['primary'] if btn_text == "Close" else 'white',
                fg='white' if btn_text == "Close" else self.colors['dark'],
                bd=0,
                padx=15,
                pady=8,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=(0, 10))
            btn.bind('<Enter>', lambda e, b=btn, t=btn_text: b.config(bg=self.colors['secondary'] if t == "Close" else self.colors['light']))
            btn.bind('<Leave>', lambda e, b=btn, t=btn_text: b.config(bg=self.colors['primary'] if t == "Close" else 'white'))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def open_file(self, filepath):
        """Open a file using the default system application"""
        try:
            if os.name == 'nt':  # For Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # For macOS and Linux
                import subprocess
                subprocess.run(['open', filepath] if sys.platform == 'darwin' else ['xdg-open', filepath])
            else:
                messagebox.showinfo("Open File", f"File location: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file: {str(e)}")
    
    def open_attachments(self):
        """Open attachments folder for selected student record"""
        selection = self.cred_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a student record")
            return
        
        item = self.cred_tree.item(selection[0])
        cred_id = item['values'][0]
        id_number = item['values'][1]
        
        # Get attachments from database
        self.cursor.execute('SELECT attachments FROM credentials WHERE id = ? AND owner_id = ?', 
                          (cred_id, self.current_user))
        result = self.cursor.fetchone()
        
        if result and result[0]:
            try:
                attachments = json.loads(result[0])
                if attachments:
                    # Open the first attachment
                    self.open_file(attachments[0])
                else:
                    messagebox.showwarning("No Attachments", "This student record has no attachments")
            except:
                messagebox.showwarning("No Attachments", "This student record has no attachments")
        else:
            messagebox.showwarning("No Attachments", "This student record has no attachments")
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Text copied to clipboard!")
    
    def delete_credential(self):
        """Delete selected student record"""
        selection = self.cred_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a student record to delete")
            return
        
        item = self.cred_tree.item(selection[0])
        cred_id = item['values'][0]
        first_name = item['values'][2]
        last_name = item['values'][3]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{first_name} {last_name}'?"):
            try:
                # Get attachments before deleting
                self.cursor.execute('SELECT attachments FROM credentials WHERE id = ? AND owner_id = ?', 
                                  (cred_id, self.current_user))
                result = self.cursor.fetchone()
                
                # Delete from database
                self.cursor.execute('DELETE FROM credentials WHERE id = ? AND owner_id = ?', 
                                  (cred_id, self.current_user))
                self.conn.commit()
                
                # Optionally delete attachment files
                if result and result[0]:
                    try:
                        attachments = json.loads(result[0])
                        for attachment in attachments:
                            if os.path.exists(attachment):
                                try:
                                    os.remove(attachment)
                                except:
                                    pass
                    except:
                        pass
                
                messagebox.showinfo("Success", "Student record deleted successfully!")
                self.show_credentials()  # Refresh the list
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete student record: {str(e)}")
    
    def export_credentials(self):
        """Export student records to file"""
        self.export_options()
    
    def show_settings(self):
        """Show settings screen"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.main_content,
            text="⚙️ Settings",
            font=('Arial', 24, 'bold'),
            bg=self.colors['light'],
            fg=self.colors['dark']
        ).pack(pady=50)
    
    def show_help(self):
        """Show help screen"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.main_content,
            text="🆘 Help & Support",
            font=('Arial', 24, 'bold'),
            bg=self.colors['light'],
            fg=self.colors['dark']
        ).pack(pady=50)
    
    def request_credentials(self):
        """Handle credentials request"""
        messagebox.showinfo("Student Records Request", 
                          "Student records request feature coming soon!\n\n"
                          "This will allow users to request access to student records.")
    
    def change_password(self):
        """Open change password window"""
        messagebox.showinfo("Coming Soon", "Change password feature coming soon!")
    
    def generate_report(self):
        """Generate system report"""
        messagebox.showinfo("Coming Soon", "Report generation feature coming soon!")
    
    def forgot_password(self):
        """Handle forgot password"""
        messagebox.showinfo("Password Reset", 
                          "Please contact your system administrator to reset your password.")
    
    def logout(self):
        """Handle logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.current_user = None
            self.current_role = None
            self.create_login_screen()

# Run the application
if __name__ == "__main__":
    app = ModernLoginSystem()

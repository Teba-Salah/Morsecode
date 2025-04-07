import tkinter as tk
from tkinter import ttk, messagebox
import re
from PIL import Image, ImageTk
import mysql.connector
from mysql.connector import Error
import bcrypt
import subprocess
import sys
import os
import webbrowser
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading


class MorseAuthApp:
    def __init__(self):
        # إعدادات ملف HTML
        self.HTML_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.HTML_FILE_PATH = os.path.join(self.HTML_FILE_DIR, "hello-world.html")

        # قاموس مورس
        self.MORSE_CODE_DICT = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z', '-----': '0', '.----': '1', '..---': '2', '...--': '3',
            '....-': '4', '.....': '5', '-....': '6', '--...': '7', '---..': '8',
            '----.': '9'
        }

        # حالة النظام
        self.click_hold_timer = None
        self.password_input = ""
        self.back_arrow_icon = None

        # إنشاء النافذة الرئيسية
        self.root = tk.Tk()
        self.root.title("Morse Code Authentication")

        # جعل النافذة تأخذ الشاشة كاملة
        self.root.attributes('-fullscreen', True)

        # إعداد الخطوط
        self.font_large = ("Arial", 16)
        self.font_medium = ("Arial", 14)
        self.font_small = ("Arial", 12)

        self.root.configure(bg="#f0f0f0")

        # تحميل أيقونة العودة
        self.load_back_icon()

        # تهيئة الواجهة
        self.setup_ui()
        self.create_tables()

        # بدء خادم الويب المحلي
        self.start_local_server()
        self.create_html_file()

    def start_local_server(self):
        """بدء خادم ويب محلي"""

        def run_server():
            os.chdir(self.HTML_FILE_DIR)
            server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
            print("Local server started at http://localhost:8000")
            server.serve_forever()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

    def create_html_file(self):
        """إنشاء ملف HTML إذا لم يكن موجوداً"""
        if not os.path.exists(self.HTML_FILE_PATH):
            html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Hello World</title>
    <style>
        body {
            background-color: #f0f0f0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
        }
        h1 {
            color: #007BFF;
            font-size: 3em;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Hello World!</h1>
    <p>Welcome to our website</p>
</body>
</html>"""
            with open(self.HTML_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Created HTML file at: {self.HTML_FILE_PATH}")

    def open_hello_world(self):
        """فتح صفحة Hello World في المتصفح"""
        try:
            webbrowser.open(f"http://localhost:8000/hello-world.html?t={time.time()}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open page: {str(e)}")

    def load_back_icon(self):
        """تحميل أيقونة زر العودة"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icons8-home-50.png")
            if os.path.exists(icon_path):
                back_arrow_image = Image.open(icon_path)
                back_arrow_image = back_arrow_image.resize((40, 40), Image.Resampling.LANCZOS)
                self.back_arrow_icon = ImageTk.PhotoImage(back_arrow_image)
        except Exception as e:
            print(f"Error loading back icon: {e}")

    def setup_ui(self):
        """تهيئة واجهة المستخدم"""
        # إطار رئيسي
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=50, pady=50)
        main_frame.pack(fill="both", expand=True)

        # إضافة زر العودة في أعلى الصفحة
        self.add_back_button(main_frame)

        # دفتر التبويبات
        self.tab_control = ttk.Notebook(main_frame)

        # تبويب التسجيل
        self.sign_up_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.sign_up_tab, text="Sign Up")

        # تبويب الدخول
        self.sign_in_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.sign_in_tab, text="Sign In")

        self.tab_control.pack(fill="both", expand=True, pady=(20, 0))

        # تهيئة التبويبات
        self.setup_sign_up_tab()
        self.setup_sign_in_tab()

        # زر الخروج من وضع ملء الشاشة
        exit_btn = tk.Button(self.root, text="Exit Full Screen (Esc)",
                             command=lambda: self.root.attributes('-fullscreen', False),
                             bg='#ff4444', fg='white', font=self.font_small)
        exit_btn.place(relx=1.0, rely=0.0, anchor='ne', x=-20, y=20)

        # ربط مفتاح Escape للخروج من وضع ملء الشاشة
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))

    def add_back_button(self, parent_frame):
        """إضافة زر العودة إلى الإطار المحدد"""
        back_frame = tk.Frame(parent_frame, bg="#f0f0f0")
        back_frame.pack(fill="x", pady=(0, 20))

        if self.back_arrow_icon:
            btn = tk.Button(back_frame,
                            image=self.back_arrow_icon,
                            command=self.go_back_to_main,
                            bd=0, bg="#f0f0f0",
                            activebackground="#f0f0f0")
            btn.pack(side="left")
        else:
            btn = tk.Button(back_frame,
                            text="← Back to Main",
                            command=self.go_back_to_main,
                            font=self.font_medium,
                            fg="white", bg="#3498db",
                            padx=15, pady=8)
            btn.pack(side="left")

    def setup_sign_up_tab(self):
        """تهيئة تبويب التسجيل"""
        # إطار المحتوى
        content_frame = tk.Frame(self.sign_up_tab, bg="white", padx=40, pady=40)
        content_frame.pack(fill="both", expand=True)

        # جعل العناصر تتوسع مع توسع النافذة
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # العنوان
        tk.Label(content_frame,
                 text="Create New Account",
                 font=self.font_large,
                 bg="white").grid(row=0, column=0, pady=(0, 30), sticky="w")

        # حقل الاسم الكامل
        tk.Label(content_frame,
                 text="Full Name:",
                 bg="white",
                 font=self.font_medium).grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.full_name_entry = tk.Entry(content_frame, font=self.font_medium)
        self.full_name_entry.grid(row=2, column=0, sticky="ew", pady=(0, 20))

        # حقل البريد الإلكتروني
        tk.Label(content_frame,
                 text="Email Address:",
                 bg="white",
                 font=self.font_medium).grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.email_entry_sign_up = tk.Entry(content_frame, font=self.font_medium)
        self.email_entry_sign_up.grid(row=4, column=0, sticky="ew", pady=(0, 20))

        # حقل كلمة المرور مع أحداث مورس
        tk.Label(content_frame,
                 text="Password (Morse):",
                 bg="white",
                 font=self.font_medium).grid(row=5, column=0, sticky="w", pady=(0, 5))
        self.password_entry_sign_up = tk.Entry(content_frame, show="*", font=self.font_medium)
        self.password_entry_sign_up.grid(row=6, column=0, sticky="ew", pady=(0, 10))
        self.bind_morse_events(self.password_entry_sign_up)

        # زر إظهار/إخفاء كلمة المرور
        show_hide_frame = tk.Frame(content_frame, bg="white")
        show_hide_frame.grid(row=7, column=0, sticky="w", pady=(0, 20))
        self.toggle_label_sign_up = tk.Label(show_hide_frame,
                                             text="Show Password",
                                             fg="blue",
                                             cursor="hand2",
                                             bg="white",
                                             font=self.font_small)
        self.toggle_label_sign_up.pack(side="left")
        self.toggle_label_sign_up.bind("<Button-1>",
                                       lambda e: self.toggle_password_visibility(self.password_entry_sign_up,
                                                                                 self.toggle_label_sign_up))

        # زر التسجيل
        sign_up_btn = tk.Button(content_frame,
                                text="Sign Up",
                                command=self.sign_up_user,
                                bg="#4CAF50",
                                fg="white",
                                font=self.font_medium,
                                padx=30,
                                pady=10)
        sign_up_btn.grid(row=8, column=0, pady=(20, 0), sticky="ew")

        # رابط للانتقال إلى تبويب الدخول
        switch_frame = tk.Frame(content_frame, bg="white")
        switch_frame.grid(row=9, column=0, pady=(20, 0), sticky="w")
        tk.Label(switch_frame,
                 text="Already have an account?",
                 bg="white",
                 font=self.font_small).pack(side="left")
        sign_in_link = tk.Label(switch_frame,
                                text="Sign In",
                                fg="blue",
                                cursor="hand2",
                                bg="white",
                                font=self.font_small)
        sign_in_link.pack(side="left")
        sign_in_link.bind("<Button-1>", lambda e: self.tab_control.select(self.sign_in_tab))

    def setup_sign_in_tab(self):
        """تهيئة تبويب الدخول"""
        # إطار المحتوى
        content_frame = tk.Frame(self.sign_in_tab, bg="white", padx=40, pady=40)
        content_frame.pack(fill="both", expand=True)

        # جعل العناصر تتوسع مع توسع النافذة
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # العنوان
        tk.Label(content_frame,
                 text="Sign In to Your Account",
                 font=self.font_large,
                 bg="white").grid(row=0, column=0, pady=(0, 30), sticky="w")

        # حقل البريد الإلكتروني
        tk.Label(content_frame,
                 text="Email Address:",
                 bg="white",
                 font=self.font_medium).grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.email_entry = tk.Entry(content_frame, font=self.font_medium)
        self.email_entry.grid(row=2, column=0, sticky="ew", pady=(0, 20))

        # حقل كلمة المرور مع أحداث مورس
        tk.Label(content_frame,
                 text="Password (Morse):",
                 bg="white",
                 font=self.font_medium).grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.password_entry_sign_in = tk.Entry(content_frame, show="*", font=self.font_medium)
        self.password_entry_sign_in.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        self.bind_morse_events(self.password_entry_sign_in)

        # زر إظهار/إخفاء كلمة المرور
        show_hide_frame = tk.Frame(content_frame, bg="white")
        show_hide_frame.grid(row=5, column=0, sticky="w", pady=(0, 20))
        self.toggle_label_sign_in = tk.Label(show_hide_frame,
                                             text="Show Password",
                                             fg="blue",
                                             cursor="hand2",
                                             bg="white",
                                             font=self.font_small)
        self.toggle_label_sign_in.pack(side="left")
        self.toggle_label_sign_in.bind("<Button-1>",
                                       lambda e: self.toggle_password_visibility(self.password_entry_sign_in,
                                                                                 self.toggle_label_sign_in))

        # زر الدخول
        sign_in_btn = tk.Button(content_frame,
                                text="Sign In",
                                command=self.sign_in_user,
                                bg="#2196F3",
                                fg="white",
                                font=self.font_medium,
                                padx=30,
                                pady=10)
        sign_in_btn.grid(row=6, column=0, pady=(20, 0), sticky="ew")

        # رابط للانتقال إلى تبويب التسجيل
        switch_frame = tk.Frame(content_frame, bg="white")
        switch_frame.grid(row=7, column=0, pady=(20, 0), sticky="w")
        tk.Label(switch_frame,
                 text="Don't have an account?",
                 bg="white",
                 font=self.font_small).pack(side="left")
        sign_up_link = tk.Label(switch_frame,
                                text="Sign Up",
                                fg="blue",
                                cursor="hand2",
                                bg="white",
                                font=self.font_small)
        sign_up_link.pack(side="left")
        sign_up_link.bind("<Button-1>", lambda e: self.tab_control.select(self.sign_up_tab))

    def bind_morse_events(self, entry_widget):
        """ربط أحداث مورس بحقل الإدخال"""
        entry_widget.bind("<Button-1>", lambda e: self.on_morse_click(e, entry_widget))
        entry_widget.bind("<ButtonRelease-1>", lambda e: self.on_morse_release(e, entry_widget))
        entry_widget.bind("<Button-3>", lambda e: self.on_morse_right_click(e, entry_widget))
        entry_widget.bind("<Double-Button-1>", lambda e: self.on_morse_double_click(e, entry_widget))
        entry_widget.bind("<BackSpace>", lambda e: self.on_morse_backspace(e, entry_widget))

    def on_morse_click(self, event, entry_widget):
        """معالجة ضغط زر الفأرة الأيسر"""
        if self.click_hold_timer:
            self.root.after_cancel(self.click_hold_timer)
        self.click_hold_timer = self.root.after(230, lambda: self.add_morse_dot(entry_widget))

    def on_morse_release(self, event, entry_widget):
        """معالجة إطلاق زر الفأرة"""
        if self.click_hold_timer:
            self.root.after_cancel(self.click_hold_timer)
            self.click_hold_timer = None

    def on_morse_right_click(self, event, entry_widget):
        """معالجة ضغط زر الفأرة الأيمن"""
        self.password_input += "-"
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, self.password_input)

    def on_morse_double_click(self, event, entry_widget):
        """معالجة النقر المزدوج"""
        self.password_input += " "
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, self.password_input)

    def on_morse_backspace(self, event, entry_widget):
        """معالجة ضغط backspace"""
        self.password_input = self.password_input[:-1]
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, self.password_input)

    def add_morse_dot(self, entry_widget):
        """إضافة نقطة مورس"""
        self.password_input += "."
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, self.password_input)
        self.click_hold_timer = None

    def toggle_password_visibility(self, entry_field, toggle_label):
        """تبديل إظهار/إخفاء كلمة المرور"""
        if entry_field.cget("show") == "*":
            entry_field.config(show="")
            toggle_label.config(text="Hide Password")
        else:
            entry_field.config(show="*")
            toggle_label.config(text="Show Password")

    def go_back_to_main(self):
        """العودة إلى الصفحة الرئيسية"""
        self.root.destroy()
        subprocess.Popen([sys.executable, "main.py"])

    def create_db_connection(self):
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='morse'
            )
            return conn
        except Error as e:
            if "Unknown database" in str(e):
                try:
                    conn = mysql.connector.connect(
                        host='localhost',
                        user='root',
                        password=''
                    )
                    cursor = conn.cursor()
                    cursor.execute("CREATE DATABASE IF NOT EXISTS morse")
                    conn.commit()
                    conn.close()

                    return mysql.connector.connect(
                        host='localhost',
                        user='root',
                        password='',
                        database='morse'
                    )
                except Error as e:
                    messagebox.showerror("Database Error", f"Failed to create database: {e}")
                    return None
            else:
                messagebox.showerror("Database Error", f"Failed to connect to MySQL: {e}")
                return None

    def create_tables(self):
        conn = self.create_db_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `sign_up_users` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `full_name` VARCHAR(255) NOT NULL,
                        `email` VARCHAR(255) NOT NULL UNIQUE,
                        `password` VARCHAR(255) NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `logins` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `email` VARCHAR(255) NOT NULL,
                        `login_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to create tables: {e}")
            finally:
                conn.close()

    def check_email_in_db(self, email):
        conn = self.create_db_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM `sign_up_users` WHERE email = %s", (email,))
                user = cursor.fetchone()
                return user is not None
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to check email: {e}")
                return False
            finally:
                conn.close()
        return False

    def save_user_to_db(self, full_name, email, password):
        conn = self.create_db_connection()
        if conn is not None:
            try:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO `sign_up_users` (full_name, email, password)
                    VALUES (%s, %s, %s)
                """, (full_name, email, hashed_password))
                conn.commit()
                messagebox.showinfo("Success", "User registered successfully!")
                self.open_hello_world()
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to save user: {e}")
            finally:
                conn.close()

    def check_password(self, email, password):
        conn = self.create_db_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM `sign_up_users` WHERE email = %s", (email,))
                result = cursor.fetchone()
                if result:
                    return bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8'))
                return False
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to check password: {e}")
                return False
            finally:
                conn.close()
        return False

    def save_login_to_db(self, email):
        conn = self.create_db_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO `logins` (email) VALUES (%s)", (email,))
                conn.commit()
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to save login: {e}")
            finally:
                conn.close()

    def is_valid_email(self, email):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def sign_up_user(self):
        full_name = self.full_name_entry.get().strip()
        email = self.email_entry_sign_up.get().strip()
        password = self.password_entry_sign_up.get().strip()

        if not full_name or not email or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if not self.is_valid_email(email):
            messagebox.showerror("Error", "Please enter a valid email address.")
            return

        if self.check_email_in_db(email):
            messagebox.showerror("Error", "Email already registered!")
            return

        self.save_user_to_db(full_name, email, password)

    def sign_in_user(self):
        email = self.email_entry.get().strip()
        password = self.password_entry_sign_in.get().strip()

        if not email or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if not self.is_valid_email(email):
            messagebox.showerror("Error", "Please enter a valid email address.")
            return

        if not self.check_email_in_db(email):
            messagebox.showerror("Error", "Email not found. Please sign up first.")
            return

        if not self.check_password(email, password):
            messagebox.showerror("Error", "Invalid password.")
            return

        self.save_login_to_db(email)
        messagebox.showinfo("Success", "Login successful!")
        self.open_hello_world()


if __name__ == "__main__":
    app = MorseAuthApp()
    app.root.mainloop()
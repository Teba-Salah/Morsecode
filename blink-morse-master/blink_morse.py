import re
from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
import numpy as np
import imutils
import cv2
import tkinter as tk
from tkinter import messagebox, ttk
import dlib
import time
import mysql.connector
from mysql.connector import Error
import bcrypt
import webbrowser
import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# تعريف الفترات الزمنية
DOT_TIME = 0.5
DASH_TIME = 1.0
SEPARATOR_TIME = 2.0

# قاموس مورس
MORSE_CODE_DICT = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
    '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
    '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
    '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
    '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
    '--..': 'Z', '.----': '1', '..---': '2', '...--': '3', '....-': '4',
    '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9',
    '-----': '0', '/': ' '
}

# متغيرات عالمية
temp_password = ""
signup_data = {"full_name": "", "email": ""}
HTML_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE_PATH = os.path.join(HTML_FILE_DIR, "hello-world.html")


def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    eye_ar = (A + B) / (2.0 * C)
    return eye_ar


def setup_detector_video(args):
    print("[INFO] Loading facial landmark predictor...")
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(args["shape_predictor"])

    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    print("[INFO] Starting video stream...")
    vs = VideoStream(src=0).start()
    return vs, detector, predictor, lStart, lEnd, rStart, rEnd


def loop_camera(vs, detector, predictor, lStart, lEnd, rStart, rEnd):
    total_morse = []
    displayed_text = ""
    text_timer = 0

    focal_length = 700
    real_eye_width = 6.3

    eye_closed_start_time = None

    while True:
        frame = vs.read()
        if frame is None:
            print("[ERROR] Could not read frame from the camera. Exiting...")
            break

        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)

        eye_ar = 0.0
        for rect in rects:
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)
            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]
            left_eye_ar = eye_aspect_ratio(leftEye)
            right_eye_ar = eye_aspect_ratio(rightEye)
            eye_ar = (left_eye_ar + right_eye_ar) / 2.0

            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

            leftEye_center = np.mean(leftEye, axis=0)
            rightEye_center = np.mean(rightEye, axis=0)
            pixel_eye_width = dist.euclidean(leftEye_center, rightEye_center)
            distance = (focal_length * real_eye_width) / pixel_eye_width
            cv2.putText(frame, "Distance: {:.2f} m".format(distance), (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            eye_ar_threshold = 0.25 if distance > 1.5 else 0.3

            if eye_ar < eye_ar_threshold:
                if eye_closed_start_time is None:
                    eye_closed_start_time = time.time()
            else:
                if eye_closed_start_time is not None:
                    eye_closed_duration = time.time() - eye_closed_start_time
                    if eye_closed_duration < DOT_TIME:
                        total_morse.append(".")
                        displayed_text = "Dot (.)"
                    elif DOT_TIME <= eye_closed_duration < DASH_TIME:
                        total_morse.append("-")
                        displayed_text = "Dash (-)"
                    elif DASH_TIME <= eye_closed_duration < SEPARATOR_TIME:
                        total_morse.append("/")
                        displayed_text = "Separator (/)"
                    text_timer = 20
                    eye_closed_start_time = None

        if text_timer > 0:
            text_timer -= 1
            cv2.putText(frame, displayed_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        morse_text = "".join(total_morse)
        cv2.putText(frame, f"Morse: {morse_text}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(frame, "EAR: {:.2f}".format(eye_ar), (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Camera Feed", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("[INFO] Exiting...")
            break
        elif key == 8:
            if total_morse:
                total_morse.pop()
                print("[INFO] Last character deleted.")

    return "".join(total_morse)


def cleanup(vs):
    cv2.destroyAllWindows()
    vs.stop()


def print_results(total_morse):
    print("Morse Code: ", total_morse.replace("/", " "))
    translated_text = ""
    for code in total_morse.split("/"):
        if code in MORSE_CODE_DICT:
            translated_text += MORSE_CODE_DICT[code]
    print("Translated: ", translated_text)


def create_db_connection():
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

                conn = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='',
                    database='morse'
                )
                return conn
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to create database: {e}")
                return None
        else:
            messagebox.showerror("Database Error", f"Failed to connect to MySQL: {e}")
            return None


def save_user_to_db(full_name, email, morse_password):
    conn = create_db_connection()
    if conn is not None:
        try:
            translated_password = ""
            for code in morse_password.split("/"):
                if code in MORSE_CODE_DICT:
                    translated_password += MORSE_CODE_DICT[code]

            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(translated_password.encode('utf-8'), salt)

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO `sign_up_users` (full_name, email, password_hash)
                VALUES (%s, %s, %s)
            """, (full_name, email, hashed_password))
            conn.commit()
            messagebox.showinfo("Success", "User registered successfully!")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to save user: {e}")
        finally:
            conn.close()


def check_email_in_db(email, morse_password=None):
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            if morse_password:
                cursor.execute("SELECT password_hash FROM `sign_up_users` WHERE email = %s", (email,))
                result = cursor.fetchone()
                if result:
                    hashed_password = result[0]

                    translated_password = ""
                    for code in morse_password.split("/"):
                        if code in MORSE_CODE_DICT:
                            translated_password += MORSE_CODE_DICT[code]

                    return bcrypt.checkpw(translated_password.encode('utf-8'), hashed_password.encode('utf-8'))
                return False
            else:
                cursor.execute("SELECT * FROM `sign_up_users` WHERE email = %s", (email,))
                result = cursor.fetchone()
                return result is not None
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to check email: {e}")
            return False
        finally:
            conn.close()
    return False


def save_login_to_db(email):
    conn = create_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO `logins` (email)
                VALUES (%s)
            """, (email,))
            conn.commit()
            messagebox.showinfo("Success", "Login recorded successfully!")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to save login: {e}")
        finally:
            conn.close()


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def start_camera(args):
    if messagebox.askokcancel("Attention", "Please look at the camera to enter the password."):
        (vs, detector, predictor, lStart, lEnd, rStart, rEnd) = setup_detector_video(args)
        total_morse = loop_camera(vs, detector, predictor, lStart, lEnd, rStart, rEnd)
        cleanup(vs)
        print_results(total_morse)
        return total_morse
    return ""


def run_local_server():
    os.chdir(HTML_FILE_DIR)
    server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
    print("Local server started at http://localhost:8000")
    server.serve_forever()


def create_html_file():
    """إنشاء ملف HTML إذا لم يكن موجوداً"""
    if not os.path.exists(HTML_FILE_PATH):
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
        with open(HTML_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Created HTML file at: {HTML_FILE_PATH}")


def open_hello_world():
    """فتح صفحة Hello World في المتصفح"""
    try:
        create_html_file()
        webbrowser.open(f"http://localhost:8000/hello-world.html?t={time.time()}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open page: {str(e)}")


def on_enter_password():
    """دالة خاصة بإدخال كلمة المرور"""
    global temp_password
    temp_password = start_camera({"shape_predictor": "shape_predictor_68_face_landmarks.dat"})
    if temp_password:
        messagebox.showinfo("Success", "Password entered successfully!")


def on_signup():
    """دالة التسجيل المعدلة"""
    global temp_password, signup_data

    # جمع بيانات المستخدم
    signup_data["full_name"] = full_name_entry.get().strip()
    signup_data["email"] = email_entry_sign_up.get().strip()

    # التحقق من البيانات
    if not signup_data["full_name"]:
        messagebox.showerror("Error", "Please enter your full name.")
        return

    if not is_valid_email(signup_data["email"]):
        messagebox.showerror("Error", "Please enter a valid email address.")
        return

    if check_email_in_db(signup_data["email"]):
        messagebox.showerror("Error", "Email already registered!")
        return

    if not temp_password:
        messagebox.showerror("Error", "Please enter your password first!")
        return

    # حفظ البيانات في قاعدة البيانات
    save_user_to_db(signup_data["full_name"], signup_data["email"], temp_password)

    # فتح صفحة Hello World
    open_hello_world()

    temp_password = ""


def on_login():
    """دالة تسجيل الدخول المعدلة"""
    email = email_entry.get().strip()

    if not is_valid_email(email):
        messagebox.showerror("Error", "Please enter a valid email address.")
        return

    if not check_email_in_db(email):
        messagebox.showerror("Error", "Email not found. Please sign up first.")
        return

    morse_password = start_camera({"shape_predictor": "shape_predictor_68_face_landmarks.dat"})
    if morse_password and check_email_in_db(email, morse_password):
        save_login_to_db(email)
        open_hello_world()
    else:
        messagebox.showerror("Error", "Incorrect password!")


def go_back_to_main():
    """إغلاق نافذة مورس والعودة للرئيسية"""
    global root
    root.destroy()

# ... (جميع الاستيرادات والكود السابق يبقى كما هو حتى جزء إنشاء النافذة الرئيسية)

# Create Main Window
root = tk.Tk()
root.title("Login System")

# جعل النافذة تأخذ الشاشة كاملة
root.attributes('-fullscreen', True)
root.configure(bg="white")

# إعداد الخطوط
font_large = ("Arial", 24, "bold")
font_medium = ("Arial", 16)
font_small = ("Arial", 12)

# إطار رئيسي
main_frame = tk.Frame(root, bg="white", padx=50, pady=50)
main_frame.pack(fill="both", expand=True)

# زر العودة في أعلى الصفحة
back_btn = tk.Button(main_frame,
                    text="← Back to Main",
                    command=go_back_to_main,
                    font=font_medium,
                    bg="#3498db",
                    fg="white",
                    padx=15,
                    pady=8,
                    bd=0)
back_btn.pack(side="top", anchor="nw", pady=(0, 20))

# Tabs Setup
tab_control = ttk.Notebook(main_frame)
sign_up_tab = ttk.Frame(tab_control)
sign_in_tab = ttk.Frame(tab_control)
tab_control.add(sign_up_tab, text="Sign Up")
tab_control.add(sign_in_tab, text="Sign In")
tab_control.pack(fill="both", expand=True, pady=(10, 0))

# Sign Up Section
sign_up_frame = tk.Frame(sign_up_tab, bg="#EBEEF1", padx=60, pady=60)
sign_up_frame.pack(fill="both", expand=True)

# جعل العناصر تتوسع مع توسع النافذة
sign_up_frame.grid_rowconfigure(0, weight=1)
sign_up_frame.grid_columnconfigure(0, weight=1)

# العنوان
tk.Label(sign_up_frame,
       text="Create New Account",
       font=font_large,
       bg="#EBEEF1",
       fg="dark blue").grid(row=0, column=0, pady=(0, 30), sticky="w")

# حقل الاسم الكامل
tk.Label(sign_up_frame,
       text="Full Name:",
       anchor="w",
       bg="#EBEEF1",
       fg="dark blue",
       font=font_medium).grid(row=1, column=0, sticky="ew", pady=(0, 5))
full_name_entry = tk.Entry(sign_up_frame,
                         font=font_medium,
                         relief=tk.FLAT,
                         bd=2)
full_name_entry.grid(row=2, column=0, sticky="ew", pady=(0, 20))

# حقل البريد الإلكتروني
tk.Label(sign_up_frame,
       text="Email Address:",
       anchor="w",
       bg="#EBEEF1",
       fg="dark blue",
       font=font_medium).grid(row=3, column=0, sticky="ew", pady=(0, 5))
email_entry_sign_up = tk.Entry(sign_up_frame,
                             font=font_medium,
                             relief=tk.FLAT,
                             bd=2)
email_entry_sign_up.grid(row=4, column=0, sticky="ew", pady=(0, 20))

# زر إدخال كلمة المرور
enter_pass_btn = tk.Button(sign_up_frame,
                         text="Enter Your Password",
                         command=on_enter_password,
                         bg="#EBEEF1",
                         fg="black",
                         font=font_medium,
                         padx=25,
                         pady=10,
                         relief=tk.GROOVE,
                         bd=2)
enter_pass_btn.grid(row=5, column=0, sticky="ew", pady=(0, 20))

# زر التسجيل
sign_up_btn = tk.Button(sign_up_frame,
                      text="Sign Up",
                      command=on_signup,
                      bg="#007BFF",
                      fg="white",
                      font=font_medium,
                      padx=30,
                      pady=12,
                      relief=tk.GROOVE,
                      bd=0)
sign_up_btn.grid(row=6, column=0, sticky="ew", pady=(10, 0))

# رابط الانتقال إلى تسجيل الدخول
switch_frame = tk.Frame(sign_up_frame, bg="#EBEEF1")
switch_frame.grid(row=7, column=0, pady=(20, 0), sticky="w")
tk.Label(switch_frame,
       text="Already have an account?",
       bg="#EBEEF1",
       font=font_small).pack(side="left")
sign_in_link = tk.Label(switch_frame,
                      text="Sign In",
                      fg="blue",
                      cursor="hand2",
                      bg="#EBEEF1",
                      font=font_small)
sign_in_link.pack(side="left")
sign_in_link.bind("<Button-1>", lambda e: tab_control.select(sign_in_tab))

# Sign In Section
sign_in_frame = tk.Frame(sign_in_tab, bg="white", padx=60, pady=60)
sign_in_frame.pack(fill="both", expand=True)

# جعل العناصر تتوسع مع توسع النافذة
sign_in_frame.grid_rowconfigure(0, weight=1)
sign_in_frame.grid_columnconfigure(0, weight=1)

# العنوان
tk.Label(sign_in_frame,
       text="Sign In to Your Account",
       font=font_large,
       bg="white").grid(row=0, column=0, pady=(0, 30), sticky="w")

# حقل البريد الإلكتروني
tk.Label(sign_in_frame,
       text="Email Address:",
       anchor="w",
       bg="white",
       font=font_medium).grid(row=1, column=0, sticky="ew", pady=(0, 5))
email_entry = tk.Entry(sign_in_frame,
                     font=font_medium,
                     relief=tk.FLAT,
                     bd=2)
email_entry.grid(row=2, column=0, sticky="ew", pady=(0, 20))

# زر إدخال كلمة المرور
enter_pass_btn_sign_in = tk.Button(sign_in_frame,
                                 text="Enter Your Password",
                                 command=lambda: start_camera({"shape_predictor": "shape_predictor_68_face_landmarks.dat"}),
                                 bg="white",
                                 fg="black",
                                 font=font_medium,
                                 padx=25,
                                 pady=10,
                                 relief=tk.GROOVE,
                                 bd=2)
enter_pass_btn_sign_in.grid(row=3, column=0, sticky="ew", pady=(0, 20))

# زر تسجيل الدخول
sign_in_btn = tk.Button(sign_in_frame,
                      text="Sign In",
                      command=on_login,
                      bg="#007BFF",
                      fg="white",
                      font=font_medium,
                      padx=30,
                      pady=12,
                      relief=tk.GROOVE,
                      bd=0)
sign_in_btn.grid(row=4, column=0, sticky="ew", pady=(10, 0))

# رابط الانتقال إلى تبويب التسجيل
switch_frame = tk.Frame(sign_in_frame, bg="white")
switch_frame.grid(row=5, column=0, pady=(20, 0), sticky="w")
tk.Label(switch_frame,
       text="Don't have an account?",
       bg="white",
       font=font_small).pack(side="left")
sign_up_link = tk.Label(switch_frame,
                      text="Sign Up",
                      fg="blue",
                      cursor="hand2",
                      bg="white",
                      font=font_small)
sign_up_link.pack(side="left")
sign_up_link.bind("<Button-1>", lambda e: tab_control.select(sign_up_tab))

# زر الخروج من وضع ملء الشاشة
exit_btn = tk.Button(root,
                    text="Exit Full Screen (Esc)",
                    command=lambda: root.attributes('-fullscreen', False),
                    bg='#ff4444',
                    fg='white',
                    font=font_small,
                    bd=0)
exit_btn.place(relx=1.0, rely=0.0, anchor='ne', x=-20, y=20)

# ربط مفتاح Escape للخروج من وضع ملء الشاشة
root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))

# بدء خادم الويب المحلي في خيط منفصل
server_thread = threading.Thread(target=run_local_server, daemon=True)
server_thread.start()

# إنشاء ملف HTML إذا لم يكن موجوداً
create_html_file()

# بدء التطبيق
root.mainloop()
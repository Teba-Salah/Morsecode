import tkinter as tk
import subprocess

def run_eye_auth():
    """تشغيل ملف العين مع إخفاء النافذة الرئيسية"""
    root.withdraw()
    subprocess.run(["python", "blink_morse.py"])
    root.deiconify()  # إعادة عرض النافذة الرئيسية عند العودة

def run_morse_auth():
    """تشغيل ملف المورس مع إخفاء النافذة الرئيسية"""
    root.withdraw()
    subprocess.run(["python", "cliclk.py"])  # تأكد من اسم ملف المورس
    root.deiconify()

# إنشاء النافذة الرئيسية
root = tk.Tk()
root.title("Morse Code System")

# جعل النافذة تأخذ الشاشة كاملة
root.attributes('-fullscreen', True)
root.configure(bg="#001C47")

# إعداد الخطوط
font_large = ("Arial", 24, "bold")
font_medium = ("Arial", 16)
font_small = ("Arial", 12)

# إطار مركزي لتجميع العناصر
center_frame = tk.Frame(root, bg="#001C47")
center_frame.place(relx=0.5, rely=0.5, anchor="center")

# واجهة المستخدم الرئيسية
welcome_label = tk.Label(center_frame,
                        text="Welcome to User !",
                        fg="white",
                        font=font_large,
                        bg="#001C47")
welcome_label.pack(pady=(0, 20))

choose_label = tk.Label(center_frame,
                       text="Please choose one of the options below",
                       fg="white",
                       font=font_medium,
                       bg="#001C47")
choose_label.pack(pady=(0, 30))

# زر العين
eye_btn = tk.Button(center_frame,
                   text="Eye Gaze Authentication",
                   command=run_eye_auth,
                   font=font_medium,
                   bg="#2c3e50",
                   fg="white",
                   width=25,
                   height=2,
                   bd=0,
                   activebackground="#34495e")
eye_btn.pack(pady=15)

# زر المورس
morse_btn = tk.Button(center_frame,
                     text="Morse Code Authentication",
                     command=run_morse_auth,
                     font=font_medium,
                     bg="#2c3e50",
                     fg="white",
                     width=25,
                     height=2,
                     bd=0,
                     activebackground="#34495e")
morse_btn.pack(pady=15)

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

root.mainloop()
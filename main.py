"""
Face Recognition Attendance Monitoring System
==============================================
A desktop GUI application (Tkinter + OpenCV) that:
  1. Registers a person by capturing face samples from a webcam.
  2. Trains an LBPH face-recognition model on the captured samples.
  3. Recognizes faces in real time and automatically logs attendance
     (ID, Name, Date, Time) into a daily CSV file.

This is a cleaned-up, runnable version of the project described in the
"Face Recognition Attendance Monitoring System and Management" report
(Chapter 5 - Implementation). The original report's code listing had
broken indentation and Windows-only hardcoded paths from being copied
out of a PDF; those issues are fixed here using os.path.join so the
project runs on Windows, macOS, and Linux.
"""

import os
import csv
import time
import datetime

import cv2
import numpy as np
import pandas as pd
from PIL import Image

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mess
import tkinter.simpledialog as tsd

# --------------------------------------------------------------------------- #
# Paths / constants
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HAARCASCADE_PATH = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
STUDENT_DETAILS_DIR = os.path.join(BASE_DIR, "StudentDetails")
STUDENT_DETAILS_CSV = os.path.join(STUDENT_DETAILS_DIR, "StudentDetails.csv")
TRAINING_IMAGE_DIR = os.path.join(BASE_DIR, "TrainingImage")
TRAINING_LABEL_DIR = os.path.join(BASE_DIR, "TrainingImageLabel")
TRAINER_FILE = os.path.join(TRAINING_LABEL_DIR, "Trainner.yml")
PASSWORD_FILE = os.path.join(TRAINING_LABEL_DIR, "psd.txt")
ATTENDANCE_DIR = os.path.join(BASE_DIR, "Attendance")


def assure_path_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def check_haarcascadefile():
    if not os.path.isfile(HAARCASCADE_PATH):
        mess._show(
            title="File missing",
            message=(
                "haarcascade_frontalface_default.xml was not found.\n"
                "Please make sure it is in the same folder as main.py."
            ),
        )
        window.destroy()


# --------------------------------------------------------------------------- #
# Clock
# --------------------------------------------------------------------------- #
def tick():
    time_string = time.strftime("%H:%M:%S")
    clock.config(text=time_string)
    clock.after(200, tick)


def contact():
    mess._show(title="Contact us", message="Please contact us at: your-email@example.com")


# --------------------------------------------------------------------------- #
# Password handling (used to protect the "Save Profile / Train" action)
# --------------------------------------------------------------------------- #
def save_pass():
    assure_path_exists(TRAINING_LABEL_DIR)

    if os.path.isfile(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as tf:
            key = tf.read()
    else:
        master.destroy()
        new_pas = tsd.askstring(
            "Old Password not found", "Please enter a new password below", show="*"
        )
        if new_pas is None:
            mess._show(title="No Password Entered", message="Password not set!! Please try again")
        else:
            with open(PASSWORD_FILE, "w") as tf:
                tf.write(new_pas)
            mess._show(title="Password Registered", message="New password was registered successfully!!")
        return

    op = old.get()
    newp = new.get()
    nnewp = nnew.get()

    if op == key:
        if newp == nnewp:
            with open(PASSWORD_FILE, "w") as txf:
                txf.write(newp)
            mess._show(title="Password Changed", message="Password changed successfully!!")
        else:
            mess._show(title="Error", message="Confirm new password again!!!")
            return
    else:
        mess._show(title="Wrong Password", message="Please enter correct old password.")
        return

    master.destroy()


def change_pass():
    global master, old, new, nnew
    master = tk.Tk()
    master.geometry("400x160")
    master.resizable(False, False)
    master.title("Change Password")
    master.configure(background="white")

    tk.Label(master, text="Enter Old Password", bg="white", font=("times", 12, "bold")).place(x=10, y=10)
    old = tk.Entry(master, width=25, fg="black", relief="solid", font=("times", 12, "bold"), show="*")
    old.place(x=180, y=10)

    tk.Label(master, text="Enter New Password", bg="white", font=("times", 12, "bold")).place(x=10, y=45)
    new = tk.Entry(master, width=25, fg="black", relief="solid", font=("times", 12, "bold"), show="*")
    new.place(x=180, y=45)

    tk.Label(master, text="Confirm New Password", bg="white", font=("times", 12, "bold")).place(x=10, y=80)
    nnew = tk.Entry(master, width=25, fg="black", relief="solid", font=("times", 12, "bold"), show="*")
    nnew.place(x=180, y=80)

    tk.Button(
        master, text="Cancel", command=master.destroy, fg="black", bg="red",
        height=1, width=25, activebackground="white", font=("times", 10, "bold"),
    ).place(x=200, y=120)
    tk.Button(
        master, text="Save", command=save_pass, fg="black", bg="#3ece48",
        height=1, width=25, activebackground="white", font=("times", 10, "bold"),
    ).place(x=10, y=120)

    master.mainloop()


def psw():
    assure_path_exists(TRAINING_LABEL_DIR)

    if os.path.isfile(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as tf:
            key = tf.read()
    else:
        new_pas = tsd.askstring(
            "Old Password not found", "Please enter a new password below", show="*"
        )
        if new_pas is None:
            mess._show(title="No Password Entered", message="Password not set!! Please try again")
        else:
            with open(PASSWORD_FILE, "w") as tf:
                tf.write(new_pas)
            mess._show(title="Password Registered", message="New password was registered successfully!!")
        return

    password = tsd.askstring("Password", "Enter Password", show="*")
    if password == key:
        TrainImages()
    elif password is None:
        pass
    else:
        mess._show(title="Wrong Password", message="You have entered the wrong password")


# --------------------------------------------------------------------------- #
# Form helpers
# --------------------------------------------------------------------------- #
def clear():
    txt.delete(0, "end")
    message1.configure(text="1) Take Images  >>>  2) Save Profile")


def clear2():
    txt2.delete(0, "end")
    message1.configure(text="1) Take Images  >>>  2) Save Profile")


# --------------------------------------------------------------------------- #
# Core face-recognition functions
# --------------------------------------------------------------------------- #
def TakeImages():
    """Capture ~100 face samples from the webcam for a new registration."""
    check_haarcascadefile()
    columns = ["SERIAL NO.", "ID", "NAME"]
    assure_path_exists(STUDENT_DETAILS_DIR)
    assure_path_exists(TRAINING_IMAGE_DIR)

    serial = 0
    if os.path.isfile(STUDENT_DETAILS_CSV):
        with open(STUDENT_DETAILS_CSV, "r") as csv_file:
            reader = csv.reader(csv_file)
            for _ in reader:
                serial += 1
        serial = serial // 2
    else:
        with open(STUDENT_DETAILS_CSV, "a+", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)
        serial = 1

    Id = txt.get().strip()
    name = txt2.get().strip()

    if not Id:
        message1.configure(text="Please enter an ID")
        return

    if name.replace(" ", "").isalpha():
        cam = cv2.VideoCapture(0)
        detector = cv2.CascadeClassifier(HAARCASCADE_PATH)
        sample_num = 0

        while True:
            ret, img = cam.read()
            if not ret:
                break
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                sample_num += 1
                cv2.imwrite(
                    os.path.join(TRAINING_IMAGE_DIR, f"{name}.{serial}.{Id}.{sample_num}.jpg"),
                    gray[y:y + h, x:x + w],
                )
                cv2.imshow("Taking Images - press q to stop early", img)

            if cv2.waitKey(100) & 0xFF == ord("q"):
                break
            if sample_num > 100:
                break

        cam.release()
        cv2.destroyAllWindows()

        row = [serial, Id, name]
        with open(STUDENT_DETAILS_CSV, "a+", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(row)

        message1.configure(text=f"Images Taken for ID : {Id}")
    else:
        message1.configure(text="Enter a correct name (letters and spaces only)")


def getImagesAndLabels(path):
    image_paths = [
        os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(".jpg")
    ]
    faces = []
    ids = []

    for image_path in image_paths:
        pil_image = Image.open(image_path).convert("L")
        image_np = np.array(pil_image, "uint8")
        img_id = int(os.path.split(image_path)[-1].split(".")[1])
        faces.append(image_np)
        ids.append(img_id)

    return faces, ids


def TrainImages():
    """Train the LBPH recognizer on every captured face sample."""
    check_haarcascadefile()
    assure_path_exists(TRAINING_LABEL_DIR)

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces, ids = getImagesAndLabels(TRAINING_IMAGE_DIR)

    if not faces:
        mess._show(title="No Registrations", message="Please register someone first!")
        return

    recognizer.train(faces, np.array(ids))
    recognizer.save(TRAINER_FILE)

    message1.configure(text="Profile Saved Successfully")
    message.configure(text=f"Total Registrations till now : {len(set(ids))}")


def TrackImages():
    """Run live recognition from the webcam and log attendance for recognized faces."""
    check_haarcascadefile()
    assure_path_exists(ATTENDANCE_DIR)
    assure_path_exists(STUDENT_DETAILS_DIR)

    for k in tv.get_children():
        tv.delete(k)

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    if os.path.isfile(TRAINER_FILE):
        recognizer.read(TRAINER_FILE)
    else:
        mess._show(title="Data Missing", message="Please click 'Save Profile' to train the model first!")
        return

    if os.path.isfile(STUDENT_DETAILS_CSV):
        df = pd.read_csv(STUDENT_DETAILS_CSV)
    else:
        mess._show(title="Details Missing", message="Student details are missing, please check!")
        return

    face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)
    cam = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    col_names = ["Id", "Name", "Date", "Time"]
    logged_today = set()

    ts = time.time()
    date = datetime.datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
    attendance_file = os.path.join(ATTENDANCE_DIR, f"Attendance_{date}.csv")
    file_exists = os.path.isfile(attendance_file)

    while True:
        ret, im = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(im, (x, y), (x + w, y + h), (225, 0, 0), 2)
            serial, conf = recognizer.predict(gray[y:y + h, x:x + w])

            if conf < 50:
                match = df.loc[df["SERIAL NO."] == serial]
                if len(match):
                    name = str(match["NAME"].values[0])
                    student_id = str(match["ID"].values[0])

                    if student_id not in logged_today:
                        now = datetime.datetime.now()
                        attendance_row = [
                            student_id, name,
                            now.strftime("%d-%m-%Y"), now.strftime("%H:%M:%S"),
                        ]
                        with open(attendance_file, "a+", newline="") as csv_file:
                            writer = csv.writer(csv_file)
                            if not file_exists:
                                writer.writerow(col_names)
                                file_exists = True
                            writer.writerow(attendance_row)

                        tv.insert("", 0, text=student_id, values=(name, attendance_row[2], attendance_row[3]))
                        logged_today.add(student_id)

                    display_name = name
                else:
                    display_name = "Unknown"
            else:
                display_name = "Unknown"

            cv2.putText(im, str(display_name), (x, y + h), font, 1, (255, 255, 255), 2)

        cv2.imshow("Taking Attendance - press q to stop", im)
        if cv2.waitKey(1) == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()


# --------------------------------------------------------------------------- #
# GUI front-end
# --------------------------------------------------------------------------- #
ts = time.time()
date = datetime.datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
day, month, year = date.split("-")
MONTHS = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}

window = tk.Tk()
window.geometry("1280x720")
window.resizable(True, False)
window.title("Face Recognition Attendance System")
window.configure(background="#262523")

frame1 = tk.Frame(window, bg="#00aeff")
frame1.place(relx=0.11, rely=0.17, relwidth=0.39, relheight=0.80)

frame2 = tk.Frame(window, bg="#00aeff")
frame2.place(relx=0.51, rely=0.17, relwidth=0.38, relheight=0.80)

message3 = tk.Label(
    window, text="Face Recognition Based Attendance System",
    fg="white", bg="#262523", width=55, height=1, font=("times", 29, "bold"),
)
message3.place(x=10, y=10)

frame3 = tk.Frame(window, bg="#c4c6ce")
frame3.place(relx=0.52, rely=0.09, relwidth=0.09, relheight=0.07)

frame4 = tk.Frame(window, bg="#c4c6ce")
frame4.place(relx=0.36, rely=0.09, relwidth=0.16, relheight=0.07)

datef = tk.Label(
    frame4, text=f"{day}-{MONTHS[month]}-{year} | ",
    fg="orange", bg="#262523", width=55, height=1, font=("times", 22, "bold"),
)
datef.pack(fill="both", expand=1)

clock = tk.Label(frame3, fg="orange", bg="#262523", width=55, height=1, font=("times", 22, "bold"))
clock.pack(fill="both", expand=1)
tick()

tk.Label(
    frame2, text=" For New Registrations ", fg="black", bg="#3ece48", font=("times", 17, "bold")
).grid(row=0, column=0)
tk.Label(
    frame1, text=" For Already Registered ", fg="black", bg="#3ece48", font=("times", 17, "bold")
).place(x=0, y=0)

tk.Label(
    frame2, text="Enter ID", width=20, height=1, fg="black", bg="#00aeff", font=("times", 17, "bold")
).place(x=80, y=55)
txt = tk.Entry(frame2, width=32, fg="black", font=("times", 15, "bold"))
txt.place(x=30, y=88)

tk.Label(
    frame2, text="Enter Name", width=20, fg="black", bg="#00aeff", font=("times", 17, "bold")
).place(x=80, y=140)
txt2 = tk.Entry(frame2, width=32, fg="black", font=("times", 15, "bold"))
txt2.place(x=30, y=173)

message1 = tk.Label(
    frame2, text="1) Take Images  >>>  2) Save Profile", bg="#00aeff", fg="black",
    width=39, height=1, activebackground="yellow", font=("times", 15, "bold"),
)
message1.place(x=7, y=230)

message = tk.Label(
    frame2, text="", bg="#00aeff", fg="black", width=39, height=1,
    activebackground="yellow", font=("times", 16, "bold"),
)
message.place(x=7, y=450)

tk.Label(
    frame1, text="Attendance", width=20, fg="black", bg="#00aeff", height=1, font=("times", 17, "bold")
).place(x=100, y=115)

res = 0
if os.path.isfile(STUDENT_DETAILS_CSV):
    with open(STUDENT_DETAILS_CSV, "r") as csv_file:
        reader = csv.reader(csv_file)
        for _ in reader:
            res += 1
    res = max((res // 2) - 1, 0)
message.configure(text=f"Total Registrations till now : {res}")

# Menu bar
menubar = tk.Menu(window, relief="ridge")
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Change Password", command=change_pass)
filemenu.add_command(label="Contact Us", command=contact)
filemenu.add_command(label="Exit", command=window.destroy)
menubar.add_cascade(label="Help", font=("times", 14, "bold"), menu=filemenu)
window.configure(menu=menubar)

# Attendance table
tv = ttk.Treeview(frame1, height=13, columns=("name", "date", "time"))
tv.column("#0", width=82)
tv.column("name", width=130)
tv.column("date", width=133)
tv.column("time", width=133)
tv.grid(row=2, column=0, padx=(0, 0), pady=(150, 0), columnspan=4)
tv.heading("#0", text="ID")
tv.heading("name", text="NAME")
tv.heading("date", text="DATE")
tv.heading("time", text="TIME")

scroll = ttk.Scrollbar(frame1, orient="vertical", command=tv.yview)
scroll.grid(row=2, column=4, padx=(0, 100), pady=(150, 0), sticky="ns")
tv.configure(yscrollcommand=scroll.set)

# Buttons
tk.Button(
    frame2, text="Clear", command=clear, fg="black", bg="#ea2a2a",
    width=11, activebackground="white", font=("times", 11, "bold"),
).place(x=335, y=86)
tk.Button(
    frame2, text="Clear", command=clear2, fg="black", bg="#ea2a2a",
    width=11, activebackground="white", font=("times", 11, "bold"),
).place(x=335, y=172)
tk.Button(
    frame2, text="Take Images", command=TakeImages, fg="white", bg="blue",
    width=34, height=1, activebackground="white", font=("times", 15, "bold"),
).place(x=30, y=300)
tk.Button(
    frame2, text="Save Profile", command=psw, fg="white", bg="blue",
    width=34, height=1, activebackground="white", font=("times", 15, "bold"),
).place(x=30, y=380)
tk.Button(
    frame1, text="Take Attendance", command=TrackImages, fg="black", bg="yellow",
    width=35, height=1, activebackground="white", font=("times", 15, "bold"),
).place(x=30, y=50)
tk.Button(
    frame1, text="Quit", command=window.destroy, fg="black", bg="red",
    width=35, height=1, activebackground="white", font=("times", 15, "bold"),
).place(x=30, y=450)

if __name__ == "__main__":
    window.mainloop()

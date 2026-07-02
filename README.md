# Face Recognition Attendance Monitoring System

A desktop application that uses face recognition to automate attendance
tracking, eliminating manual roll calls and proxy attendance. Built with
**Python, OpenCV (LBPH face recognizer), and Tkinter**.

This is the working implementation of the project documented in the
accompanying project report — registration, model training, and
real-time recognition with automatic CSV attendance logging.

## Features

- **Enrollment**: Capture ~100 face samples per person via webcam.
- **Training**: Train an LBPH (Local Binary Patterns Histograms) model
  on all enrolled faces.
- **Recognition & Attendance**: Detect faces in real time and log
  ID, Name, Date, and Time to a daily CSV file (one entry per person per day).
- **Password-protected training**: A password gate (set on first use)
  protects the "Save Profile" / training step.
- **Attendance viewer**: See today's logged attendance directly in the app.

## Project Structure

```
face_recognition_attendance_system/
├── main.py                              # Application entry point (run this)
├── requirements.txt                     # Python dependencies
├── haarcascade_frontalface_default.xml  # Face-detection model (OpenCV)
├── StudentDetails/                      # Enrolled people (auto-created CSV)
├── TrainingImage/                       # Captured face samples (auto-created)
├── TrainingImageLabel/                  # Trained model + password file
└── Attendance/                          # Daily attendance CSV logs
```

## Setup

1. **Install Python 3.9+** if you don't already have it.
2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   > Note: `opencv-contrib-python` (not plain `opencv-python`) is required —
   > it includes the `cv2.face` module used for the LBPH recognizer.

4. **Run the app:**
   ```bash
   python main.py
   ```

The `haarcascade_frontalface_default.xml` file is already included in this
folder, so no separate download is needed.

## Usage

1. **Register a new person**
   - Enter an **ID** and **Name** on the right ("For New Registrations").
   - Click **Take Images** — a webcam window opens and captures ~100 face
     samples (press `q` to stop early). Look at the camera from a few angles.
   - Click **Save Profile** to train the model on all captured faces. The
     first time you do this, you'll be asked to set a password — you'll
     need it for training again later.

2. **Take attendance**
   - Click **Take Attendance** (left side) to open the webcam.
   - Recognized faces are labeled with their name and automatically logged
     to `Attendance/Attendance_<date>.csv` (once per person per day).
   - Press `q` to close the camera window.

3. **View attendance**
   - The attendance table on the left fills in as people are recognized.
   - Full logs are saved as CSV files in the `Attendance/` folder, which you
     can open in Excel/Google Sheets.

## How it works (brief)

1. **Face Detection** — Haar Cascade (Viola-Jones) locates faces in each
   webcam frame.
2. **Feature Extraction & Recognition** — LBPH computes local texture
   patterns around each face and compares them against the trained model
   to identify who it is.
3. **Attendance Logging** — On a confident match (low prediction distance),
   the person's ID, name, date, and time are appended to the day's CSV.

## Notes & Limitations

- This is a **local, single-machine** demo system — not intended for
  production use without further hardening (e.g., encrypted templates
  instead of raw face images, consent management, and access controls,
  as discussed in the project report's conclusion).
- Recognition accuracy depends on lighting, camera quality, and the
  number/diversity of training samples per person.
- Tested with a single webcam at index `0` (`cv2.VideoCapture(0)`) — change
  this in `main.py` if you have multiple cameras.

## Possible Enhancements

- Multi-modal biometrics (fingerprint/iris) alongside face recognition.
- Active learning: ask for confirmation on uncertain matches to improve
  the model over time.
- A companion mobile app for viewing attendance/notifications.
- Remote/virtual attendance support.

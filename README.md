# Computer-Vision-Based-Eye-Tracking-Interface-with-Integrated-Emergency-and-Assistive-Alert-Module

A real-time assistive technology application that enables individuals with upper-limb disabilities to control a computer using only facial movements, eye gestures, and hand gestures through a standard webcam — no physical mouse or keyboard required.

---

## About the Project

This project was developed as a Graduate Capstone Seminar Project at Governors State University (2026) to address the challenge of computer accessibility for people with physical disabilities. The system uses computer vision and machine learning to detect natural human movements and convert them into computer commands in real time.

---

## Features

- **Cursor Movement** — Tracks nose position to move the mouse cursor smoothly across the screen
- **Eye-Controlled Clicking** — Detects sustained eye closure (2 seconds) to perform a mouse click, reducing accidental clicks
- **Gesture-Based Start / Stop** — Nod detection and head movement patterns to activate or deactivate the system
- **Hand Gesture Control** — Open palm and fist recognition for system interaction
- **Quick Communication Buttons** — Pre-set messages for hunger, pain, thirst, and other needs delivered through voice feedback and popup notifications
- **Emergency Email Alerts** — Sends an automated email alert with an attached Excel activity log to a caregiver
- **Activity Logging** — Every user action is stored with timestamps in `tracking_details.xlsx` for caregiver monitoring
- **Voice Feedback** — Audio confirmation for every action using text-to-speech

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| OpenCV | Real-time video capture and image processing |
| MediaPipe | Facial landmark and hand tracking |
| PyAutoGUI | Mouse cursor movement and click automation |
| pyttsx3 | Text-to-speech voice feedback |
| Tkinter | Graphical user interface |
| pandas | Data handling for activity logs |
| openpyxl | Reading and writing Excel activity log files |
| smtplib | Sending emergency email alerts |

---

## Project Structure

```
├── Eyetrack.py           # Main GUI and interface management
├── controller.py         # Gesture recognition and mouse control logic
├── email_sender.py       # Emergency email alert functionality
├── tracking_details.xlsx # Activity log file with timestamps
```

---

## How It Works

1. The webcam captures a live video stream continuously
2. MediaPipe processes each frame to detect face landmarks and hand landmarks
3. Nose coordinates are mapped to screen position for cursor movement
4. Eye closure duration is measured to trigger mouse clicks
5. Head nod patterns and hand gestures control system start/stop
6. All actions are logged with timestamps to an Excel file
7. Emergency gestures trigger automated email alerts to caregivers

---

## Performance Results

| Metric | Result |
|---|---|
| Nod Detection Accuracy | 94% |
| Eye Closure Click Accuracy | 92% |
| Hand Gesture Accuracy | 88% |
| Quick Action Accuracy | 96% |
| Average System Latency | < 100 ms |
| Real-Time Processing Speed | ~30 FPS |

---

## Requirements

```
python >= 3.8
opencv-python
mediapipe
pyautogui
pyttsx3
pandas
openpyxl
```

Install all dependencies:

```bash
pip install opencv-python mediapipe pyautogui pyttsx3 pandas openpyxl
```

---

## How to Run

1. Clone the repository
```bash
git clone https://github.com/ramchandharmuddam/Computer-Vision-Based-Eye-Tracking-Interface-with-Integrated-Emergency-and-Assistive-Alert-Module.git
```

2. Install the required libraries
```bash
pip install opencv-python mediapipe pyautogui pyttsx3 pandas openpyxl
```

3. Run the main application
```bash
python Eyetrack.py
```

4. Allow webcam access when prompted and position your face in front of the camera

---

## System Requirements

- Windows 10 / 11
- Standard webcam (built-in or USB)
- Python 3.8 or higher
- Internet connection (for emergency email feature only)

---

## Academic Context

> Submitted in partial fulfillment of the requirements for the Degree of Master of Science with a Major in Computer Science — Governors State University, University Park, IL, 2026.

---

## Acknowledgements

Built using open-source libraries: OpenCV, MediaPipe, PyAutoGUI, pyttsx3, pandas, and openpyxl. Thanks to the disabled volunteers who participated in usability testing and provided feedback that helped improve the system.

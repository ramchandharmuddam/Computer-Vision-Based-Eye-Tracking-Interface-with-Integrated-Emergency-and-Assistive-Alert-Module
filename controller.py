import platform
import subprocess
import threading
import time

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import pyttsx3


class FaceHandController:
    def __init__(self, callback=None):
        """
        callback: function(frame, status_text) called after each processed frame
        """
        self.callback = callback
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

        # MediaPipe models
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7,
                                          min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

        # TTS engine
        self.tts = pyttsx3.init()
        self.tts.setProperty('rate', 150)

        # Screen size
        self.screen_w, self.screen_h = pyautogui.size()

        # Mouse smoothing (lower = faster/more direct, higher = smoother)
        # Set to 1 for no smoothing (laser‑like but may be shaky)
        # Set to 2–4 for a good balance
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 2          # <-- ADJUST HERE: 1 = instant, 2-4 = smooth & fast

        # Dead zone margins (pixels from edge of frame where movement stops)
        # Smaller = more sensitive, larger = requires more head movement
        self.margin = 30                 # <-- ADJUST HERE: 30-100

        # Eye landmarks for blink detection
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        self.BLINK_THRESHOLD = 0.20

        # Long‑closure click
        self.long_closure_start = 0
        self.long_closure_triggered = False
        self.LONG_CLOSURE_DURATION = 2.0
        self.LONG_CLOSURE_ACTION = pyautogui.leftClick

        # Gesture variables
        self.state = 'idle'           # 'idle', 'starting', 'active'
        self.start_countdown_end = 0

        # Head nod (start gesture) – 3 nods
        self.nod_count = 0
        self.nod_state = 'up'
        self.nod_start_time = 0
        self.NOD_THRESHOLD = 15
        self.NOD_TIMEOUT = 3.0

        # Head left‑right‑left (stop gesture) – requires full pattern
        self.lr_state = 'neutral'
        self.lr_count = 0
        self.lr_start_time = 0
        self.LR_THRESHOLD = 20
        self.LR_TIMEOUT = 3.0

        # Hand gesture detection
        self.hand_open = False
        self.hand_closed = False
        self.both_hands_open = False

        # Frame size (updated each frame)
        self.frame_w = 640
        self.frame_h = 480

    # ------------------------------------------------------------------
    # Helper: eye aspect ratio
    # ------------------------------------------------------------------
    def eye_aspect_ratio(self, landmarks, eye_points):
        points = []
        for p in eye_points:
            x = int(landmarks[p].x * self.frame_w)
            y = int(landmarks[p].y * self.frame_h)
            points.append((x, y))
        v1 = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
        v2 = np.linalg.norm(np.array(points[2]) - np.array(points[4]))
        h  = np.linalg.norm(np.array(points[0]) - np.array(points[3]))
        return (v1 + v2) / (2.0 * h)

    # ------------------------------------------------------------------
    # Helper: count extended fingers
    # ------------------------------------------------------------------
    def count_fingers(self, hand_landmarks, handedness):
        tips = [4, 8, 12, 16, 20]
        pips = [3, 6, 10, 14, 18]
        count = 0
        for i in range(5):
            tip = hand_landmarks.landmark[tips[i]]
            pip = hand_landmarks.landmark[pips[i]]
            if i == 0:  # thumb
                if handedness == 'Right':
                    if tip.x > pip.x:
                        count += 1
                else:
                    if tip.x < pip.x:
                        count += 1
            else:
                if tip.y < pip.y:
                    count += 1
        return count

    # ------------------------------------------------------------------
    # Open on-screen keyboard (OS‑aware)
    # ------------------------------------------------------------------
    def open_keyboard(self):
        system = platform.system()
        try:
            if system == 'Windows':
                subprocess.Popen('osk', shell=True)
            elif system == 'Linux':
                try:
                    subprocess.Popen(['onboard'])
                except FileNotFoundError:
                    subprocess.Popen(['florence'])
            else:
                self.tts.say("On‑screen keyboard not available on this system")
                self.tts.runAndWait()
                return
            self.tts.say("Opening keyboard")
            self.tts.runAndWait()
        except Exception as e:
            print(f"Error opening keyboard: {e}")

    # ------------------------------------------------------------------
    # Main processing loop
    # ------------------------------------------------------------------
    def _process(self):
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_results = self.face_mesh.process(rgb)
            hand_results = self.hands.process(rgb)

            self.frame_h, self.frame_w, _ = frame.shape

            status_text = f"State: {self.state.upper()}"
            nose_x, nose_y = 0, 0

            # ----- Hand gesture detection -----
            self.both_hands_open = False
            if hand_results.multi_hand_landmarks and hand_results.multi_handedness:
                open_hands = 0
                for idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                    handedness = hand_results.multi_handedness[idx].classification[0].label
                    fingers = self.count_fingers(hand_landmarks, handedness)
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    if fingers >= 4:
                        open_hands += 1
                self.both_hands_open = (open_hands == 2)
                self.hand_open = (open_hands >= 1)
                self.hand_closed = (open_hands == 0)
            else:
                self.hand_open = False
                self.hand_closed = False
                self.both_hands_open = False

            # Keyboard trigger
            if self.both_hands_open:
                if not hasattr(self, '_keyboard_triggered'):
                    self._keyboard_triggered = False
                if not self._keyboard_triggered:
                    self.open_keyboard()
                    self._keyboard_triggered = True
            else:
                self._keyboard_triggered = False

            # ----- Face landmark processing -----
            if face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    landmarks = face_landmarks.landmark

                    # Nose tip – used for mouse control
                    nose = landmarks[1]
                    nose_x = int(nose.x * self.frame_w)
                    nose_y = int(nose.y * self.frame_h)

                    # Draw face landmarks (optional)
                    self.mp_draw.draw_landmarks(
                        frame, face_landmarks, self.mp_face_mesh.FACEMESH_CONTOURS)

                    # ----- State machine -----
                    now = time.time()

                    if self.state == 'idle':
                        # Head nod detection
                        if 'prev_nose_y' not in locals():
                            prev_nose_y = nose_y
                        diff_y = nose_y - prev_nose_y

                        if self.nod_state == 'up' and diff_y > self.NOD_THRESHOLD:
                            self.nod_state = 'down'
                            self.nod_start_time = now
                        elif self.nod_state == 'down' and diff_y < -self.NOD_THRESHOLD:
                            self.nod_count += 1
                            self.nod_state = 'up'
                            self.nod_start_time = now

                        if now - self.nod_start_time > self.NOD_TIMEOUT:
                            self.nod_count = 0
                            self.nod_state = 'up'

                        if self.nod_count >= 3:
                            self.state = 'starting'
                            self.start_countdown_end = now + 5
                            self.nod_count = 0
                            self.tts.say("Starting in 5 seconds")
                            self.tts.runAndWait()

                        prev_nose_y = nose_y

                        if self.hand_open:
                            self.state = 'active'
                            self.tts.say("Started by hand")
                            self.tts.runAndWait()

                    elif self.state == 'starting':
                        if now >= self.start_countdown_end:
                            self.state = 'active'
                            self.tts.say("System active")
                            self.tts.runAndWait()

                    elif self.state == 'active':
                        # ----- Nose‑only mouse control (laser‑like) -----
                        # Map nose position to screen coordinates with adjustable margins
                        screen_x = np.interp(nose_x, [self.margin, self.frame_w-self.margin], [0, self.screen_w])
                        screen_y = np.interp(nose_y, [self.margin, self.frame_h-self.margin], [0, self.screen_h])

                        # Smoothing – set smooth_factor=1 for no smoothing (instant response)
                        curr_x = self.prev_x + (screen_x - self.prev_x) / self.smooth_factor
                        curr_y = self.prev_y + (screen_y - self.prev_y) / self.smooth_factor

                        pyautogui.moveTo(curr_x, curr_y)
                        self.prev_x, self.prev_y = curr_x, curr_y

                        # ----- Eye closure detection with progress bar -----
                        ear_left = self.eye_aspect_ratio(landmarks, self.LEFT_EYE)
                        ear_right = self.eye_aspect_ratio(landmarks, self.RIGHT_EYE)
                        ear = (ear_left + ear_right) / 2.0

                        # Draw progress bar for long closure
                        if ear < self.BLINK_THRESHOLD:   # eyes closed
                            if self.long_closure_start == 0:
                                self.long_closure_start = now
                                self.long_closure_triggered = False
                            else:
                                elapsed = now - self.long_closure_start
                                # Draw progress bar on frame
                                progress = min(elapsed / self.LONG_CLOSURE_DURATION, 1.0)
                                bar_x = 50
                                bar_y = self.frame_h - 50
                                bar_w = 300
                                bar_h = 20
                                cv2.rectangle(frame, (bar_x, bar_y), (bar_x+bar_w, bar_y+bar_h), (200,200,200), 2)
                                cv2.rectangle(frame, (bar_x, bar_y), (bar_x+int(bar_w*progress), bar_y+bar_h), (0,255,0), -1)
                                cv2.putText(frame, f"Click in {max(0, self.LONG_CLOSURE_DURATION-elapsed):.1f}s",
                                            (bar_x, bar_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                                if not self.long_closure_triggered and elapsed >= self.LONG_CLOSURE_DURATION:
                                    self.LONG_CLOSURE_ACTION()
                                    self.tts.say("button clicked")
                                    self.tts.runAndWait()
                                    self.long_closure_triggered = True
                        else:                             # eyes open
                            self.long_closure_start = 0
                            self.long_closure_triggered = False

                        # ----- Head left‑right‑left stop gesture -----
                        if 'prev_nose_x' not in locals():
                            prev_nose_x = nose_x
                        diff_x = nose_x - prev_nose_x

                        if self.lr_state == 'neutral':
                            if diff_x < -self.LR_THRESHOLD:
                                self.lr_state = 'left'
                                self.lr_count = 1
                                self.lr_start_time = now
                            elif diff_x > self.LR_THRESHOLD:
                                self.lr_state = 'right'
                                self.lr_count = 1
                                self.lr_start_time = now
                        elif self.lr_state == 'left':
                            if diff_x > self.LR_THRESHOLD:
                                self.lr_state = 'right'
                                self.lr_count = 2
                                self.lr_start_time = now
                        elif self.lr_state == 'right':
                            if diff_x < -self.LR_THRESHOLD:
                                self.lr_state = 'left'
                                self.lr_count = 3
                                self.lr_start_time = now

                        if self.lr_count == 3:
                            self.state = 'idle'
                            self.tts.say("Stopped by head gesture")
                            self.tts.runAndWait()
                            self.lr_count = 0
                            self.lr_state = 'neutral'

                        if now - self.lr_start_time > self.LR_TIMEOUT:
                            self.lr_count = 0
                            self.lr_state = 'neutral'

                        prev_nose_x = nose_x

                        # Hand closed stop gesture
                        if self.hand_closed:
                            self.state = 'idle'
                            self.tts.say("Stopped by hand")
                            self.tts.runAndWait()

            # Build status text
            if self.state == 'active':
                status_text = "ACTIVE - Move nose like a laser pointer - Close eyes to click"
            elif self.state == 'starting':
                remaining = max(0, int(self.start_countdown_end - time.time()))
                status_text = f"STARTING in {remaining}s"
            else:
                status_text = "IDLE - Nod 3x, show open hand, or click Start"

            # Callback to GUI
            if self.callback:
                self.callback(frame, status_text)

        cap.release()

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
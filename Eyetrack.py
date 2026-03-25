import tkinter as tk
from tkinter import ttk

import cv2
from PIL import Image, ImageTk

from controller import FaceHandController


class FullScreenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face & Hand Controlled Mouse")
        self.root.state('zoomed')           # Windows maximized
        # For cross‑platform fullscreen:
        # self.root.attributes('-fullscreen', True)

        # Variables
        self.video_frame = None
        self.status_var = tk.StringVar(value="System ready")

        # Create GUI layout
        self.setup_ui()

        # Controller instance (with callback)
        self.controller = FaceHandController(callback=self.update_gui)

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left side: video feed
        video_frame = ttk.LabelFrame(main_frame, text="Camera Feed", padding="5")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Right side: controls and info
        control_frame = ttk.Frame(main_frame, width=350)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0))
        control_frame.pack_propagate(False)

        # Buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start_controller)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_controller, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # New: Keyboard button
        self.keyboard_btn = ttk.Button(btn_frame, text="Keyboard", command=self.open_keyboard)
        self.keyboard_btn.pack(side=tk.LEFT, padx=5)

        self.exit_btn = ttk.Button(btn_frame, text="Exit", command=self.exit_app)
        self.exit_btn.pack(side=tk.LEFT, padx=5)

        # Status
        ttk.Label(control_frame, text="Status:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(20,0))
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var,
                                      font=('Arial', 10), foreground='blue')
        self.status_label.pack(anchor=tk.W, pady=5)

        # Instructions
        instr_frame = ttk.LabelFrame(control_frame, text="How to use", padding="10")
        instr_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        instructions = [
            "• Click START or:",
            "  - Nod head 3 times",
            "  - Show open hand",
            "",
            "• When ACTIVE:",
            "  - Move head to move cursor",
            "  - Close eyes for 2s to click",
            "  - You'll hear 'button clicked'",
            "",
            "• To STOP:",
            "  - Click STOP button",
            "  - Move head left→right→left",
            "  - Make a fist",
            "",
            "• To open on‑screen keyboard:",
            "  - Click 'Keyboard' button",
            "  - OR show both hands fully open",
            "",
            "• Press EXIT to close"
        ]
        for line in instructions:
            ttk.Label(instr_frame, text=line, justify=tk.LEFT).pack(anchor=tk.W)

    def start_controller(self):
        self.controller.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Controller started")

    def stop_controller(self):
        self.controller.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Controller stopped")

    def open_keyboard(self):
        """Call the controller's keyboard method."""
        self.controller.open_keyboard()

    def exit_app(self):
        self.controller.stop()
        self.root.quit()
        self.root.destroy()

    def update_gui(self, frame, status_text):
        """Called from controller thread – update GUI safely."""
        # Convert OpenCV BGR to RGB, then to PIL Image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        # Resize to fit video area (maintain aspect)
        video_width = self.video_label.winfo_width()
        video_height = self.video_label.winfo_height()
        if video_width > 1 and video_height > 1:
            img.thumbnail((video_width, video_height), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)

        # Update GUI in main thread
        self.root.after(0, self._display_frame, imgtk, status_text)

    def _display_frame(self, imgtk, status_text):
        self.video_label.config(image=imgtk)
        self.video_label.image = imgtk   # keep reference
        self.status_var.set(status_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = FullScreenApp(root)
    root.mainloop()
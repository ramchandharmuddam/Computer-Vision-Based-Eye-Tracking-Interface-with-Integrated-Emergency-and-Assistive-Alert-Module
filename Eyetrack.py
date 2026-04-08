import tkinter as tk
from tkinter import ttk

import cv2
from PIL import Image, ImageTk

from controller import FaceHandController


class FullScreenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face & Hand Controlled Mouse")
        self.root.geometry("1200x800")
        self.status_var = tk.StringVar(value="System ready")
        self.quick_buttons = []

        self.setup_ui()

        self.controller = FaceHandController(
            callback=self.update_gui,
            on_long_click=self.handle_button_click
        )

        # Schedule updates after window is fully rendered
        self.root.after(500, self.update_button_rects)
        self.root.bind("<Configure>", self.on_window_resize)   # update on resize

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Video feed
        video_frame = ttk.LabelFrame(main_frame, text="Camera Feed", padding="5")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Control panel
        control_frame = ttk.Frame(main_frame, width=350)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0))
        control_frame.pack_propagate(False)

        # Top buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=10)
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start_controller)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_controller, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.keyboard_btn = ttk.Button(btn_frame, text="Keyboard", command=self.open_keyboard)
        self.keyboard_btn.pack(side=tk.LEFT, padx=5)
        self.exit_btn = ttk.Button(btn_frame, text="Exit", command=self.exit_app)
        self.exit_btn.pack(side=tk.LEFT, padx=5)

        # Status
        ttk.Label(control_frame, text="Status:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(20,0))
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var,
                                      font=('Arial', 10), foreground='blue')
        self.status_label.pack(anchor=tk.W, pady=5)

        # Quick Actions
        quick_frame = ttk.LabelFrame(control_frame, text="Quick Actions (hover & close eyes)", padding="10")
        quick_frame.pack(fill=tk.X, pady=10)

        quick_actions = [
            ("Hungry", "hungry"),
            ("Thirsty", "thirsty"),
            ("Help", "help"),
            ("Take me out", "take me out"),
            ("Water", "water"),
            ("Bathroom", "bathroom"),
            ("Pain", "pain"),
            ("I need attention", "attention")
        ]
        for text, phrase in quick_actions:
            btn = ttk.Button(quick_frame, text=text, width=15)
            btn.pack(pady=2)
            self.quick_buttons.append({
                'widget': btn,
                'phrase': phrase,
                'rect': None
            })

        # Test TTS button
        test_btn = ttk.Button(control_frame, text="Test TTS", command=self.test_tts)
        test_btn.pack(pady=5)

        # Instructions
        instr_frame = ttk.LabelFrame(control_frame, text="How to use", padding="10")
        instr_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        instructions = [
            "• Click START or:",
            "  - Nod head 3 times",
            "  - Show open hand",
            "",
            "• When ACTIVE:",
            "  - Move nose to move cursor",
            "  - Close eyes for 2s to click",
            "  - Hover over a Quick Action button",
            "  - Close eyes → button phrase spoken 5x",
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

    def update_button_rects(self):
        """Get screen coordinates of each quick action button."""
        print("Updating button rects...")
        for btn_info in self.quick_buttons:
            widget = btn_info['widget']
            widget.update_idletasks()
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            w = widget.winfo_width()
            h = widget.winfo_height()
            btn_info['rect'] = (x, y, x + w, y + h)
            print(f"Button '{btn_info['phrase']}' rect = {btn_info['rect']}")

    def on_window_resize(self, event):
        """Update button positions when window is moved/resized."""
        self.root.after(100, self.update_button_rects)

    def handle_button_click(self, x, y):
        """Called by controller when a long closure happens. Returns True if a quick button was triggered."""
        print(f"Long click at screen ({x}, {y})")
        for btn_info in self.quick_buttons:
            rect = btn_info['rect']
            if rect:
                print(f"Checking button '{btn_info['phrase']}' rect {rect}")
                if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                    phrase = btn_info['phrase']
                    print(f"Triggering phrase: {phrase}")
                    self.controller.speak_repeated(phrase, times=5)
                    return True
        print("No button hovered.")
        return False

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
        self.controller.open_keyboard()

    def test_tts(self):
        self.controller.speak_repeated("Test voice", times=1)

    def exit_app(self):
        self.controller.stop()
        self.root.quit()
        self.root.destroy()

    def update_gui(self, frame, status_text):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        video_width = self.video_label.winfo_width()
        video_height = self.video_label.winfo_height()
        if video_width > 1 and video_height > 1:
            img.thumbnail((video_width, video_height), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.root.after(0, self._display_frame, imgtk, status_text)

    def _display_frame(self, imgtk, status_text):
        self.video_label.config(image=imgtk)
        self.video_label.image = imgtk
        self.status_var.set(status_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = FullScreenApp(root)
    root.mainloop()
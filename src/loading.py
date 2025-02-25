import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import time


class LoadingScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Loading Screen")
        self.root.geometry("330x330+400+300")  # Set your desired size and position

        # Load the GIF image
        self.loading_gif = Image.open(r'C:\src\python\python\RtKg.gif')
        self.frames = [ImageTk.PhotoImage(frame.copy()) for frame in ImageSequence.Iterator(self.loading_gif)]

        self.loading_label = tk.Label(root, width=330, height=330)
        self.loading_label.pack()

        # Start playing the GIF in the popup
        self.frame_num = 0
        self.update_frames()

        # Simulate file loading (replace this with your actual file loading logic)
        root.after(100, self.load_big_file(root))

    def update_frames(self):
        # Check if the label widget exists before updating
        if self.loading_label.winfo_exists():
            for frame_num in range(len(self.frames)):
                # Update the displayed frame
                self.loading_label.configure(image=self.frames[frame_num])
                self.loading_label.update()  # Force update

                # Add a small delay between frames (adjust as needed)
                time.sleep(0.05)

    def load_big_file(self, root):
        # Simulate loading a big file (replace this with your actual file loading logic)
        load_data(value, drop2, clicked2, file_list2)

        # Destroy the loading label
        self.loading_label.destroy()
        root.destroy()

def loading_fun():
    root = tk.Toplevel()
    app = LoadingScreen(root)
    root.mainloop()

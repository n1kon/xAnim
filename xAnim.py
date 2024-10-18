import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import vlc
import os
from ftplib import FTP
import threading  # Import threading for background operations

class VideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("xAnim")
        self.root.geometry("1000x600")  # Set the window size

        # Load the icon from the current directory
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')  # Full path
        self.root.iconbitmap(icon_path)  # Set the application icon

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#222222")
        self.style.configure("TButton", padding=6, relief="flat", background="#0078d7", foreground="white")
        self.style.configure("TButton", font=("Helvetica", 12))
        self.style.configure("TLabel", background="#222222", foreground="white", font=("Helvetica", 12))

        self.button_frame = ttk.Frame(root, padding="10")
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

        self.load_button = ttk.Button(self.button_frame, text="Select Folder", command=self.load_videos)
        self.load_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.ftp_button = ttk.Button(self.button_frame, text="Transfer to Xbox", command=self.start_transfer_thread)
        self.ftp_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.ip_label = ttk.Label(self.button_frame, text="Xbox IP:")
        self.ip_label.pack(side=tk.LEFT, padx=5)

        self.ip_entry = ttk.Entry(self.button_frame)
        self.ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.drive_label_var = tk.StringVar(value="/C/")
        self.drive_label_combobox = ttk.Combobox(self.button_frame, textvariable=self.drive_label_var, state="readonly")
        self.drive_label_combobox['values'] = ("/C/", "/HDD0-C/")
        self.drive_label_combobox.pack(side=tk.LEFT, padx=5)

        # Frame for the listbox and scrollbar
        self.listbox_frame = ttk.Frame(root, padding="10")
        self.listbox_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        self.listbox = tk.Listbox(self.listbox_frame, width=30, height=20, font=("Helvetica", 12))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.listbox.bind('<Double-1>', self.play_video)

        # Frame to embed the VLC player
        self.video_frame = ttk.Frame(root, padding="10", relief="raised", borderwidth=5)
        self.video_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Set VLC path to the bundled directory
        vlc_path = os.path.join(os.path.dirname(__file__), 'VLC')  # Path to the bundled VLC folder
        self.instance = vlc.Instance('--no-xlib', '--plugin-path=' + vlc_path)
        self.player = self.instance.media_player_new()

        self.video_paths = {}

    def load_videos(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.listbox.delete(0, tk.END)
            self.video_paths.clear()
            for file_name in os.listdir(folder_path):
                if file_name.endswith('.xmv'):
                    file_name_without_ext = os.path.splitext(file_name)[0]
                    self.listbox.insert(tk.END, file_name_without_ext)
                    self.video_paths[file_name_without_ext] = os.path.join(folder_path, file_name)

    def play_video(self, event):
        # Check if an item is selected
        if not self.listbox.curselection():
            messagebox.showerror("Error", "Please select a video to play.")
            return

        selected_file = self.listbox.get(self.listbox.curselection())
        video_path = self.video_paths[selected_file]
        self.show_video(video_path)

    def show_video(self, video_path):
        media = self.instance.media_new(video_path)
        self.player.set_media(media)

        # Set the VLC player to the video_frame
        self.player.set_hwnd(self.video_frame.winfo_id())
        self.player.play()

    def start_transfer_thread(self):
        """Start the FTP transfer in a separate thread."""
        threading.Thread(target=self.transfer_to_xbox, daemon=True).start()

    def transfer_to_xbox(self):
        # Check if an item is selected
        if not self.listbox.curselection():
            self.show_error("Please select a video from the list.")
            return

        selected_file = self.listbox.get(self.listbox.curselection())
        local_video_path = self.video_paths[selected_file]

        # Pause the video before transferring
        self.player.pause()  # Pause the video playback

        xbox_ip = self.ip_entry.get().strip()  # Strip any whitespace from the IP address

        if not xbox_ip:
            self.show_error("Please enter the Xbox IP address.")
            return

        try:
            # Attempt to connect to the Xbox
            ftp = FTP(xbox_ip)
            ftp.login(user='xbox', passwd='xbox')
            ftp.set_pasv(True)  # Always set passive mode

            ftp_path = self.drive_label_var.get()
            xbox_video_dir = f"{ftp_path}BootAnims/XMV Player/"
            try:
                ftp.cwd(xbox_video_dir)
            except Exception:
                # Create the directory if it does not exist
                parts = xbox_video_dir.strip("/").split("/")
                current_path = ""
                for part in parts:
                    current_path += f"/{part}"
                    try:
                        ftp.cwd(current_path)
                    except Exception:
                        ftp.mkd(current_path)
                        ftp.cwd(current_path)

            xbox_video_path = f"{xbox_video_dir}bootanim.xmv"
            with open(local_video_path, 'rb') as file:
                ftp.storbinary(f'STOR {xbox_video_path}', file)

            ftp.quit()
            self.show_info("File transferred successfully!")
        except (Exception) as e:
            self.show_error(f"Failed to transfer file: {str(e)}")
        finally:
            self.player.play()  # Optionally resume playing the video after transfer is done

    def show_error(self, message):
        """Display an error message in a message box."""
        self.root.after(0, lambda: messagebox.showerror("Error", message))

    def show_info(self, message):
        """Display an info message in a message box."""
        self.root.after(0, lambda: messagebox.showinfo("Success", message))


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoApp(root)
    root.mainloop()
    

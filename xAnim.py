import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import vlc
import os 
from ftplib import FTP

class VideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("xAmin")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.button_frame = ttk.Frame(root, padding="10 10 10 10")
        self.button_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.load_button = ttk.Button(self.button_frame, text="Select Folder", command=self.load_videos)
        self.load_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.ftp_button = ttk.Button(self.button_frame, text="Transfer to Xbox", command=self.transfer_to_xbox)
        self.ftp_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.ip_label = ttk.Label(self.button_frame, text="Xbox IP:")
        self.ip_label.pack(side=tk.LEFT, padx=5)
        
        self.ip_entry = ttk.Entry(self.button_frame)
        self.ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Combobox for selecting the drive label
        self.drive_label_var = tk.StringVar(value="/C/")
        self.drive_label_combobox = ttk.Combobox(self.button_frame, textvariable=self.drive_label_var, state="readonly")
        self.drive_label_combobox['values'] = ("/C/", "/HDD0-C/")
        self.drive_label_combobox.pack(side=tk.LEFT, padx=5)
        self.drive_label_combobox.bind("<<ComboboxSelected>>", self.on_drive_or_mode_change)
        
        # Checkbox for Passive Mode
        self.passive_mode_var = tk.BooleanVar(value=True)
        self.passive_mode_checkbox = ttk.Checkbutton(self.button_frame, text="Use Passive Mode", variable=self.passive_mode_var, command=self.on_drive_or_mode_change)
        self.passive_mode_checkbox.pack(side=tk.LEFT, padx=5)
        
        self.listbox_frame = ttk.Frame(root, padding="10 10 10 10")
        self.listbox_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.listbox = tk.Listbox(self.listbox_frame, width=50, height=20)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        
        self.listbox.bind('<Double-1>', self.play_video)
        
        self.video_outer_frame = ttk.Frame(root, padding="10 10 10 10", relief="raised", borderwidth=5, style="Video.TFrame")
        self.video_outer_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.video_frame = ttk.Frame(self.video_outer_frame, width=800, height=450, style="InnerVideo.TFrame")
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        self.video_paths = {}  
        
        self.style.configure("Video.TFrame", background="#333333", relief="raised", borderwidth=5)
        self.style.configure("InnerVideo.TFrame", background="#000000")
    
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
        
        self.player.set_hwnd(self.video_frame.winfo_id())
        self.player.play()
    
    def transfer_to_xbox(self):
        # Check if an item is selected
        if not self.listbox.curselection():
            messagebox.showerror("Error", "Please select a video from the list.")
            return

        # Get the selected file from the listbox
        selected_file = self.listbox.get(self.listbox.curselection())
        local_video_path = self.video_paths[selected_file]
        
        self.player.stop()
        
        xbox_ip = self.ip_entry.get()
        
        if not xbox_ip:
            messagebox.showerror("Error", "Please enter the Xbox IP address.")
            return
        
        try:
            ftp = FTP(xbox_ip)
            ftp.login(user='xbox', passwd='xbox')
            
            # Set passive mode based on checkbox
            ftp.set_pasv(self.passive_mode_var.get())
            
            # Get the selected drive label
            ftp_path = self.drive_label_var.get()
            
            # Ensure the target directory exists
            xbox_video_dir = f"{ftp_path}BootAnims/XMV Player/"
            try:
                ftp.cwd(xbox_video_dir)
            except Exception:
                # If the directory does not exist, create it
                parts = xbox_video_dir.strip("/").split("/")
                current_path = ""
                for part in parts:
                    current_path += f"/{part}"
                    try:
                        ftp.cwd(current_path)
                    except Exception:
                        ftp.mkd(current_path)
                        ftp.cwd(current_path)
            
            # Transfer the video file
            xbox_video_path = f"{xbox_video_dir}bootanim.xmv"
            with open(local_video_path, 'rb') as file:
                ftp.storbinary(f'STOR {xbox_video_path}', file)
            
            ftp.quit()
            messagebox.showinfo("Success", "File transferred successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to transfer file: {e}")

    def on_drive_or_mode_change(self, event=None):
        # Save the current selection index
        selected_index = self.listbox.curselection()
        
        # Perform any actions needed on drive or mode change
        # ...

        # Restore the previous selection
        if selected_index:
            self.listbox.selection_set(selected_index)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoApp(root)
    root.mainloop()
    

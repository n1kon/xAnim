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
        selected_file = self.listbox.get(self.listbox.curselection())
        video_path = self.video_paths[selected_file]
        self.show_video(video_path)
    
    def show_video(self, video_path):
        media = self.instance.media_new(video_path)
        self.player.set_media(media)
        
        self.player.set_hwnd(self.video_frame.winfo_id())
        self.player.play()
    
    def transfer_to_xbox(self):
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
            
            file_name = os.path.basename(local_video_path).strip().replace('\n', '').replace('\r', '')
            xbox_video_path = f"/C/BootAnims/XMV Player/bootanim.xmv"
            
            with open(local_video_path, 'rb') as file:
                ftp.storbinary(f'STOR {xbox_video_path}', file)
            
            ftp.quit()
            messagebox.showinfo("Success", "File transferred successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to transfer file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoApp(root)
    root.mainloop()


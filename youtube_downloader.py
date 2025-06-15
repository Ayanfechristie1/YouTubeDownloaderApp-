"""
YouTube Downloader GUI Application
A Tkinter-based desktop application for downloading YouTube videos
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
from pathlib import Path
import urllib.parse
import time

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is required. Install it with: pip install yt-dlp")
    sys.exit(1)

from utils import validate_youtube_url, format_duration, format_file_size


class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configure style
        self.setup_styles()
        
        # Initialize variables
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.url_var = tk.StringVar()
        self.format_var = tk.StringVar(value="mp4")
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")
        
        # Video info variables
        self.video_title = tk.StringVar(value="No video selected")
        self.video_duration = tk.StringVar(value="")
        self.video_filesize = tk.StringVar(value="")
        
        # Download control
        self.is_downloading = False
        self.download_thread = None
        
        # Create GUI
        self.create_widgets()
        
    def setup_styles(self):
        """Configure ttk styles for better appearance"""
        style = ttk.Style()
        
        # Configure button styles
        style.configure("Action.TButton", padding=(10, 5))
        style.configure("Download.TButton", padding=(15, 8))
        
    def create_widgets(self):
        """Create and arrange all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # URL Input Section
        self.create_url_section(main_frame, row=0)
        
        # Video Info Section
        self.create_video_info_section(main_frame, row=1)
        
        # Format Selection Section
        self.create_format_section(main_frame, row=2)
        
        # Download Location Section
        self.create_location_section(main_frame, row=3)
        
        # Progress Section
        self.create_progress_section(main_frame, row=4)
        
        # Control Buttons Section
        self.create_control_section(main_frame, row=5)
        
        # Status Section
        self.create_status_section(main_frame, row=6)
        
    def create_url_section(self, parent, row):
        """Create URL input section"""
        url_frame = ttk.LabelFrame(parent, text="YouTube URL", padding="5")
        url_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        # URL Entry
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Arial", 10))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.url_entry.bind("<Return>", lambda e: self.fetch_video_info())
        
        # Fetch Info Button
        self.fetch_btn = ttk.Button(url_frame, text="Get Info", command=self.fetch_video_info, style="Action.TButton")
        self.fetch_btn.grid(row=0, column=1)
        
    def create_video_info_section(self, parent, row):
        """Create video information display section"""
        info_frame = ttk.LabelFrame(parent, text="Video Information", padding="5")
        info_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        # Title
        ttk.Label(info_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        title_label = ttk.Label(info_frame, textvariable=self.video_title, wraplength=400)
        title_label.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 2))
        
        # Duration
        ttk.Label(info_frame, text="Duration:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_frame, textvariable=self.video_duration).grid(row=1, column=1, sticky=tk.W, pady=(0, 2))
        
        # File Size (estimated)
        ttk.Label(info_frame, text="Est. Size:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_frame, textvariable=self.video_filesize).grid(row=2, column=1, sticky=tk.W)
        
    def create_format_section(self, parent, row):
        """Create format selection section"""
        format_frame = ttk.LabelFrame(parent, text="Download Format", padding="5")
        format_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Format options
        formats = [
            ("MP4 Video (720p)", "mp4_720"),
            ("MP4 Video (480p)", "mp4_480"),
            ("MP4 Video (Best Quality)", "mp4_best"),
            ("Audio Only (MP3)", "audio_mp3"),
            ("Audio Only (M4A)", "audio_m4a")
        ]
        
        for i, (text, value) in enumerate(formats):
            ttk.Radiobutton(format_frame, text=text, variable=self.format_var, 
                           value=value).grid(row=i//2, column=i%2, sticky=tk.W, padx=(0, 20), pady=2)
    
    def create_location_section(self, parent, row):
        """Create download location section"""
        location_frame = ttk.LabelFrame(parent, text="Download Location", padding="5")
        location_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        location_frame.columnconfigure(0, weight=1)
        
        # Path display
        path_label = ttk.Label(location_frame, textvariable=self.download_path, 
                              relief="sunken", background="white")
        path_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Browse button
        ttk.Button(location_frame, text="Browse", command=self.select_download_path,
                  style="Action.TButton").grid(row=0, column=1)
    
    def create_progress_section(self, parent, row):
        """Create progress display section"""
        progress_frame = ttk.LabelFrame(parent, text="Download Progress", padding="5")
        progress_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Progress percentage
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=0, column=1, padx=(5, 0))
    
    def create_control_section(self, parent, row):
        """Create control buttons section"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=0, columnspan=2, pady=(0, 10))
        
        # Download button
        self.download_btn = ttk.Button(control_frame, text="Download Video", 
                                      command=self.start_download, style="Download.TButton")
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button
        self.cancel_btn = ttk.Button(control_frame, text="Cancel", 
                                    command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(side=tk.LEFT)
    
    def create_status_section(self, parent, row):
        """Create status display section"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        # Status label
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                relief="sunken", padding="5")
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def fetch_video_info(self):
        """Fetch video information from YouTube URL"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a YouTube URL")
            return
        
        if not validate_youtube_url(url):
            messagebox.showerror("Error", "Invalid YouTube URL")
            return
        
        # Disable fetch button and show loading
        self.fetch_btn.config(state="disabled", text="Loading...")
        self.status_var.set("Fetching video information...")
        
        # Use threading to avoid UI freeze
        thread = threading.Thread(target=self._fetch_info_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _fetch_info_thread(self, url):
        """Thread function to fetch video info"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Update UI in main thread
                self.root.after(0, self._update_video_info, info)
                
        except Exception as e:
            error_msg = f"Failed to fetch video info: {str(e)}"
            self.root.after(0, self._show_error, error_msg)
        finally:
            # Re-enable fetch button
            self.root.after(0, self._reset_fetch_button)
    
    def _update_video_info(self, info):
        """Update video information in UI"""
        try:
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            
            self.video_title.set(title)
            self.video_duration.set(format_duration(duration))
            
            # Estimate file size based on format
            filesize = self._estimate_filesize(info)
            self.video_filesize.set(format_file_size(filesize))
            
            self.status_var.set("Video information loaded successfully")
            
        except Exception as e:
            self._show_error(f"Error updating video info: {str(e)}")
    
    def _estimate_filesize(self, info):
        """Estimate file size based on selected format"""
        try:
            formats = info.get('formats', [])
            format_type = self.format_var.get()
            
            if 'audio' in format_type:
                # Audio files are typically smaller
                duration = info.get('duration', 0)
                return duration * 128000 / 8  # Estimate for 128kbps
            else:
                # Video files - try to find matching format
                for fmt in formats:
                    if fmt.get('filesize'):
                        return fmt['filesize']
                
                # Fallback estimation
                duration = info.get('duration', 0)
                if '720' in format_type:
                    return duration * 1000000  # ~1MB per second for 720p
                elif '480' in format_type:
                    return duration * 500000   # ~0.5MB per second for 480p
                else:
                    return duration * 2000000  # ~2MB per second for best quality
        except:
            return 0
    
    def _reset_fetch_button(self):
        """Reset fetch button state"""
        self.fetch_btn.config(state="normal", text="Get Info")
    
    def _show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        self.status_var.set("Error occurred")
    
    def select_download_path(self):
        """Open directory selection dialog"""
        path = filedialog.askdirectory(initialdir=self.download_path.get())
        if path:
            self.download_path.set(path)
    
    def start_download(self):
        """Start video download"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a YouTube URL")
            return
        
        if not validate_youtube_url(url):
            messagebox.showerror("Error", "Invalid YouTube URL")
            return
        
        if not os.path.exists(self.download_path.get()):
            messagebox.showerror("Error", "Download path does not exist")
            return
        
        # Update UI for download state
        self.is_downloading = True
        self.download_btn.config(state="disabled", text="Downloading...")
        self.cancel_btn.config(state="normal")
        self.progress_var.set(0)
        self.status_var.set("Starting download...")
        
        # Start download thread
        self.download_thread = threading.Thread(target=self._download_thread, args=(url,))
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def _download_thread(self, url):
        """Thread function for downloading video"""
        try:
            # Configure yt-dlp options based on selected format
            ydl_opts = self._get_download_options()
            ydl_opts['progress_hooks'] = [self._progress_hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Download completed successfully
            self.root.after(0, self._download_complete)
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.root.after(0, self._download_error, error_msg)
    
    def _get_download_options(self):
        """Get yt-dlp download options based on selected format"""
        format_type = self.format_var.get()
        
        base_opts = {
            'outtmpl': os.path.join(self.download_path.get(), '%(title)s.%(ext)s'),
            'ignoreerrors': False,
        }
        
        if format_type == "mp4_720":
            base_opts['format'] = 'best[height<=720][ext=mp4]'
        elif format_type == "mp4_480":
            base_opts['format'] = 'best[height<=480][ext=mp4]'
        elif format_type == "mp4_best":
            base_opts['format'] = 'best[ext=mp4]'
        elif format_type == "audio_mp3":
            base_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif format_type == "audio_m4a":
            base_opts.update({
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }],
            })
        
        return base_opts
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if not self.is_downloading:
            return
        
        if d['status'] == 'downloading':
            try:
                # Calculate progress percentage
                if 'total_bytes' in d:
                    total = d['total_bytes']
                    downloaded = d['downloaded_bytes']
                    percent = (downloaded / total) * 100
                elif 'total_bytes_estimate' in d:
                    total = d['total_bytes_estimate']
                    downloaded = d['downloaded_bytes']
                    percent = (downloaded / total) * 100
                else:
                    percent = 0
                
                # Update progress in main thread
                self.root.after(0, self._update_progress, percent)
                
            except (KeyError, ZeroDivisionError, TypeError):
                pass
        
        elif d['status'] == 'finished':
            self.root.after(0, self._update_progress, 100)
    
    def _update_progress(self, percent):
        """Update progress bar and label"""
        self.progress_var.set(percent)
        self.progress_label.config(text=f"{percent:.1f}%")
        self.status_var.set(f"Downloading... {percent:.1f}%")
    
    def _download_complete(self):
        """Handle successful download completion"""
        self.is_downloading = False
        self.download_btn.config(state="normal", text="Download Video")
        self.cancel_btn.config(state="disabled")
        self.progress_var.set(100)
        self.progress_label.config(text="100%")
        self.status_var.set("Download completed successfully!")
        
        messagebox.showinfo("Success", "Video downloaded successfully!")
    
    def _download_error(self, error_msg):
        """Handle download error"""
        self.is_downloading = False
        self.download_btn.config(state="normal", text="Download Video")
        self.cancel_btn.config(state="disabled")
        self.status_var.set("Download failed")
        
        messagebox.showerror("Download Error", error_msg)
    
    def cancel_download(self):
        """Cancel ongoing download"""
        if self.is_downloading:
            self.is_downloading = False
            self.download_btn.config(state="normal", text="Download Video")
            self.cancel_btn.config(state="disabled")
            self.progress_var.set(0)
            self.progress_label.config(text="0%")
            self.status_var.set("Download cancelled")
            
            messagebox.showinfo("Cancelled", "Download has been cancelled")

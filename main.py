#!/usr/bin/env python3
"""
YouTube Downloader Desktop Application
Main entry point for the Tkinter GUI application
"""

import tkinter as tk
from youtube_downloader import YouTubeDownloaderApp

def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
  

if __name__ == "__main__":
    main()

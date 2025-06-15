"""
Utility functions for the YouTube Downloader application
"""

import urllib.parse
import re


def validate_youtube_url(url):
    """
    Validate if the given URL is a valid YouTube URL
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid YouTube URL, False otherwise
    """
    if not url:
        return False
    
    # YouTube URL patterns
    youtube_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(www\.)?youtube\.com/embed/[\w-]+',
        r'^https?://youtu\.be/[\w-]+',
        r'^https?://(www\.)?youtube\.com/v/[\w-]+',
        r'^https?://m\.youtube\.com/watch\?v=[\w-]+',
    ]
    
    # Check if URL matches any YouTube pattern
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    return False


def format_duration(seconds):
    """
    Format duration from seconds to human-readable format
    
    Args:
        seconds (int): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if not seconds or seconds <= 0:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_file_size(bytes_size):
    """
    Format file size from bytes to human-readable format
    
    Args:
        bytes_size (int): File size in bytes
        
    Returns:
        str: Formatted file size string
    """
    if not bytes_size or bytes_size <= 0:
        return "Unknown"
    
    # Size units
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_size)
    
    # Convert to appropriate unit
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    # Format with appropriate decimal places
    if unit_index == 0:  # Bytes
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def sanitize_filename(filename):
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return "untitled"
    
    # Remove invalid characters for file systems
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    return filename


def extract_video_id(url):
    """
    Extract video ID from YouTube URL
    
    Args:
        url (str): YouTube URL
        
    Returns:
        str: Video ID or None if not found
    """
    if not url:
        return None
    
    # Various YouTube URL patterns and their video ID extraction
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_safe_path(base_path, filename):
    """
    Get a safe file path, avoiding conflicts with existing files
    
    Args:
        base_path (str): Base directory path
        filename (str): Desired filename
        
    Returns:
        str: Safe file path
    """
    import os
    from pathlib import Path
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    full_path = Path(base_path) / safe_filename
    
    # If file doesn't exist, return as is
    if not full_path.exists():
        return str(full_path)
    
    # If file exists, add number suffix
    name_part = full_path.stem
    ext_part = full_path.suffix
    counter = 1
    
    while True:
        new_name = f"{name_part}_{counter}{ext_part}"
        new_path = full_path.parent / new_name
        
        if not new_path.exists():
            return str(new_path)
        
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 9999:
            break
    
    # Fallback
    return str(full_path.parent / f"{name_part}_final{ext_part}")


def validate_download_path(path):
    """
    Validate if the download path is valid and writable
    
    Args:
        path (str): Path to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    import os
    from pathlib import Path
    
    if not path:
        return False, "Path cannot be empty"
    
    try:
        path_obj = Path(path)
        
        # Check if path exists
        if not path_obj.exists():
            return False, "Path does not exist"
        
        # Check if it's a directory
        if not path_obj.is_dir():
            return False, "Path is not a directory"
        
        # Check if it's writable
        if not os.access(path, os.W_OK):
            return False, "Path is not writable"
        
        return True, ""
        
    except Exception as e:
        return False, f"Invalid path: {str(e)}"

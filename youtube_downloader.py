import os
import re
import subprocess
from typing import Optional, Tuple
from tqdm import tqdm

def is_youtube_url(url: str) -> bool:
    """Check if the provided string is a YouTube URL."""
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|shorts/|.+\?v=)?([^&=%\?]{11})'
    return bool(re.match(youtube_regex, url))

def normalize_youtube_url(url: str) -> str:
    """
    Normalize different YouTube URL formats to a standard watch URL.
    Handles regular videos, shorts, and mobile links.
    """
    # Extract video ID using regex
    patterns = [
        r'(?:v=|\/)([\w\-]{11})(?:\S+)?$',  # Regular and mobile URLs
        r'(?:shorts\/)([\w\-]{11})(?:\S+)?$',  # Shorts URLs
        r'^([\w\-]{11})$'  # Just the video ID
    ]
    
    video_id = None
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    
    if not video_id:
        return url  # Return original if no ID found
    
    # Return normalized URL
    return f"https://www.youtube.com/watch?v={video_id}"

def download_youtube_video(url: str, output_dir: str = "downloads", filename: Optional[str] = None,
                          resolution: str = "720p") -> Tuple[bool, str]:
    """
    Download a YouTube video at the specified resolution using yt-dlp.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save the downloaded video
        filename: Custom filename (without extension)
        resolution: Video resolution (e.g., '720p', '1080p')
        
    Returns:
        Tuple containing (success status, path to downloaded file or error message)
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Normalize YouTube URL
        normalized_url = normalize_youtube_url(url)
        print(f"Using normalized URL: {normalized_url}")
        
        # Set format based on resolution
        if resolution == "1080p":
            format_code = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best"
        elif resolution == "720p":
            format_code = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
        elif resolution == "480p":
            format_code = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best"
        elif resolution == "360p":
            format_code = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best"
        else:
            format_code = "best[ext=mp4]/best"
        
        # Set output filename template
        if filename:
            output_template = f"{output_dir}/{filename}.%(ext)s"
        else:
            # Use a more sanitized output template to avoid shell escaping issues
            output_template = f"{output_dir}/%(id)s.%(ext)s"
        
        # Construct yt-dlp command
        cmd = [
            "yt-dlp", 
            normalized_url,
            "--format", format_code,
            "--output", output_template,
            "--merge-output-format", "mp4",
            "--no-playlist",
            "--no-mtime",  # Don't use the media timestamp for the file
            "--restrict-filenames",  # Restrict filenames to ASCII characters
        ]
        
        # Run the download command
        print(f"Downloading video...")
        process = subprocess.run(cmd, text=True, capture_output=True)
        
        if process.returncode != 0:
            return False, f"yt-dlp error: {process.stderr}"
        
        # Find the last line that may contain the path
        output_file = None
        for line in reversed(process.stdout.split('\n')):
            if '[Merger] Merging formats into' in line:
                filename_match = re.search(r'\[Merger\] Merging formats into "(.*?)"', line)
                if filename_match:
                    output_file = filename_match.group(1)
                    break
            elif '[download] Destination:' in line:
                filename_match = re.search(r'\[download\] Destination: (.*?)$', line)
                if filename_match:
                    output_file = filename_match.group(1)
                    break
        
        if not output_file:
            # Try to get the video ID and search for it as a fallback
            video_id = None
            for pattern in [r'(?:v=)([\w\-]{11})', r'(?:shorts\/)([\w\-]{11})']:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    break
            
            if video_id:
                candidates = [f for f in os.listdir(output_dir) if video_id in f and f.endswith('.mp4')]
                if candidates:
                    output_file = os.path.join(output_dir, candidates[0])
                else:
                    # Final fallback: find the most recently created mp4 file in the output directory
                    mp4_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
                    if mp4_files:
                        mp4_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_dir, f)), reverse=True)
                        output_file = os.path.join(output_dir, mp4_files[0])
        
        if not output_file or not os.path.exists(output_file):
            return False, "Could not determine the downloaded file path"
        
        print(f"Download completed: {output_file}")
        return True, output_file
        
    except Exception as e:
        error_message = f"Error downloading video: {str(e)}"
        print(error_message)
        return False, error_message

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Download YouTube videos")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--output-dir", default="downloads", help="Output directory for downloaded videos")
    parser.add_argument("--filename", help="Custom filename (without extension)")
    parser.add_argument("--resolution", default="720p", help="Video resolution (e.g., '720p', '1080p')")
    
    args = parser.parse_args()
    
    success, result = download_youtube_video(
        args.url, 
        args.output_dir, 
        args.filename, 
        args.resolution
    )
    
    if success:
        print(f"Video downloaded successfully to: {result}")
    else:
        print(f"Failed to download video: {result}") 
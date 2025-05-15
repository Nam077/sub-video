# Sub-Video: Video/Audio Transcription with Subtitles

This project uses faster-whisper to generate subtitles for video and audio files. It supports multiple input formats, YouTube video downloads, and generates SRT subtitle files.

## Requirements

- Python 3.8+
- FFmpeg installed on your system
- CUDA-compatible GPU (optional, but recommended for faster processing)

## Installation

1. Install FFmpeg:
   - On macOS: `brew install ffmpeg`
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

2. Set up the virtual environment and install dependencies:

   **Using the setup script:**
   ```bash
   # Make the setup script executable
   chmod +x setup.sh
   
   # Run the setup script
   ./setup.sh
   ```

   **Manual setup:**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. Activate the virtual environment before running the script:
   ```bash
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   ```

## Usage

### Process Local Video/Audio Files

Basic usage:
```bash
python sub_video.py path/to/your/video.mp4
```

Advanced options:
```bash
python sub_video.py path/to/your/video.mp4 --output-dir subtitles --model large --language en
```

### Process YouTube Videos

You can directly provide a YouTube URL to download and transcribe the video:
```bash
python sub_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --model medium
```

YouTube-specific options:
```bash
python sub_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --resolution 1080p --keep-video
```

### Standalone YouTube Downloader

You can also use the YouTube downloader module separately:
```bash
python youtube_downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --output-dir downloads --resolution 720p
```

## Arguments

- `input`: Path to input video/audio file or YouTube URL (required)
- `--output-dir`: Output directory for subtitles (default: "subtitles")
- `--model`: Whisper model size (choices: tiny, base, small, medium, large, default: base)
- `--language`: Language code (e.g., 'en', 'vi'). If not specified, will auto-detect
- `--resolution`: Resolution for YouTube video downloads (e.g., '720p', '1080p', default: '720p')
- `--keep-video`: Keep downloaded YouTube videos after processing (by default, videos are deleted after subtitle generation)

### Supported Input Formats

- Video: .mp4, .avi, .mkv, .mov
- Audio: .wav, .mp3, .m4a, .flac
- YouTube: Any valid YouTube URL

## Output

The script generates an SRT subtitle file in the specified output directory. The filename will match the input filename with a .srt extension.

## Notes

- For better accuracy, use larger models (medium or large), but they require more processing power
- If you have a CUDA-compatible GPU, the script will automatically use it for faster processing
- The script automatically detects the language if not specified
- Always make sure the virtual environment is activated before running the script
- When processing YouTube videos, they are downloaded to the output directory and deleted after processing unless the `--keep-video` option is specified 
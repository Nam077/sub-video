#!/bin/bash

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: FFmpeg is not installed or not in PATH."
    echo "Please install FFmpeg before proceeding:"
    echo "  - macOS: brew install ffmpeg"
    echo "  - Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  - Windows: Download from https://ffmpeg.org/download.html"
    exit 1
fi

echo "✓ FFmpeg is installed"

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p subtitles
mkdir -p downloads

echo "✓ Setup completed!"
echo "To activate the virtual environment, run:"
echo "source venv/bin/activate"
echo ""
echo "Example usage:"
echo "python sub_video.py path/to/video.mp4"
echo "or"
echo "python sub_video.py https://www.youtube.com/watch?v=example" 
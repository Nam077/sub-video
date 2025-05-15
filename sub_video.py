import os
import argparse
import shutil
import time
import platform
import sys
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import ffmpeg
from faster_whisper import WhisperModel, download_model
from tqdm import tqdm
import json

# Import YouTube downloader
from youtube_downloader import download_youtube_video, normalize_youtube_url, is_youtube_url

# Định nghĩa thư mục lưu mô hình
MODEL_CACHE_DIR = os.path.expanduser("~/.cache/whisper-models")

# Định nghĩa màu cho ASS
ASS_COLORS = {
    "yellow": "&H00FFFF&",
    "white": "&HFFFFFF&",
    "blue": "&HFF0000&",
    "green": "&H00FF00&",
    "red": "&H0000FF&",
    "cyan": "&HFFFF00&",
    "magenta": "&HFF00FF&",
    "black": "&H000000&",
}

class ProgressTracker:
    """Theo dõi tiến trình của các bước xử lý."""
    def __init__(self, total_steps: int, verbose: bool = True):
        self.total_steps = total_steps
        self.current_step = 0
        self.verbose = verbose
        self.step_progress = None
        self.step_name = ""
        self.start_time = time.time()
        
    def start_step(self, step_name: str):
        """Bắt đầu một bước xử lý mới."""
        self.current_step += 1
        self.step_name = step_name
        if self.verbose:
            print(f"\n[{self.current_step}/{self.total_steps}] {step_name}...")
        self.step_start_time = time.time()
        
    def update_progress(self, current: int, total: int):
        """Cập nhật tiến trình của bước hiện tại."""
        if self.verbose:
            progress = int(current * 50 / total)
            sys.stdout.write(f"\r[{self.current_step}/{self.total_steps}] {self.step_name}: "
                            f"[{'#' * progress}{' ' * (50 - progress)}] {current}/{total} "
                            f"({current * 100 / total:.1f}%)")
            sys.stdout.flush()
    
    def finish_step(self):
        """Hoàn thành bước hiện tại."""
        elapsed = time.time() - self.step_start_time
        if self.verbose:
            print(f"\r[{self.current_step}/{self.total_steps}] {self.step_name}: Hoàn thành trong {elapsed:.2f}s")
    
    def finish(self):
        """Hoàn thành tất cả các bước."""
        total_elapsed = time.time() - self.start_time
        if self.verbose:
            print(f"\nHoàn thành tất cả {self.total_steps} bước trong {total_elapsed:.2f}s")

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename and replace spaces."""
    # Replace invalid filename characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove any non-ASCII characters
    filename = re.sub(r'[^\x00-\x7F]+', '_', filename)
    # Limit length
    return filename[:100] if len(filename) > 100 else filename

def extract_audio(video_path: str, output_path: str, progress: Optional[ProgressTracker] = None) -> None:
    """Extract audio from video file using ffmpeg."""
    try:
        if progress:
            progress.start_step(f"Trích xuất âm thanh từ {os.path.basename(video_path)}")
            
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(stream, output_path, acodec='pcm_s16le', ac=1, ar='16k')
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        if progress:
            progress.finish_step()
    except ffmpeg.Error as e:
        print(f"Lỗi khi trích xuất âm thanh: {e.stderr.decode()}")
        raise

def format_timestamp(seconds: float, format_type: str = "srt") -> str:
    """Format timestamp in seconds to different formats."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if format_type == "srt":
        # SRT format: HH:MM:SS,mmm
        milliseconds = int((secs - int(secs)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{milliseconds:03d}"
    elif format_type == "ass":
        # ASS format: H:MM:SS.cc
        centiseconds = int((secs - int(secs)) * 100)
        return f"{hours}:{minutes:02d}:{int(secs):02d}.{centiseconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{secs:.3f}"

def create_srt(segments, output_path: str) -> None:
    """Create SRT subtitle file from segments."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, start=1):
            start_time = format_timestamp(segment.start, "srt")
            end_time = format_timestamp(segment.end, "srt")
            text = segment.text.strip()
            f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

def create_ass(segments, output_path: str, title: str = "", karaoke: bool = True, 
               style: str = "Default", color: str = "white") -> None:
    """Create ASS subtitle file from segments with optional karaoke effect."""
    ass_color = ASS_COLORS.get(color.lower(), ASS_COLORS["white"])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write ASS header
        f.write("[Script Info]\n")
        f.write(f"Title: {title}\n")
        f.write("ScriptType: v4.00+\n")
        f.write("WrapStyle: 0\n")
        f.write("ScaledBorderAndShadow: yes\n")
        f.write("YCbCr Matrix: None\n")
        f.write("PlayResX: 1920\n")
        f.write("PlayResY: 1080\n\n")
        
        # Write styles
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
                "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
                "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        
        # Default style
        f.write(f"Style: Default,Arial,48,{ass_color},&HFFFFFF&,&H000000&,&H000000&,0,0,0,0,100,100,0,0,1,2,2,2,20,20,20,1\n")
        # Karaoke style
        f.write(f"Style: Karaoke,Arial,48,{ass_color},&HFFFFFF&,&H000000&,&H000000&,0,0,0,0,100,100,0,0,1,2,2,2,20,20,20,1\n\n")
        
        # Write events
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        
        # Write dialogue lines
        for i, segment in enumerate(segments, start=1):
            start_time = format_timestamp(segment.start, "ass")
            end_time = format_timestamp(segment.end, "ass")
            text = segment.text.strip()
            
            if karaoke and hasattr(segment, 'words') and segment.words:
                # Create karaoke effect if word timestamps are available
                words_text = ""
                last_end = segment.start
                
                for word in segment.words:
                    # Calculate timing for karaoke effect
                    word_duration = word.end - word.start
                    delay = word.start - last_end
                    
                    if delay > 0:
                        # Add delay before current word
                        words_text += f"{{\\k{int(delay * 100)}}} "
                    
                    # Add the word with karaoke timing
                    words_text += f"{{\\k{int(word_duration * 100)}}}{word.word} "
                    last_end = word.end
                
                f.write(f"Dialogue: 0,{start_time},{end_time},Karaoke,,0,0,0,,{words_text.strip()}\n")
            else:
                # Regular subtitle without karaoke effect
                f.write(f"Dialogue: 0,{start_time},{end_time},{style},,0,0,0,,{text}\n")

def detect_device_and_compute_type(requested_device: str = "auto", requested_compute: str = "auto") -> Tuple[str, str]:
    """Detect the best device and compute type for the current system."""
    import platform
    
    # Check for CUDA
    cuda_available = os.environ.get("CUDA_VISIBLE_DEVICES") is not None
    
    # Check for Apple Silicon
    is_mac = platform.system() == "Darwin"
    is_arm = platform.machine().startswith("arm")
    is_apple_silicon = is_mac and is_arm
    
    # Override with requested values if not auto
    if requested_device != "auto":
        device = requested_device
    else:
        device = "cuda" if cuda_available else "cpu"
    
    if requested_compute != "auto":
        compute_type = requested_compute
    else:
        if device == "cuda":
            compute_type = "float16"
        elif is_apple_silicon:
            compute_type = "int8"  # int8 is often faster on Apple Silicon
        else:
            compute_type = "int8"  # Default to int8 for better speed on CPU
    
    return device, compute_type

def get_memory_info() -> Dict[str, Any]:
    """Get system memory information."""
    import psutil
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percent": memory.percent
    }

def auto_select_model(memory_available: Optional[int] = None) -> str:
    """Automatically select the appropriate model size based on available memory."""
    if memory_available is None:
        try:
            memory_info = get_memory_info()
            memory_available = memory_info["available"]
        except:
            # If we can't get memory info, default to medium
            return "medium"
    
    # Model size requirements in bytes (approximate)
    model_sizes = {
        "large": 6 * 1024 * 1024 * 1024,  # ~6GB
        "medium": 2.5 * 1024 * 1024 * 1024,  # ~2.5GB
        "small": 1 * 1024 * 1024 * 1024,  # ~1GB
        "base": 500 * 1024 * 1024,  # ~500MB
        "tiny": 150 * 1024 * 1024,  # ~150MB
    }
    
    # Select the largest model that can fit in memory
    # We leave some headroom (use 70% of available memory)
    available_with_headroom = memory_available * 0.7
    
    for model, size in sorted(model_sizes.items(), key=lambda x: x[1], reverse=True):
        if size < available_with_headroom:
            return model
    
    # If all models are too large, return tiny
    return "tiny"

def is_model_cached(model_size: str) -> bool:
    """Kiểm tra xem model đã được tải về và lưu trong bộ nhớ cache chưa."""
    model_path = os.path.join(MODEL_CACHE_DIR, model_size)
    return os.path.exists(model_path) and os.path.isdir(model_path)

def ensure_model_cached(model_size: str, progress: ProgressTracker = None) -> None:
    """Đảm bảo model đã được tải về và lưu trong bộ nhớ cache."""
    if not is_model_cached(model_size):
        if progress:
            progress.start_step(f"Tải model {model_size} lần đầu tiên (sẽ được lưu vào cache)")
        
        # Tạo thư mục cache nếu chưa tồn tại
        os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
        
        # Tải model (sẽ được lưu trong thư mục cache)
        download_model(model_size, output_dir=MODEL_CACHE_DIR)
        
        if progress:
            progress.finish_step()
    else:
        print(f"Sử dụng model {model_size} từ cache")

def process_media(input_path: str, output_dir: str, model_size: str = "auto", language: Optional[str] = None,
                  resolution: str = "720p", keep_video: bool = True, subtitle_formats: List[str] = ["srt"],
                  karaoke: bool = False, device: str = "auto", compute_type: str = "auto",
                  verbose: bool = True, force_download: bool = False) -> None:
    """Process media file and generate subtitles."""
    # Determine total steps for progress tracking
    total_steps = 4  # Model load, download/extract, transcribe, generate subtitles
    if is_youtube_url(input_path):
        total_steps += 1  # Add download step
    
    progress = ProgressTracker(total_steps, verbose)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # If auto model selection, detect best model size
    if model_size == "auto":
        try:
            progress.start_step("Tự động lựa chọn model dựa trên bộ nhớ khả dụng")
            model_size = auto_select_model()
            progress.finish_step()
            print(f"Đã chọn model: {model_size}")
        except Exception as e:
            print(f"Không thể tự động chọn model: {str(e)}")
            model_size = "medium"  # Fall back to medium
    
    # Đảm bảo model đã được tải về và lưu trong cache
    if not force_download and is_model_cached(model_size):
        # Giảm tổng số bước vì không cần tải model
        progress.total_steps -= 1
        print(f"Model {model_size} đã được tải trước đó, sử dụng từ cache")
    else:
        ensure_model_cached(model_size, progress)
    
    # If input is a YouTube URL, download the video first
    downloaded_file = None
    if is_youtube_url(input_path):
        progress.start_step(f"Tải video từ YouTube")
        success, result = download_youtube_video(input_path, output_dir, resolution=resolution)
        progress.finish_step()
        
        if not success:
            print(f"Lỗi khi tải video YouTube: {result}")
            return
        
        # Set the input path to the downloaded video
        downloaded_file = result
        input_path = result
        print(f"Đã tải video thành công: {input_path}")
        
        # Create a sanitized copy of the file to avoid path issues
        video_name = Path(input_path).stem
        sanitized_name = sanitize_filename(video_name)
        sanitized_path = os.path.join(output_dir, f"{sanitized_name}.mp4")
        
        if input_path != sanitized_path:
            progress.start_step(f"Tạo bản sao với tên file hợp lệ")
            shutil.copy2(input_path, sanitized_path)
            input_path = sanitized_path
            progress.finish_step()
    
    # Get input file name without extension
    input_name = Path(input_path).stem
    sanitized_input_name = sanitize_filename(input_name)
    
    # Extract audio if input is video
    temp_audio = os.path.join(output_dir, f"{sanitized_input_name}_temp.wav")
    if input_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
        extract_audio(input_path, temp_audio, progress)
        audio_path = temp_audio
    else:
        audio_path = input_path
        progress.start_step("Sử dụng trực tiếp file âm thanh")
        progress.finish_step()

    # Detect the best device and compute type
    device, compute_type = detect_device_and_compute_type(device, compute_type)
    print(f"Đang sử dụng thiết bị: {device}, kiểu tính toán: {compute_type}")
    
    # Initialize Whisper model
    progress.start_step(f"Đang tải model Whisper ({model_size})")
    model = WhisperModel(model_size, device=device, compute_type=compute_type, download_root=MODEL_CACHE_DIR)
    progress.finish_step()

    # Transcribe audio
    progress.start_step("Đang chuyển đổi âm thanh thành văn bản")
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        word_timestamps=True if "ass" in subtitle_formats and karaoke else False,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    # Convert generator to list so we can iterate over it multiple times
    segments_list = list(segments)
    progress.finish_step()

    # Create subtitle files in requested formats
    progress.start_step(f"Đang tạo file phụ đề ({', '.join(subtitle_formats)})")
    
    for fmt in subtitle_formats:
        if fmt.lower() == "srt":
            srt_path = os.path.join(output_dir, f"{sanitized_input_name}.srt")
            create_srt(segments_list, srt_path)
            print(f"Đã tạo file SRT: {srt_path}")
            
        elif fmt.lower() == "ass":
            ass_path = os.path.join(output_dir, f"{sanitized_input_name}.ass")
            create_ass(segments_list, ass_path, title=input_name, karaoke=karaoke)
            print(f"Đã tạo file ASS{' với hiệu ứng karaoke' if karaoke else ''}: {ass_path}")
    
    progress.finish_step()
    
    # Clean up temporary audio file if it was created
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
        
    # Clean up downloaded video if not keeping it
    if downloaded_file and not keep_video:
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
            print(f"Đã xóa video đã tải: {downloaded_file}")
        
        # Also remove sanitized copy if it exists and is different
        if downloaded_file != input_path and os.path.exists(input_path):
            os.remove(input_path)
            print(f"Đã xóa bản sao: {input_path}")
    
    # Complete the process
    progress.finish()
    print(f"Phụ đề được tạo thành công")
    print(f"Ngôn ngữ phát hiện được: {info.language} (độ tin cậy: {info.language_probability:.2f})")

def main():
    parser = argparse.ArgumentParser(description="Tạo phụ đề cho video/audio bằng Whisper")
    parser.add_argument("input", help="Đường dẫn đến video/audio hoặc URL YouTube")
    parser.add_argument("--output-dir", default="subtitles", help="Thư mục lưu phụ đề")
    parser.add_argument("--model", default="auto", 
                      help="Kích thước model Whisper (tiny, base, small, medium, large, hoặc auto để tự động chọn)")
    parser.add_argument("--language", help="Mã ngôn ngữ (ví dụ: 'en', 'vi'). Nếu không chỉ định, sẽ tự động phát hiện")
    parser.add_argument("--resolution", default="720p", help="Độ phân giải video khi tải từ YouTube (ví dụ: '720p', '1080p')")
    parser.add_argument("--keep-video", action="store_true", default=True, help="Giữ lại video YouTube sau khi xử lý (mặc định)")
    parser.add_argument("--no-keep-video", action="store_false", dest="keep_video", help="Xóa video YouTube sau khi xử lý")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto",
                      help="Thiết bị để xử lý (auto sẽ tự động phát hiện)")
    parser.add_argument("--compute-type", choices=["auto", "float32", "float16", "int8"], default="auto",
                      help="Kiểu tính toán (auto sẽ tự động phát hiện)")
    parser.add_argument("--formats", default="srt", help="Định dạng phụ đề cần tạo, phân tách bằng dấu phẩy (srt,ass)")
    parser.add_argument("--karaoke", action="store_true", help="Tạo hiệu ứng karaoke trong file ASS")
    parser.add_argument("--verbose", action="store_true", default=True, help="Hiển thị thông tin chi tiết")
    parser.add_argument("--force-download", action="store_true", help="Buộc tải lại model ngay cả khi đã có trong cache")
    
    args = parser.parse_args()
    
    # Parse subtitle formats
    subtitle_formats = [fmt.strip().lower() for fmt in args.formats.split(",")]
    
    process_media(
        args.input, 
        args.output_dir, 
        args.model, 
        args.language, 
        args.resolution, 
        args.keep_video,
        subtitle_formats,
        args.karaoke,
        args.device,
        args.compute_type,
        args.verbose,
        args.force_download
    )

if __name__ == "__main__":
    main() 
# Sub-Video: Tạo phụ đề từ Video/Audio

Công cụ này sử dụng faster-whisper để tạo phụ đề cho video và audio. Hỗ trợ tải video từ YouTube và tạo phụ đề dạng SRT, ASS (với hiệu ứng karaoke).

## Yêu cầu hệ thống

- Python 3.8 trở lên
- FFmpeg đã cài đặt trong hệ thống
- GPU tương thích CUDA (tùy chọn, nhưng khuyến khích cho xử lý nhanh hơn)
- Mac M1/M2 được hỗ trợ tốt với tối ưu đặc biệt

## Cài đặt

1. Cài đặt FFmpeg:
   - Trên macOS: `brew install ffmpeg`
   - Trên Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - Trên Windows: Tải từ [trang web FFmpeg](https://ffmpeg.org/download.html)

2. Thiết lập môi trường ảo và cài đặt các thư viện:

   **Sử dụng script cài đặt:**
   ```bash
   # Cấp quyền thực thi cho script
   chmod +x setup.sh
   
   # Chạy script cài đặt
   ./setup.sh
   ```

   **Cài đặt thủ công:**
   ```bash
   # Tạo môi trường ảo
   python3 -m venv venv
   
   # Kích hoạt môi trường ảo
   source venv/bin/activate  # Trên Unix/macOS
   # hoặc
   .\venv\Scripts\activate  # Trên Windows
   
   # Cài đặt các thư viện
   pip install -r requirements.txt
   ```

3. Cấp quyền thực thi cho script tối ưu cho MacM1/M2 (nếu bạn dùng Mac):
   ```bash
   chmod +x run_on_m1.sh
   ```

## Cách sử dụng

### Sử dụng trên Mac M1/M2

```bash
./run_on_m1.sh URL_YOUTUBE_HOẶC_ĐƯỜNG_DẪN_VIDEO [model]
```

Ví dụ:
```bash
./run_on_m1.sh https://www.youtube.com/watch?v=dQw4w9WgXcQ
./run_on_m1.sh path/to/video.mp4 medium
```

### Sử dụng thông thường

Kích hoạt môi trường ảo trước khi chạy:
```bash
source venv/bin/activate  # Trên macOS/Linux
# hoặc
.\venv\Scripts\activate  # Trên Windows
```

Xử lý video/audio trong máy:
```bash
python sub_video.py path/to/video.mp4 --model medium --formats srt,ass --karaoke
```

Tải và xử lý video từ YouTube:
```bash
python sub_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --formats srt,ass --karaoke
```

### Tham số

- `input`: Đường dẫn đến file video/audio hoặc URL YouTube (bắt buộc)
- `--output-dir`: Thư mục lưu phụ đề (mặc định: "subtitles")
- `--model`: Kích thước model Whisper (tiny, base, small, medium, large, auto). Sử dụng "auto" để tự động chọn phù hợp với bộ nhớ của bạn.
- `--language`: Mã ngôn ngữ (ví dụ: 'en', 'vi'). Nếu không chỉ định, sẽ tự động phát hiện
- `--formats`: Định dạng phụ đề cần tạo, phân tách bằng dấu phẩy (srt,ass)
- `--karaoke`: Tạo hiệu ứng karaoke trong file ASS
- `--resolution`: Độ phân giải khi tải video từ YouTube (ví dụ: '720p', '1080p')
- `--keep-video`: Giữ lại video YouTube sau khi xử lý (mặc định là xóa sau khi tạo phụ đề)
- `--compute-type`: Kiểu tính toán (auto, float32, float16, int8). Nên dùng int8 cho MacM1/M2

### Các định dạng đầu vào hỗ trợ

- Video: .mp4, .avi, .mkv, .mov
- Audio: .wav, .mp3, .m4a, .flac
- YouTube: URL YouTube bất kỳ

## Kết quả

Script tạo ra file phụ đề trong thư mục chỉ định. Tên file sẽ giống với tên file đầu vào với phần mở rộng khác:
- File .srt: Phụ đề chuẩn, tương thích với hầu hết trình phát
- File .ass: Phụ đề nâng cao, hỗ trợ hiệu ứng karaoke (từng từ sáng lên theo thời gian)

## Lưu ý

- Model lớn hơn (medium, large) cho kết quả chính xác hơn nhưng yêu cầu nhiều tài nguyên hệ thống
- Nếu bạn có GPU tương thích CUDA, script sẽ tự động sử dụng
- Script tự động phát hiện ngôn ngữ nếu không được chỉ định
- Luôn đảm bảo môi trường ảo được kích hoạt trước khi chạy script
- Trên Mac M1/M2, sử dụng chế độ tính toán int8 sẽ nhanh hơn đáng kể 
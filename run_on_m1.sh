#!/bin/bash

# Script tối ưu để chạy sub-video trên Mac M1/M2
# Kích hoạt môi trường ảo
source venv/bin/activate

# Đặt biến môi trường để tránh các cảnh báo
export PYTHONIOENCODING=utf-8

# Tạo thư mục cache cho models nếu chưa tồn tại
CACHE_DIR="$HOME/.cache/whisper-models"
mkdir -p "$CACHE_DIR"

# Kiểm tra xem tham số đầu vào có được cung cấp không
if [ -z "$1" ]; then
    echo "Sử dụng: $0 <đường dẫn video hoặc URL YouTube> [model]"
    echo "Model mặc định là 'auto'. Các tùy chọn: tiny, base, small, medium, large, auto"
    exit 1
fi

# Kiểm tra xem tham số đầu vào có phải URL YouTube không
if [[ $1 == *youtube.com* ]] || [[ $1 == *youtu.be* ]]; then
    echo "Phát hiện URL YouTube: $1"
    
    # Chọn mô hình (tối ưu cho tốc độ và chất lượng trên M1)
    MODEL=${2:-"auto"}  # Sử dụng auto làm mặc định
    
    # Chạy với cài đặt tối ưu cho M1/M2
    python sub_video.py "$1" \
        --model $MODEL \
        --compute-type int8 \
        --formats "srt,ass" \
        --karaoke
else
    # Nếu là tệp cục bộ
    echo "Phát hiện tệp cục bộ: $1"
    
    # Chọn mô hình (tối ưu cho tốc độ và chất lượng trên M1)
    MODEL=${2:-"auto"}  # Sử dụng auto làm mặc định
    
    # Chạy với cài đặt tối ưu cho M1/M2
    python sub_video.py "$1" \
        --model $MODEL \
        --compute-type int8 \
        --formats "srt,ass" \
        --karaoke
fi

echo -e "\nCác file phụ đề được lưu trong thư mục 'subtitles'"
echo "Để xem các tùy chọn chi tiết hơn, chạy: python sub_video.py --help" 
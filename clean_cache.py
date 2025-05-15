#!/usr/bin/env python3
"""
Công cụ quản lý cache cho các model Whisper.
Cho phép xem, xóa từng model cụ thể hoặc toàn bộ cache.
"""

import os
import shutil
import argparse
import json
from pathlib import Path
import humanize

# Thư mục cache mặc định
DEFAULT_CACHE_DIR = os.path.expanduser("~/.cache/whisper-models")
MODEL_SIZES = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "distil-large-v3"]

def format_size(size_bytes):
    """Định dạng kích thước theo đơn vị dễ đọc (MB, GB)."""
    return humanize.naturalsize(size_bytes)

def get_directory_size(path):
    """Tính toán kích thước của thư mục."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if not os.path.islink(file_path):  # Bỏ qua các symbolic link
                total_size += os.path.getsize(file_path)
    return total_size

def list_cached_models(cache_dir=DEFAULT_CACHE_DIR):
    """Liệt kê tất cả các model đã cache và kích thước của chúng."""
    if not os.path.exists(cache_dir):
        print(f"Thư mục cache {cache_dir} không tồn tại.")
        return {}

    cached_models = {}
    
    for item in os.listdir(cache_dir):
        item_path = os.path.join(cache_dir, item)
        if os.path.isdir(item_path):
            # Kiểm tra xem đây có phải thư mục model hay không
            if os.path.exists(os.path.join(item_path, "model.bin")) or os.path.exists(os.path.join(item_path, "pytorch_model.bin")):
                size = get_directory_size(item_path)
                cached_models[item] = {
                    "path": item_path,
                    "size": size,
                    "size_format": format_size(size)
                }

    return cached_models

def remove_model(model_name, cache_dir=DEFAULT_CACHE_DIR, force=False):
    """Xóa một model cụ thể khỏi cache."""
    model_path = os.path.join(cache_dir, model_name)
    
    if not os.path.exists(model_path):
        print(f"Model '{model_name}' không tồn tại trong cache.")
        return False
    
    if not force:
        confirm = input(f"Bạn có chắc chắn muốn xóa model '{model_name}' ({format_size(get_directory_size(model_path))})? (y/N): ")
        if confirm.lower() != 'y':
            print("Hủy thao tác xóa.")
            return False
    
    try:
        shutil.rmtree(model_path)
        print(f"Đã xóa model '{model_name}' thành công.")
        return True
    except Exception as e:
        print(f"Lỗi khi xóa model '{model_name}': {str(e)}")
        return False

def clear_all_cache(cache_dir=DEFAULT_CACHE_DIR, force=False):
    """Xóa toàn bộ thư mục cache."""
    if not os.path.exists(cache_dir):
        print(f"Thư mục cache {cache_dir} không tồn tại.")
        return False
    
    if not force:
        confirm = input(f"Bạn có chắc chắn muốn xóa TOÀN BỘ cache ({format_size(get_directory_size(cache_dir))})? (y/N): ")
        if confirm.lower() != 'y':
            print("Hủy thao tác xóa.")
            return False
    
    try:
        # Xóa từng model trong thư mục cache
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"Đã xóa {item_path}")
            else:
                os.remove(item_path)
                print(f"Đã xóa file {item_path}")
        
        print(f"Đã xóa toàn bộ cache thành công.")
        return True
    except Exception as e:
        print(f"Lỗi khi xóa cache: {str(e)}")
        return False

def show_cache_info(cache_dir=DEFAULT_CACHE_DIR):
    """Hiển thị thông tin về cache."""
    if not os.path.exists(cache_dir):
        print(f"Thư mục cache {cache_dir} không tồn tại.")
        return
    
    cached_models = list_cached_models(cache_dir)
    
    if not cached_models:
        print("Không có model nào trong cache.")
        return
    
    print("\nCác model trong cache:")
    print("=" * 60)
    print(f"{'Tên Model':<20} {'Kích thước':<15} {'Đường dẫn':<25}")
    print("-" * 60)
    
    total_size = 0
    for model_name, info in cached_models.items():
        print(f"{model_name:<20} {info['size_format']:<15} {info['path']:<25}")
        total_size += info['size']
    
    print("-" * 60)
    print(f"Tổng cộng: {len(cached_models)} model, {format_size(total_size)}")
    print(f"Thư mục cache: {cache_dir}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Công cụ quản lý cache cho các model Whisper")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Đường dẫn đến thư mục cache (mặc định: ~/.cache/whisper-models)")
    
    subparsers = parser.add_subparsers(dest="command", help="Lệnh")
    
    # Lệnh info - hiển thị thông tin cache
    info_parser = subparsers.add_parser("info", help="Hiển thị thông tin về các model trong cache")
    
    # Lệnh remove - xóa một model cụ thể
    remove_parser = subparsers.add_parser("remove", help="Xóa một model cụ thể khỏi cache")
    remove_parser.add_argument("model", choices=MODEL_SIZES + ["other"], help="Tên model cần xóa hoặc 'other' để chỉ định model khác")
    remove_parser.add_argument("--custom-model", help="Tên model tùy chỉnh (khi chọn 'other')")
    remove_parser.add_argument("--force", "-f", action="store_true", help="Xóa mà không cần xác nhận")
    
    # Lệnh clear - xóa toàn bộ cache
    clear_parser = subparsers.add_parser("clear", help="Xóa toàn bộ cache")
    clear_parser.add_argument("--force", "-f", action="store_true", help="Xóa mà không cần xác nhận")
    
    args = parser.parse_args()
    
    # Nếu không có tham số, hiển thị thông tin cache
    if not args.command:
        show_cache_info(args.cache_dir)
        return
    
    # Xử lý các lệnh
    if args.command == "info":
        show_cache_info(args.cache_dir)
    
    elif args.command == "remove":
        model_name = args.model
        if model_name == "other" and args.custom_model:
            model_name = args.custom_model
        elif model_name == "other" and not args.custom_model:
            print("Lỗi: Bạn phải chỉ định tên model tùy chỉnh với --custom-model khi chọn 'other'")
            return
        
        remove_model(model_name, args.cache_dir, args.force)
    
    elif args.command == "clear":
        clear_all_cache(args.cache_dir, args.force)

if __name__ == "__main__":
    main() 
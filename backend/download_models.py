#!/usr/bin/env python3
import os
import sys
import urllib.request

MODELS = {
    "qwen2.5-7b-instruct-q4_k_m.gguf": "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
    "en_US-amy-medium.onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx",
    "en_US-amy-medium.onnx.json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"
}

def download_file(url, dest):
    if os.path.exists(dest):
        print(f"Already exists: {dest} (skipping)")
        return
    print(f"Downloading {url} to {dest}...")
    
    # Progress reporter
    def report(block_num, block_size, total_size):
        read = block_num * block_size
        if total_size > 0:
            percent = min(100.0, read * 100.0 / total_size)
            sys.stdout.write(f"\rProgress: {percent:.1f}% ({read // (1024*1024)}MB / {total_size // (1024*1024)}MB)")
        else:
            sys.stdout.write(f"\rDownloaded: {read // (1024*1024)}MB")
        sys.stdout.flush()

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest, reporthook=report)
        print("\nDownload complete!")
    except Exception as e:
        print(f"\nError downloading {url}: {e}")
        if os.path.exists(dest):
            try:
                os.remove(dest)
            except OSError:
                pass
        sys.exit(1)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")
    
    print("xEnglish Model Downloader")
    print(f"Target directory: {models_dir}\n")
    
    for filename, url in MODELS.items():
        dest_path = os.path.join(models_dir, filename)
        download_file(url, dest_path)
        
    print("\nAll models checked/downloaded successfully!")

if __name__ == "__main__":
    main()

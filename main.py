import os
import platform
from datetime import datetime
from PIL import Image # type: ignore
import pillow_heif

# Hachoir components for decoding video metadata streams securely
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

# Register the HEIC decoder so Pillow can read iPhone photos
pillow_heif.register_heif_opener()

target_dir = 'C:/Users/thoma/Main/FileName2Date/photos'

def get_file_directories(target_dir):
    file_paths = []
    for item in os.listdir(target_dir):
        full_path = os.path.join(target_dir, item)
        if os.path.isfile(full_path):
            file_paths.append(full_path)
    return file_paths

def clean_and_format_date(date_str):
    """Standardizes varying date outputs down to: YYYY-MM-DD_HHMMSS"""
    cleaned = date_str.replace("-", ":").replace("_", " ").strip()
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d_%H%M%S")
        except ValueError:
            continue
    return date_str.replace(":", "-").replace(" ", "_")

def get_video_media_created(path):
    """Attempts to read internal binary metadata of video containers."""
    try:
        parser = createParser(path)
        if not parser:
            return None
        with parser:
            metadata = extractMetadata(parser)
            if metadata and metadata.has('creation_date'):
                creation_date = metadata.get('creation_date')
                if isinstance(creation_date, datetime):
                    return creation_date.strftime("%Y-%m-%d_%H%M%S")
    except Exception:
        pass
    return None

def get_best_image_date(path):
    # 1. Image Check: EXIF
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if exif:
                date_taken = exif.get(36867) or exif.get(306)
                if date_taken and str(date_taken).strip():
                    return clean_and_format_date(str(date_taken))
    except Exception:
        pass  

    # 2. Video Check: Media Created
    video_date = get_video_media_created(path)
    if video_date:
        return video_date

    # 3. Fallback: OS File Date
    try:
        if platform.system() == "Windows":
            timestamp = os.path.getctime(path)
        else:
            timestamp = os.path.getmtime(path)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d_%H%M%S")
    except OSError:
        return None

def extract_dates(file_paths):
    file_dates = {}
    for path in file_paths:
        date = get_best_image_date(path)
        if date:
            file_dates[path] = date
        else:
            # 4. Final Safety Net: Original name without extension
            base_name = os.path.basename(path)
            name_without_ext, _ = os.path.splitext(base_name)
            file_dates[path] = name_without_ext
    return file_dates

def rename_files_to_date(target_directory):
    """
    Gathers all files in the directory, determines their best date string,
    and safely renames them, protecting against name collisions.
    """
    print("Scanning directory and extracting metadata...")
    paths = get_file_directories(target_directory)
    path_to_date_mapping = extract_dates(paths)
    
    success_count = 0
    
    print("\nStarting the renaming process...")
    for old_path, target_name in path_to_date_mapping.items():
        # Keep the original file extension (e.g., '.heic', '.mp4')
        _, ext = os.path.splitext(old_path)
        ext = ext.lower() 
        
        # Build the initial proposed new path
        new_path = os.path.join(target_directory, f"{target_name}{ext}")
        
        # Anti-collision system: If the name already exists, append a counter
        counter = 1
        while os.path.exists(new_path):
            # If the file is already named exactly what it should be, skip it
            if old_path == new_path:
                break
                
            new_path = os.path.join(target_directory, f"{target_name}-{counter}{ext}")
            counter += 1
            
        # Execute the rename if the path actually changed
        if old_path != new_path:
            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                success_count += 1
            except Exception as e:
                print(f"Error renaming {os.path.basename(old_path)}: {e}")
        else:
            print(f"Skipped (Already correctly named): {os.path.basename(old_path)}")

    print(f"\nDone! Successfully renamed {success_count} files.")

# Execute the master function
if __name__ == "__main__":
    rename_files_to_date(target_dir)
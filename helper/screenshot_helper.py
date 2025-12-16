#(©) Codeflix_Bots - Screenshot Helper

import asyncio
import os
import shutil
import tempfile
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Global variable to store found FFmpeg path
FFMPEG_PATH = None
FFPROBE_PATH = None


def get_ffmpeg_path() -> str:
    """Get the FFmpeg executable path."""
    global FFMPEG_PATH
    import glob
    
    # Check if we found it before
    if FFMPEG_PATH:
        return FFMPEG_PATH
    
    # Try shutil.which first
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        FFMPEG_PATH = ffmpeg_path
        return ffmpeg_path
    
    # Check WinGet Packages folder on Windows (where winget installs apps)
    user_profile = os.environ.get('LOCALAPPDATA', '')
    if user_profile:
        # Search in WinGet Packages folder
        pattern = os.path.join(user_profile, 'Microsoft', 'WinGet', 'Packages', '*ffmpeg*', '*', 'bin', 'ffmpeg.exe')
        matches = glob.glob(pattern)
        if matches:
            FFMPEG_PATH = matches[0]
            logger.info(f"Found FFmpeg in WinGet Packages: {FFMPEG_PATH}")
            return matches[0]
        
        # Also check WinGet Links folder
        winget_link = os.path.join(user_profile, 'Microsoft', 'WinGet', 'Links', 'ffmpeg.exe')
        if os.path.exists(winget_link):
            FFMPEG_PATH = winget_link
            return winget_link
    
    # Try common Windows installation paths
    common_paths = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            FFMPEG_PATH = path
            return path
    
    return 'ffmpeg'  # Default fallback


def get_ffprobe_path() -> str:
    """Get the FFprobe executable path."""
    global FFPROBE_PATH
    import glob
    
    # Check if we found it before
    if FFPROBE_PATH:
        return FFPROBE_PATH
    
    # Try shutil.which first
    ffprobe_path = shutil.which('ffprobe')
    if ffprobe_path:
        FFPROBE_PATH = ffprobe_path
        return ffprobe_path
    
    # Check WinGet Packages folder on Windows (where winget installs apps)
    user_profile = os.environ.get('LOCALAPPDATA', '')
    if user_profile:
        # Search in WinGet Packages folder
        pattern = os.path.join(user_profile, 'Microsoft', 'WinGet', 'Packages', '*ffmpeg*', '*', 'bin', 'ffprobe.exe')
        matches = glob.glob(pattern)
        if matches:
            FFPROBE_PATH = matches[0]
            logger.info(f"Found FFprobe in WinGet Packages: {FFPROBE_PATH}")
            return matches[0]
        
        # Also check WinGet Links folder
        winget_link = os.path.join(user_profile, 'Microsoft', 'WinGet', 'Links', 'ffprobe.exe')
        if os.path.exists(winget_link):
            FFPROBE_PATH = winget_link
            return winget_link
    
    # Try common Windows installation paths
    common_paths = [
        r'C:\ffmpeg\bin\ffprobe.exe',
        r'C:\Program Files\ffmpeg\bin\ffprobe.exe',
        r'C:\Program Files (x86)\ffmpeg\bin\ffprobe.exe',
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            FFPROBE_PATH = path
            return path
    
    return 'ffprobe'  # Default fallback


async def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and available.
    
    Returns:
        True if FFmpeg is available, False otherwise
    """
    import subprocess
    
    ffmpeg_path = get_ffmpeg_path()
    logger.info(f"Checking FFmpeg at: {ffmpeg_path}")
    
    # Check if file exists first
    if ffmpeg_path != 'ffmpeg' and not os.path.exists(ffmpeg_path):
        logger.warning(f"FFmpeg path does not exist: {ffmpeg_path}")
        return False
    
    try:
        # Use subprocess.run instead of asyncio for more reliable Windows support
        result = subprocess.run(
            [ffmpeg_path, '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"FFmpeg found and working at: {ffmpeg_path}")
            return True
        else:
            logger.warning(f"FFmpeg returned error code: {result.returncode}")
    except FileNotFoundError:
        logger.warning(f"FFmpeg not found at: {ffmpeg_path}")
    except subprocess.TimeoutExpired:
        logger.warning(f"FFmpeg check timed out at: {ffmpeg_path}")
    except Exception as e:
        logger.warning(f"FFmpeg check error: {type(e).__name__}: {e}")
    
    return False


async def get_video_duration(video_path: str) -> Optional[float]:
    """
    Get video duration in seconds using FFprobe.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Duration in seconds or None if failed
    """
    import subprocess
    
    try:
        ffprobe_cmd = get_ffprobe_path()
        logger.info(f"Using FFprobe at: {ffprobe_cmd}")
        logger.info(f"Video path: {video_path}")
        
        # Check if video file exists
        if not os.path.exists(video_path):
            logger.error(f"Video file does not exist: {video_path}")
            return None
        
        cmd = [
            ffprobe_cmd,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        # Use subprocess.run for better Windows compatibility
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout.decode().strip()
            if output:
                duration = float(output)
                logger.info(f"Video duration: {duration}s")
                return duration
            else:
                logger.error("FFprobe returned empty output")
                return None
        else:
            logger.error(f"FFprobe error (return code {result.returncode}): {result.stderr.decode()}")
            return None
    except subprocess.TimeoutExpired:
        logger.error("FFprobe timed out")
        return None
    except ValueError as e:
        logger.error(f"Error parsing duration: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting video duration: {type(e).__name__}: {e}")
        return None


async def extract_screenshots(
    video_path: str, 
    num_screenshots: int = 4,
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Extract screenshots from a video at equidistant timestamps.
    
    Args:
        video_path: Path to the video file
        num_screenshots: Number of screenshots to extract (default: 4)
        output_dir: Directory to save screenshots (uses temp dir if None)
        
    Returns:
        List of paths to extracted screenshot images
    """
    screenshot_paths = []
    
    try:
        # Get video duration
        duration = await get_video_duration(video_path)
        if duration is None or duration <= 0:
            logger.error("Could not determine video duration")
            return []
        
        # Create output directory if not provided
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="screenshots_")
        
        # Calculate timestamps for equidistant screenshots
        # Skip first and last 5% to avoid black frames
        start_offset = duration * 0.05
        end_offset = duration * 0.95
        usable_duration = end_offset - start_offset
        
        if usable_duration <= 0:
            # For very short videos, just take middle frame
            timestamps = [duration / 2]
        else:
            interval = usable_duration / (num_screenshots + 1)
            timestamps = [start_offset + interval * (i + 1) for i in range(num_screenshots)]
        
        ffmpeg_cmd = get_ffmpeg_path()
        logger.info(f"Using FFmpeg at: {ffmpeg_cmd}")
        logger.info(f"Extracting {len(timestamps)} screenshots from video")
        
        import subprocess
        
        # Extract screenshots at each timestamp
        for i, timestamp in enumerate(timestamps):
            output_path = os.path.join(output_dir, f"screenshot_{i+1}.jpg")
            
            cmd = [
                ffmpeg_cmd,
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',  # High quality JPEG
                '-y',  # Overwrite output file
                output_path
            ]
            
            logger.info(f"Extracting screenshot {i+1} at {timestamp:.2f}s")
            
            try:
                # Use subprocess.run for better Windows compatibility
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60
                )
                
                if result.returncode == 0 and os.path.exists(output_path):
                    screenshot_paths.append(output_path)
                    logger.info(f"✓ Extracted screenshot {i+1} successfully")
                else:
                    logger.error(f"Failed to extract screenshot at {timestamp}s")
                    logger.error(f"Return code: {result.returncode}")
                    logger.error(f"Error: {result.stderr.decode()}")
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout extracting screenshot {i+1}")
            except Exception as e:
                logger.error(f"Exception extracting screenshot {i+1}: {type(e).__name__}: {e}")
        
        return screenshot_paths
        
    except Exception as e:
        logger.error(f"Error extracting screenshots: {e}")
        return screenshot_paths


def cleanup_temp_files(file_paths: List[str]) -> None:
    """
    Remove temporary files and their parent directories if empty.
    
    Args:
        file_paths: List of file paths to remove
    """
    dirs_to_check = set()
    
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                dirs_to_check.add(os.path.dirname(file_path))
                os.remove(file_path)
                logger.info(f"Removed temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not remove temp file {file_path}: {e}")
    
    # Try to remove empty directories
    for dir_path in dirs_to_check:
        try:
            if os.path.isdir(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)
                logger.info(f"Removed empty temp dir: {dir_path}")
        except Exception as e:
            logger.warning(f"Could not remove temp dir {dir_path}: {e}")

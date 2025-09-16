import yt_dlp
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime
import time
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TikTokDownloader:
    def __init__(self, output_dir: str = "downloads"):
        """
        Initialize TikTok video downloader
        
        Args:
            output_dir: Directory to save downloaded videos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configure yt-dlp options for TikTok
        self.ydl_opts = {
            'format': 'best[ext=mp4]',  # Download best quality mp4
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'writeinfojson': True,  # Save metadata
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': True,  # Continue on errors
            'no_warnings': False,
            'extractaudio': False,
            'audioformat': 'mp3',
            'audioquality': '192K',
        }
    
    def download_video(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Download a single TikTok video with retry logic
        
        Args:
            url: TikTok video URL
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with download information or None if failed
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Add random delay between retries to avoid rate limiting
                if attempt > 0:
                    delay = random.uniform(1, 3) * attempt
                    logger.info(f"Retrying {url} (attempt {attempt + 1}/{max_retries}) after {delay:.1f}s delay...")
                    time.sleep(delay)
                
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    # Extract video information
                    info = ydl.extract_info(url, download=True)
                    
                    # Construct the expected filename
                    filename = ydl.prepare_filename(info)
                    
                    # Format upload date properly
                    upload_date_raw = info.get('upload_date', '')
                    upload_date_formatted = 'Unknown'
                    upload_date_iso = None
                    
                    if upload_date_raw and upload_date_raw != 'Unknown':
                        try:
                            # yt-dlp returns date in YYYYMMDD format
                            if len(upload_date_raw) == 8:
                                date_obj = datetime.strptime(upload_date_raw, '%Y%m%d')
                                upload_date_formatted = date_obj.strftime('%Y-%m-%d')
                                upload_date_iso = date_obj.isoformat()
                            else:
                                upload_date_formatted = upload_date_raw
                        except ValueError:
                            upload_date_formatted = upload_date_raw
                    
                    logger.info(f"Successfully downloaded: {info.get('title', 'Unknown')}")
                    return {
                        'url': url,
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'filename': filename,
                        'uploader': info.get('uploader', 'Unknown'),
                        'uploader_id': info.get('uploader_id', 'Unknown'),
                        'upload_date': upload_date_raw,
                        'upload_date_formatted': upload_date_formatted,
                        'upload_date_iso': upload_date_iso,
                        'view_count': info.get('view_count', 0),
                        'like_count': info.get('like_count', 0),
                        'comment_count': info.get('comment_count', 0),
                        'description': info.get('description', ''),
                        'thumbnail': info.get('thumbnail', ''),
                        'webpage_url': info.get('webpage_url', url),
                        'success': True,
                        'attempts': attempt + 1
                    }
                    
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Categorize errors for better user feedback
                if 'unable to extract webpage video data' in error_msg:
                    error_type = "TikTok blocked extraction - video may be private or region-locked"
                elif 'video unavailable' in error_msg:
                    error_type = "Video is unavailable or has been deleted"
                elif 'private video' in error_msg:
                    error_type = "Video is private and cannot be accessed"
                elif 'network' in error_msg or 'connection' in error_msg:
                    error_type = "Network connection error"
                elif 'rate limit' in error_msg or 'too many requests' in error_msg:
                    error_type = "Rate limited - too many requests"
                else:
                    error_type = "Unknown extraction error"
                
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {error_type}")
                
                # Don't retry for certain error types
                if any(keyword in error_msg for keyword in ['private video', 'video unavailable', 'deleted']):
                    logger.error(f"Permanent error for {url}: {error_type}")
                    break
        
        # All retries failed
        logger.error(f"Failed to download {url} after {max_retries} attempts: {str(last_error)}")
        return {
            'url': url,
            'error': str(last_error),
            'error_type': error_type if 'error_type' in locals() else 'Unknown error',
            'success': False,
            'attempts': max_retries
        }
    
    def download_bulk(self, urls: List[str]) -> List[Dict]:
        """
        Download multiple TikTok videos
        
        Args:
            urls: List of TikTok video URLs
            
        Returns:
            List of download results
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Downloading video {i}/{len(urls)}: {url}")
            result = self.download_video(url.strip())
            if result:
                results.append(result)
            else:
                results.append({
                    'url': url,
                    'error': 'Download failed',
                    'success': False
                })
        
        return results
    
    def get_video_info(self, url: str, max_retries: int = 2) -> Optional[Dict]:
        """
        Get video information without downloading (with retry logic)
        
        Args:
            url: TikTok video URL
            max_retries: Maximum number of retry attempts
            
        Returns:
            Video information dictionary
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = random.uniform(0.5, 1.5) * attempt
                    logger.info(f"Retrying info extraction for {url} (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info
                    
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Don't retry for permanent errors
                if any(keyword in error_msg for keyword in ['private video', 'video unavailable', 'deleted']):
                    logger.error(f"Permanent error extracting info for {url}: {str(e)}")
                    break
                    
                logger.warning(f"Info extraction attempt {attempt + 1}/{max_retries} failed for {url}: {str(e)}")
        
        logger.error(f"Failed to extract info for {url} after {max_retries} attempts: {str(last_error)}")
        return None
    
    def cleanup_downloads(self):
        """Clean up downloaded files"""
        try:
            for file in self.output_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info("Cleaned up download directory")
        except Exception as e:
            logger.error(f"Error cleaning up: {str(e)}")

def validate_tiktok_url(url: str) -> bool:
    """
    Validate if URL is a valid TikTok URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid TikTok URL
    """
    tiktok_domains = ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']
    return any(domain in url.lower() for domain in tiktok_domains)

def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract TikTok URLs from text
    
    Args:
        text: Text containing URLs
        
    Returns:
        List of valid TikTok URLs
    """
    import re
    
    # Pattern to match TikTok URLs
    pattern = r'https?://(?:www\.)?(?:vm\.)?(?:vt\.)?tiktok\.com/[^\s]+'
    urls = re.findall(pattern, text)
    
    # Validate each URL
    valid_urls = [url for url in urls if validate_tiktok_url(url)]
    
    return valid_urls
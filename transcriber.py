import whisper
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import logging
import ffmpeg
import torch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoTranscriber:
    def __init__(self, model_size: str = "base"):
        """
        Initialize video transcriber with Whisper model
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self.temp_dir = Path(tempfile.gettempdir()) / "tiktok_transcriber"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def extract_audio(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file or None if failed
        """
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return None
            
            # Create audio output path
            audio_path = self.temp_dir / f"{video_path.stem}.wav"
            
            # Extract audio using ffmpeg
            (
                ffmpeg
                .input(str(video_path))
                .output(str(audio_path), acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run(quiet=True)
            )
            
            logger.info(f"Audio extracted to: {audio_path}")
            return str(audio_path)
            
        except Exception as e:
            logger.error(f"Error extracting audio from {video_path}: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_path: str, language: str = None) -> Optional[Dict]:
        """
        Transcribe audio file using Whisper
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional, auto-detect if None)
            
        Returns:
            Transcription result dictionary
        """
        try:
            if not self.model:
                logger.error("Model not loaded")
                return None
            
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_path,
                language=language,
                verbose=False
            )
            
            # Extract segments with timestamps
            segments = []
            for segment in result.get('segments', []):
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip()
                })
            
            transcription_result = {
                'text': result['text'].strip(),
                'language': result.get('language', 'unknown'),
                'segments': segments,
                'duration': segments[-1]['end'] if segments else 0
            }
            
            logger.info("Transcription completed successfully")
            return transcription_result
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_path}: {str(e)}")
            return None
    
    def transcribe_video(self, video_path: str, language: str = None) -> Optional[Dict]:
        """
        Transcribe video file (extract audio + transcribe)
        
        Args:
            video_path: Path to video file
            language: Language code (optional)
            
        Returns:
            Transcription result dictionary
        """
        try:
            # Extract audio
            audio_path = self.extract_audio(video_path)
            if not audio_path:
                return None
            
            # Transcribe audio
            result = self.transcribe_audio(audio_path, language)
            
            # Clean up temporary audio file
            try:
                os.unlink(audio_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing video {video_path}: {str(e)}")
            return None
    
    def transcribe_bulk_videos(self, video_files: List[str], language: str = None) -> List[Dict]:
        """
        Transcribe multiple video files
        
        Args:
            video_files: List of video file paths
            language: Language code (optional)
            
        Returns:
            List of transcription results
        """
        results = []
        
        for i, video_path in enumerate(video_files, 1):
            logger.info(f"Transcribing video {i}/{len(video_files)}: {Path(video_path).name}")
            
            result = self.transcribe_video(video_path, language)
            
            if result:
                result['video_path'] = video_path
                result['video_name'] = Path(video_path).name
                result['success'] = True
            else:
                result = {
                    'video_path': video_path,
                    'video_name': Path(video_path).name,
                    'error': 'Transcription failed',
                    'success': False
                }
            
            results.append(result)
        
        return results
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large"]
    
    def change_model(self, model_size: str):
        """Change Whisper model"""
        if model_size in self.get_available_models():
            self.model_size = model_size
            self._load_model()
        else:
            raise ValueError(f"Invalid model size: {model_size}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            for file in self.temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")

def format_timestamp(seconds: float) -> str:
    """
    Format seconds to MM:SS format
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def export_transcription_to_srt(transcription: Dict, output_path: str):
    """
    Export transcription to SRT subtitle format
    
    Args:
        transcription: Transcription result dictionary
        output_path: Output SRT file path
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(transcription.get('segments', []), 1):
                start_time = format_timestamp(segment['start'])
                end_time = format_timestamp(segment['end'])
                text = segment['text'].strip()
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        
        logger.info(f"SRT file exported to: {output_path}")
    except Exception as e:
        logger.error(f"Error exporting SRT: {str(e)}")

def get_system_info() -> Dict:
    """Get system information for optimal model selection"""
    return {
        'cuda_available': torch.cuda.is_available(),
        'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
        'device_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'
    }
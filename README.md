# 🎵 TikTok Video Transcriber

A powerful web application for bulk transcribing TikTok videos using free AI models. Built with Streamlit, yt-dlp, and OpenAI Whisper.

## ✨ Features

- **Bulk Processing**: Transcribe multiple TikTok videos at once
- **Free AI Models**: Uses OpenAI Whisper (completely free)
- **Multiple Input Methods**: Paste URLs or upload text files
- **Language Support**: Auto-detection or manual language selection
- **Export Options**: CSV, JSON, and SRT subtitle files
- **Progress Tracking**: Real-time progress updates
- **Modern UI**: Beautiful and intuitive web interface

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- FFmpeg (for audio processing)

### Installation

1. **Clone or download this repository**
   ```bash
   cd understanding-video
   ```

2. **Install FFmpeg** (required for audio processing)
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```
   
   **Windows:**
   Download from https://ffmpeg.org/download.html

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** and go to `http://localhost:8501`

## 📖 Usage

### Step 1: Configure Settings
- Choose Whisper model size (tiny/base/small/medium/large)
- Select language (auto-detect or specific language)
- Check system info (GPU availability)

### Step 2: Input TikTok URLs
- **Method 1**: Paste URLs directly (one per line)
- **Method 2**: Upload a text file containing URLs

### Step 3: Process Videos
- Click "Start Processing" to begin
- Watch real-time progress updates
- Wait for completion

### Step 4: View Results
- Check transcription results in the Results tab
- View video metadata and transcriptions
- See timestamped segments

### Step 5: Export Data
- Export as CSV for spreadsheet analysis
- Export as JSON for programmatic use
- Download SRT subtitle files

## 🎛️ Model Selection Guide

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | ~39 MB | Fastest | Basic | Quick testing |
| base | ~74 MB | Fast | Good | **Recommended** |
| small | ~244 MB | Medium | Better | Higher accuracy needed |
| medium | ~769 MB | Slow | High | Professional use |
| large | ~1550 MB | Slowest | Best | Maximum accuracy |

## 🔧 Technical Details

### Components

1. **video_downloader.py**: TikTok video downloading using yt-dlp
2. **transcriber.py**: Audio extraction and transcription using Whisper
3. **app.py**: Streamlit web interface

### Supported URLs

- `https://www.tiktok.com/@username/video/123456789`
- `https://vm.tiktok.com/abcdef`
- `https://vt.tiktok.com/abcdef`

### Output Formats

- **CSV**: Spreadsheet with video metadata and transcriptions
- **JSON**: Structured data with full details
- **SRT**: Subtitle files with timestamps

## 🛠️ Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Install FFmpeg using the instructions above
   - Ensure it's in your system PATH

2. **CUDA/GPU issues**
   - The app works on CPU (slower but functional)
   - For GPU acceleration, install PyTorch with CUDA support

3. **Download failures**
   - Some TikTok videos may be private or restricted
   - Check if URLs are valid and accessible

4. **Memory issues**
   - Use smaller Whisper models (tiny/base)
   - Process fewer videos at once

5. **SSL Certificate Error**: If you encounter SSL certificate verification errors when downloading Whisper models, try:
   ```bash
   # Option 1: Update certificates
   /Applications/Python\ 3.x/Install\ Certificates.command
   
   # Option 2: Set environment variable (temporary fix)
   export SSL_VERIFY=false
   
   # Option 3: Use pip to install certificates
   pip install --upgrade certifi
   ```

6. **Model Download Issues**: If Whisper models fail to download, you can manually download them:
   ```bash
   python -c "import whisper; whisper.load_model('tiny')"
   ```

### Performance Tips

- Use GPU if available for faster transcription
- Start with "base" model for good balance
- Process videos in smaller batches for large datasets

## 📝 License

This project is for educational and personal use. Respect TikTok's terms of service and content creators' rights.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section
2. Ensure all dependencies are installed correctly
3. Verify FFmpeg installation
4. Check Python version compatibility

---

**Note**: This application downloads videos temporarily for processing and cleans them up afterward. Always respect content creators' rights and platform terms of service.
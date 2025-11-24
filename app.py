import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime
import zipfile
import io

from video_downloader import TikTokDownloader, validate_tiktok_url, extract_urls_from_text
from transcriber import VideoTranscriber, format_timestamp, export_transcription_to_srt, get_system_info

# Page configuration
st.set_page_config(
    page_title="TikTok Video Transcriber",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #ff0050, #00f2ea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'transcription_results' not in st.session_state:
        st.session_state.transcription_results = []
    if 'download_results' not in st.session_state:
        st.session_state.download_results = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

def main():
    """Main application function"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎵 TikTok Video Transcriber</h1>', unsafe_allow_html=True)
    st.markdown("### Bulk transcribe TikTok videos using free AI models")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection
        st.subheader("Whisper Model")
        model_options = ["tiny", "base", "small", "medium", "large"]
        model_descriptions = {
            "tiny": "Fastest, least accurate (~39 MB)",
            "base": "Good balance (~74 MB)",
            "small": "Better accuracy (~244 MB)",
            "medium": "High accuracy (~769 MB)",
            "large": "Best accuracy (~1550 MB)"
        }
        
        selected_model = st.selectbox(
            "Select Model Size",
            model_options,
            index=1,  # Default to 'base'
            format_func=lambda x: f"{x.title()} - {model_descriptions[x]}"
        )
        
        # Language selection
        st.subheader("Language")
        language_options = {
            "Auto-detect": None,
            "Indonesian": "id",
            "English": "en",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Portuguese": "pt",
            "Chinese": "zh",
            "Japanese": "ja",
            "Korean": "ko"
        }
        
        selected_language = st.selectbox(
            "Select Language",
            list(language_options.keys()),
            index=0
        )
        
        # System info
        st.subheader("System Info")
        sys_info = get_system_info()
        if sys_info['cuda_available']:
            st.success(f"🚀 GPU Available: {sys_info['device_name']}")
        else:
            st.info("💻 Using CPU (slower but works)")
        
        # Clear results button
        if st.button("🗑️ Clear All Results"):
            st.session_state.transcription_results = []
            st.session_state.download_results = []
            st.session_state.processing_complete = False
            st.rerun()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📥 Input URLs", "📊 Results", "📁 Export"])
    
    with tab1:
        st.header("Input TikTok URLs")
        
        # URL input methods
        input_method = st.radio(
            "Choose input method:",
            ["Paste URLs", "Upload Text File"],
            horizontal=True
        )
        
        urls = []
        
        if input_method == "Paste URLs":
            url_text = st.text_area(
                "Enter TikTok URLs (one per line or separated by spaces):",
                height=200,
                placeholder="https://www.tiktok.com/@username/video/1234567890\nhttps://vm.tiktok.com/abcdef\n..."
            )
            
            if url_text:
                # Extract URLs from text
                extracted_urls = extract_urls_from_text(url_text)
                manual_urls = [url.strip() for url in url_text.split('\n') if url.strip()]
                
                # Combine and validate
                all_urls = list(set(extracted_urls + manual_urls))
                urls = [url for url in all_urls if validate_tiktok_url(url)]
                
                if urls:
                    st.success(f"✅ Found {len(urls)} valid TikTok URLs")
                    with st.expander("Preview URLs"):
                        for i, url in enumerate(urls, 1):
                            st.write(f"{i}. {url}")
                elif url_text:
                    st.error("❌ No valid TikTok URLs found")
        
        else:  # Upload file
            uploaded_file = st.file_uploader(
                "Upload a text file containing TikTok URLs",
                type=['txt'],
                help="Upload a .txt file with TikTok URLs (one per line)"
            )
            
            if uploaded_file:
                content = uploaded_file.read().decode('utf-8')
                extracted_urls = extract_urls_from_text(content)
                urls = [url for url in extracted_urls if validate_tiktok_url(url)]
                
                if urls:
                    st.success(f"✅ Found {len(urls)} valid TikTok URLs in file")
                    with st.expander("Preview URLs"):
                        for i, url in enumerate(urls, 1):
                            st.write(f"{i}. {url}")
                else:
                    st.error("❌ No valid TikTok URLs found in file")
        
        # Process button
        if urls:
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                    process_videos(urls, selected_model, language_options[selected_language])
        
        # Processing status
        if st.session_state.get('processing_complete', False):
            st.balloons()
            st.success("🎉 Processing completed! Check the Results tab.")
    
    with tab2:
        st.header("Transcription Results")
        
        if st.session_state.transcription_results:
            display_results()
        else:
            st.info("No results yet. Process some videos first!")
    
    with tab3:
        st.header("Export Results")
        
        if st.session_state.transcription_results:
            export_results()
        else:
            st.info("No results to export. Process some videos first!")

def process_videos(urls, model_size, language):
    """Process videos: download and transcribe"""
    
    # Initialize components
    downloader = TikTokDownloader()
    transcriber = VideoTranscriber(model_size)
    
    # Progress tracking
    total_steps = len(urls) * 2  # Download + Transcribe
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Download videos
        status_text.text("📥 Downloading videos...")
        download_results = []
        failed_downloads = []
        
        for i, url in enumerate(urls):
            status_text.text(f"📥 Downloading video {i+1}/{len(urls)}")
            result = downloader.download_video(url)
            download_results.append(result)
            
            # Track failed downloads for user feedback
            if not result.get('success', False):
                failed_downloads.append({
                    'url': url,
                    'error': result.get('error', 'Unknown error'),
                    'error_type': result.get('error_type', 'unknown'),
                    'attempts': result.get('attempts', 1)
                })
            
            progress_bar.progress((i + 1) / total_steps)
        
        # Show download summary
        successful_downloads = [r for r in download_results if r.get('success', False)]
        
        if failed_downloads:
            st.warning(f"⚠️ {len(failed_downloads)} out of {len(urls)} videos failed to download:")
            for failure in failed_downloads:
                error_type = failure['error_type']
                attempts = failure['attempts']
                
                if error_type == 'blocked':
                    st.error(f"🚫 **TikTok blocked access** to {failure['url'][:50]}... (tried {attempts} times)")
                    st.info("💡 Try again later or use a different network connection.")
                elif error_type == 'unavailable':
                    st.error(f"📵 **Video unavailable** at {failure['url'][:50]}... (may be private or deleted)")
                elif error_type == 'network':
                    st.error(f"🌐 **Network error** downloading {failure['url'][:50]}... (tried {attempts} times)")
                    st.info("💡 Check your internet connection and try again.")
                else:
                    st.error(f"❌ **Download failed** for {failure['url'][:50]}...: {failure['error']}")
        
        if successful_downloads:
            st.success(f"✅ Successfully downloaded {len(successful_downloads)} videos!")
        
        st.session_state.download_results = download_results
        
        # Step 2: Transcribe videos
        status_text.text("🎤 Transcribing videos...")
        transcription_results = []
        
        # Add failed downloads to results (for display purposes)
        failed_download_results = [r for r in download_results if not r.get('success', False)]
        for failed_result in failed_download_results:
            transcription_results.append({
                **failed_result,
                'transcription_success': False,
                'transcription_error': 'Download failed - transcription not attempted'
            })
        
        successful_downloads = [r for r in download_results if r.get('success', False)]
        
        for i, download_result in enumerate(successful_downloads):
            video_path = download_result['filename']
            status_text.text(f"🎤 Transcribing video {i+1}/{len(successful_downloads)}")
            
            transcription = transcriber.transcribe_video(video_path, language)
            
            if transcription:
                # Combine download and transcription info
                combined_result = {
                    **download_result,
                    **transcription,
                    'transcription_success': True
                }
            else:
                combined_result = {
                    **download_result,
                    'transcription_success': False,
                    'transcription_error': 'Failed to transcribe'
                }
            
            transcription_results.append(combined_result)
            progress_bar.progress((len(urls) + i + 1) / total_steps)
        
        st.session_state.transcription_results = transcription_results
        st.session_state.processing_complete = True
        
        # Cleanup
        status_text.text("🧹 Cleaning up...")
        downloader.cleanup_downloads()
        transcriber.cleanup_temp_files()
        
        progress_bar.progress(1.0)
        status_text.text("✅ Processing completed!")
        
    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")
        status_text.text("❌ Processing failed!")

def display_results():
    """Display transcription results"""
    results = st.session_state.transcription_results
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_videos = len(results)
    successful_transcriptions = len([r for r in results if r.get('transcription_success', False)])
    total_duration = sum([r.get('duration', 0) for r in results])
    
    with col1:
        st.metric("Total Videos", total_videos)
    with col2:
        st.metric("Successful", successful_transcriptions)
    with col3:
        st.metric("Success Rate", f"{(successful_transcriptions/total_videos*100):.1f}%")
    with col4:
        st.metric("Total Duration", f"{total_duration:.1f}s")
    
    # Individual results
    for i, result in enumerate(results):
        with st.expander(f"Video {i+1}: {result.get('title', 'Unknown Title')}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write("**Video Info:**")
                st.write(f"URL: {result.get('url', 'N/A')}")
                st.write(f"Uploader: {result.get('uploader', 'N/A')}")
                
                # Display creation date if available
                if result.get('upload_date_formatted'):
                    st.write(f"Created: {result.get('upload_date_formatted')}")
                elif result.get('upload_date'):
                    st.write(f"Created: {result.get('upload_date')}")
                
                st.write(f"Duration: {result.get('duration', 0):.1f}s")
                st.write(f"Views: {result.get('view_count', 0):,}")
                st.write(f"Likes: {result.get('like_count', 0):,}")
                
                # Display additional metadata if available
                if result.get('comment_count') is not None:
                    st.write(f"Comments: {result.get('comment_count', 0):,}")
                
                if result.get('uploader_id'):
                    st.write(f"Uploader ID: @{result.get('uploader_id')}")
                
                if result.get('transcription_success', False):
                    st.write(f"**Language:** {result.get('language', 'Unknown')}")
            
            with col2:
                if result.get('transcription_success', False):
                    st.write("**Transcription:**")
                    st.write(result.get('text', 'No text available'))
                    
                    # Show segments if available
                    if result.get('segments'):
                        st.write("**Segments with Timestamps:**")
                        for segment in result['segments']:
                            start_time = format_timestamp(segment['start'])
                            end_time = format_timestamp(segment['end'])
                            st.write(f"**{start_time} - {end_time}:** {segment['text']}")
                else:
                    # Enhanced error display
                    error_msg = result.get('transcription_error', 'Unknown error')
                    
                    if error_msg == 'Download failed - transcription not attempted':
                        # This is a download failure
                        error_type = result.get('error_type', 'unknown')
                        attempts = result.get('attempts', 1)
                        
                        if error_type == 'blocked':
                            st.error("🚫 **Download Failed: TikTok blocked access**")
                            st.info("💡 **Solution:** Try again later or use a different network connection.")
                        elif error_type == 'unavailable':
                            st.error("📵 **Download Failed: Video unavailable**")
                            st.info("💡 **Reason:** Video may be private, deleted, or region-restricted.")
                        elif error_type == 'network':
                            st.error(f"🌐 **Download Failed: Network error** (tried {attempts} times)")
                            st.info("💡 **Solution:** Check your internet connection and try again.")
                        else:
                            st.error(f"❌ **Download Failed:** {result.get('error', 'Unknown error')}")
                    else:
                        # This is a transcription failure
                        st.error(f"🎤 **Transcription Failed:** {error_msg}")
                        st.info("💡 **Possible causes:** Audio quality issues, unsupported language, or file corruption.")

def export_results():
    """Export results in various formats"""
    results = st.session_state.transcription_results
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Export as CSV")
        if st.button("Download CSV", use_container_width=True):
            csv_data = create_csv_export(results)
            st.download_button(
                label="📥 Download CSV File",
                data=csv_data,
                file_name=f"tiktok_transcriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.subheader("📋 Export as JSON")
        if st.button("Download JSON", use_container_width=True):
            json_data = create_json_export(results)
            st.download_button(
                label="📥 Download JSON File",
                data=json_data,
                file_name=f"tiktok_transcriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # SRT files export
    st.subheader("🎬 Export SRT Subtitle Files")
    successful_results = [r for r in results if r.get('transcription_success', False) and r.get('segments')]
    
    if successful_results:
        if st.button("📥 Download All SRT Files (ZIP)", use_container_width=True):
            zip_data = create_srt_zip_export(successful_results)
            st.download_button(
                label="📥 Download SRT ZIP File",
                data=zip_data,
                file_name=f"tiktok_subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )
    else:
        st.info("No videos with segment data available for SRT export")

def create_csv_export(results):
    """Create CSV export data"""
    data = []
    for result in results:
        data.append({
            'URL': result.get('url', ''),
            'Title': result.get('title', ''),
            'Uploader': result.get('uploader', ''),
            'Uploader_ID': result.get('uploader_id', ''),
            'Created_Date': result.get('upload_date_formatted', result.get('upload_date', '')),
            'Created_Date_ISO': result.get('upload_date_iso', ''),
            'Duration': result.get('duration', 0),
            'Views': result.get('view_count', 0),
            'Likes': result.get('like_count', 0),
            'Comments': result.get('comment_count', 0),
            'Language': result.get('language', ''),
            'Transcription': result.get('text', ''),
            'Success': result.get('transcription_success', False)
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)

def create_json_export(results):
    """Create JSON export data"""
    export_data = {
        'export_date': datetime.now().isoformat(),
        'total_videos': len(results),
        'successful_transcriptions': len([r for r in results if r.get('transcription_success', False)]),
        'results': results
    }
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def create_srt_zip_export(results):
    """Create ZIP file with SRT subtitle files"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, result in enumerate(results):
            if result.get('segments'):
                # Create SRT content
                srt_content = ""
                for j, segment in enumerate(result['segments'], 1):
                    start_time = format_timestamp(segment['start'])
                    end_time = format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    
                    srt_content += f"{j}\n{start_time} --> {end_time}\n{text}\n\n"
                
                # Add to ZIP
                filename = f"video_{i+1}_{result.get('title', 'unknown')[:50]}.srt"
                # Clean filename
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                zip_file.writestr(filename, srt_content.encode('utf-8'))
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

if __name__ == "__main__":
    main()
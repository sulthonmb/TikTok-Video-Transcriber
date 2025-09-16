#!/usr/bin/env python3
"""
Test script for TikTok Video Transcriber
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from video_downloader import validate_tiktok_url, extract_urls_from_text
from transcriber import VideoTranscriber, get_system_info

def test_url_validation():
    """Test URL validation functionality"""
    print("🔍 Testing URL validation...")
    
    valid_urls = [
        "https://www.tiktok.com/@username/video/1234567890",
        "https://vm.tiktok.com/abcdef",
        "https://vt.tiktok.com/xyz123"
    ]
    
    invalid_urls = [
        "https://youtube.com/watch?v=123",
        "https://instagram.com/p/abc",
        "not_a_url"
    ]
    
    # Test valid URLs
    for url in valid_urls:
        if validate_tiktok_url(url):
            print(f"✅ Valid: {url}")
        else:
            print(f"❌ Should be valid: {url}")
    
    # Test invalid URLs
    for url in invalid_urls:
        if not validate_tiktok_url(url):
            print(f"✅ Correctly rejected: {url}")
        else:
            print(f"❌ Should be invalid: {url}")

def test_url_extraction():
    """Test URL extraction from text"""
    print("\n🔍 Testing URL extraction...")
    
    text = """
    Check out these TikTok videos:
    https://www.tiktok.com/@user1/video/1234567890
    https://vm.tiktok.com/abcdef
    Also this YouTube video: https://youtube.com/watch?v=123
    And this TikTok: https://vt.tiktok.com/xyz123
    """
    
    extracted_urls = extract_urls_from_text(text)
    print(f"Extracted {len(extracted_urls)} TikTok URLs:")
    for url in extracted_urls:
        print(f"  - {url}")

def test_transcriber_initialization():
    """Test transcriber initialization"""
    print("\n🔍 Testing transcriber initialization...")
    
    try:
        transcriber = VideoTranscriber("tiny")  # Use smallest model for testing
        print("✅ Transcriber initialized successfully")
        
        available_models = transcriber.get_available_models()
        print(f"Available models: {available_models}")
        
    except Exception as e:
        print(f"❌ Transcriber initialization failed: {e}")

def test_system_info():
    """Test system information"""
    print("\n🔍 Testing system information...")
    
    info = get_system_info()
    print(f"CUDA available: {info['cuda_available']}")
    print(f"Device count: {info['device_count']}")
    print(f"Device name: {info['device_name']}")

def main():
    """Run all tests"""
    print("🎵 TikTok Video Transcriber - Test Suite")
    print("=" * 50)
    
    test_url_validation()
    test_url_extraction()
    test_system_info()
    test_transcriber_initialization()
    
    print("\n🎉 Test suite completed!")
    print("\n📝 Note: This only tests basic functionality.")
    print("For full testing, use the Streamlit app with real TikTok URLs.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
YouTube Music Player API Startup Script
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'yt_dlp',
        'youtubesearchpython',
        'httpx',
        'aiofiles',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            print("Please run: pip install -r requirements.txt")
            return False
    
    print("✅ All dependencies are installed")
    return True

def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("⚠️  FFmpeg not found - required for audio conversion")
    print("Please install FFmpeg:")
    print("  Windows: Download from https://ffmpeg.org/download.html")
    print("  macOS: brew install ffmpeg")
    print("  Linux: sudo apt install ffmpeg")
    return False

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting YouTube Music Player API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🌐 Web Client: Open client.html in your browser")
    print("\n⏹️  Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

def main():
    """Main function"""
    print("🎵 YouTube Music Player API Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found. Please run this script from the project directory.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check FFmpeg (warning only)
    ffmpeg_available = check_ffmpeg()
    if not ffmpeg_available:
        print("⚠️  You can still use the streaming features without FFmpeg")
        print("   Download functionality requires FFmpeg\n")
    
    print("\n✅ Setup complete!")
    
    # Ask user if they want to start the server
    try:
        start_now = input("\nStart the server now? (y/n): ").lower().strip()
        if start_now in ['y', 'yes', '']:
            start_server()
        else:
            print("\n📝 To start the server manually, run:")
            print("   python main.py")
            print("   or")
            print("   uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main() 
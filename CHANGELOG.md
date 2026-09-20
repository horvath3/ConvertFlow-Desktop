# Changelog

All notable changes to ConvertFlow Desktop will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-09-19

### Added
- **Modern Dark UI**: Premium dark theme with electric blue/cyan neon accents
- **Custom Branding**: Unique ConvertFlow logo (SVG, PNG, ICO) with animated elements
- **Video Conversion**: Full-featured converter with MP4, MKV, MOV, WebM, AVI output
- **Video Compression**: Three modes — quality-based, target size, custom bitrate
- **Hardware Acceleration**: Automatic NVIDIA NVENC detection (H.264, HEVC, AV1)
- **Task Queue**: Parallel processing (1-2 jobs), pause/resume/retry/cancel
- **Drag & Drop**: Intuitive file handling with visual drop zone feedback
- **Performance Modes**: Quiet (2 threads, idle priority), Normal, Fast
- **Real-time Progress**: Progress bar, ETA, speed, FFmpeg status per task
- **Settings Persistence**: JSON-based settings in `%APPDATA%/ConvertFlow/`
- **Logging**: Rotating log files with configurable levels (DEBUG/INFO/WARNING/ERROR)
- **Portable Build**: Single-folder distribution + portable ZIP via PyInstaller
- **GitHub Actions CI/CD**: Automated testing, building, and releases
- **Professional Documentation**: Comprehensive README with screenshots

### Features
- **Video Converter Page**: Organized sections (Format, Video, Audio, Advanced)
- **Video Compressor Page**: Live target size estimation with savings calculation
- **Home Dashboard**: System status, quick actions, disk space monitoring
- **Settings Page**: Categorized sections (General, Encoding, Behavior, Performance, FFmpeg, Logging)
- **Task Items**: Modern card design with status colors, progress animation, action buttons
- **Error Handling**: User-friendly dialogs with technical details on demand
- **FFmpeg Management**: Bundled or custom FFmpeg path with version detection

### Technical
- Python 3.12 + PySide6 (Qt6)
- PyInstaller 6.9+ with UPX compression
- Type hints throughout codebase
- Modular architecture (core/ui/utils separation)
- Comprehensive test suite (pytest)

### Placeholder Modules (Future Versions)
- Audio Conversion
- Image Conversion
- Document Tools
- PDF Tools

---

## [Unreleased]

### Planned
- Conversion history / recent files panel
- Batch preset management
- Watch folder automation
- Multi-language support (i18n)
- Hardware encoding for AMD/Intel (VAAPI/QSV)
- Subtitle burn-in options
- Video preview thumbnails
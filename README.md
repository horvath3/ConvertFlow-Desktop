# ConvertFlow Desktop

<div align="center">

![ConvertFlow Logo](app/resources/icons/logo.png)

**Modern, offline video converter and compressor for Windows**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/horvath3/ConvertFlowDesktop/releases)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-6.7-green.svg)](https://pypi.org/project/PySide6/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-7.0-orange.svg)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)

</div>

---

## 🎯 Overview

**ConvertFlow Desktop** is a powerful, privacy-focused video conversion and compression application for Windows. Built with Python 3.12, PySide6 (Qt6), and FFmpeg, it processes all files locally on your machine—no uploads, no cloud, no data leaving your computer.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎬 **Video Conversion** | Convert between MP4, MKV, MOV, WebM, AVI with H.264, H.265/HEVC, AV1, VP9 codecs |
| 🗜️ **Video Compression** | Quality-based, target file size, or custom bitrate modes with 2-pass encoding |
| ⚡ **Hardware Acceleration** | Automatic NVIDIA NVENC detection (H.264, HEVC, AV1) |
| 📋 **Task Queue** | Parallel processing (1-2 jobs), pause/resume, retry, cancel |
| 🎨 **Modern Dark UI** | Premium dark theme with neon accents, smooth animations |
| 🖱️ **Drag & Drop** | Intuitive file handling with visual feedback |
| ⚙️ **Flexible Settings** | Performance modes (Quiet/Normal/Fast), output defaults, FFmpeg path |
| 📊 **Progress Tracking** | Real-time progress, ETA, speed, detailed FFmpeg status |
| 🔒 **Privacy First** | 100% offline, no telemetry, no accounts, no internet required |

---

## 📸 Screenshots

<div align="center">

### Home Dashboard
*Clean dashboard with system status, quick actions, and live stats*

![Home](docs/screenshots/home.png)

### Video Converter
*Comprehensive conversion settings with live codec compatibility*

![Converter](docs/screenshots/converter.png)

### Video Compressor
*Target size calculator with real-time estimation*

![Compressor](docs/screenshots/compressor.png)

### Settings
*Organized settings with performance profiles and FFmpeg management*

![Settings](docs/screenshots/settings.png)

</div>

---

## 🚀 Quick Start

### Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.12** (for development)
- **FFmpeg & ffprobe** binaries

### Installation (End Users)

1. Download the latest **`ConvertFlowDesktop-<version>-portable.zip`** from [Releases](https://github.com/horvath3/ConvertFlowDesktop/releases)
2. Extract to any folder
3. Run `ConvertFlowDesktop.exe`

> **Note**: FFmpeg binaries are included in the portable release. If missing, download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and place `ffmpeg.exe` + `ffprobe.exe` in `tools/ffmpeg/`.

### Development Setup

```bash
# Clone repository
git clone https://github.com/horvath3/ConvertFlowDesktop.git
cd ConvertFlowDesktop

# Run development script (creates venv, installs deps, launches app)
run.bat
```

Or manually:
```bash
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

---

## 🏗️ Building from Source

```bash
# Full build with portable ZIP
build.bat
```

Output:
- **Folder distribution**: `dist/ConvertFlowDesktop/ConvertFlowDesktop.exe`
- **Portable ZIP**: `dist/ConvertFlowDesktop-<version>-portable.zip`

### Build Requirements

- Python 3.12
- PyInstaller 6.9+
- UPX (optional, for smaller binaries)

---

## ⚙️ Configuration

Settings are stored in `%APPDATA%\ConvertFlow\settings.json`:

```json
{
  "default_output_dir": "C:\\Users\\<user>\\Videos\\ConvertFlow",
  "use_nvenc": true,
  "default_video_codec": "H.264",
  "default_quality_profile": "Jó minőség",
  "default_audio_bitrate": 160,
  "open_folder_after_conversion": false,
  "auto_remove_successful": false,
  "parallel_jobs": 1,
  "performance_mode": "Normál",
  "log_level": "INFO",
  "custom_ffmpeg_dir": ""
}
```

Logs: `%APPDATA%\ConvertFlow\logs\convertflow.log`

---

## 🎮 Usage Guide

### Converting Videos
1. Click **"Videó konvertálása"** in sidebar
2. Drag video files or click **"Fájl hozzáadása"**
3. Choose container (MP4, MKV, etc.)
4. Select codec (H.264, HEVC, AV1, VP9)
5. Pick quality profile or customize
6. Click **"Indít"** on each task or **"Összes várakozó indítása"**

### Compressing Videos
1. Click **"Videó tömörítése"**
2. Choose compression mode:
   - **Minőség alapján** — CRF-based quality
   - **Célfájlméret alapján** — Enter target size (MB/GB), auto-calculates bitrate
   - **Egyéni bitráta alapján** — Manual bitrate control
3. Add videos, start queue

### Performance Modes
| Mode | Threads | CPU Preset | NVENC Preset | Priority |
|------|---------|------------|--------------|----------|
| **Halk / kímélő** | 2 | veryfast | p3 | Idle |
| **Normál** | Auto | medium | p5 | Normal |
| **Gyors** | Auto | fast | p4 | Normal |

---

## 📦 Supported Formats

### Input (via FFmpeg)
MP4, MKV, MOV, AVI, WebM, WMV, M4V, MPEG, MPG, FLV, TS, MTS, M2TS, and more

### Output Containers
| Container | Video Codecs | Audio Codecs |
|-----------|--------------|--------------|
| MP4 | H.264, HEVC, AV1 | AAC, MP3, Opus |
| MKV | H.264, HEVC, AV1, VP9 | AAC, MP3, Opus, Copy |
| MOV | H.264, HEVC | AAC, MP3, Opus, Copy |
| WebM | VP9, AV1 | Opus |
| AVI | H.264 | MP3, Copy |

---

## 🔧 Technical Architecture

```
ConvertFlowDesktop/
├── main.py                    # Entry point
├── app/
│   ├── application.py         # App initialization, theming, icon
│   ├── core/                  # Business logic
│   │   ├── conversion_queue.py    # Task queue management
│   │   ├── conversion_worker.py   # FFmpeg process worker
│   │   ├── ffmpeg_manager.py      # FFmpeg command builder
│   │   ├── ffprobe_manager.py     # Video metadata extraction
│   │   ├── hardware_detection.py  # NVENC detection
│   │   ├── models.py              # Data classes
│   │   ├── performance_profiles.py# Performance presets
│   │   ├── settings_manager.py    # Persistent settings
│   │   ├── target_size_calculator.py # Bitrate calculator
│   │   └── video_profiles.py      # Codec/quality mappings
│   ├── ui/                    # User interface
│   │   ├── main_window.py         # Main window with sidebar
│   │   ├── home_page.py           # Dashboard
│   │   ├── video_converter_page.py # Conversion UI
│   │   ├── video_compressor_page.py # Compression UI
│   │   ├── settings_page.py       # Settings UI
│   │   ├── conversion_item_widget.py # Task item widget
│   │   └── dialogs.py             # Custom dialogs
│   ├── utils/                 # Utilities
│   └── resources/
│       ├── styles/dark.qss      # Premium dark theme
│       └── icons/               # Logo, app icon (ICO, SVG, PNG)
├── tools/ffmpeg/              # FFmpeg binaries (gitignored)
├── ConvertFlowDesktop.spec    # PyInstaller spec
├── build.bat                  # Build script
├── run.bat                    # Development run script
└── requirements.txt           # Python dependencies
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style
- Type hints on all functions
- Docstrings for public APIs
- Follow existing patterns in `app/core/` and `app/ui/`

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **[FFmpeg](https://ffmpeg.org/)** — The backbone of all video processing
- **[PySide6](https://wiki.qt.io/Qt_for_Python)** — Qt6 bindings for Python
- **[PyInstaller](https://pyinstaller.org/)** — Python application bundler
- **NVIDIA** — NVENC hardware acceleration

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/horvath3/ConvertFlowDesktop/issues)
- **Discussions**: [GitHub Discussions](https://github.com/horvath3/ConvertFlowDesktop/discussions)

---

<div align="center">

**Made with ❤️ for Windows users who value privacy and quality**

</div>

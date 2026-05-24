<!-- markdownlint-disable MD033 MD041 -->
<!-- Don't delete it -->
<div name="readme-top"></div>

<p align="center">
  <img src="docs/assets/banner.png" alt="PictoPy Banner" width="100%"/>
</p>

<!-- Organization/Project Social Handles -->
<p align="center">
<!-- Discord -->
<a href="https://discord.gg/hjUhu33uAn">
<img src="https://img.shields.io/discord/1022871757289422898?style=flat&logo=discord&logoColor=white&logoSize=auto&label=Discord&labelColor=5865F2&color=57F287" alt="Discord Badge"/></a>
&nbsp;&nbsp;
<!-- X (formerly Twitter) -->
<a href="https://x.com/aossie_org">
<img src="https://img.shields.io/twitter/follow/aossie_org" alt="X (formerly Twitter) Badge"/></a>
&nbsp;&nbsp;
<!-- LinkedIn -->
<a href="https://www.linkedin.com/company/aossie/">
  <img src="https://img.shields.io/badge/LinkedIn-black?style=flat&logo=LinkedIn&logoColor=white&logoSize=auto&color=0A66C2" alt="LinkedIn Badge"></a>
&nbsp;&nbsp;
<!-- Medium -->
<a href="https://news.stability.nexus/">
  <img src="https://img.shields.io/badge/Medium-black?style=flat&logo=medium&logoColor=black&logoSize=auto&color=white" alt="Medium Badge"></a>
&nbsp;&nbsp;
<!-- Telegram -->
<a href="https://t.me/StabilityNexus">
<img src="https://img.shields.io/badge/Telegram-black?style=flat&logo=telegram&logoColor=white&logoSize=auto&color=24A1DE" alt="Telegram Badge"/></a>
&nbsp;&nbsp;
<!-- Youtube -->
<a href="https://www.youtube.com/@AOSSIE-Org">
  <img src="https://img.shields.io/youtube/channel/subscribers/UCKVVLbawY7Gej_3o2WKsoiA?style=flat&logo=youtube&logoColor=white%20&logoSize=auto&labelColor=FF0000&color=FF0000" alt="Youtube Badge"></a>
</p>

<p align="center">
  <span style="font-size:18px;font-weight:bold">Download:</span>
    <span style="display:inline-flex;align-items:center;gap:0.5rem;">
      <a href="https://github.com/AOSSIE-Org/PictoPy/releases/latest/download/PictoPy_1.1.0_x64-setup.exe">
        <span style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.55rem 1rem;background:#017EC6;color:#ffffff;border-radius:6px;font-weight:700;line-height:1;">
          <span>Windows</span>
          <svg xmlns="http://www.w3.org/2000/svg" alt="Windows logo" width="18" height="18" fill="currentColor" class="bi bi-microsoft" viewBox="0 0 16 16">
            <path d="M7.462 0H0v7.19h7.462zM16 0H8.538v7.19H16zM7.462 8.211H0V16h7.462zm8.538 0H8.538V16H16z"/>
          </svg>
        </span>
      </a>
      <a href="https://github.com/AOSSIE-Org/PictoPy/releases/latest/download/PictoPy_aarch64.app.tar.gz">
        <span style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.55rem 1rem;background:#000000;color:#ffffff;border-radius:6px;font-weight:700;line-height:1;">
          <span>MacOS</span>
          <img src="https://cdn.simpleicons.org/apple/ffffff" alt="MacOS logo" width="" height="18" />
        </span>
      </a>
      <a href="https://github.com/AOSSIE-Org/PictoPy/releases/latest/download/PictoPy_1.1.0_amd64.deb">
        <span style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.55rem 1rem;background:#A81D33;color:#ffffff;border-radius:6px;font-weight:700;line-height:1;">
          <span>Debian</span>
          <img src="https://cdn.simpleicons.org/debian/ffffff" alt="Debian logo" width="18" height="18" />
        </span>
      </a>
      <a href="https://github.com/AOSSIE-Org/PictoPy/releases/latest">
        <span style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.55rem 1rem;background:#181717;color:#ffffff;border-radius:6px;font-weight:700;line-height:1;">
          <span>GitHub Releases</span>
          <img src="https://cdn.simpleicons.org/github/ffffff" alt="GitHub logo" width="18" height="18" />
        </span>
      </a>
    </span>
  </a>
</p>

# PictoPy

**PictoPy is an open-source, privacy-first AI photo management application built for the desktop - featuring on-device face recognition, object detection, and smart search, with zero data leaving your machine.**

PictoPy brings the intelligence of modern AI photo management to your local machine, without the privacy trade-offs of cloud-based alternatives. Built as a fully offline desktop application with Rust, React, and Python, PictoPy automatically groups faces across your library, tags photos with detected objects, and lets you search your pictures with simple words - all powered by state-of-the-art on-device models, without an internet connection or a subscription.

Find out more at [https://pictopy.aossie.org/](https://pictopy.aossie.org/).

## Features

### AI-powered

* Smart tagging based on detected faces and objects
* Advanced image analysis with object detection and facial recognition
* Smart search and retrieval

### Gallery management

* Album management with traditional gallery features
* Cross-platform compatibility

### Privacy & performance

* Privacy-focused design with fully offline functionality
* Efficient data handling and parallel processing

## Demonstration

<p align="center">
  <a href="https://youtu.be/RWp-9xT9jow?si=c1vNO5cDgI4GYM6y">
    <img src="docs/assets/demo.png" alt="PictoPy Demonstration">
  </a>
</p>

## Technology Stack

| Component         | Technology           |
| ----------------- | -------------------- |
| Frontend          | React                |
| Desktop Framework | Tauri                |
| Backend           | Rust, Python         |
| Database          | SQLite               |
| Image Processing  | OpenCV, ONNX Runtime |
| Object Detection  | YOLOv11              |
| Face Recognition  | FaceNet              |
| API Framework     | FastAPI              |
| State Management  | Redux Toolkit        |
| Styling           | Tailwind CSS         |
| Routing           | React Router         |
| UI Components     | ShadCN               |
| Build Tool        | Vite                 |
| Type Checking     | TypeScript           |

## High Level Architecture

<div align="center">
  <img src="docs/assets/architectual-design-light.svg#gh-light-mode-only" alt="PictoPy architecture diagram"/>
  <img src="docs/assets/architectual-design-dark.svg#gh-dark-mode-only" alt="PictoPy architecture diagram"/>
</div>

## Want to Contribute?

<a href="https://discord.gg/hjUhu33uAn"><img src="https://img.shields.io/discord/1022871757289422898?style=flat&logo=discord&logoColor=white&logoSize=auto&label=Discord&labelColor=5865F2&color=57F287" alt="Discord" height="30"></a>

1. First, join the **[Discord Server](https://discord.gg/hjUhu33uAn) (Go to Projects->PictoPy)** to chat with everyone.
2. For detailed setup instructions, coding guidelines, and the contribution process, please check out our [CONTRIBUTING.md](./CONTRIBUTING.md) file.

Don't forget to star this repository if you find it useful! ⭐

Our Code of Conduct: [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)

## License

This project is licensed under the GNU General Public License v3.0.
See the [LICENSE](LICENSE) file for details.

## Thanks To All Contributors

Thanks a lot for spending your time helping PictoPy grow. Keep rocking 🥂

[![Contributors](https://contrib.rocks/image?repo=AOSSIE-Org/PictoPy)](https://github.com/AOSSIE-Org/PictoPy/graphs/contributors)

© 2026 AOSSIE

# Changelog

All notable changes to PictoPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-22

### Added

- Settings page with folder and user preference management ([#606](https://github.com/AOSSIE-Org/PictoPy/pull/606), [#516](https://github.com/AOSSIE-Org/PictoPy/pull/516))
- Memories backend implementation ([#777](https://github.com/AOSSIE-Org/PictoPy/pull/777))
- Global face reclustering option with backend API and UI support ([#560](https://github.com/AOSSIE-Org/PictoPy/pull/560))
- Centralized logging system ([#548](https://github.com/AOSSIE-Org/PictoPy/pull/548))
- Live progress tracking with polling and animated progress bar ([#574](https://github.com/AOSSIE-Org/PictoPy/pull/574))
- Scrollbar timeline with month-year markers for Home and AI Tagging pages ([#552](https://github.com/AOSSIE-Org/PictoPy/pull/552))
- Empty state placeholders for AI tagging and home pages ([#549](https://github.com/AOSSIE-Org/PictoPy/pull/549))
- Camera selection for the webcam component ([#624](https://github.com/AOSSIE-Org/PictoPy/pull/624))
- Advanced zoom-on-scroll and panning logic in image preview ([#530](https://github.com/AOSSIE-Org/PictoPy/pull/530), [#835](https://github.com/AOSSIE-Org/PictoPy/pull/835))
- Slideshow looping for seamless playback ([#1100](https://github.com/AOSSIE-Org/PictoPy/pull/1100))
- Smooth exit animation for the image details panel ([#978](https://github.com/AOSSIE-Org/PictoPy/pull/978))
- Face renaming via Enter key ([#581](https://github.com/AOSSIE-Org/PictoPy/pull/581))
- Spawning and closing of backend and sync microservice from the Tauri app itself ([#1009](https://github.com/AOSSIE-Org/PictoPy/pull/1009))
- Arch Linux AUR package with automated publishing workflow ([#1268](https://github.com/AOSSIE-Org/PictoPy/pull/1268))
- AI models-based app size optimization ([#1263](https://github.com/AOSSIE-Org/PictoPy/pull/1263))

### Changed

- Streamlined Rust backend to a minimal API and updated docs structure ([#515](https://github.com/AOSSIE-Org/PictoPy/pull/515))
- Extended hover activation hotspot for navigation arrows ([#702](https://github.com/AOSSIE-Org/PictoPy/pull/702))
- Reversed marquee animation direction ([#894](https://github.com/AOSSIE-Org/PictoPy/pull/894))
- Improved gallery hover interaction with hover delay and cursor cleanup ([#715](https://github.com/AOSSIE-Org/PictoPy/pull/715))
- Switched backend setup to use Conda ([#975](https://github.com/AOSSIE-Org/PictoPy/pull/975))
- Separated backend services and changed server port numbers ([#933](https://github.com/AOSSIE-Org/PictoPy/pull/933), [#934](https://github.com/AOSSIE-Org/PictoPy/pull/934))
- Simplified Redux state ([#599](https://github.com/AOSSIE-Org/PictoPy/pull/599))

### Fixed

- Validated and sanitized image_ids in album APIs to prevent empty/invalid input and unsafe IN clauses ([#1253](https://github.com/AOSSIE-Org/PictoPy/pull/1253), [#629](https://github.com/AOSSIE-Org/PictoPy/pull/629))
- Prevented InfoDialog from flickering to blue variant on close ([#630](https://github.com/AOSSIE-Org/PictoPy/pull/630))
- Prevented duplicate scrollbars on Windows/Tauri ([#941](https://github.com/AOSSIE-Org/PictoPy/pull/941))
- Enabled "Open Folder" button functionality ([#976](https://github.com/AOSSIE-Org/PictoPy/pull/976))
- Fixed infinite recursion in InterceptHandler logging ([#940](https://github.com/AOSSIE-Org/PictoPy/pull/940))
- Fixed Windows build not opening on first launch ([#922](https://github.com/AOSSIE-Org/PictoPy/pull/922))
- Fixed macOS build not opening ([#659](https://github.com/AOSSIE-Org/PictoPy/pull/659))
- Fixed progress bar overflow in onboarding steps ([#726](https://github.com/AOSSIE-Org/PictoPy/pull/726))
- Improved face clustering accuracy with a similarity threshold ([#771](https://github.com/AOSSIE-Org/PictoPy/pull/771))
- Fixed atomic DB operations and consistency in global reclustering ([#570](https://github.com/AOSSIE-Org/PictoPy/pull/570))
- Fixed 500 error in the `/cluster_id/images` API ([#598](https://github.com/AOSSIE-Org/PictoPy/pull/598))
- Fixed critical database connection leaks ([#547](https://github.com/AOSSIE-Org/PictoPy/pull/547))
- Fixed database consistency on external image deletion events ([#520](https://github.com/AOSSIE-Org/PictoPy/pull/520))
- Fixed "Open Original File" button in the image details panel ([#542](https://github.com/AOSSIE-Org/PictoPy/pull/542))
- Fixed text overflow in the image details panel ([#537](https://github.com/AOSSIE-Org/PictoPy/pull/537))
- Fixed oversized navbar height on first load ([#692](https://github.com/AOSSIE-Org/PictoPy/pull/692))
- Fixed hover state and search bar UI issues ([#532](https://github.com/AOSSIE-Org/PictoPy/pull/532), [#529](https://github.com/AOSSIE-Org/PictoPy/pull/529))
- Fixed image lock error ([#565](https://github.com/AOSSIE-Org/PictoPy/pull/565))

### Documentation

- Added CI check for markdown linting ([#1266](https://github.com/AOSSIE-Org/PictoPy/pull/1266))
- Restructured intro page and sidebar navigation ([#1264](https://github.com/AOSSIE-Org/PictoPy/pull/1264))
- Improved documentation site responsiveness on mobile devices ([#601](https://github.com/AOSSIE-Org/PictoPy/pull/601), [#763](https://github.com/AOSSIE-Org/PictoPy/pull/763))
- Added Miniconda installation instructions to the Manual Setup Guide ([#971](https://github.com/AOSSIE-Org/PictoPy/pull/971))

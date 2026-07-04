# Changelog

All notable changes to PictoPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-07-04

<!-- Auto-generated draft. Review and edit before merging. -->

### Added
- Feat: Global Search Support for Face Collections and AI Tags (#1338) by @rohan-pandeyy
- Add CHANGELOG.md management and update CI release workflow (#1331) by @rohan-pandeyy
- Add expandable search dropdown with face clusters (#1314) by @rohan-pandeyy
- Added Fedora compatibility (#1310) by @DhruvK278
- Add version bump script and docs (#1308) by @rohan-pandeyy
- UI Based Multi-Person Face Image Search with Ranked Results (#1304) by @rohan-pandeyy
- Feat: Improve Model Tier Recommendation for Apple Silicon (#1299) by @rohan-pandeyy
-  Face Quality and Adaptive Density-Aware Face Clustering (#1290) by @rohan-pandeyy
- feat: auto-close inactive merge-conflicted PRs (#1289) by @VanshajPoonia
- feat: add long word validation for name input in onboarding and settings (#1286) by @Umang-Khemka
- feat(packaging): add Arch Linux AUR package with automated publishing workflow (#1268) by @akshajtiwari
- feat: add looping functionality to slideshow for seamless experience (#1100) by @monu808
- fix: fixed hardcoded copyright year (#1098) by @monu808
- fix: optimize toggle_favourite endpoint performance (#1094) by @harsh1519
- CI/CD: Refresh Frontend Test Suites (#1056) by @rohan-pandeyy
- ui(animation): smooth exit animation for image details panel (#978) by @skyforge-glitch
- ui(empty-state): make Settings link clickable in empty gallery (#964) by @skyforge-glitch
- fix(ui): prevent duplicate scrollbars on Windows/Tauri (#941) by @skyforge-glitch
- Reverse marquee animation direction  (#894) by @Supritha-gurazala
- Feat/memories backend implementation (#777) by @dehydrated-bear
- fix: Landing Page Improvements - Download/Docs Buttons, Branding & Dynamic Releases (#746) by @manishyad375375
- fixed progress bar overflow in onboarding steps (#726) by @Garry400
- feat(landing): PR for issue #714 Improve Gallery Feature Interaction (hover delay + cursor cleanup)  (#715) by @Supritha-gurazala
- feat(ui): extend hover activation hotspot for navigation arrows (#658) (#702) by @Arpitsh7
- FIX: #684 Navbar height is oversized on first load and fixes only after refresh (#692) by @kanishka-commits
- Fix/remove share icon (#631) by @DecodeX15
- Fix: prevent InfoDialog from flickering to blue variant on close (#630) by @kunalbansal23cs227
- feat: Implement settings page functionality(#566) (#606) by @ShivaGupta-14
- Fix #543: Improve documentation site responsiveness on mobile devices (#601) by @suryansh00001
- Fix/dependency error (#596) by @tushar1977
- Removed notification icon (#587) by @Adarsh-ops
- feat: allow renaming a face using Enter key in addition to  button (#581) by @rebeccabas
- Enhancement: Bottom Horizontal Scroll Grid in Media View (#578) by @rohan-pandeyy
-  Added title and aria-labels to buttons (#576) by @Pritom2357
- Implement live progress tracking with 1s polling, animated progress b… (#574) by @SiddharthJiyani
- fixed error of lock  (#565) by @DecodeX15
- feat: add global face reclustering option in settings with backend API and UI support (#560) by @Hemil36
- Feat: Scrollbar Timeline with {Month-Year} Markers for Home page and AI Tagging page. (#552) by @rohan-pandeyy
- Add empty state placeholders for AI tagging and home pages (#549) by @Hemil36
- feat : Centralized Logging System (#548) by @Hemil36
- Add linked issue workflow (#544) by @rahulharpal1603
- fix: prevent text overflow in Image Details panel (#533) (#537) by @smeet96
- fix(landing): centralize dark mode on <body> and remove duplicate toggles (#535) by @Pritom2357
- Fix the Hover state issue (#531) (#532) by @ShivaGupta-14
-  Zoom-on-Scroll Support in Image Preiew (#530) by @DecodeX15
- UI fix search bar (#529) by @DecodeX15
- [Feat] Implemented the search feature by uploading a image -2nd PR (#524) by @tushar1977
- feat: Refactored settings page with folder and user preferences manag… (#516) by @Hemil36
- Issue #511: refactor(rust): streamline backend to minimal API and update docs structure (#515) by @codiphile

### Fixed
- Fix Small Dataset Clustering Issue in Adaptive Density-Aware Clustering (#1330) by @rohan-pandeyy
- fix(person-images): prevent flash of previous page's images (#1315) (#1321) by @tanmaysachann
- Fix: standardize logging configuration across backend services (#1297) by @rohan-pandeyy
- Fix production zoom scroll behavior (#1295) by @VanshajPoonia
- feat: add long word validation for name input in onboarding and settings (#1286) by @Umang-Khemka
- Fix: Show "Folder is empty" message for empty folders in AI tagging - Remove merge conflict (#1285) by @akshajtiwari
- Fix README.md (#1283) by @rohan-pandeyy
- Fix duplicate issue detection logic (#1273) by @DhruvK278
- Validate image_ids to prevent empty or invalid inputs (#1253) by @Varun-JP
- Feat: Implemented spawing and closing of backend & sync microservice from tauri application itself (#1009) by @tushar1977
- fix: Enable "Open Folder" button functionality (#976) by @monu808
- fix(ui): prevent duplicate scrollbars on Windows/Tauri (#941) by @skyforge-glitch
- Fix infinite recursion in InterceptHandler logging (#940) by @sawarn24
- Fix BUG: Windows build does not open on the first try.  (#922) by @rahulharpal1603
- Enhancement: Advanced Zoom on Scroll & Panning Logic (#835) by @rohan-pandeyy
- fix: improve face clustering accuracy with similarity threshold and p… (#771) by @keshaviscool
- fixed progress bar overflow in onboarding steps (#726) by @Garry400
- Bump version to 1.1.0 in Cargo files and fix MacOS build not opening error. (#659) by @rahulharpal1603
- Fix Issues in favourites PR (#634) by @rahulharpal1603
- Fix: prevent InfoDialog from flickering to blue variant on close (#630) by @kunalbansal23cs227
- fix(albums): sanitize image_ids and secure IN clause (#629) by @g-k-s-03
- Enhancement: Add Camera Selection to Webcam Component. (#624) by @rohan-pandeyy
- [Fix] Fixed 500 issue in ```/cluster_id/images``` API (#598) by @tushar1977
- feat(media-view): Implement open folder and enhance controls (#539) (#577) by @ShivaGupta-14
-  Added title and aria-labels to buttons (#576) by @Pritom2357
- Fix: Ensure atomic DB operations and consistency in global reclustering (#562) (#570) by @Hemil36
- fixed error of lock  (#565) by @DecodeX15
- Fix: Critical database connection leaks in all database functions (#547) by @Aditya30ag
- fix: Open Original File Button in Image Details Panel  (#536)fix: Open Original File Button in Image Details Panel  (#536) (#542) by @ShivaGupta-14
- fix: prevent text overflow in Image Details panel (#533) (#537) by @smeet96
- fix(landing): centralize dark mode on <body> and remove duplicate toggles (#535) by @Pritom2357
- Fix the Hover state issue (#531) (#532) by @ShivaGupta-14
- UI fix search bar (#529) by @DecodeX15
- Fix PR #524 Lint and Build Errors (#525) by @rahulharpal1603
- Fix: Ensure Database Consistency on External Image Deletion Events (#520) by @Hemil36
- fix: update FastAPI command for Windows compatibility (#507) by @Hemil36

### Changed
- Add CHANGELOG.md management and update CI release workflow (#1331) by @rohan-pandeyy
- Added Fedora compatibility (#1310) by @DhruvK278
- docs: improve README - reorder badges, add downloads, fix dark/light diagram, fix contributor note (#1281) by @Umang-Khemka
- Improve mkdocs navigation structure (#1276) by @Awaneesh03
- Fix markdown linting issues and add CI check (#1266) by @VanshajPoonia
- Restructures intro page aligning sidebar sections (#1264) by @steam-bell-92
- Fix broken docs links  (#1075) by @PranjaliBhardwaj
- Reverse marquee animation direction  (#894) by @Supritha-gurazala
- fix: Landing Page Improvements - Download/Docs Buttons, Branding & Dynamic Releases (#746) by @manishyad375375
- feat(landing): PR for issue #714 Improve Gallery Feature Interaction (hover delay + cursor cleanup)  (#715) by @Supritha-gurazala
- FIX: #684 Navbar height is oversized on first load and fixes only after refresh (#692) by @kanishka-commits
- Fix #543: Improve documentation site responsiveness on mobile devices (#601) by @suryansh00001
- fix the layout (#586) by @Aditya30ag
- Issue #511: refactor(rust): streamline backend to minimal API and update docs structure (#515) by @codiphile
- Updated Documents (#512) by @Code-Builder-io

### Other
- refactor: replace broad except blocks with specific exceptions and logger (#1335) by @Dotify71
- fix: navigate back to previous page instead of hardcoded AI Tagging route (#1327) by @akshajtiwari
- fix: resolve act warnings and prevent runtime crashes on empty data (#1323) by @MayankSharma-ops
- fix(database): improve SQLite error handling and logging in images.py and folders.py (#1316) by @Dotify71
- feat: added the validation test (#1303) by @Umang-Khemka
- Update auto-issue-comment workflow with author check (#1300) by @Hemil36
- fix: guard addFolderMutate call when no folder is selected in onboarding (#1287) by @Rishiii57
- Fix:File Formatting and bug fix in previous PR (#1284) by @akshajtiwari
- docs: fix spelling in backend directory structure (#1282) by @yosinn1-blip
- Chore: Bump Versioning to "1.1.0" (#1274) by @rohan-pandeyy
- AI Models Based App Size Optimization (#1263) by @rohan-pandeyy
- Refactor README structure for improved readability and maintainability (#1258) by @rohan-pandeyy
- Add automated merge conflict labeling workflow (#1209) by @dhruvi-16-me
- Add CodeRabbit.YML config file (#1189) by @rohan-pandeyy
- initialize-semantic-issue-similarity-analysis-and-duplicate-detection-automation-workflow (#1175) by @aniket866
- chore: remove unused files and cache management code (#1149) by @rahulharpal1603
- fix: changed to make correct thumbnail path (#1124) by @tushar1977
- added tooltip on face search, like it was on all other icons (#1086) by @Ujjiyara
- fix: upgrade pre-commit hooks for ruff and black and reformated some files (#1073) by @tushar1977
- Enhancement/using conda for backend setup (#975) by @rahulharpal1603
- Update Manual Setup Guide to include Miniconda installation instructions (#971) by @rahulharpal1603
- [Fix] Added utils folder in build stage (#957) by @tushar1977
- Change server port numbers (#934) by @rahulharpal1603
- Separation of backend services (#933) by @rahulharpal1603
- Back button error fix (#892) by @ritigya03
- Fix text padding issue where letters were getting cut off (#814) by @Aditya30ag
- Fix docs mobile responsiveness: prevent horizontal overflow, wrap lon… (#763) by @HardikMathur11
- Add LICENSE.md (#740) by @singhshaurya01
- Add COPYRIGHT.md (#736) by @singhshaurya01
- Fix index error (#600) by @rahulharpal1603
- Fix/redux state simplification (#599) by @rahulharpal1603
- UI: Add Padding to Images Grid in ChronologicalGallery (#588) by @rohan-pandeyy
- Fix typo in image metadata utility filename (#559) by @VasuS609
- fix(utils): rename image_metatdata.py → image_metadata.py (#558) by @aryash45


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

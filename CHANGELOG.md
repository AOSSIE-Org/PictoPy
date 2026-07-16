# Changelog

All notable changes to PictoPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-07-16

### Added

- Model Manager: install, switch between, and uninstall YOLO model variants directly from Settings (#1357)
- Global search across face collections and AI tags from a single search bar (#1338)
- Multi-person face search with ranked results, so you can search for photos containing several specific people at once (#1304)
- Expandable search dropdown showing face clusters right in the navbar (#1314)
- Adaptive, density-aware face clustering that automatically tunes itself to your photo library for more accurate grouping (#1290)
- Smarter model tier recommendations for Apple Silicon Macs (#1299)
- Fedora Linux development compatibility (#1310)

### Changed

- Improved performance when marking photos as favourites (#1094)
- Added validation to prevent overly long names during onboarding and in Settings (#1286)
- Added a tooltip to the face-search icon for consistency with other icons (#1086)

### Fixed

- Settings page not reflecting the active YOLO model after switching it in Model Manager (#1371)
- Image flicker during slideshow (#1370)
- Several video player bugs (#1339)
- Face clustering failing on very small photo libraries (#1330)
- A flash of the previous person's images when switching between people in face search (#1321)
- Incorrect zoom/scroll behavior in production builds (#1295)
- Inconsistent logging configuration across backend services (#1297)
- Missing "folder is empty" message on the AI tagging page (#1285)
- A crash when trying to add a folder without selecting one during onboarding (#1287)
- SQLite error handling and logging in image and folder operations (#1316)
- Back navigation always returning to AI Tagging instead of the previous page (#1327)

### Other

- Refreshed the frontend test suite (#1056)
- Added a version bump script and supporting release docs (#1308)
- Added CHANGELOG.md management and updated the CI release workflow (#1331)
- Automated closing of inactive, merge-conflicted PRs (#1289)
- Added a validation test suite (#1303)
- Fixed broken documentation links (#1075)
- General README improvements - badges, download links, contributor notes (#1281, #1283)
- Improved documentation navigation structure (#1276)
- Backend cleanup: replaced broad exception handling with specific, logged exceptions (#1335)
- Various internal fixes: duplicate-issue detection logic, CI warning cleanup, formatting, and a docs typo (#1273, #1323, #1284, #1282, #1300)

**Contributors:** @Awaneesh03, @DhruvK278, @Dotify71, @Hemil36, @MayankSharma-ops, @PranjaliBhardwaj, @Rishiii57, @Takitxt, @Ujjiyara, @Umang-Khemka, @VanshajPoonia, @akshajtiwari, @harsh1519, @rahulharpal1603, @rohan-pandeyy, @siddharthsai218, @tanmaysachann, @yosinn1-blip

---

## [1.1.0] - 2026-05-22

### Added

- Search your library by uploading a reference image, powered by visual similarity matching (#524)
- Global face re-clustering option in Settings, to recompute face groups across your entire library on demand (#560)
- Live progress tracking for long-running tasks with an animated, real-time progress bar (#574)
- Zoom-on-scroll support in image preview (#530), later extended with more advanced zoom and panning behavior (#835)
- A scrollbar timeline with month-year markers on the Home and AI Tagging pages (#552)
- A horizontal scroll grid at the bottom of the media viewer (#578)
- Reworked Settings page with folder and user preference management (#516, #606)
- Centralized logging system across the backend (#548)
- Camera selection support in the webcam capture component (#624)
- Backend groundwork for an upcoming Memories feature that will resurface photos from past dates and trips (#777)
- Seamless slideshow looping (#1100)
- App-size optimizations that reduce the installer footprint by making AI models downloadable rather than bundled (#1263)
- Arch Linux (AUR) package with automated publishing, making installs easier on Arch-based systems (#1268)

### Changed

- The desktop app now manages starting and stopping its own backend and sync microservice, so you no longer need to run them separately (#1009)
- Improved accessibility with titles and aria-labels on icon-only buttons (#576)
- Improved the media viewer's open-folder action and general playback controls (#577)
- Extended the hover area for gallery navigation arrows, making them easier to trigger (#702)
- Improved gallery hover-delay behavior and cursor styling (#715)
- Smoother exit animation for the image details panel (#978)
- Reversed the marquee scroll direction on the landing page (#894)
- Refreshed the landing page's download/docs buttons, branding, and made release info load dynamically (#746)
- Removed the notification icon (#587) and the share icon (#631) from the interface
- Streamlined the backend API surface and reorganized docs structure (#515)
- You can now confirm a face rename by pressing Enter, not just clicking the button (#581)
- Backend services split apart with clearer local port configuration for manual setup (#933, #934)

### Fixed

- FastAPI startup command on Windows (#507)
- Database inconsistency when images were deleted outside the app (#520)
- Search bar UI issues (#529)
- Incorrect hover state styling (#532)
- Duplicate dark-mode toggles on the landing page (#535)
- Text overflowing in the Image Details panel (#537)
- The "Open Original File" button in the Image Details panel (#542)
- Critical database connection leaks across backend functions (#547)
- A locking error affecting face operations (#565)
- Database consistency issues during global face re-clustering (#570)
- A broken layout on the docs site (#586)
- A server error (500) when fetching images for a face cluster (#598)
- An indexing error (#600)
- A security issue by sanitizing image IDs used in album queries (#629)
- The info dialog flickering to the wrong color when closing (#630)
- Issues in the Favourites feature (#634)
- macOS builds failing to open (#659)
- The onboarding progress bar overflowing its container (#726)
- Face clustering accuracy, by tuning the similarity threshold (#771)
- Text getting cut off due to incorrect padding (#814)
- An error when using the back button (#892)
- Windows builds not opening on the first launch attempt (#922)
- An infinite recursion bug in the logging system (#940)
- Duplicate scrollbars appearing on Windows (#941)
- The "Open Folder" button not working (#976)
- The Settings link in the empty gallery state not being clickable (#964)
- A hardcoded copyright year (#1098)
- Thumbnails pointing to the wrong file path (#1124)
- Missing empty-state placeholders on the AI tagging and home pages (#549)
- Added validation to reject empty or invalid image IDs (#1253)
- A dependency error causing build/runtime issues (#596)

### Other

- Documentation updates (#512)
- Improved documentation site responsiveness on mobile (#601, #763)
- Added COPYRIGHT.md and LICENSE.md (#736, #740)
- Documented and added support for using Miniconda/conda for backend setup (#971, #975)
- Added a linked-issue workflow for contributors (#544)
- Various CI/CD, linting, and internal tooling improvements (#1073, #1149, #1175, #1189, #1209, #1266, #957, #599, #558, #559, #525)

**Contributors:** @Adarsh-ops, @Aditya30ag, @Arpitsh7, @Code-Builder-io, @DecodeX15, @Garry400, @HardikMathur11, @Hemil36, @Pritom2357, @ShivaGupta-14, @SiddharthJiyani, @Supritha-gurazala, @VanshajPoonia, @Varun-JP, @VasuS609, @akshajtiwari, @aniket866, @aryash45, @codiphile, @dehydrated-bear, @dhruvi-16-me, @g-k-s-03, @kanishka-commits, @keshaviscool, @kunal30114, @kunalbansal23cs227, @manishyad375375, @monu808, @rahulharpal1603, @rebeccabas, @ritigya03, @rohan-pandeyy, @sawarn24, @singhshaurya01, @skyforge-glitch, @smeet96, @steam-bell-92, @suryansh00001, @tushar1977

---

## [1.0.0] - 2025-09-07

### Added

- New sync microservice that watches the file system for changes and keeps your library in sync, with supporting build pipeline updates (#486, #492)
- Swagger-based API documentation on the docs site (#483)
- Backend database schema reference page (#463)
- Initial landing page (#404)
- New in-app dialogs for surfacing messages and notifications (#488)

### Changed

- Revamped the frontend UI as part of the GSoC 2025 redesign (#489)
- Revamped the backend architecture as part of the GSoC 2025 backend work (#466)
- Updated setup and feature documentation for clarity (#462)

### Fixed

- Build pipeline issues (#503, #493)
- Removed an unnecessary uvloop dependency that was breaking Windows builds (#494)

### Other

- Updated documentation deployment workflow and added a missing requirements file (#484)
- Removed unused files from the web UI (#498)

**Contributors:** @Aditya30ag, @Anjali-Kan, @Ashutoshx7, @Code-Builder-io, @Hemil36, @rahulharpal1603, @rohan-pandeyy, @ssz2605

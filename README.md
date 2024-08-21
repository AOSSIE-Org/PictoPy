<div align="center">
  <img src="https://aossie.org/_next/static/media/Pictopy.bdb654f4.png" alt="PictoPy Logo" width="100px">

  <a href="https://aossie.org/">
    <img src="https://aossie.org/logo1.png" alt="PictoPy Logo" width="100px">
  </a>
</div>


## PictoPy

PictoPy is an advanced multimedia management application designed to streamline the organization, classification, and manipulation of images and videos. Built with a robust backend using Flask and a dynamic frontend leveraging modern web technologies, PictoPy provides a seamless user experience for managing media files.

> For Other Sections Of Documentation including Development phase, check [Docs folder](./docs) or the [**Wiki**](https://github.com/imxade/pictopyGSOC/wiki).

### Key Features

- **Media Viewing:** Effortlessly display images and videos, organized by directory or class.
- **Media Management:** Easily hide, delete, and restore media files with intuitive controls.
- **Organizational Tools:** Group media into categories and manage their visibility with AI models.
- **Interactive User Interface:** Enjoy a responsive, card-based layout with interactive media display and playback.

### Core Functionalities

- **Grouping and Classification:** Media can be organized into groups based on directories or user-defined classes, allowing for flexible categorization.
- **Dynamic UI:** The frontend is designed to provide a fluid user experience, with real-time updates and interactive elements.
- **Enhanced Media Operations:** Perform advanced media operations, such as hiding, deleting, and restoring files, directly from the web interface.

----

## Requirements

| **OS**   | **Requirements**                   |
|-------------|---------------------------------|
| Linux       | packages: GLIBC(>=2.31), libxcb       |
| Windows     | |
| OSX         | *Yet to be declared* |

----

## Where to Get the Executables?

### Bleeding Edge Candidates:
- **Location:**
  - Navigate to the [**Actions**](https://github.com/imxade/pictopyGSOC/actions) section of the repository.
- **Details:**
  - This section contains the latest builds, which may include new features and bug fixes.
  - Click on the latest (topmost) action in the list.
  - Scroll down to find a download icon (often labeled as "Artifacts").
  - Click on the download icon to download a zip file.
  - Extract the zip file to access the executable files.

### Released Candidates:
> Currently no releases has been made
- **Location:**
  - Navigate to the [**Releases**](https://github.com/imxade/pictopyGSOC/releases) section of the repository.
- **Details:**
  - This section **will** contain stable versions of the application.
  - Download the desired release by clicking on the relevant version.


---

## Executing the Application

> Note:
>  - Due to the unavailability of physical machines, we can't assure support for OSX or architectures other than x86.
>
>  - For Windows: **False Positive Detection**
>    - Windows Defender may falsely detect the executable as a Trojan. This is a known issue, as mentioned [here](../issues/39).
>    - To proceed, you need to allow this threat in Windows Defender.
>    - Once allowed, you can execute the application.

### General Instructions:
- Once you have the executable files, simply run them to start the application.

### Successful Execution:
- Upon successful execution, you should see the gallery interface with a navigation bar.
- Hovering over the icons in the navigation bar will display tooltips explaining their functions.

## Enabling AI Tagging:

- **Navigation:**
  - The leftmost icon on the navigation bar is the toggle for AI tags. Hover over it to verify.
- **First-Time Use:**
  - Clicking this icon for the first time will initiate a processing task for all media under the home directory. This can take some time.
  - To avoid waiting, click the icon again to toggle `AI tags` off, and browse the gallery while the processing continues in the background.

---

## Resetting the App:

> This shouldn't be needed under any circumstance, but the option remains.

- Simply delete the `.pictopy` directory from your home directory.
- This will reset the app to its initial state.

## Reporting issues

1. Describe the exact steps to reproduce the issue.
2. Afterward, share the link to the content of `.pictopy/log.txt` from your home directory by pasting it on [Pastebin](https://pastebin.com/).

---

Following these steps will help you get started with the application, enable AI tagging, and reset the app if necessary. For any issue or query, visit [Issues](../issues) or [Discussions](../discussions)

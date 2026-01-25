# Gallery View

The gallery view is the main way users browse and interact with their photos in PictoPy. It presents media in a responsive grid, organized by date, with filtering and AI-backed organization.

## Overview

The main gallery shows photos and videos in a grid layout. Images are grouped by date, and users can filter by tags, favourites, and other criteria. The gallery connects to the [state management](state-management.md) layer for images and folders, and uses shared [UI components](ui-components.md) for layout and controls.

## Layout and Behavior

- **Grid layout** – Media is displayed in a responsive grid that adapts to window size.
- **Date grouping** – Items are organized chronologically (by capture or file date) for quick scanning.
- **Filtering** – Users can filter by tagged status, favourites, and other attributes exposed in the UI.
- **Thumbnails** – Each item is shown as a thumbnail with optional overlays (e.g. favourite icon, AI tags).

## Key Components

The gallery experience is built from several frontend components:

- **ChronologicalGallery** – Renders the date-grouped grid of media.
- **ImageCard** – Renders a single thumbnail, metadata hints, and interaction targets (e.g. select, favourite).
- **MediaView** / **ImageViewer** – Full-size view and navigation when a photo or video is opened.
- **MediaThumbnails** – Thumbnail strip or grid used in the lightbox/viewer.
- **MediaInfoPanel** – Shows metadata, tags, and location for the currently viewed item.
- **MediaViewControls**, **ZoomControls**, **NavigationButtons** – Control zoom, next/previous, and other viewer actions.

## Screenshots

For visual examples of the main gallery, AI tagging, and related screens, see [Screenshots](screenshots.md).

## Related Documentation

- [State Management](state-management.md) – How images and folders are stored and updated in the Redux store.
- [Screenshots](screenshots.md) – Screenshots of the main gallery and other views.
- [UI Components](ui-components.md) – Shared components used in the gallery and across the app.

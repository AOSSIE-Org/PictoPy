# Memories Feature Documentation

## Overview

The Memories feature automatically resurfaces photos from your gallery based on time and location, creating nostalgic moments like "On This Day" and location-based trip highlights.

## Features

### 1. **On This Day Memories**
- Automatically finds photos taken on the same day in previous years
- Groups photos within a 3-day window
- Shows "1 year ago", "2 years ago", etc.

### 2. **Location-Based Trip Memories**
- Clusters photos taken at the same or nearby locations (within 5km radius)
- Groups photos from trips automatically
- Displays location information when available

### 3. **Interactive Memory Cards**
- Beautiful, story-style presentation
- Shows photo count, date, and location
- Tap to view full memory details

## API Endpoints

### GET `/memories`
Get all memories with optional limit parameter.

**Query Parameters:**
- `limit` (optional): Maximum number of memories to return

**Response:**
```json
{
  "memories": [...],
  "total": 10
}
```

### GET `/memories/{memory_id}`
Get a specific memory by ID and mark it as viewed.

### POST `/memories/generate`
Generate new memories from existing photos based on time and location.

**Response:**
```json
{
  "success": true,
  "generated_count": 5,
  "message": "Successfully generated 5 memories"
}
```

### DELETE `/memories/{memory_id}`
Delete a specific memory.

### POST `/memories/{memory_id}/view`
Mark a memory as viewed (updates last_shown_at timestamp).

## Database Schema

### `memories` Table
- `id`: Unique memory identifier
- `title`: Memory title
- `description`: Memory description
- `memory_type`: Type (on_this_day, location_trip)
- `date_range_start`: Start date of memory period
- `date_range_end`: End date of memory period
- `location`: Location name (optional)
- `latitude`/`longitude`: GPS coordinates (optional)
- `image_count`: Number of photos
- `cover_image_id`: Cover photo ID
- `created_at`: When memory was created
- `last_shown_at`: When last viewed

### `memory_images` Junction Table
Links memories to their associated images.

## Frontend Components

### `MemoryCard`
Interactive card component displaying memory information with:
- Memory type icon
- Title and date
- Photo count
- Location (if available)
- Hover effects

### `Memories` Page
Main page featuring:
- Grid layout of memory cards
- Generate memories button
- Loading and empty states
- Memory detail modal

### `useMemories` Hook
React hook providing:
- `memories`: List of all memories
- `isLoading`: Loading state
- `generateMemories()`: Generate new memories
- `deleteMemory()`: Delete a memory
- `markMemoryViewed()`: Track memory views

## Usage

1. **Generate Memories**: Click "Generate Memories" button
2. **View Memories**: Click on any memory card
3. **Navigate**: Memories refresh automatically based on current date

## Technical Details

### Memory Generation Algorithm

**On This Day:**
- Scans all images for matching month/day ±3 days
- Groups by year
- Minimum 1 photo required

**Location Trips:**
- Extracts GPS data from EXIF metadata
- Clusters photos within 5km radius
- Minimum 5 photos required for a trip memory
- Uses Haversine formula for distance calculation

### Performance
- Database indexes on date_range and location for fast queries
- Lazy loading of memory images
- Background generation using async tasks

## Future Enhancements
- Reverse geocoding for better location names
- More memory types (seasonal, events, people)
- Customizable clustering parameters
- Smart memory rotation based on viewing history

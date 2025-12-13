# Memories Feature Documentation

## Overview

The Memories feature automatically resurfaces photos from your gallery based on time and location, creating beautiful story-style highlights that help you relive past moments.

## Features

### Time-Based Memories
- **"On This Day" Memories**: Automatically generated for 1, 2, 3, 5, and 10 years ago
- **Date Window**: Uses a ±7 day window around the target date
- **Automatic Generation**: No manual intervention required

### Location-Based Memories
- **Geographic Clustering**: Groups photos taken at the same or nearby locations
- **Trip Detection**: Identifies trips and events based on location patterns
- **Location Naming**: Uses EXIF location data or generates descriptive names

### Memory Presentation
- **Interactive Cards**: Displays memories as beautiful cards on the memories page
- **Story-Style View**: Full-screen modal for viewing all photos in a memory
- **Cover Images**: Automatically selects representative cover images
- **Metadata Display**: Shows date, location, and photo count

## Architecture

### Backend (Python/FastAPI)

```
backend/app/
├── database/
│   └── memories.py          # Database operations
├── routes/
│   └── memories.py          # API endpoints
└── schemas/
    └── memories.py          # Pydantic models
```

#### Database Schema

**memories table:**
- `id`: Primary key
- `memory_type`: 'time_based' or 'location_based'
- `title`: Memory title (e.g., "On This Day 2 Years Ago")
- `description`: Memory description
- `start_date`, `end_date`: Date range
- `location`, `latitude`, `longitude`: Location data
- `cover_image_id`: Foreign key to images table
- `image_count`: Number of images
- `created_at`, `last_viewed`: Timestamps

**memory_images table:**
- `memory_id`: Foreign key to memories
- `image_id`: Foreign key to images
- `sequence_order`: Display order

### Frontend (React/TypeScript)

```
frontend/src/
├── pages/
│   └── Memories.tsx         # Main memories page
├── components/memories/
│   ├── MemoryCard.tsx       # Individual memory card
│   └── MemoryDetail.tsx     # Full memory view modal
├── services/
│   └── memoriesApi.ts       # API service
└── types/
    └── memories.ts          # TypeScript types
```

## API Endpoints

### Generate Memories
```http
POST /api/memories/generate
Content-Type: application/json

{
  "include_time_based": true,
  "include_location_based": true,
  "reference_date": "2024-12-13",  // Optional
  "min_images_for_location": 5,
  "distance_threshold": 0.05
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully generated 8 memories",
  "time_based_count": 3,
  "location_based_count": 5,
  "total_memories": 8
}
```

### List All Memories
```http
GET /api/memories/list
```

**Response:**
```json
{
  "memories": [
    {
      "id": 1,
      "type": "time_based",
      "title": "On This Day 2 Years Ago",
      "description": "Memories from December 13, 2023",
      "start_date": "2023-12-06",
      "end_date": "2023-12-20",
      "cover_image": {
        "id": 123,
        "path": "/path/to/image.jpg"
      },
      "image_count": 15,
      "images": [...]
    }
  ],
  "total_count": 8
}
```

### Get Memory Details
```http
GET /api/memories/{memory_id}
```

### Delete Memory
```http
DELETE /api/memories/delete
Content-Type: application/json

{
  "memory_id": 1
}
```

### Refresh All Memories
```http
POST /api/memories/refresh
```

## Memory Generation Algorithm

### Time-Based Algorithm

1. **Calculate Target Dates**: For each year (1, 2, 3, 5, 10 years ago)
2. **Query Images**: Get images within ±7 days of target date
3. **Create Memory**: If images found, create memory with:
   - Title: "On This Day X Years Ago"
   - Date range: Target date ±7 days
   - Cover: First image chronologically

### Location-Based Algorithm

1. **Get Images with Location**: Query all images with latitude/longitude
2. **Cluster by Proximity**: 
   - Use distance threshold (default 0.05° ≈ 5km)
   - Group images within threshold distance
3. **Filter Clusters**: Only create memories with minimum image count (default 5)
4. **Generate Metadata**:
   - Title based on location name and duration
   - Date range from earliest to latest photo
   - Cover image from chronologically first photo

## Usage Guide

### For Users

1. **Generate Memories**:
   - Navigate to Memories page
   - Click "Generate Memories" button
   - Wait for processing to complete

2. **View Memories**:
   - Browse memory cards in grid layout
   - Click any card to view full story
   - Navigate through photos using arrows

3. **Manage Memories**:
   - Refresh to regenerate all memories
   - Delete individual memories (photos remain in gallery)
   - Memories update automatically with new photos

### For Developers

#### Backend Integration

Add memories routes to main application:

```python
# backend/main.py
from app.routes import memories
from app.database import memories as memories_db

# Initialize database
conn = get_db_connection()
memories_db.create_memories_table(conn)

# Include router
app.include_router(memories.router, prefix="/api")
```

#### Frontend Integration

Add Memories route to your React Router:

```typescript
// frontend/src/App.tsx
import MemoriesPage from './pages/Memories';

<Route path="/memories" element={<MemoriesPage />} />
```

## Configuration

### Backend Settings

```python
# Adjust in app/config/settings.py or pass to functions

# Minimum images required for location-based memory
MIN_IMAGES_FOR_LOCATION = 5

# Distance threshold for location clustering (degrees)
# 0.05° ≈ 5km, 0.1° ≈ 11km
DISTANCE_THRESHOLD = 0.05

# Years to generate time-based memories for
YEARS_AGO = [1, 2, 3, 5, 10]

# Date window for time-based memories (days)
DATE_WINDOW = 7
```

### Frontend Settings

```typescript
// frontend/src/services/memoriesApi.ts

// API base URL
const API_BASE_URL = 'http://localhost:8000/api';

// Default generation parameters
const DEFAULT_PARAMS = {
  include_time_based: true,
  include_location_based: true,
  min_images_for_location: 5,
  distance_threshold: 0.05
};
```

## Performance Considerations

### Memory Generation
- **Time Complexity**: O(n) for time-based, O(n²) for location clustering
- **Optimization**: Use spatial indexing for large datasets
- **Caching**: Generated memories are cached in database

### Image Loading
- **Lazy Loading**: Implement for large memory collections
- **Thumbnail Generation**: Use thumbnails for grid view
- **Progressive Loading**: Load images incrementally in story view

## Testing

### Backend Tests

```python
# tests/test_memories.py
import pytest
from app.database import memories as memories_db

def test_generate_time_based_memories():
    # Test memory generation logic
    pass

def test_location_clustering():
    # Test location clustering algorithm
    pass
```

### Frontend Tests

```typescript
// tests/Memories.test.tsx
import { render, screen } from '@testing-library/react';
import MemoriesPage from '../pages/Memories';

test('renders memories page', () => {
  render(<MemoriesPage />);
  expect(screen.getByText('Memories')).toBeInTheDocument();
});
```

## Troubleshooting

### No Memories Generated
- **Check Image Metadata**: Ensure images have date_taken in database
- **Verify Date Range**: Images must be at least 1 year old for time-based
- **Location Data**: Check if images have latitude/longitude for location-based

### Memory Generation Slow
- **Reduce Distance Threshold**: Lower threshold = faster clustering
- **Limit Years**: Generate fewer time-based memories
- **Batch Processing**: Process images in batches

### Images Not Displaying
- **Check File Paths**: Verify file paths are correct
- **Permissions**: Ensure app has read access to image directories
- **CORS**: Configure CORS for local file access in Tauri

## Future Enhancements

- [ ] AI-powered memory titles and descriptions
- [ ] Face recognition integration for person-based memories
- [ ] Weather data integration
- [ ] Music/soundtrack suggestions for memories
- [ ] Social sharing capabilities
- [ ] Customizable memory templates
- [ ] Animated transitions between photos
- [ ] Video support in memories
- [ ] Memory notifications ("On this day...")
- [ ] Export memories as video/slideshow

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to the Memories feature.

## License

See [LICENSE](../LICENSE) for license information.

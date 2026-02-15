# Memories Feature Documentation

## Overview

The Memories feature automatically organizes photos into meaningful collections based on location and date, providing a Google Photos-style experience for reliving past moments.

## Features

### 1. On This Day
Shows photos from the same date in previous years with a prominent featured card.

**Display:**
- "On this day last year" for photos from exactly 1 year ago
- "[X] years ago" for photos from multiple years ago
- Featured hero image with gradient overlay
- Photo count and year badges

### 2. Memory Types

#### Location-Based Memories
Photos grouped by GPS coordinates using DBSCAN clustering:
- **Radius**: 5km (configurable)
- **Title Format**: "Trip to [City Name], [Year]"
- **Example**: "Trip to Jaipur, 2025"
- **Reverse Geocoding**: Maps coordinates to actual city names
- **Supported Cities**: 30+ major cities worldwide (Indian, European, American, Asian, etc.)

#### Date-Based Memories
Photos grouped by month for images without GPS:
- **Grouping**: Monthly clusters
- **Title Format**: "[Month] [Year]"
- **Flexibility**: Works even without location data

### 3. Memory Sections

#### Recent Memories
- **Timeframe**: Last 30 days
- **Use Case**: Recent trips and events
- **API**: `GET /api/memories/timeline?days=30`

#### This Year
- **Timeframe**: Last 365 days (current year)
- **Use Case**: Year-in-review
- **API**: `GET /api/memories/timeline?days=365`

#### All Memories
- **Timeframe**: All time
- **Use Case**: Complete memory collection
- **API**: `POST /api/memories/generate`

### 4. Filtering

**Filter Options:**
- **All**: Shows all memories (default)
- **Location**: Only memories with GPS coordinates
- **Date**: Only memories without GPS (date-based)

**Implementation:**
```typescript
const applyFilter = (memories: Memory[]) => {
  if (filter === 'location') {
    return memories.filter(m => m.center_lat !== 0 || m.center_lon !== 0);
  }
  if (filter === 'date') {
    return memories.filter(m => m.center_lat === 0 && m.center_lon === 0);
  }
  return memories; // 'all'
};
```

### 5. Memory Viewer

Full-screen modal for viewing memory photos:

**Features:**
- Image grid with hover effects
- Click to open MediaView
- Zoom and pan support
- Slideshow mode
- Keyboard navigation
- Info panel with metadata
- Thumbnail strip

**Controls:**
- **Zoom**: Mouse wheel or +/- keys
- **Navigation**: Arrow keys or buttons
- **Slideshow**: Play/Pause button or Space key
- **Info Panel**: Toggle with 'I' key
- **Close**: ESC key or X button

## Components

### MemoriesPage
Main page component with sections:
- Header with refresh button
- Filter buttons
- On This Day section
- Recent Memories grid
- This Year grid
- All Memories grid

### MemoryCard
Individual memory card display:
- Thumbnail image
- Memory title (formatted based on type)
- Date range (relative format)
- Location (if available)
- Photo count badge
- Type badge (Location/Date)

### FeaturedMemoryCard
Large featured card for "On This Day":
- Hero image with gradient overlay
- "On this day last year" text
- Photo count and year info
- Additional image previews

### MemoryViewer
Modal for viewing memory album:
- Conditionally rendered to prevent event bubbling
- Grid layout of all photos
- MediaView integration for full-screen viewing
- Proper z-index layering

## State Management

Using Redux Toolkit with slices:

```typescript
// Store structure
{
  memories: {
    onThisDay: {
      images: MemoryImage[],
      meta: { today: string, years: number[] }
    },
    recent: Memory[],
    year: Memory[],
    all: Memory[],
    selectedMemory: Memory | null,
    loading: { onThisDay, recent, year, all },
    error: { onThisDay, recent, year, all }
  }
}
```

**Key Actions:**
- `fetchOnThisDay()` - Get photos from same date
- `fetchRecentMemories(days)` - Get timeline memories
- `fetchYearMemories(days)` - Get year memories
- `fetchAllMemories()` - Generate all memories
- `setSelectedMemory(memory)` - Open memory viewer

## API Endpoints

### GET `/api/memories/on-this-day`
Returns photos from the same date in previous years.

**Response:**
```json
{
  "images": [...],
  "today": "December 14",
  "years": [2024, 2023, 2022]
}
```

### GET `/api/memories/timeline?days=30`
Returns timeline-based memories for specified days.

**Parameters:**
- `days` (query): Number of days to look back

**Response:**
```json
{
  "memories": [...]
}
```

### POST `/api/memories/generate`
Generates all memories with clustering.

**Parameters (query):**
- `location_radius_km` (default: 5.0)
- `date_tolerance_days` (default: 3)
- `min_images` (default: 2)

**Response:**
```json
{
  "memories": [...],
  "breakdown": {
    "total": 10,
    "location": 6,
    "date": 4
  }
}
```

## Backend Implementation

### Memory Clustering Algorithm

**Location-based (DBSCAN):**
1. Extract GPS coordinates from images
2. Convert to radians for haversine distance
3. Apply DBSCAN clustering (5km radius)
4. Group images by cluster
5. Reverse geocode center coordinates
6. Generate title with city name and year

**Date-based (Monthly grouping):**
1. Filter images without GPS
2. Group by year-month
3. Create monthly memories
4. Use date as title

### Reverse Geocoding

Maps GPS coordinates to city names using pre-defined database:

```python
def _reverse_geocode(self, lat: float, lon: float) -> str:
    """Find nearest city within 50km"""
    for city_name, (city_lat, city_lon) in self.CITY_COORDINATES.items():
        distance = haversine_distance(lat, lon, city_lat, city_lon)
        if distance < 50:
            return city_name
    return f"{lat:.4f}°, {lon:.4f}°"
```

**Supported Cities:**
- India: Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad, Jaipur, Lucknow, Kanpur, Nagpur, Visakhapatnam, Bhopal, Patna, Vadodara
- Europe: London, Paris, Berlin, Madrid, Rome, Amsterdam, Prague, Vienna, Barcelona, Budapest, Lisbon
- Americas: New York, Los Angeles, Toronto, San Francisco, Chicago, Vancouver
- Asia-Pacific: Tokyo, Seoul, Singapore, Hong Kong, Sydney, Melbourne

## Bug Fixes & Improvements

### Event Bubbling Fix
**Problem:** Clicking MediaView controls (slideshow, info) closed the entire viewer.

**Solution:** Conditional rendering of MemoryViewer backdrop:
```tsx
{!showMediaView && (
  <div onClick={handleCloseViewer}>
    {/* Grid content */}
  </div>
)}
```

### Image Upload Fix
**Problem:** Images without GPS couldn't be inserted into database.

**Solution:** Always include latitude/longitude fields (set to `None` if not available):
```python
image_record = {
    "latitude": latitude,  # Can be None
    "longitude": longitude,  # Can be None
    "captured_at": captured_at
}
```

### Title Display Enhancement
**Problem:** Generic "Location - Nov 2025" titles.

**Solution:** Format as "Trip to [City], [Year]" using reverse geocoding:
```typescript
const year = memory.date_start ? new Date(memory.date_start).getFullYear() : '';
displayTitle = `Trip to ${displayLocation}${year ? `, ${year}` : ''}`;
```

## Testing

### Backend Tests
Located in `backend/tests/`:
- 100 unit tests covering all routes
- Run with: `pytest tests/`

### Frontend Tests
Located in `frontend/src/pages/__tests__/`:
- Page rendering tests
- Run with: `npm test`

### Manual Testing
Use `backend/test_memories_api.py` for API endpoint testing:
```bash
python test_memories_api.py
```

## Performance Considerations

1. **Lazy Loading**: Images load on-demand with `loading="lazy"`
2. **Thumbnail Optimization**: Uses Tauri's `convertFileSrc()` for efficient file access
3. **Redux Memoization**: Uses `React.memo()` for card components
4. **Efficient Queries**: SQLite indexes on `latitude`, `longitude`, `captured_at`
5. **Background Processing**: Memory generation runs asynchronously

## Future Enhancements

- [ ] Custom memory creation
- [ ] Memory sharing and export
- [ ] Advanced filtering (by location, date range, etc.)
- [ ] Memory annotations and descriptions
- [ ] Map view for location-based memories
- [ ] AI-generated memory titles
- [ ] Multi-photo featured cards
- [ ] Memory notifications and reminders

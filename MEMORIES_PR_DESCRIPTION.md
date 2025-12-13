# Pull Request: Implement Memories Feature with Time and Location-Based Clustering

## Related Issue
Implements #723 - Memories feature for organizing photos by time and location

## Overview
This PR introduces a comprehensive **Memories** feature that automatically generates meaningful photo collections based on temporal and geographical patterns. The feature intelligently clusters images to create "On This Day" memories and trip-based collections.

## Features Implemented

### 1. Time-Based Memories (On This Day)
- Automatically finds photos taken on the same date 1-5 years ago
- Creates nostalgic collections showing "what you were doing on this day in previous years"
- Groups memories by year and date for easy browsing

### 2. Location-Based Trip Memories
- Uses **Haversine formula** to calculate geographic distances between photos
- Clusters images taken within 7 days and 10km radius into trip memories
- Detects travel patterns and groups photos from the same location/event
- Automatically extracts location names from image metadata

### 3. Smart Memory Generation
- Processes all images in the database to generate memories
- Uses efficient spatial clustering algorithms
- Respects date ranges and location proximity thresholds
- Generates descriptive titles and metadata for each memory

## Technical Implementation

### Backend Changes

#### Database Layer (`backend/app/database/memories.py`)
- **New Table**: `memories` with columns:
  - `id`, `title`, `description`, `type` (on_this_day/trip)
  - `image_count`, `representative_image_id`
  - `date_range_start`, `date_range_end`
  - `location_name`, `year`, `created_at`
- **Indexes**: Optimized for year and type queries
- **CRUD Operations**: Complete set of database functions

#### Memory Generation (`backend/app/utils/memories.py`)
- **Haversine Distance Calculation**: Accurate geographic distance between coordinates
- **Location Clustering**: Groups images within 5km threshold
- **Time-Based Detection**: Finds images from 1-5 years ago on same date
- **Trip Detection**: Clusters images by 7-day windows and 10km proximity
- **Metadata Extraction**: Parses EXIF data for dates and locations

#### API Endpoints (`backend/app/routes/memories.py`)
- `GET /memories/` - Fetch all memories with representative images
- `GET /memories/{memory_id}/images` - Get specific memory with all images
- `POST /memories/generate` - Trigger memory generation process

#### Integration (`backend/main.py`)
- Added memories table creation on startup
- Registered memories router with `/memories` prefix

### Frontend Changes

#### API Layer (`frontend/src/api/`)
- **Endpoints**: Added `memoriesEndpoints` in `apiEndpoints.ts`
- **Functions**: Created `memories.ts` with:
  - `fetchAllMemories()` - Retrieve all memories
  - `fetchMemoryImages(memoryId)` - Get memory details
  - `generateMemories()` - Trigger generation

#### Type Definitions (`frontend/src/types/Media.ts`)
- **Memory Interface**: Complete type definitions for memories
- **MemoryImage Interface**: Type-safe image data in memories

#### UI Components

**Memories Page** (`frontend/src/pages/Memories/Memories.tsx`)
- Grid layout displaying memory cards
- Color-coded badges for memory types (blue for "On This Day", green for "Trip")
- Shows representative image, title, image count, and date range
- Generate/Regenerate button with loading states
- Empty state with helpful message
- Click to navigate to detailed view

**Memory Detail Page** (`frontend/src/pages/Memories/MemoryDetail.tsx`)
- Full memory information header with metadata
- Chronological gallery view of all images in the memory
- Date range formatting (single date or range)
- Location display with icon
- Image count badge
- Back navigation to memories list

#### Routing (`frontend/src/routes/AppRoutes.tsx`)
- `/memories` - Main memories page
- `/memories/:memoryId` - Individual memory detail view

## Algorithm Details

### Haversine Formula
```
Distance = 2 × R × arcsin(√(sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)))
```
Where R = Earth's radius (6371 km)

### Clustering Thresholds
- **Trip Location**: 10km radius for same trip
- **Location Grouping**: 5km radius for image clusters
- **Time Window**: 7 days for trip detection
- **Historical Range**: 1-5 years for "On This Day"

## Files Changed

### New Files (6)
- `backend/app/database/memories.py` - Database schema and operations
- `backend/app/utils/memories.py` - Memory generation algorithms
- `backend/app/routes/memories.py` - FastAPI endpoints
- `frontend/src/api/api-functions/memories.ts` - API client
- `frontend/src/pages/Memories/Memories.tsx` - Main page
- `frontend/src/pages/Memories/MemoryDetail.tsx` - Detail view

### Modified Files (6)
- `backend/main.py` - Added memories integration
- `frontend/src/api/apiEndpoints.ts` - Added endpoints
- `frontend/src/api/api-functions/index.ts` - Exported functions
- `frontend/src/types/Media.ts` - Added type definitions
- `frontend/src/routes/AppRoutes.tsx` - Added routing
- `frontend/src/pages/Memories/Memories.tsx` - Created new component

## Testing Performed
- [x] Python syntax validation (all files compile successfully)
- [x] Type definitions validated
- [x] API endpoint structure verified
- [x] UI components follow existing patterns
- [x] Redux integration for image viewing
- [x] Error handling and loading states

## Usage Instructions
1. Navigate to `/memories` in the app
2. Click "Generate Memories" to create initial collections
3. Browse memory cards showing different types
4. Click any memory to view all images in that collection
5. Use the back button to return to the memories list

## Performance Considerations
- Database indexes on `year` and `type` for fast queries
- Efficient spatial clustering with distance caching
- Batch processing of images during generation
- Representative image selection for quick loading

## Future Enhancements
- Face-based memories (group by people)
- Smart filtering by season or weather
- Memory sharing capabilities
- Custom memory creation by users
- Memory notifications/reminders

## Breaking Changes
None - this is a new feature with no impact on existing functionality

## Additional Context
The Memories feature leverages existing image metadata (EXIF data) and provides an intuitive way for users to rediscover their photos through automatic temporal and geographical organization. The implementation follows the app's existing patterns for database operations, API design, and UI components.

# Memories Feature

The Memories feature automatically creates engaging photo collections based on dates, people, and themes, helping users rediscover and relive their special moments.

## Overview

Memories intelligently organizes your photos into meaningful collections without any manual effort. It uses AI-powered face recognition, object detection, and date analysis to create four types of memories:

1. **On This Day** - Photos from the same day in previous years
2. **Recent Highlights** - Days when you captured many moments
3. **People** - Collections featuring specific individuals
4. **Themes** - Photos grouped by detected objects or scenes

## Features

### On This Day Memories

Automatically surfaces photos taken on the same date in previous years, creating a nostalgic "On This Day" experience.

- **Time Range**: Configurable (default: 5 years back)
- **Grouping**: By year
- **Display**: Shows how many years ago each memory is from

### Recent Highlights

Identifies days when you took multiple photos, highlighting significant photo-taking events like trips, parties, or special occasions.

- **Time Range**: Configurable (default: last 30 days)
- **Threshold**: Minimum number of photos per day (default: 5)
- **Sorting**: Most recent first

### People Memories

Creates personalized collections featuring the same person across multiple photos.

- **Requirements**: Face detection and clustering must be enabled
- **Minimum Photos**: At least 3 photos per person
- **Naming**: Uses cluster names assigned in the People page
- **Limit**: Configurable number of people to display (default: 10)

### Theme Memories

Groups photos by common objects or themes detected through AI tagging.

- **Requirements**: AI tagging must be enabled
- **Minimum Photos**: At least 5 photos per theme
- **Categories**: Based on YOLO object detection (e.g., "Dogs", "Cars", "Food")
- **Limit**: Configurable number of themes (default: 10)

## API Endpoints

### Get All Memories

```
GET /memories/all
```

Retrieves all types of memories in a single request.

**Query Parameters:**
- `years_back` (integer, 1-20): Years to look back for "On This Day" (default: 5)
- `recent_days` (integer, 1-365): Days to look back for recent memories (default: 30)
- `min_images` (integer, 1-50): Minimum images per recent memory (default: 5)
- `people_limit` (integer, 1-50): Maximum people memories to return (default: 10)
- `tags_limit` (integer, 1-50): Maximum theme memories to return (default: 10)

**Response:**
```json
{
  "success": true,
  "message": "Successfully retrieved X total memories",
  "data": {
    "on_this_day": [...],
    "recent": [...],
    "people": [...],
    "tags": [...]
  }
}
```

### Get On This Day Memories

```
GET /memories/on-this-day
```

**Query Parameters:**
- `years_back` (integer, 1-20): Number of years to look back (default: 5)

### Get Recent Memories

```
GET /memories/recent
```

**Query Parameters:**
- `days` (integer, 1-365): Number of days to look back (default: 30)
- `min_images` (integer, 1-50): Minimum images per day (default: 5)

### Get People Memories

```
GET /memories/people
```

**Query Parameters:**
- `limit` (integer, 1-50): Maximum number of people to return (default: 10)

### Get Theme Memories

```
GET /memories/tags
```

**Query Parameters:**
- `limit` (integer, 1-50): Maximum number of themes to return (default: 10)

## User Interface

### Memory Cards

Each memory is displayed as a card containing:
- **Icon**: Visual indicator of memory type (calendar, clock, users, or tag)
- **Title**: Memory name or description
- **Subtitle**: Additional context (date, years ago, photo count)
- **Image Grid**: Thumbnail preview of photos (up to 6 initially)
- **Expand/Collapse**: Show more photos if available

### Memory Sections

Memories are organized into collapsible sections:
- Clear section headers with descriptions
- Empty state messages when no memories are found
- Helpful hints for enabling required features (AI tagging, face detection)

### Interactions

- **Click on Image**: Opens the full-screen media viewer
- **Show More/Less**: Expands/collapses the image grid
- **Scroll**: Smooth scrolling through all memory sections

## Technical Implementation

### Backend

**Database Functions** (`backend/app/database/memories.py`):
- `db_get_memories_on_this_day()`: Queries images by date
- `db_get_recent_memories()`: Groups images by recent dates
- `db_get_memories_by_people()`: Joins faces and clusters tables
- `db_get_memories_by_tags()`: Joins image_classes and mappings tables

**API Routes** (`backend/app/routes/memories.py`):
- FastAPI endpoints with query parameter validation
- Comprehensive error handling and logging
- Pydantic schemas for type safety

**Schemas** (`backend/app/schemas/memories.py`):
- Type-safe request/response models
- Nested data structures for complex memories

### Frontend

**Components**:
- `MemoryCard.tsx`: Individual memory display with image grid
- `MemorySection.tsx`: Section wrapper with header and empty states
- `Memories.tsx`: Main page component with data fetching

**State Management**:
- React Query for data fetching and caching
- Redux for image viewer state
- Loading and error states with user feedback

**Styling**:
- Tailwind CSS for responsive design
- Dark mode support
- Smooth animations and transitions

## Performance Considerations

### Database Optimization

- Efficient SQL queries with proper indexing
- LEFT JOINs to include images without tags
- Grouping and aggregation at the database level
- Configurable limits to prevent excessive data transfer

### Frontend Optimization

- Lazy loading of images
- Thumbnail previews for faster loading
- Expand/collapse to limit initial render
- React Query caching to prevent redundant API calls

## Future Enhancements

Potential improvements for the Memories feature:

1. **Location-based Memories**: Group photos by GPS coordinates
2. **Seasonal Memories**: Automatic collections for holidays and seasons
3. **Smart Titles**: AI-generated descriptive titles for memories
4. **Sharing**: Export or share memory collections
5. **Customization**: User-defined memory rules and preferences
6. **Notifications**: Daily reminders for "On This Day" memories
7. **Video Support**: Include videos in memory collections
8. **Timeline View**: Visual timeline representation of memories

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_memories.py -v
```

Tests cover:
- All API endpoints
- Parameter validation
- Response structure
- Edge cases (empty results, invalid parameters)

## Troubleshooting

### No "On This Day" Memories

- Ensure photos have valid `date_created` metadata
- Check that photos exist from previous years on the same date
- Verify the `years_back` parameter is appropriate

### No People Memories

- Enable AI tagging for folders containing photos
- Ensure face detection has run on your images
- Assign names to face clusters in the People page
- Check that clusters have at least 3 photos

### No Theme Memories

- Enable AI tagging for your photo folders
- Wait for object detection to complete
- Ensure you have at least 5 photos with the same detected object

### Performance Issues

- Reduce the `years_back`, `recent_days`, or limit parameters
- Ensure database has proper indexes
- Check for slow queries in the backend logs

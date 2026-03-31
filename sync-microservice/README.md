# PictoPy Sync Microservice

A file system synchronization microservice for PictoPy that monitors folder changes and keeps the database in sync with the filesystem.

## Features

- 🔍 **Real-time File Monitoring**: Watches all folders registered in PictoPy database
- 🗄️ **Database Integration**: Connects to main PictoPy database to get folder information
- 📊 **Health Monitoring**: Provides health check endpoints for monitoring
- ⚡ **Async Processing**: Built with FastAPI and async/await for high performance
- 🔄 **Hot Reload**: Automatically starts watching folders on startup

## Quick Start

### Prerequisites

- Python 3.8+
- PictoPy backend database should be set up and accessible
- Virtual environment (recommended)

### Installation

1. **Navigate to the sync microservice directory:**

   ```bash
   cd sync-microservice
   ```

2. **Create and activate virtual environment:**

   ```bash
   python -m venv .sync-env
   source .sync-env/bin/activate  # On Windows: .sync-env\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Start the service:**
   ```bash
   fastapi dev --port 52124
   ```

## API Endpoints

### Core Endpoints

- **`GET /`** - Service information
- **`GET /health`** - Health check with database and watcher status
- **`GET /folders`** - List all folders being watched
- **`GET /watcher/status`** - Current watcher status

### Example Responses

**Health Check:**

```json
{
  "status": "healthy",
  "database": "connected",
  "watcher": "running"
}
```

**Folders List:**

```json
{
  "total_folders": 3,
  "folders": [
    { "id": "uuid-1", "path": "/path/to/folder1" },
    { "id": "uuid-2", "path": "/path/to/folder2" }
  ]
}
```

## Architecture

```
sync-microservice/
├── app/
│   ├── config/
│   │   └── settings.py          # Configuration settings
│   ├── database/
│   │   ├── __init__.py
│   │   └── folders.py           # Database operations for folders
│   └── utils/
│       ├── __init__.py
│       └── file_watcher.py      # File watching implementation
├── main.py                      # FastAPI application
└── requirements.txt             # Dependencies
```

## Configuration

The service connects to the main PictoPy database. Update `app/config/settings.py` if needed:

```python
DATABASE_PATH = "../backend/app/database/PictoPy.db"
```

## File Watching

The service automatically:

1. **On Startup:**

   - Connects to PictoPy database
   - Retrieves all folder paths and IDs
   - Starts watching existing folders
   - Reports status

2. **During Operation:**

   - Monitors file changes (add, modify, delete)
   - Logs all detected changes
   - Maps changes to specific folder IDs
   - Prepares for future database sync operations

3. **On Shutdown:**
   - Gracefully stops file watcher
   - Cleans up resources

## Development

### Adding New Features

1. **Database Operations**: Add new functions to `app/database/folders.py`
2. **File Processing**: Extend `app/utils/file_watcher.py`
3. **API Endpoints**: Add routes to `main.py`

### Current TODOs

The file watcher currently logs changes but doesn't process them. Future enhancements:

- Image file detection and database updates
- Thumbnail generation for new images
- AI processing trigger for new images
- Database cleanup for deleted files
- Integration with main PictoPy backend APIs

## Monitoring

Use the health endpoint to monitor service status:

```bash
curl http://localhost:52124/health
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**

   - Ensure PictoPy backend database exists
   - Check database path in settings.py
   - Verify file permissions

2. **No Folders to Watch**

   - Add folders to PictoPy backend first
   - Check database has folder entries
   - Verify folder paths exist in filesystem

3. **Watcher Not Starting**
   - Check folder permissions
   - Ensure folders exist on filesystem
   - Review logs for specific errors

### Logs

The service provides detailed console output for:

- Startup process
- Database connections
- Folder discovery
- File change events
- Error conditions

## Integration

This microservice is designed to work alongside the main PictoPy backend:

- **Port 52123**: Main PictoPy backend
- **Port 52124**: Sync microservice (this service)
- **Shared Database**: Both services use the same SQLite database

The sync service operates independently but relies on the main backend's database structure.

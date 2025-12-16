# Database Migration Guide

## Quick Fix for "no such column" Errors

If you see errors like:
```
[BACKEND] | ERROR | Error getting all images: no such column: i.isFavourite
```

### Solution 1: Run Migration Script (Recommended)
This preserves your existing data:

```bash
cd backend
python migrate_database.py
```

### Solution 2: Reset Database (Nuclear Option)
⚠️ **Warning: This deletes all your data!**

```bash
cd backend
python reset_database.py
```

Then restart the backend server.

## How Migrations Work

The application now includes automatic schema migrations:

1. **Automatic Migration**: When the app starts, it checks if required columns exist
2. **Zero Downtime**: Migrations run transparently without data loss
3. **Safe Defaults**: New columns are added with sensible default values

## Manual Migration

If you need to run migrations manually:

```python
from app.database.images import db_create_images_table

# This will create tables and run any necessary migrations
db_create_images_table()
```

## Adding New Columns (For Developers)

When adding new database columns:

1. **Update the CREATE TABLE statement** in the respective database file
2. **Add migration logic** to the `_check_and_migrate_schema()` function
3. **Test the migration** on a copy of the production database
4. **Document the change** in this file

Example:
```python
def _check_and_migrate_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(images)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add new column if it doesn't exist
    if "newColumn" not in columns:
        logger.info("Adding 'newColumn' to images table")
        cursor.execute("ALTER TABLE images ADD COLUMN newColumn TEXT DEFAULT ''")
        conn.commit()
```

## Troubleshooting

### Migration Fails
- Check database file permissions
- Ensure no other process is locking the database
- Check available disk space

### Column Still Missing After Migration
- Restart the backend server
- Check logs for migration success message
- Verify the database file path in settings

### Database is Corrupted
If migration fails due to corruption:
1. Backup your database file (`*.db`)
2. Try SQLite recovery tools
3. As last resort, use `reset_database.py` (data loss!)

## Database Schema Version

Current schema includes:
- ✅ `images.isFavourite` (added: Dec 2025)
- ✅ `images.isTagged`
- ✅ `images.metadata`
- ✅ `image_classes` junction table

## Future Migrations

Planned schema changes:
- [ ] Add `rating` column for star ratings (1-5)
- [ ] Add `dateModified` column for edit tracking
- [ ] Add `albums` table for album management

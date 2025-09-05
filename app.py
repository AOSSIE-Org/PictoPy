"""
PictoPy Application Entry Point

This module serves as the main entry point for the PictoPy application.
It handles application initialization, cache management, and provides
utility functions for data refresh operations.

The module includes:
- Application initialization with cache clearing
- Data refresh functionality with selective cache invalidation
- Cache management utilities for optimal performance
"""

# Import cache utilities for managing application cache
from utils.cache import invalidate_cache


def initialize_app():
    """
    Initialize the PictoPy application.
    
    This function sets up the application environment and clears any
    stale cache data to ensure a clean startup state.
    """
    # ...existing code...
    
    # Clear any stale cache data on startup to ensure fresh data
    # This prevents issues with outdated cached information
    invalidate_cache()
    
    # ...existing code...


def refresh_data():
    """
    Refresh application data and clear relevant caches.
    
    This function is called when data needs to be refreshed, such as
    after folder structure changes or album modifications. It selectively
    clears specific cache entries to maintain performance while ensuring
    data consistency.
    """
    # ...existing code...
    
    # Clear specific caches that need refreshing
    # Albums cache - cleared when album data changes
    invalidate_cache("albums:get_all_albums")
    
    # Folder structure cache - cleared when folder hierarchy changes
    invalidate_cache("folder_structure:get_folder_structure")
    
    # ...existing code...


# ...existing code...

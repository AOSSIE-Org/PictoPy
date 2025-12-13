# Fix: Incorrect Clustering for Folders with Many Images

## 🐛 Issue
Fixes #722

## 📋 Description
This PR addresses the bug where face clustering incorrectly groups unrelated images together when processing folders with many images. The issue was caused by overly permissive DBSCAN clustering parameters that allowed faces with relatively low similarity (>0.7) to be grouped together.

## 🔧 Changes Made

### 1. **DBSCAN Clustering Parameters** (`backend/app/utils/face_clusters.py`)
- **`eps` parameter**: Reduced from `0.3` → `0.15`
  - With cosine distance, this now requires similarity > 0.85 (previously > 0.7)
  - Ensures only genuinely similar faces are clustered together
  
- **`min_samples` parameter**: Increased from `2` → `3`
  - Requires at least 3 similar faces to form a cluster
  - Reduces noise and prevents false groupings from face detection errors

### 2. **Incremental Assignment Threshold** (`backend/app/utils/face_clusters.py`)
- **`similarity_threshold`**: Increased from `0.7` → `0.85`
  - Matches the DBSCAN eps parameter for consistency
  - Prevents new faces from being incorrectly assigned to existing clusters

### 3. **Test Script Update** (`backend/test.py`)
- Updated DBSCAN parameters to match the main implementation

### 4. **Documentation Update** (`docs/backend/backend_python/image-processing.md`)
- Updated parameter values and descriptions to reflect new settings
- Added explanation of what the parameters mean for face similarity

## 🎯 Impact

### Before
- Folders with many images would create clusters with 314+ unrelated images
- Face similarity threshold of ~70% was too low for reliable clustering
- Any 2 faces with moderate similarity would form a cluster

### After
- Stricter similarity requirement (>85%) ensures accurate face grouping
- Minimum of 3 faces required prevents spurious clusters from noise
- Better clustering quality with fewer false positives

## ✅ Testing

- [x] Syntax validation passed (no Python compilation errors)
- [x] No linting errors introduced
- [x] Code changes follow existing patterns
- [x] Documentation updated to match code changes

### Testing Instructions for Reviewers

1. Reset the database: `python backend/reset_database.py`
2. Start backend and frontend
3. Add a folder with many diverse images
4. Enable AI Tagging for the folder
5. Navigate to AI-Tagging page
6. Verify that clusters now contain only related faces (no large clusters of 314+ unrelated images)

## 📊 Technical Details

The DBSCAN algorithm uses cosine distance for face embeddings. With the updated parameters:

- **eps=0.15**: Maximum cosine distance = 0.15, meaning minimum cosine similarity = 0.85
- **min_samples=3**: At least 3 faces must be within eps distance to form a cluster core

This aligns with face recognition best practices where similarity > 0.85 is considered a reliable match.

## 🔗 Related Files Changed
- `backend/app/utils/face_clusters.py`
- `backend/test.py`
- `docs/backend/backend_python/image-processing.md`

## 📝 Checklist

- [x] Code follows the project's coding standards
- [x] Changes are backward compatible
- [x] Documentation has been updated
- [x] No breaking changes introduced
- [x] Commit message follows conventional commit format
- [x] Issue number referenced in commit message

---

**Note**: This fix improves clustering accuracy but may result in fewer clusters being formed initially. This is the desired behavior as it prevents incorrect groupings. As more images of the same person are added, proper clusters will form with the higher confidence threshold.

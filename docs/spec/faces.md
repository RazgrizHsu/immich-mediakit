# Immich Face Tagging Database Structure


## Core Database Tables

### 1. `person` Table
- **Purpose**: Stores basic person information
- **Key Fields**:
  - `id`: Primary key for the person
  - `name`: Person's name (when manually assigned)
  - `faceAssetId`: Foreign key reference to `asset_faces` table
  - Other metadata fields for person management

### 2. `asset_faces` Table *(Primary Table)*
- **Purpose**: Core table storing face detection and tagging information
- **Key Fields**:
  - `id`: Primary key for the face record
  - `assetId`: Foreign key linking to the `assets` table (which image contains this face)
  - `personId`: Foreign key linking to the `person` table (which person this face belongs to)
  - `embedding`: Vector representation of the face features (used for similarity matching)
  - `imageWidth`: Width of the source image
  - `imageHeight`: Height of the source image
  - `boundingBoxX1`: Left boundary of face detection box
  - `boundingBoxY1`: Top boundary of face detection box
  - `boundingBoxX2`: Right boundary of face detection box
  - `boundingBoxY2`: Bottom boundary of face detection box

### 3. `assets` Table
- **Purpose**: Main table for all media assets
- **Relationship**: Referenced by `asset_faces.assetId`

## Table Relationships

```
assets (1) ←→ (many) asset_faces (many) ←→ (1) person
```

- **One-to-Many**: One asset can contain multiple faces
- **Many-to-One**: Multiple face detections can belong to the same person
- **Foreign Key Constraint**: `FK_95ad7106dd7b484275443f580f9` ensures `asset_faces.personId` references valid `person.id`

## Data Flow for Face Tagging

1. **Face Detection**: When an image is processed, faces are detected and stored in `asset_faces`
2. **Face Recognition**: The system uses the `embedding` field to cluster similar faces
3. **Person Assignment**: Faces are assigned to persons in the `person` table
4. **Manual Tagging**: Users can manually tag faces, creating or updating `person` records

## Implications for Duplicate Synchronization

When synchronizing metadata between duplicate images, tools need to consider:

### Face Data Synchronization
- **Person Assignments**: Merge person tags from all duplicate images
- **Face Counts**: Track total number of tagged faces across duplicates
- **Manual Tags**: Preserve manually assigned person names
- **Bounding Boxes**: Handle different face positions if image resolutions differ

### Database Operations Required
1. Query `asset_faces` for all faces in duplicate images
2. Identify unique persons across all duplicates
3. Merge person assignments to the kept image
4. Update or create new `asset_faces` records for the preserved asset
5. Ensure foreign key constraints are maintained

## Example Query Structure

```sql
-- Get all faces for a specific asset
SELECT af.*, p.name as person_name 
FROM asset_faces af 
LEFT JOIN person p ON af.personId = p.id 
WHERE af.assetId = 'your-asset-id';

-- Count unique persons in an asset
SELECT COUNT(DISTINCT personId) as unique_people_count
FROM asset_faces 
WHERE assetId = 'your-asset-id' 
AND personId IS NOT NULL;
```

## Key Considerations

- **Foreign Key Constraints**: Always ensure `personId` exists in `person` table before creating `asset_faces` records
- **Embedding Vectors**: The `embedding` field uses vector data types and requires proper database extensions (pgvector/vchord)
- **Coordinate System**: Bounding box coordinates are relative to the image dimensions
- **Manual vs Automatic**: Distinguish between automatically detected faces and manually tagged ones

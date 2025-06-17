# MediaKit Similarity Processing Data Flow Analysis

## Data Structure Overview

### Related Database Fields
- **simOk**: `INTEGER` (0=unprocessed, 1=resolved)
- **simInfos**: `TEXT` JSON array containing detailed information about similar assets
- **simGIDs**: `TEXT` JSON array containing group ID references

### Similarity Processing States
1. **Not vectorized**: `isVectored=0`
2. **Vectorized but not searched**: `isVectored=1, simOk=0, simInfos='[]'`
3. **Searched pending processing**: `isVectored=1, simOk=0, simInfos='[...]'`
4. **Resolved**: `isVectored=1, simOk=1, simGIDs='[]', simInfos='[]'`

## Main Process Analysis

### 1. Similarity Search Process (sim_FindSimilar)

```
Start → Select Asset → Vector Similarity Search → Set Group Relations → Recursive Search Child Nodes → Complete
```

**Detailed Steps:**
1. **Asset Selection**:
   - URL-specified asset takes priority
   - Otherwise select `db.pics.getAnyNonSim()` (simOk!=1 and simInfos is empty)

2. **Similarity Search**:
   - Call `db.vecs.findSimiliar()` to find similar assets
   - Threshold range: thMin ~ thMax

3. **Group Relationship Establishment**:
   - Main asset: `setSimInfos(asset.id, bseInfos, GID=rootAuid)`
   - Child assets: `setSimInfos(assId, cInfos, GID=rootAuid)`

4. **Recursive Processing**:
   - Queue processing for similar assets of child assets

### 2. User Decision Process

Select group from pending → Display in current → User selects action:

#### A. sim_SelectedDelete (Delete Selected)
```
Selected assets → immich.trashByAssets() → db.pics.deleteBy() → Remaining assets setResloveBy()
```

#### B. sim_SelectedReslove (Keep Selected)
```
Selected assets → setResloveBy() → Other assets → immich.trashByAssets() → deleteBy()
```

#### C. sim_AllReslove (Keep All)
```
All assets → setResloveBy()
```

#### D. sim_AllDelete (Delete All)
```
All assets → immich.trashByAssets() → deleteBy()
```

### 3. deleteBy Method Detailed Analysis

```python
def deleteBy(assets: List[models.Asset]):
    # 1. Collect main group IDs
    mainGIDs = [a.autoId for a in assets if a.view.isMain]
    
    # 2. Delete assets from database
    # 3. Delete from vector database
    
    # 4. Handle references in other assets
    for mainGID in mainGIDs:
        # Find unfinished assets referencing this GID
        # Remove this GID from simGIDs
        # If no remaining GIDs, clear simInfos and simGIDs
```

### 4. setResloveBy Method Analysis

```python
def setResloveBy(assets: List[models.Asset]):
    # Mark assets as resolved
    # simOk = 1, simGIDs = '[]', simInfos = '[]'
```

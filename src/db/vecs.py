from time import sleep

import numpy as np
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

from conf import envs, isDock
from util import log

lg = log.get(__name__)

keyColl = "mediakit"

conn: Optional[QdrantClient] = None

def init():
    global conn
    try:
        conn = QdrantClient(envs.qdrantUrl)

        create()
    except Exception as e:
        lg.error(f"Failed to initialize Qdrant: {str(e)}")


def close():
    global conn
    try:
        if conn is not None: conn.close()
        conn = None
        return True
    except Exception as e:
        lg.error(f"Failed to close database connection: {str(e)}")
        return False

def create():
    try:
        cols = conn.get_collections().collections
        names = [c.name for c in cols]

        if keyColl not in names:
            lg.info( f"[qdrant] creating coll[{keyColl}]..." )
            conn.create_collection(
                collection_name=keyColl,
                vectors_config=models.VectorParams(
                    size=2048,
                    distance=models.Distance.COSINE
                )
            )
            lg.info( f"[qdrant] create successfully, coll[{keyColl}]" )

    except Exception as e:
        lg.error(f"Failed to initialize Qdrant: {str(e)}")

def clear():

    try:
        if conn is None: raise RuntimeError( "[qdrant] not connectioned" )

        collections = conn.get_collections().collections
        collection_names = [c.name for c in collections]

        if keyColl in collection_names:
            lg.info( f"[qdrant] Start Clear coll[{keyColl}].." )
            conn.recreate_collection(
                collection_name=keyColl,
                vectors_config=models.VectorParams(
                    size=2048,
                    distance=models.Distance.COSINE
                ),
                timeout=60
            )
            lg.info( f"[qdrant] Success, coll[{keyColl}] deleted successfully" )

    except Exception as e:
        lg.error(f"[qdrant] Failed to clear vector database: {str(e)}")

def count():
    try:
        if conn is None: return 0

        rst = conn.count(collection_name=keyColl)
        return rst.count
    except Exception as e:
        lg.error(f"Error checking database population: {str(e)}")
        return False


def hasData():
    c = count()
    return c > 0


def deleteBy(photo_id):
    try:
        if conn is None: return False

        conn.delete(
            collection_name=keyColl,
            points_selector=models.PointIdsList(points=[photo_id])
        )
        return True
    except Exception as e:
        lg.error(f"Error deleting vector for photo {photo_id}: {str(e)}")
        return False


def save(photo_id, vector):
    try:
        if conn is None:
            return False

        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()
        elif hasattr(vector, 'tolist') and callable(getattr(vector, 'tolist')):
            vector_list = vector.tolist()
        elif isinstance(vector, list):
            vector_list = vector
        else:
            try:
                vector_list = list(vector)
            except:
                raise ValueError(f"Cannot convert vector from {type(vector)} to list")

        if not vector_list or len(vector_list) != 2048:
            raise ValueError(f"Vector length is incorrect, expected 2048, actual {len(vector_list) if vector_list else 0}")

        # lg.info(f"Saving vector to Qdrant: photo_id={photo_id}, vector length={len(vector_list)}")

        conn.upsert(
            collection_name=keyColl,
            points=[
                models.PointStruct(
                    id=photo_id,
                    vector=vector_list,
                    payload={
                        "id": photo_id
                    }
                )
            ]
        )

        try:
            stored = conn.retrieve(
                collection_name=keyColl,
                ids=[photo_id], with_vectors=True
            )
            if not stored:
                lg.info(f"Warning: Vector not successfully saved to Qdrant")
                return False

            if not hasattr(stored[0], 'vector') or stored[0].vector is None:
                lg.warn(f"Stored vector is null")

            #lg.info(f"Vector successfully saved: length={len(stored[0].vector)}")
        except Exception as ve:
            lg.info(f"Error validating vector storage: {str(ve)}")

        return True
    except Exception as e:
        lg.error(f"Error saving vector for photo {photo_id}: {str(e)}")
        return False


def find_similar_photos(photo_id, min_threshold, max_threshold, limit=100, similarity_method='cosine'):
    try:
        if conn is None:
            lg.info("Qdrant connection not initialized")
            return []

        lg.info(f"Finding similar photos for {photo_id}, threshold range: {min_threshold} - {max_threshold}")

        lg.info(f"Getting vector for photo {photo_id}...")
        target = conn.retrieve(
            collection_name=keyColl,
            ids=[photo_id],
            with_payload=True, with_vectors=True
        )

        if not target:
            lg.info(f"Vector for photo {photo_id} does not exist")
            return []

        # lg.info(f"Successfully retrieved vector for photo {photo_id}")

        vector = None
        if not hasattr(target[0], 'vector') or target[0].vector is None:
            lg.info(f"Vector for photo {photo_id} is empty")
            return []
        else:
            vector = target[0].vector

        # lg.info(f"Original vector data type: {type(vector)}")

        if isinstance(vector, np.ndarray):
            lg.info(f"Vector is a NumPy array, converting to list")
            vector = vector.tolist()
        elif hasattr(vector, 'tolist') and callable(getattr(vector, 'tolist')):
            lg.info(f"Vector has tolist method, attempting conversion")
            vector = vector.tolist()

        if not hasattr(vector, '__len__') or len(vector) == 0:
            lg.info(f"Vector format for photo {photo_id} is incorrect: {type(vector)}")
            return []

        if not isinstance(vector, list):
            try:
                vector = list(vector)
                lg.info(f"Converted vector from {type(vector)} to list, length: {len(vector)}")
            except Exception as e:
                lg.info(f"Cannot convert vector to list: {str(e)}")
                return []

        count = conn.count(collection_name=keyColl)
        lg.info(f"Total vectors in database: {count.count}")

        lg.info(f"Searching for similar photos, threshold: {min_threshold}, limit: {limit}...")

        # Set distance type
        distance = models.Distance.COSINE
        if similarity_method == 'euclidean':
            distance = models.Distance.EUCLID

        results = conn.search(
            collection_name=keyColl,
            query_vector=vector,
            limit=limit,
            score_threshold=min_threshold,
            with_payload=True
        )

        lg.info(f"Number of search results: {len(results)}")

        lg.info("All search results:")
        for i, hit in enumerate(results):
            lg.info(f"  Result {i + 1}: ID={hit.id}, similarity score={hit.score:.6f}, is self={hit.id == photo_id}")

        similar_photos = []
        for hit in results:
            if hit.id != photo_id and hit.score <= max_threshold:
                # Avoid adding the same pair twice (ensure smaller ID always comes first)
                if photo_id < hit.id:
                    similar_photos.append((photo_id, hit.id, hit.score))
                else:
                    similar_photos.append((hit.id, photo_id, hit.score))

        lg.info(f"Number of similar photos after filtering: {len(similar_photos)}")
        for i, (id1, id2, score) in enumerate(similar_photos):
            lg.info(f"  Similar pair {i + 1}: ID1={id1}, ID2={id2}, similarity score={score:.6f}")

        return similar_photos
    except Exception as e:
        lg.info(f"Error finding similar photos for {photo_id}: {str(e)}")
        import traceback
        traceback.print_stack()
        return []

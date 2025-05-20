from typing import Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmod

from conf import envs
from util import log, models
from util.err import mkErr

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
        raise mkErr(f"Failed to close database connection", e)

def create():
    try:
        cols = conn.get_collections().collections
        names = [c.name for c in cols]

        if keyColl not in names:
            lg.info(f"[qdrant] creating coll[{keyColl}]...")
            conn.create_collection(
                collection_name=keyColl,
                vectors_config=qmod.VectorParams(
                    size=2048,
                    distance=qmod.Distance.COSINE
                )
            )
            lg.info(f"[qdrant] create successfully, coll[{keyColl}]")

    except Exception as e:
        raise mkErr(f"Failed to initialize Qdrant", e)

def clear():
    try:
        if conn is None: raise RuntimeError("[qdrant] not connectioned")

        collections = conn.get_collections().collections
        collection_names = [c.name for c in collections]

        if keyColl in collection_names:
            lg.info(f"[qdrant] Start Clear coll[{keyColl}]..")
            conn.recreate_collection(
                collection_name=keyColl,
                vectors_config=qmod.VectorParams(
                    size=2048,
                    distance=qmod.Distance.COSINE
                ),
                timeout=60
            )
            lg.info(f"[qdrant] Success, coll[{keyColl}] deleted successfully")

    except Exception as e:
        raise mkErr(f"[qdrant] Failed to clear vector database", e)

def count():
    try:
        if conn is None: return 0

        rst = conn.count(collection_name=keyColl)
        return rst.count
    except Exception as e:
        raise mkErr(f"Error checking database population", e)


def hasData():
    c = count()
    return c > 0


def deleteBy(photo_id):
    try:
        if conn is None: return False

        conn.delete(
            collection_name=keyColl,
            points_selector=qmod.PointIdsList(points=[photo_id])
        )
        return True
    except Exception as e:
        raise mkErr(f"Error deleting vector for photo {photo_id}", e)


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
                qmod.PointStruct(
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
            lg.error(f"Error validating vector storage: {str(ve)}")
            raise

        return True
    except Exception as e:
        raise mkErr(f"Error saving vector for photo {photo_id}", e)


def findSimiliar(assId, thMin: float = 0.85, thMax: float = 1.0, limit=100) -> list[models.SimilarInfo]:
    try:
        if conn is None:
            lg.info("Qdrant connection not initialized")
            return []

        lg.info(f"Finding similar photos for {assId}, threshold range[{thMin}-{thMax}]")

        target = conn.retrieve(
            collection_name=keyColl,
            ids=[assId],
            with_payload=True, with_vectors=True
        )

        if not target: raise f"Vector for photo {assId} does not exist"

        # lg.info(f"Successfully retrieved vector for photo {photo_id}")

        if not hasattr(target[0], 'vector') or target[0].vector is None:
            raise f"Vector for photo {assId} is empty"

        vector = target[0].vector

        # lg.info(f"Original vector data type: {type(vector)}")

        if isinstance(vector, np.ndarray):
            lg.warn(f"Vector is a NumPy array, converting to list")
            vector = vector.tolist()
        elif hasattr(vector, 'tolist') and callable(getattr(vector, 'tolist')):
            lg.warn(f"Vector has tolist method, attempting conversion")
            vector = vector.tolist()

        if not hasattr(vector, '__len__') or len(vector) == 0:
            raise f"Vector format for photo {assId} is incorrect: {type(vector)}"

        if not isinstance(vector, list):
            try:
                vector = list(vector)
                lg.warn(f"Converted vector from {type(vector)} to list, length: {len(vector)}")
            except Exception as e:
                raise f"Cannot convert vector to list: {str(e)}"

        count = conn.count(collection_name=keyColl)
        lg.info(f"Total vectors in database: {count.count}")

        lg.info(f"Searching for similar photos, threshold: {thMin}, limit: {limit}...")

        # distance = qmod.Distance.COSINE if method == ks.use.mth.cosine else qmod.Distance.EUCLID

        rst = conn.search(collection_name=keyColl, query_vector=vector, limit=limit, score_threshold=thMin, with_payload=True)

        lg.info(f"[vecs] search results( {len(rst)} ):")
        for i, hit in enumerate(rst):
            lg.info(f"    no.{i + 1}: ID[{hit.id}], score[{hit.score:.6f}] self[{hit.id == assId}]")

        infos: list[models.SimilarInfo] = []
        for hit in rst:
            if hit.id != assId and hit.score <= thMax:
                #------------------------------------------------------------------------------------------------
                # This code compares IDs to ensure consistent ordering of similar image pairs.
                #   By always placing the smaller ID first (ida) and larger ID second (idb):
                #
                #   1. Prevents duplicate pairs - avoids storing both (A,B) and (B,A)
                #   2. Creates consistent results regardless of search direction
                #   3. Simplifies database operations by maintaining a canonical representation
                #
                #   Example: For photos 100 and 200, only stores (100,200) instead of both (100,200) and (200,100).
                #------------------------------------------------------------------------------------------------
                if assId < hit.id:
                    infos.append(models.SimilarInfo(assId, hit.id, hit.score))
                else:
                    infos.append(models.SimilarInfo(hit.id, assId, hit.score))

        lg.info(f"Number of similar photos after filtering: {len(infos)}")
        for i, (id1, id2, score) in enumerate(infos):
            lg.info(f"  Similar pair {i + 1}: ID1={id1}, ID2={id2}, similarity score={score:.6f}")

        return infos
    except Exception as e:
        raise mkErr(f"Error finding similar photos for {assId}", e)

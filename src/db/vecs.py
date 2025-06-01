from typing import Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmod

from conf import envs
from util import log
from mod import models
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
        if not conn.collection_exists(keyColl):
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

def cleanAll():
    try:
        if conn is None: raise RuntimeError("[qdrant] not connectioned")

        exist = conn.collection_exists(keyColl)

        if exist:
            lg.info(f"[qdrant] Start Clear coll[{keyColl}]..")
            conn.delete_collection(keyColl, 60 * 5)
            lg.info(f"[qdrant] coll[{keyColl}] deleted")

        create()

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


def deleteBy(assIds: list[str]):
    try:
        if conn is None: return False

        rst = conn.delete(
            collection_name=keyColl,
            points_selector=qmod.PointIdsList(points=assIds)
        )

        lg.info(f"[vec] delete status[{rst}] ids: {assIds}")

        return True
    except Exception as e:
        raise mkErr(f"Error deleting vector for asset {assIds}", e)


def save(assId, vector):
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

        # lg.info(f"Saving vector to Qdrant: assId={assId}, vector length={len(vector_list)}")

        conn.upsert(
            collection_name=keyColl,
            points=[
                qmod.PointStruct(
                    id=assId,
                    vector=vector_list,
                    payload={
                        "id": assId
                    }
                )
            ]
        )

        try:
            stored = conn.retrieve(
                collection_name=keyColl,
                ids=[assId], with_vectors=True
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
        raise mkErr(f"Error saving vector for asset {assId}", e)


#------------------------------------------------------------------------
# only return different id
#------------------------------------------------------------------------
def findSimiliar(assId, thMin: float = 0.95, thMax: float = 1.0, limit=100) -> list[models.SimInfo]:
    try:
        if conn is None:
            lg.info("Qdrant connection not initialized")
            return []

        lg.info(f"Finding similar assets for {assId}, threshold[{thMin}-{thMax}]")

        target = conn.retrieve(
            collection_name=keyColl,
            ids=[assId],
            with_payload=True, with_vectors=True
        )

        if not target: raise RuntimeError(f"Vector for asset {assId} does not exist")

        # lg.info(f"Successfully retrieved vector for asset {assId}")

        if not hasattr(target[0], 'vector') or target[0].vector is None:
            raise RuntimeError(f"Vector for asset {assId} is empty")

        vector = target[0].vector

        # lg.info(f"Original vector data type: {type(vector)}")

        if isinstance(vector, np.ndarray):
            lg.warn(f"Vector is a NumPy array, converting to list")
            vector = vector.tolist()
        elif hasattr(vector, 'tolist') and callable(getattr(vector, 'tolist')):
            lg.warn(f"Vector has tolist method, attempting conversion")
            vector = vector.tolist()

        if not hasattr(vector, '__len__') or len(vector) == 0:
            raise RuntimeError(f"Vector format for asset {assId} is incorrect: {type(vector)}")

        if not isinstance(vector, list):
            try:
                vector = list(vector)
                lg.warn(f"Converted vector from {type(vector)} to list, length: {len(vector)}")
            except Exception as e:
                raise RuntimeError(f"Cannot convert vector to list: {str(e)}")

        count = conn.count(collection_name=keyColl)
        lg.info(f"Total vectors in database: {count.count}")

        lg.info(f"Searching for similar assets, threshold: {thMin}, limit: {limit}...")

        # distance = qmod.Distance.COSINE if method == ks.use.mth.cosine else qmod.Distance.EUCLID

        rst = conn.search(collection_name=keyColl, query_vector=vector, limit=limit, score_threshold=thMin, with_payload=True)

        infos: list[models.SimInfo] = []

        #lg.info(f"[vecs] search results( {len(rst)} ):")
        for i, hit in enumerate(rst):
            #lg.info(f"    no.{i + 1}: ID[{hit.id}], score[{hit.score:.6f}] self[{hit.id == assId}]")

            if hit.score <= thMax or hit.id == assId:  #always add self
                isSelf = hit.id == assId
                infos.append(models.SimInfo(hit.id, hit.score, isSelf))

        return infos
    except Exception as e:
        raise mkErr(f"Error finding similar assets for {assId}", e)

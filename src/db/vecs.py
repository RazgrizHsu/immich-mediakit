from typing import Optional, Tuple

import numpy as np
import qdrant_client.http.models
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
        if conn is None: raise RuntimeError("[vecs] Qdrant connection not initialized")

        rst = conn.count(collection_name=keyColl)
        return rst.count
    except Exception as e:
        raise mkErr(f"Error checking database population", e)


def deleteBy(assIds: list[str]):
    try:
        if conn is None: raise RuntimeError("[vecs] Qdrant connection not initialized")

        rst = conn.delete(
            collection_name=keyColl,
            points_selector=qmod.PointIdsList(points=assIds)
        )

        lg.info(f"[vec] delete status[{rst}] ids: {assIds}")
        if rst.status != qmod.UpdateStatus.COMPLETED:
            raise RuntimeError(f"Delete operation failed with status: {rst.status}")


    except Exception as e:
        raise mkErr(f"Error deleting vector for asset {assIds}", e)


def save(assId: str, vector: np.ndarray, confirm=True):
    try:
        if conn is None: raise RuntimeError("[vecs] Qdrant connection not initialized")

        if not isinstance(vector, np.ndarray):
            raise ValueError(f"[vecs] Cannot convert vector from {type(vector)} to list")

        vecList = vector.tolist()
        if not vecList or len(vecList) != 2048:
            raise ValueError(f"[vecs] Vector length is incorrect, expected 2048, actual {len(vecList) if vecList else 0}")

        # override exists
        conn.upsert(
            collection_name=keyColl,
            points=[qmod.PointStruct(id=assId, vector=vecList, payload={"id": assId})]
        )

        if confirm:
            try:
                stored = conn.retrieve(
                    collection_name=keyColl,
                    ids=[assId], with_vectors=True
                )
                if not stored: raise RuntimeError(f"[vecs] Failed save vector assId[{assId}]")
                if not hasattr(stored[0], 'vector') or stored[0].vector is None: raise RuntimeError(f"[vecs] Stored vector is null assId[{assId}]")

            except Exception as ve:
                lg.error(f"Error validating vector storage: {str(ve)}")
                raise

    except Exception as e:
        raise mkErr(f"Error saving vector for asset {assId}", e)


def getBy(assId):
    try:
        if conn is None: raise RuntimeError("[vecs] Qdrant connection not initialized")

        dst = conn.retrieve(
            collection_name=keyColl,
            ids=[assId],
            with_payload=True, with_vectors=True
        )

        if not dst: raise RuntimeError(f"[vecs] Vector for asset {assId} does not exist")

        if not hasattr(dst[0], 'vector') or dst[0].vector is None:
            raise RuntimeError(f"[vecs] Vector for asset {assId} is empty")

        vector = dst[0].vector

        # lg.info(f"Original vector data type: {type(vector)}")

        if isinstance(vector, np.ndarray):
            raise RuntimeError(f"[vecs] Vector is a NumPy array, converting to list")
        if hasattr(vector, 'tolist') and callable(getattr(vector, 'tolist')):
            raise RuntimeError(f"[vecs] Vector has tolist method, attempting conversion")

        if not hasattr(vector, '__len__') or len(vector) == 0:
            raise RuntimeError(f"[vecs] Vector format for asset assId[{assId}] is incorrect: {type(vector)}")

        if not isinstance(vector, list):
            raise RuntimeError(f"[vecs] Vector not a list: {type(vector)}")
            # try:
            #     vector = list(vector)
            #     lg.warn(f"[vecs] Converted vector from {type(vector)} to list, length: {len(vector)}")
            # except Exception as e:
            #     raise RuntimeError(f"[vecs] Cannot convert vector to list: {str(e)}")

        return vector

    except Exception as e:
        raise mkErr(f"[vecs] Error get asset vector assId[{assId}]", e)


def search(vec, thMin: float = 0.95, thMax: float = 1.0, limit=100) -> list[qdrant_client.http.models.ScoredPoint]:
    try:
        if conn is None: raise RuntimeError("Qdrant connection not initialized")

        # distance = qmod.Distance.COSINE if method == ks.use.mth.cosine else qmod.Distance.EUCLID

        # if thMin >= 0.97: thMin = 0.95

        rep = conn.query_points(collection_name=keyColl, query=vec, limit=limit, score_threshold=thMin, with_payload=True)
        rst = rep.points

        return rst

    except Exception as e:
        raise mkErr(f"[vecs] Error searching {vec}", e)


#------------------------------------------------------------------------
# only return different id
#------------------------------------------------------------------------
def findSimiliar(assId, thMin: float = 0.95, thMax: float = 1.0, limit=100) -> Tuple[list[float], list[models.SimInfo]]:
    try:
        if conn is None: raise RuntimeError("Qdrant connection not initialized")

        lg.info(f"[vecs] Finding similar assets for {assId}, threshold[{thMin}-{thMax}]")
        vector = getBy(assId)

        rst = conn.count(collection_name=keyColl)

        lg.info(f"[vecs] Searching for similar assets, limit[{limit}] total{rst.count}")

        # distance = qmod.Distance.COSINE if method == ks.use.mth.cosine else qmod.Distance.EUCLID

        rep = conn.query_points(collection_name=keyColl, query=vector, limit=limit, score_threshold=thMin, with_payload=True)
        rst = rep.points
        infos: list[models.SimInfo] = []

        lg.info(f"[vecs] search results( {len(rst)} ):")
        for i, hit in enumerate(rst):
            lg.info(f"    no.{i + 1}: ID[{hit.id}], score[{hit.score:.6f}] self[{hit.id == assId}]")

            if hit.score <= thMax or hit.id == assId:  #always add self
                isSelf = hit.id == assId
                infos.append(models.SimInfo(hit.id, hit.score, isSelf))

        return vector, infos
    except Exception as e:
        raise mkErr(f"Error finding similar assets for {assId}", e)

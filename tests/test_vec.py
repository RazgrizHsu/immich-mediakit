#!/usr/bin/env python
import os
import sys
import json
import unittest
import numpy as np

import imgs
import vecs

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from util import log
from mod import models
from conf import ks, co
import db

lg = log.get(__name__)

db.init()
vecs.init()

class TestBase(unittest.TestCase):

    def test_sim(self):
        ass = db.pics.getAnyNonSim()
        lg.info(f"asset: #{ass.autoId}")


        infos = db.vecs.findSimiliar(ass.id, 0.80, 1.0)

        simIds = [i.id for i in infos]

        lg.info(f"Found {len(simIds)} similar, ids: {simIds}")

        # select back all simIds assets
        # db.pics.get()

        for idx, info in enumerate(infos):
            aid, score, self = info
            lg.info(f"  Similar pair {idx + 1}: ID[{aid}], score[{score:.6f}]")


# 16:06:24.917|INFO| [vecs] search results( 3 ):
# 16:06:24.917|INFO|     no.1: ID[6a6c4437-c5ad-492d-8c85-9fda81fe976f], score[1.000000] self[True]
# 16:06:24.917|INFO|     no.2: ID[1a307f90-4af0-4fb3-af45-a5db141116be], score[0.827678] self[False]
# 16:06:24.917|INFO|     no.3: ID[c7002045-602b-42cd-a923-53328976d67e], score[0.819848] self[False]
# 16:06:24.917|INFO| Found 3 similar, ids: ['6a6c4437-c5ad-492d-8c85-9fda81fe976f', '1a307f90-4af0-4fb3-af45-a5db141116be', 'c7002045-602b-42cd-a923-53328976d67e']

    def test_sim_2(self):
        a1 = db.pics.getById("6a6c4437-c5ad-492d-8c85-9fda81fe976f")
        a2 = db.pics.getById("1a307f90-4af0-4fb3-af45-a5db141116be")

        v1 = db.vecs.getBy(a1.id)
        v2 = db.vecs.getBy(a2.id)

        lg.info( f"v1:{v1} v2:{v2}" )

        rst = np.dot(v1, v2)

        lg.info( f"rst: {rst}" )

    def test_sim(self):
        ass = db.pics.getAnyNonSim()
        if not ass: raise RuntimeError( "no asset" )
        lg.info(f"asset: #{ass.autoId}")


        infos = db.vecs.findSimiliar(ass.autoId, 0.80, 1.0)

        simIds = [info.dix for info in infos]

        lg.info(f"Found {len(simIds)} similar, ids: {simIds}")

        # select back all simIds assets
        # db.pics.get()

        for idx, info in enumerate(infos):
            aid, score = info.toTuple()
            lg.info(f"  Similar pair {idx + 1}: ID[{aid}], score[{score:.6f}]")




    def test_insert(self):
        ass = db.pics.getAnyNonSim()
        lg.info(f"asset: #{ass.autoId}")

        #vecs.deleteBy([ ass.id ])

        pathImg = ass.getImagePath()
        lg.info( f"path: {pathImg}" )

        img = imgs.getImg(pathImg)
        vec = imgs.extractFeatures( img )

        lg.info( f"vec: {vec}" )

        ps = vecs.search( vec )
        lg.info( f"rst: {ps}" )

        vecs.save( ass.id, vec )

        lg.info( "save, read agagin.." )

        ps = vecs.search( vec )
        lg.info( f"rst: {ps}" )


    def test_spec(self):
        aid = "8d84a68f-ff7c-4559-bbe8-034ba5162260"

        ass = db.pics.getById(aid)

        lg.info( f"ass: {ass}" )

        pathImg = ass.getImagePath()
        lg.info( f"path: {pathImg}" )

        img = imgs.getImg(pathImg)
        vec = imgs.extractFeatures( img )

        lg.info( f"vec: {vec}" )

        ps = db.vecs.search( vec, 0.5 )
        cntPs = len(ps)
        lg.info( f"rst({cntPs}): {ps}" )

        if cntPs <= 0: self.fail( "should had point in vec db" )

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python
import os
import sys
import json
import unittest

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

        ps = vecs.search( vec, 0.5 )
        cntPs = len(ps)
        lg.info( f"rst({cntPs}): {ps}" )

        if cntPs <= 0: self.fail( "should had point in vec db" )




        #if not simIds:
        #    self.fail(f"no similar pairs")


if __name__ == "__main__":
    unittest.main()

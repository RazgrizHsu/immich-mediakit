#!/usr/bin/env python
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from util import log
from mod import models
from conf import ks, co
import db

lg = log.get(__name__)

db.init()

class TestBase(unittest.TestCase):
    def test_base(self):
        lg.info("ok")

    def test_code(self):
        mdl = models.Mdl()

        mdl.id = ks.pg.fetch
        mdl.cmd = ks.cmd.fetch.asset
        mdl.args = {'a': 'what?'}

        tsk = mdl.mkTsk()
        if not tsk: self.fail("no task")

        self.assertEqual(mdl.id, tsk.id)
        self.assertEqual(mdl.cmd, tsk.cmd)
        self.assertEqual(mdl.args, tsk.args)
        lg.info(f"mdl: {mdl}")
        lg.info(f"tsk: {tsk}")

        self.assertEqual(tsk.name, ks.pg.fetch.name)

        tit = ks.pg.find(tsk.id)
        self.assertIsNotNone(tit, f'NotFound id[{tsk.id}]')

        if tit:
            lg.info(f'tit.cmds.fetch: {tit}')


        class a(co.to):
            a = 1
            b = 2

        lg.info(f"a.to: {a.dict()}")


    def test_sim_nonFinish(self):
        asset = db.pics.getAnySimPending()

        lg.info(f"asset: {asset}")

        for idx, info in enumerate(asset.simInfos):
            aid, score = info.toTuple()
            lg.info(f"  Similar pair {idx + 1}: ID[{aid}], score[{score:.6f}]")

    def test_sim(self):
        asset = db.pics.getAnyNonSim()
        lg.info(f"asset: {asset}")

        infos = db.vecs.findSimiliar(asset.id, 0.8, 1.0)

        simIds = [i.id for i in infos]

        lg.info(f"Found {len(simIds)} similar, ids: {simIds}")

        # select back all simIds assets
        # db.pics.get()

        for idx, info in enumerate(infos):
            aid, score = info.toTuple()
            lg.info(f"  Similar pair {idx + 1}: ID[{aid}], score[{score:.6f}]")


if __name__ == "__main__":
    unittest.main()

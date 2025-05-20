#!/usr/bin/env python
import json
import os
import sys
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from util.models import Now, Usr, Nfy, Tsk, Mdl, Asset, AssetExif
from util.baseModel import Json
from util import log
from conf import ks, co

lg = log.get(__name__)


class TestBase(unittest.TestCase):
    def test_base(self):
        lg.info( "ok" )

    def test_code(self):
        mdl = Mdl()

        mdl.id = ks.pg.fetch
        mdl.cmd = ks.cmd.fetch.asset
        mdl.args = { 'a':'what?' }

        tsk = mdl.mkTsk()
        if not tsk: self.fail( "no task" )

        self.assertEqual(mdl.id, tsk.id)
        self.assertEqual(mdl.cmd, tsk.cmd)
        self.assertEqual(mdl.args, tsk.args)
        lg.info( f"mdl: {mdl}" )
        lg.info( f"tsk: {tsk}" )

        self.assertEqual(tsk.name, ks.pg.fetch.name )


        tit = ks.pg.find( tsk.id )
        self.assertIsNotNone( tit, f'NotFound id[{tsk.id}]' )

        if tit:
            lg.info( f'tit.cmds.fetch: {tit}')


        class a(co.to):
            a = 1
            b = 2

        lg.info( f"a.to: { a.dict() }" )



if __name__ == "__main__":
    unittest.main()

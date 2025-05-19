#!/usr/bin/env python
import json
import os
import sys
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from util.models import Now, Usr, AppState, Nfy, Tsk, Mdl, Asset, AssetExif
from util.baseModel import Json
import db.pics as pics
from util import log

lg = log.get(__name__)


class TestBase(unittest.TestCase):
    def test_base(self):
        lg.info( "ok" )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


from util import log
lg = log.get(__name__)

class TestBase(unittest.TestCase):

    def test(self):

        v = 1
        b = v + 50

        lg.info(f"test b[ {b} ]")



        pass




        #if not simIds:
        #    self.fail(f"no similar pairs")


if __name__ == "__main__":
    unittest.main()

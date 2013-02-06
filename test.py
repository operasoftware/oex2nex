#!/usr/bin/env python

import unittest

from tests.api_finder import TestAPIFinder
from tests.browser_action import TestBrowserAction
from tests.norm_version import TestNormVersion
from tests.crx import TestCRX


def tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    loader.sortTestMethodsUsing = None
    suite.addTests(loader.loadTestsFromTestCase(TestAPIFinder))
    suite.addTests(loader.loadTestsFromTestCase(TestBrowserAction))
    suite.addTests(loader.loadTestsFromTestCase(TestNormVersion))
    suite.addTests(loader.loadTestsFromTestCase(TestCRX))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(tests())

#!/usr/bin/env python

import unittest
import os
import zipfile
import subprocess


class TestCRX(unittest.TestCase):
    def setUp(self):
        subprocess.call("python convertor.py -x fixtures/manifest-test.oex fixtures/converted/manifest-test",
                        shell=True)

    def tearDown(self):
        subprocess.call("rm -r fixtures/converted/*", shell=True)

    def test_crx_exists(self):
        self.assertTrue(os.path.isfile("fixtures/converted/manifest-test.crx"))

    def test_crx_files(self):
        crx = zipfile.ZipFile("fixtures/converted/manifest-test.crx", "r")
        # we expect these files to get copied over
        expected = ["manifest.json", "hello.png", "popup.html", "index.html",
                    "oex_shim/operaextensions_popup.js",
                    "oex_shim/popup_resourceloader.html",
                    "oex_shim/popup_resourceloader.js",
                    "oex_shim/operaextensions_background.js",
                    "inline_script_index_1.js"]
        for file in expected:
            self.assertIn(file, crx.namelist())
        #config.xml shouldn't get copied over
        self.assertNotIn("config.xml", crx.namelist())

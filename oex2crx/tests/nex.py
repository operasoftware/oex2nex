#!/usr/bin/env python

import unittest
import os
import zipfile
import subprocess


class TestNEX(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.call("python convertor.py -x tests/fixtures/manifest-test.oex tests/fixtures/converted/manifest-test",
                        shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/manifest-test-dir tests/fixtures/converted/manifest-test-dir",
                        shell=True)

    @classmethod
    def tearDownClass(cls):
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_nex_exists(self):
        self.assertTrue(os.path.isfile("tests/fixtures/converted/manifest-test.nex"))

    def test_nex_exists_from_dir(self):
        self.assertTrue(os.path.isfile("tests/fixtures/converted/manifest-test-dir.nex"))

    def test_nex_files(self):
        nex = zipfile.ZipFile("tests/fixtures/converted/manifest-test.nex", "r")
        # we expect these files to get copied over
        expected = ["manifest.json", "hello.png", "popup.html", "index.html",
                    "oex_shim/operaextensions_popup.js",
                    "oex_shim/popup_resourceloader.html",
                    "oex_shim/popup_resourceloader.js",
                    "oex_shim/operaextensions_background.js",
                    "inline_script_index_1.js"]
        for file in expected:
            self.assertIn(file, nex.namelist())
        #config.xml shouldn't get copied over
        self.assertNotIn("config.xml", nex.namelist())

    def test_nex_files_from_dir(self):
        nex = zipfile.ZipFile("tests/fixtures/converted/manifest-test-dir.nex", "r")
        # we expect these files to get copied over
        expected = ["manifest.json", "hello.png", "popup.html", "index.html",
                    "oex_shim/operaextensions_popup.js",
                    "oex_shim/popup_resourceloader.html",
                    "oex_shim/popup_resourceloader.js",
                    "oex_shim/operaextensions_background.js",
                    "inline_script_index_1.js"]
        for file in expected:
            self.assertIn(file, nex.namelist())
        #config.xml shouldn't get copied over
        self.assertNotIn("config.xml", nex.namelist())

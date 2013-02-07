#!/usr/bin/env python

import unittest
import zipfile
import subprocess
import json
import re

#TODO: add another oex with multiple images, test that works
#TODO: add different oexes for different API permissions, test that works
#TODO just loop over all these tests for multiple fixtures?


class TestManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/manifest-test.oex tests/fixtures/converted/manifest-test",
                        shell=True)
        crx = zipfile.ZipFile("tests/fixtures/converted/manifest-test.crx", "r")
        cls.manifest = crx.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_manifest_parses(self):
        """The manifest should parse as JSON"""
        self.assertIsInstance(self.json, dict)

    def test_manifest_has_keys(self):
        """The manifest has expected keys"""
        keys = ["description", "manifest_version", "version", "background",
                "icons", "browser_action", "web_accessible_resources",
                "permissions"]
        for key in keys:
            self.assertIn(key, self.json)

    def test_valid_version(self):
        """The extension version is valid"""
        version = self.json.get("version")
        valid_version = re.match(r"^(([0-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|"
                                 "6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2]"
                                 "[0-9]|6553[0-6])\.){0,3}([0-9]|[1-9][0-9]"
                                 "{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4]"
                                 "[0-9]{2}|655[0-2][0-9]|6553[0-6])$", version)
        self.assertTrue(valid_version)
        self.assertIsInstance(version, basestring)

    def test_name(self):
        """Test that the extension name exists, and is a string"""
        name = self.json.get("name")
        self.assertIsNotNone(name)
        self.assertIsInstance(name, basestring)

    def test_description(self):
        """Test that the extension description exists, and is a string"""
        description = self.json.get("description")
        self.assertIsNotNone(description)
        self.assertIsInstance(description, basestring)

    def test_indexfile(self):
        """Test that the extension indexfile exists, and is a string"""
        indexfile = self.json.get("background").get("page")
        self.assertIsNotNone(indexfile)
        self.assertIsInstance(indexfile, basestring)

    def test_csp(self):
        """Test that default CSP policy is in place"""
        csp = self.json.get("content_security_policy")
        self.assertEqual(csp, "script-src \'self\' \'unsafe-eval\'; object-src \'unsafe-eval\';")


class TestManifestIconsFileName(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/manifest-icon-filename-test.oex tests/fixtures/converted/test",
                        shell=True)
        crx = zipfile.ZipFile("tests/fixtures/converted/test.crx", "r")
        cls.manifest = crx.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)
        cls.icons = cls.json.get("icons")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_expected_sizes(self):
        self.assertEqual(3, len(self.icons))

    def test_512_not_included(self):
        """This extension has a 512 icon that we don't want"""
        self.assertIsNone(self.icons.get("512"))


class TestManifestIconsAttr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/manifest-icon-attr-test.oex tests/fixtures/converted/test",
                        shell=True)
        crx = zipfile.ZipFile("tests/fixtures/converted/test.crx", "r")
        cls.manifest = crx.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)
        cls.icons = cls.json.get("icons")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_expected_sizes(self):
        self.assertEqual(3, len(self.icons))

    def test_512_not_included(self):
        """This extension has a 512 icon that we don't want"""
        self.assertIsNone(self.icons.get("512"))

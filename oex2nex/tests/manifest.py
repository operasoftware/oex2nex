#!/usr/bin/env python

import unittest
import zipfile
import subprocess
import json
import re
import os


class TestManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        if not os.path.exists("tests/fixtures/converted"):
            os.makedirs("tests/fixtures/converted")
        subprocess.call("python convertor.py -x tests/fixtures/manifest-test.oex tests/fixtures/converted/manifest-test",
                        shell=True)
        nex = zipfile.ZipFile("tests/fixtures/converted/manifest-test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
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
        nex = zipfile.ZipFile("tests/fixtures/converted/test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
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
        nex = zipfile.ZipFile("tests/fixtures/converted/test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
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


class TestManifestEmptyIconSrc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/manifest-icon-empty-src.oex tests/fixtures/converted/test",
                        shell=True)
        nex = zipfile.ZipFile("tests/fixtures/converted/test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)
        #this should be None, because the config.xml has <icon src="">
        cls.icons = cls.json.get("icons")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_no_icon_prop(self):
        """There shouldn't be any icons in the manifest.json"""
        self.assertIsNone(self.icons)

class TestManifestMultiEmptyIconSrc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/manifest-icon-src-multi-empty.oex tests/fixtures/converted/test",
                        shell=True)
        nex = zipfile.ZipFile("tests/fixtures/converted/test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)
        #this should be None, because the config.xml has <icon src="">
        cls.icons = cls.json.get("icons")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_no_icon_prop(self):
        """There shouldn't be any icons in the manifest.json"""
        self.assertIsNone(self.icons)


class TestManifestEmptyAndNonEmptyIconSrc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/manifest-icon-empty-and-nonempty-src.oex tests/fixtures/converted/test",
                        shell=True)
        nex = zipfile.ZipFile("tests/fixtures/converted/test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)
        cls.icons = cls.json.get("icons")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_no_icon_prop(self):
        """There's one bogus and one good icon in hereself."""
        self.assertIsNotNone(self.icons)

    def test_128_is_included(self):
        """This extension has a 128 icon that we want"""
        self.assertIsNotNone(self.icons.get("128"))


class TestManifestSpeedDialAttr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/permissions-speeddial-001.oex tests/fixtures/converted/test",
                        shell=True)
        nex = zipfile.ZipFile("tests/fixtures/converted/test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)
        cls.speeddial = cls.json.get("speeddial")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_is_dict(self):
        self.assertIsInstance(self.speeddial, dict)

    def test_has_url(self):
        self.assertIsNotNone(self.speeddial.get("url"))

class TestManifestDeveloperAttr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/manifest-developer-attr-001.oex tests/fixtures/converted/test",
                        shell=True)
        nex = zipfile.ZipFile("tests/fixtures/converted/test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)
        cls.developer = cls.json.get("developer")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_is_unicode(self):
        self.assertIsInstance(self.developer, unicode)

    def test_is_andreas(self):
        self.assertEqual(self.developer, "andreasbovens")

class TestManifestEmptyDeveloperAttr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/manifest-developer-attr-002.oex tests/fixtures/converted/test",
                        shell=True)
        nex = zipfile.ZipFile("tests/fixtures/converted/test.nex", "r")
        cls.manifest = nex.open("manifest.json", "r").read()
        cls.json = json.loads(cls.manifest)
        cls.developer = cls.json.get("developer")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_is_none(self):
        self.assertIsNone(self.developer)

    def test_is_not_andreas(self):
        self.assertNotEqual(self.developer, "andreasbovens")

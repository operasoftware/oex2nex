#!/usr/bin/env python

import unittest
import zipfile
import subprocess
import json


class TestContextMenuPerms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/permissions-context-menu-001.oex tests/fixtures/converted/test1", shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/permissions-context-menu-002.oex tests/fixtures/converted/test2", shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/permissions-context-menu-003.oex tests/fixtures/converted/test3", shell=True)
        cls.nex1 = zipfile.ZipFile("tests/fixtures/converted/test1.nex", "r")
        cls.nex2 = zipfile.ZipFile("tests/fixtures/converted/test2.nex", "r")
        cls.nex3 = zipfile.ZipFile("tests/fixtures/converted/test3.nex", "r")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_permission_exists1(self):
        manifest = self.nex1.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("contextMenus", perms)

    def test_permission_exists2(self):
        manifest = self.nex2.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("contextMenus", perms)

    def test_permission_exists3(self):
        manifest = self.nex3.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("contextMenus", perms)


class TestCookiesPerms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/permissions-share-cookies-001.oex tests/fixtures/converted/test1", shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/permissions-share-cookies-002.oex tests/fixtures/converted/test2", shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/permissions-share-cookies-003.oex tests/fixtures/converted/test3", shell=True)
        cls.nex1 = zipfile.ZipFile("tests/fixtures/converted/test1.nex", "r")
        cls.nex2 = zipfile.ZipFile("tests/fixtures/converted/test2.nex", "r")
        cls.nex3 = zipfile.ZipFile("tests/fixtures/converted/test3.nex", "r")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_permission_exists1(self):
        manifest = self.nex1.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("cookies", perms)

    def test_permission_exists2(self):
        manifest = self.nex2.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("cookies", perms)

    def test_permission_exists3(self):
        manifest = self.nex3.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("cookies", perms)


class TestTabsPerms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/permissions-tabs-001.oex tests/fixtures/converted/test1", shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/permissions-tabs-002.oex tests/fixtures/converted/test2", shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/permissions-tabs-003.oex tests/fixtures/converted/test3", shell=True)
        cls.nex1 = zipfile.ZipFile("tests/fixtures/converted/test1.nex", "r")
        cls.nex2 = zipfile.ZipFile("tests/fixtures/converted/test2.nex", "r")
        cls.nex3 = zipfile.ZipFile("tests/fixtures/converted/test3.nex", "r")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_permission_exists1(self):
        manifest = self.nex1.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("tabs", perms)

    def test_permission_exists2(self):
        manifest = self.nex2.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("tabs", perms)

    def test_permission_exists3(self):
        manifest = self.nex3.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("tabs", perms)


class TestWebRequestPerms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Convert the test"""
        subprocess.call("python convertor.py -x tests/fixtures/permissions-url-filter-001.oex tests/fixtures/converted/test1", shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/permissions-url-filter-002.oex tests/fixtures/converted/test2", shell=True)
        subprocess.call("python convertor.py -x tests/fixtures/permissions-url-filter-003.oex tests/fixtures/converted/test3", shell=True)
        cls.nex1 = zipfile.ZipFile("tests/fixtures/converted/test1.nex", "r")
        cls.nex2 = zipfile.ZipFile("tests/fixtures/converted/test2.nex", "r")
        cls.nex3 = zipfile.ZipFile("tests/fixtures/converted/test3.nex", "r")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        subprocess.call("rm -r tests/fixtures/converted/*", shell=True)

    def test_permission_exists1(self):
        manifest = self.nex1.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("webRequest", perms)
        self.assertIn("webRequestBlocking", perms)

    def test_permission_exists2(self):
        manifest = self.nex2.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("webRequest", perms)
        self.assertIn("webRequestBlocking", perms)

    def test_permission_exists3(self):
        manifest = self.nex3.open("manifest.json", "r").read()
        _json = json.loads(manifest)
        perms = _json.get("permissions")
        self.assertIn("webRequest", perms)
        self.assertIn("webRequestBlocking", perms)

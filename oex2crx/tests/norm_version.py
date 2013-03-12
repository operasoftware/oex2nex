#!/usr/bin/env python

import unittest
import re


class TestNormVersion(unittest.TestCase):
    # Not very elegant to repeat this method here, but useful until we
    # have a better way to test w/ actual extensions as fixtures
    def normalize_version(self, version):
        #version must be between 1-4 dot-separated integers each between
        #0 and 65536.
        version = str(version)
        version = re.sub(r'[^\d\.]+', '.', version)
        version = version.strip('.')
        valid_version = re.match(r"^(([0-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|"
                                 "6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2]"
                                 "[0-9]|6553[0-6])\.){0,3}([0-9]|[1-9][0-9]"
                                 "{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4]"
                                 "[0-9]{2}|655[0-2][0-9]|6553[0-6])$", version)
        if not valid_version:
            version = "1.0.0.1"
        return version

    def test_version(self):
        version = "0."
        self.assertEqual(self.normalize_version(version), "0")

    def test_version2(self):
        version = "1.1"
        self.assertEqual(self.normalize_version(version), "1.1")

    def test_version3(self):
        version = "21.1.1"
        self.assertEqual(self.normalize_version(version), "21.1.1")

    def test_version4(self):
        version = "1.1.65535."
        self.assertEqual(self.normalize_version(version), "1.1.65535")

    def test_version5(self):
        version = "1.65535.1.1"
        self.assertEqual(self.normalize_version(version), "1.65535.1.1")

    def test_version6(self):
        version = "1.1.1.1.99"
        self.assertEqual(self.normalize_version(version), "1.0.0.1")

    def test_version7(self):
        version = "65535.65535.65535.65535"
        self.assertEqual(self.normalize_version(version),
                         "65535.65535.65535.65535")

    def test_version8(self):
        version = "65535.65535.65535.65537"
        self.assertEqual(self.normalize_version(version), "1.0.0.1")

    def test_version9(self):
        version = "1.0-beta"
        self.assertEqual(self.normalize_version(version), "1.0")

    def test_version10(self):
        version = "Version Three Point Oh"
        self.assertEqual(self.normalize_version(version), "1.0.0.1")

    def test_version_none(self):
        version = None
        self.assertEqual(self.normalize_version(version), "1.0.0.1")

    def test_version_false(self):
        version = False
        self.assertEqual(self.normalize_version(version), "1.0.0.1")

    def test_version_true(self):
        version = True
        self.assertEqual(self.normalize_version(version), "1.0.0.1")

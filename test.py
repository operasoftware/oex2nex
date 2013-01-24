#!/usr/bin/env python

import unittest
from slimit.parser import Parser as JSParser
from astwalker import *


class TestUnaliased(unittest.TestCase):
    def setUp(self):
        self.walker = ASTWalker()
        script = """
        var sendToKaleidos = opera.contexts.menu.createItem({
          title: "Open image in Kaleidos",
          contexts: ["image"],
          icon: "butterfly_16.png",
          onclick: function(event) {
            opera.extension.tabs.create({
              url: "http://coldhead.github.com/kaleidos/?src=" + event.srcURL,
              focused: true
            });
          }
        });
        //add the menu item to the context menu
        opera.contexts.menu.addItem(sendToKaleidos);
        """
        self.jstree = JSParser().parse(script)

    def test_finder(self):
        self.assertTrue(self.walker._find(self.jstree, 'addItem'))

    def test_permission(self):
        self.assertEqual(self.walker.find_apicall(
            self.jstree,
            'addItem', 'contextMenus'),
            'contextMenus')


class TestOneAlias(unittest.TestCase):
    def setUp(self):
        self.walker = ASTWalker()
        script = """
        var tb = opera.contexts.toolbar;
        button = tb.createItem(props);
        tb.addItem(button);
        """
        self.jstree = JSParser().parse(script)

    def test_finder(self):
        self.assertTrue(self.walker._find(self.jstree, 'addItem'))

    def test_permission(self):
        self.assertEqual(self.walker.find_apicall(
            self.jstree,
            'addItem', 'browser_action'),
            'browser_action')


class TestMultiAlias(unittest.TestCase):
    def setUp(self):
        self.walker = ASTWalker()
        script = """
        var o = opera;
        c = o.contexts,
        t = c.toolbar;
        button = t.createItem(props);
        t.addItem(button);
        """
        self.jstree = JSParser().parse(script)

    def test_finder(self):
        self.assertTrue(self.walker._find(self.jstree, 'addItem'))

    def test_permission(self):
        self.assertEqual(self.walker.find_apicall(
            self.jstree,
            'addItem', 'browser_action'),
            'browser_action')


def APIFinderSimple_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestUnaliased)


def APIFinderOneAlias_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestOneAlias)


def APIFinderMultiAlias_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestMultiAlias)

if __name__ == '__main__':
        runner = unittest.TextTestRunner()
        runner.run(APIFinderSimple_suite())
        runner.run(APIFinderOneAlias_suite())
        runner.run(APIFinderMultiAlias_suite())

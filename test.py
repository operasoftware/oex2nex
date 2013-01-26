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
            self.jstree, 'addItem'), 'contextMenus')


class TestOneAlias(unittest.TestCase):
    def setUp(self):
        self.walker = ASTWalker()
        script = """
        var mn = opera.contexts.menu;
        mn.addItem(button);
        """
        self.jstree = JSParser().parse(script)

    def test_finder(self):
        self.assertTrue(self.walker._find(self.jstree, 'addItem'))

    def test_permission(self):
        self.assertEqual(self.walker.find_apicall(
            self.jstree, 'addItem'), 'contextMenus')


class TestMultiAlias(unittest.TestCase):
    def setUp(self):
        self.walker = ASTWalker()
        script = """
        var o = opera;
        c = o.contexts,
        mn = c.menu;
        mn.addItem(button);
        """
        self.jstree = JSParser().parse(script)

    def test_finder(self):
        self.assertTrue(self.walker._find(self.jstree, 'addItem'))

    def test_permission(self):
        self.assertEqual(self.walker.find_apicall(
            self.jstree, 'addItem'), 'contextMenus')


class TestBrowserAction(unittest.TestCase):
    def setUp(self):
        self.walker = ASTWalker()
        self.jstree = JSParser()

    def test_unaliased(self):
        script = """
        opera.contexts.toolbar.addItem(lolwat)
        """

    def test_unaliased2(self):
        script = """
        window.opera.contexts.toolbar.addItem(lolwat)
        """
        self.assertTrue(self.walker.find_button(self.jstree.parse(script)))

    def test_unaliased3(self):
        script = """
        window["opera"].contexts.toolbar.addItem(lolwat)
        """
        self.assertTrue(self.walker.find_button(self.jstree.parse(script)))

    def test_aliased(self):
        script = """
        var ctx = window.opera.contexts;
        ctx.toolbar.addItem(lolwat)
        """
        self.assertTrue(self.walker.find_button(self.jstree.parse(script)))

    def test_aliased2(self):
        script = """
        var ctx = window.opera.contexts;
        tb = ctx.toolbar;
        tb.addItem(lolwat)
        """
        self.assertTrue(self.walker.find_button(self.jstree.parse(script)))
        
    def test_aliased3(self):
        script = """
        var o = window.opera, c = o.contexts,
            t = c.toolbar, bloop = t.addItem(lolwat)
        """
        self.assertTrue(self.walker.find_button(self.jstree.parse(script)))


def APIFinderSimple_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestUnaliased)


def APIFinderOneAlias_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestOneAlias)


def APIFinderMultiAlias_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestMultiAlias)


def browserAction_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestBrowserAction)

if __name__ == '__main__':
        runner = unittest.TextTestRunner()
        runner.run(APIFinderSimple_suite())
        runner.run(APIFinderOneAlias_suite())
        runner.run(APIFinderMultiAlias_suite())
        runner.run(browserAction_suite())

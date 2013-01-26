#!/usr/bin/env python

import unittest
from slimit.parser import Parser as JSParser
from astwalker import *
#TODO: test for false positives


class TestAPIFinder(unittest.TestCase):
    def setUp(self):
        self.walker = ASTWalker()
        self.jstree = JSParser()

    def test_simple_find(self):
        script = """
        var sendToKaleidos = opera.contexts.menu.createItem(foo)
        opera.contexts.menu.addItem(sendToKaleidos);
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'addItem'))

    def test_permission(self):
        script = """
        var sendToKaleidos = opera.contexts.menu.createItem(foo)
        opera.contexts.menu.addItem(sendToKaleidos);
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'addItem'), 'contextMenus')

    def test_finder_aliased(self):
        script = """
        var mn = opera.contexts.menu;
        mn.addItem(button);
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'addItem'))

    def test_permission_alised(self):
        script = """
        var mn = opera.contexts.menu;
        mn.addItem(button);
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'addItem'), 'contextMenus')

    def test_finder_multi_aliased(self):
        script = """
        var o = opera;
        c = o.contexts,
        mn = c.menu;
        mn.addItem(button);
        """
        self.assertTrue(self.walker._find(
            self.jstree.parse(script), 'addItem'))

    def test_permission_multi_aliased(self):
        script = """
        var o = opera;
        c = o.contexts,
        mn = c.menu;
        mn.addItem(button);
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'addItem'), 'contextMenus')


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


def APIFinder_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestAPIFinder)


def browserAction_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestBrowserAction)

if __name__ == '__main__':
        runner = unittest.TextTestRunner()
        runner.run(APIFinder_suite())
        runner.run(browserAction_suite())

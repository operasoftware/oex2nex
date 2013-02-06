#!/usr/bin/env python

import unittest
from slimit.parser import Parser as JSParser
from astwalker import *


class TestBrowserAction(unittest.TestCase):
    def setUp(self):
        self.walker = ASTWalker()
        self.jstree = JSParser()

    def test_unaliased(self):
        script = """
        opera.contexts.toolbar.addItem(lolwat)
        """
        self.assertTrue(self.walker.find_button(self.jstree.parse(script)))

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

    def test_unaliased4(self):
        script = """
        opera.extension.bgProcess.opera.contexts.toolbar.addItem(btn);
        """
        self.assertTrue(self.walker.find_button(self.jstree.parse(script)))

    def test_unaliased5(self):
        """Presumably this shouldn't be a match--as you won't need theButton
        permission until you try to addItem() it."""
        script = """
        theButton = opera.contexts.toolbar.createItem(UIItemProperties);
        """
        self.assertFalse(self.walker.find_button(self.jstree.parse(script)))

    def test_aliased6(self):
        script = """
        function addItem(o){
            opera.contexts.toolbar.addItem(tobwithu.button);
        }
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

#!/usr/bin/env python

import unittest
from slimit.parser import Parser as JSParser
from astwalker import *


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

    def test_simple_find2(self):
        script = """
        var allTabs = opera.extension.tabs.getAll();
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'getAll'))

    def test_simple_find3(self):
        script = """
        var temp_tab = opera.extension.tabs.create(
            {url: 'http://online.translate.ua', focused: false}
        );
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'create'))

    def test_simple_find4(self):
        script = """
        var matches = opera.extension.tabs.getFocused()
        .url.match(/v=([^(\&|$)]*)/)
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'getFocused'))

    def test_permission(self):
        script = """
        var sendToKaleidos = opera.contexts.menu.createItem(foo)
        opera.contexts.tabs.getAll();
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'getAll'), 'tabs')

    def test_finder_aliased(self):
        script = """
        var mn = opera.contexts.menu;
        mn.addItem(button);
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'addItem'))

    def test_finder_aliased2(self):
        script = """
        filter.block.add(document.location.href)
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'add'))

    def test_finder_aliased3(self):
        script = """
        URLFilterAPI.block.remove(content.replace(bugReg,"*#"),newOptions);
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'remove'))

    def test_finder_aliased4(self):
        script = """
        uiitem.disabled = !o.tabs.getFocused();
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'getFocused'))

    def test_finder_aliased5(self):
        script = """
        try { return o.tabs.getFocused().url; } catch (e) { return ""; }
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'getFocused'))

    def test_finder_aliased6(self):
        script = """
        var Current = Tabs.getSelected();
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'getSelected'))

    def test_finder_aliased7(self):
        script = """
        var oTabs = opera.extension.tabs;
        oTabs.create({url: READER_URL, focused: true});
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'create'))

    def test_finder_aliased8(self):
        script = """
        d=opera.contexts.menu.createItem(
            {title:g_formfills[e].decprofilename,type:"folder"}
        );
        contextParents[b].addItem(d);
        d.addItem(opera.contexts.menu.createItem({title:gs("Fill Form"),
        onclick:cmaction1,id:g_formfills[e].ffid}));
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'addItem'))

    def test_permission_aliased(self):
        script = """
        var tb = opera.contexts.tabs;
        tb.create(tabs);
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'create'), 'tabs')

    def test_permission_aliased2(self):
        script = """
        filter.block.add(document.location.href)
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'add'), ('webRequest',
                                                'webRequestBlocking'))

    def test_permission_aliased3(self):
        script = """
        try { return o.tabs.getFocused().url; } catch (e) { return ""; }
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'getFocused'), 'tabs')

    def test_permission_aliased4(self):
        script = """
        var Current = Tabs.getSelected();
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'getSelected'), 'tabs')

    def test_permission_aliased5(self):
        script = """
        var tbs = opera.contexts.tabs;
        tbs.getFocused();
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'getFocused'), 'tabs')

    def test_finder_multi_aliased(self):
        script = """
        var o = opera;
        c = o.contexts,
        tbs = c.tabs;
        tbs.getFocused();
        """
        self.assertTrue(self.walker._find(
            self.jstree.parse(script), 'getFocused'))

    def test_permission_multi_aliased(self):
        script = """
        var o = opera;
        c = o.contexts,
        tb = c.tabs;
        tb.getSelected();
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'getSelected'), 'tabs')

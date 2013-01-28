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
        var matches = opera.extension.tabs.getFocused().url.match(/v=([^(\&|$)]*)/)
        """
        self.assertTrue(self.walker._find(self.jstree.parse(script),
                        'getFocused'))        

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
        var mn = opera.contexts.menu;
        mn.addItem(button);
        """
        self.assertEqual(self.walker.find_apicall(
            self.jstree.parse(script), 'addItem'), 'contextMenus')

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

    


def APIFinder_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestAPIFinder)


def browserAction_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestBrowserAction)

if __name__ == '__main__':
        runner = unittest.TextTestRunner()
        runner.run(APIFinder_suite())
        runner.run(browserAction_suite())

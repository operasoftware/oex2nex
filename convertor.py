#!python
""" Convertor for Opera addons to Chromium addons"""

import os
import sys
import re
import zipfile
import codecs
import json
import xml.etree.ElementTree as etree
import logging
import codecs
try:
    import html5lib
except ImportError:
    print("""\nERROR:\nYou need to install module html5lib to get this working.\n
        The easy way to do this is to run\neasy_install html5lib\nwhere easy_install
        is available as part of your Python installation.""")
    sys.exit(1)

try:
    from slimit.parser import Parser as JSParser
except ImportError:
    print("""ERROR: Could not import slimit module\nIf the module is not installed
        please install it.\ne.g. by running the command 'easy_install slimit'.""")
    sys.exit(1)

from astwalker import ASTWalker

#BEGIN
debug = False
# Only the default if we don't find any from content element
# Yeah, this could be index.{htm,html,xhtm,xhtml,svg}
indexdoc = "index.html"
# The best place to get the popup file is where it is added in the background
# process as a toolbaritem, but ...
popupdoc = "popup.html"
optionsdoc = "options.html"
shim_dir = "oex_shim/"
#"http://addons.opera.com/tools/oex_shim/"
shim_remote = "https://cgit.oslo.osa/cgi-bin/cgit.cgi/desktop/extensions/oex_shim/plain/build/"
oex_bg_shim = shim_dir + "operaextensions_background.js"
oex_anypage_shim = shim_dir + "operaextensions_popup.js"
oex_injscr_shim = shim_dir + "operaextensions_injectedscript.js"
oex_resource_loader = shim_dir + "popup_resourceloader"
# TODO: add a smart way of adding these following default permissions
permissions = ["http://*/*", "https://*/*", "storage", "cookies"]
has_button = False

#Header for Chrome 24(?) compatible .crx package
crxheader = "\x43\x72\x32\x34\x02\x00\x00\x00"


class Oex2Crx:
    """
    Converts an Opera extension packaged as .oex to an equivalent .crx file.
    - parse command line and get options (zip file/oex, maybe the key to use for signing crx)
    - the oex file is read from the input using zipfile readers.
    - from the config.xml a DOM tree is made
    - from the above DOM tree a JSON file, manifest.json is made using -
    - name, description, features, access, icons, content nodes
    - from files matching /includes/* in the zip package get the includes/excludes
    - add 'matches' part to the manifest
    - combine all scripts from index.html, popup.html, options.html to a single file
    - wrap the above in opera.isReady(function () { })
    - add manifest to .crx file
    - sign the .crx file if key is provided (also needs openssl installed)
    """
    def __init__(self, in_file, out_file, key_file=None, is_dir=False):
        if (in_file == None or out_file == None):
            raise Exception("You should provide input file and output file")
        self._in_file = in_file
        self._out_file = out_file
        self._key_file = key_file
        self._is_dir = is_dir
        self._oex = None
        self._crx = None
        self._zih_file = None

    def readoex(self):
        """
        Reads the input file, creates/overwrites the output file and returns
        the archives to the caller
        """
        if debug:
            print('Reading oex file.')
        try:
            oex = zipfile.ZipFile(self._in_file, "r")
            if self._is_dir:
                crx = zipfile.ZipFile(self._out_file + '.crx', "w", zipfile.ZIP_DEFLATED)
            else:
                crx = zipfile.ZipFile(self._out_file, "w", zipfile.ZIP_DEFLATED)
        except Exception as e:
            print(("Error reading/writing the given files.", e))
            sys.exit(2)

        self._oex, self._crx = oex, crx
        if debug:
            print(('Oex:', oex, ", Crx:", crx))

    def _add_permission(self, *perms):
        """Adds a permission (or multiple) to the permission list."""
        for perm in perms:
            if isinstance(perm, basestring):
                permissions.append(perm)
            elif isinstance(perm, tuple):
                permissions.extend(perm)

    def _get_permissions(self):
        """ Serializes permissions list to be appended to manifest.json """
        # "uniquify" permissions (as multiple perms may get in)
        def uniquify(lst):
            st = set(lst)
            return list(st)
        return ", ".join('"' + perm + '"' for perm in uniquify(permissions))

    def _normalize_version(self, version):
        """Attemps to clean up existing config.xml @version values and
        validate them against the CRX requirements (1-4 dot-separated integers
        each between 0 and 65536). If that fails, returns '1.0.0.1'
        """
        # in case a stray None (or whatever) makes it in
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

    def _convert(self):
        """
        Reads the oex file, parses its config.xml, includes/, does the
        necessary conversion to prepare the manifest.json of the crx file, add
        wrappers and shims to make the crx work and writes the crx package.
        """

        # parse config.xml to generate the suitable manifest entries
        oex = self._oex
        crx = self._crx
        try:
            # Also a quick sanity check for Opera extension format
            configStr = unicoder(oex.read("config.xml"))
        except KeyError as kex:
            sys.exit("Is the input file a valid Opera extension? We did not find a config.xml inside.\nException was:" + str(kex))


        if debug: 
            print(("Config.xml", configStr))
        root = etree.fromstring(configStr.encode('UTF-8')) # xml.etree requires UTF-8 input
        #TODO: Handle localisation (xml:lang), defaultLocale, locales folder etc.

        def _get_best_elem(xmltree, tag):
            """
            Find and return default or English tag's content when config.xml
            has same tag with different xml:lang
            """

            elems = root.findall("{http://www.w3.org/ns/widgets}" + tag)
            rval = ""
            # Use some 'en' value of the text content if the element is localised
            for it in elems:
                try:
                    lang = it.attrib['{http://www.w3.org/XML/1998/namespace}lang']
                    if not rval or ((lang is not None) and ("en" in lang)):
                        rval = it.text
                except KeyError:
                    if it is not None:
                        rval = it.text
                    break
            if not rval:
                rval = "No " + tag + " found in config.xml."
            elif not isinstance(rval, unicode):
                rval = unicoder( rval ) #.encode("utf-8")

            return rval

        name = _get_best_elem(root, "name")
        if root.find("[@version]") is not None:
            version = self._normalize_version(root.attrib["version"])
        else:
            version = "1.0.0.1"
        cid = root.find("[@id]")
        if cid is not None:
            cid = root.attrib["id"]
        description = _get_best_elem(root, "description")
        accesslist = root.findall("{http://www.w3.org/ns/widgets}access")
        accessorigins = []
        for acs in accesslist:
            if (acs.find("[@subdomains]")) is not None:
                accessorigins.append([acs.attrib["origin"], acs.attrib["subdomains"]])
            else:
                accessorigins.append([acs.attrib["origin"], "false"])
        if debug:
            print(("Access origins:", accessorigins))
        featurelist = root.findall("{http://www.w3.org/ns/widgets}feature")
        featurenames = []
        for feat in featurelist:
            featurenames.append(feat.attrib["name"])
        if debug:
            print(("Feature names: ", featurenames))
        # Store preference data and add them to the index doc using a script
        prefstore = {}
        prefnodes = root.findall("{http://www.w3.org/ns/widgets}preference")
        for pref in prefnodes:
            if "name" in pref.attrib:
                prefstore[pref.attrib["name"]] = pref.attrib["value"]
        if debug:
            print(("Preferences: ", prefstore))
        indexfile = indexdoc
        content = root.find("{http://www.w3.org/ns/widgets}content")
        if content is not None:
            if content.find("[@src]") is not None:
                indexfile = content.attrib["src"]
        icon = root.find("{http://www.w3.org/ns/widgets}icon")
        iconfile = None
        if icon is not None:
            if icon.find("[@src]") is not None:
                iconfile = icon.attrib["src"]

        shim_wrap = self._shim_wrap
        # parsing includes and excludes from the included scripts
        includes = []
        excludes = []
        injscrlist = []
        inj_scr_data = ""
        inj_scripts = ""
        matches = ""
        discards = ""
        has_popup = False
        has_option = False
        has_injscrs = False
        resources = ""
        merge_scripts = False
        zf_members = oex.namelist()
        # default_locale should be set in manifest.json *only* if there is a
        # corresponding _locales/foo folder in the input
        default_locale = root.find("[@defaultlocale]")
        if default_locale is not None:
            default_locale = root.attrib["defaultlocale"]
        # not None or empty string
        if default_locale:
                if debug:
                    print('found default locale attribute: ' + default_locale)
                # some extensions also keep a manifest.json in locales/def-loc/
                # we should probably copy over the file from locales to _locales
                # and use the default_locale entry
                if '_locales/' + default_locale + '/messages.json' not in zf_members:
                    if debug:
                        print('no _locales/' + default_locale + '/messages.json in source zip file, ignoring default locale')
                    default_locale = ''

        for filename in zf_members:
            # dropping the _locales content if default_locale is not defined
            if not default_locale and filename.startswith("_locales/"):
                continue
            if debug:
                print("Handling file: %s" % filename)
            file_data = unicoder(oex.read(filename))
            self._zih_file = filename
            # for the background process file (most likely index.html)
            # we need to parse config.xml to get the correct index.html file
            # then there can be many index files scattered across the locales folders
            # note that this also need to take care of localisation, which it doesn't now
            if filename == indexfile:
                # all scripts in indexdoc need to be combined into a single .js
                # file and wrapped in an opera.isReady() function. Also this new
                # file needs to be put in the indexdoc as a script and others
                # removed
                file_data = shim_wrap(file_data, "index", prefstore)
            elif filename == popupdoc:
                # same as with indexdoc
                has_popup = True
                file_data = shim_wrap(file_data, "popup")
            elif filename == optionsdoc:
                has_option = True
                file_data = shim_wrap(file_data, "option")
            elif filename.find("includes/") == 0 and filename.endswith(".js"):
                has_injscrs = True
                f_includes = []
                f_excludes = []
                # add individual file names to the content_scripts value
                if not merge_scripts:
                    inj_scripts += ('"' + filename + '",')
                # store the script file name to add it to manifest's content_scripts section
                if merge_scripts:
                    inj_scr_data += unicoder(oex.read(filename))
                if debug:
                    print(('Included script:', filename))
                pos = file_data.find("==/UserScript==")
                if pos != -1:
                    ijsProlog = file_data[:pos]
                    if debug:
                        print(("user script prolog: ", ijsProlog))
                    lines = ijsProlog.split("\n")
                    for line in lines:
                        ipos = line.find("@include ")
                        if ipos != -1:
                            includes.append((line[ipos + 9:]).strip())
                            f_includes.append((line[ipos + 9:]).strip())
                        epos = line.find("@exclude ")
                        if epos != -1:
                            excludes.append((line[epos + 9:]).strip())
                            f_excludes.append((line[epos + 9:]).strip())
                    if debug:
                        print(("Includes: ", includes, " Excludes: ", excludes))
                if not len(f_includes):
                    # uses glob pattern not match pattern (<all_urls>)
                    f_includes = ["*"]
                injscrlist.append({"file": filename, "includes": f_includes, "excludes": f_excludes})
            elif not merge_scripts and filename.endswith(".js"):
                # do we actually *need* to make sure it's a Unicode string and not a set of
                # UTF-bytes at this point? AFAIK we don't - as long as we're only appending
                # ASCII characters, Python doesn't actually care if data is originally
                # UTF-8 or ASCII

                # data = str.encode(data, 'utf-8')
                if debug:
                    print(('Fixing variables in ', filename))
                rv_scopefix = self._update_scopes(file_data)
                # wrap scripts inside opera.isReady()
                # Important: ONLY ASCII in these strings, please..
                # If script parsing failed, leave it alone
                if isinstance(rv_scopefix, basestring):
                    file_data = "opera.isReady(function ()\n{\n" + rv_scopefix + "\n});\n"
            elif re.search(r'\.x?html?$', filename, flags=re.I):
                if debug:
                    print("Adding shim for any page to file %s." % filename)
                file_data = shim_wrap(file_data, "")

            # Web accessible resources list
            if filename not in ["config.xml", indexdoc, popupdoc, optionsdoc]:
                resources += ('"' + filename + '",')

            if ((not filename == "config.xml")):
                # Copy files from locales/en/ to root of the .crx package
                do_copy = False
                noloc_filename = None
                if filename.startswith("locales/en"):
                    noloc_filename = re.sub(r'^locales/en[a-zA-Z-]{0,2}/', '', filename, count=1)
                    if noloc_filename != filename and not (noloc_filename in zf_members):
                        do_copy = True

                if noloc_filename and do_copy:
                    if debug:
                        print("Copying a localised file : %s to the root of package as : %s" % (filename, noloc_filename))
                try:
                    crx.writestr(filename, file_data)
                    if noloc_filename and do_copy:
                        crx.writestr(noloc_filename, file_data)
                except UnicodeEncodeError:
                    crx.writestr(filename, file_data.encode("utf-8"))
                    if noloc_filename and do_copy:
                        crx.writestr(noloc_filename, file_data.encode("utf-8"))

        if has_injscrs:
            if debug:
                print('Has injected scripts')
            # Merged injected scripts
            if merge_scripts and inj_scr_data:
                inj_scr_data = "opera.isReady(function ()\n{\n" + inj_scr_data + "\n});\n"
                crx.writestr("allscripts_injected.js", inj_scr_data.encode("utf-8"))
            # add injected script shim if we have any includes or excludes
            try:
                crx.getinfo(oex_injscr_shim)
            except KeyError:
                injfh = open(oex_injscr_shim, 'r')
                if injfh:
                    inj_data = injfh.read()
                    crx.writestr(oex_injscr_shim, inj_data)
                    injfh.close()
                else:
                    print(("Could not open " + oex_injscr_shim))

            if merge_scripts:
                inj_scripts = '"' + oex_injscr_shim + '", "allscripts_injected.js"'
            else:
                inj_scripts = '"' + oex_injscr_shim + '", ' + inj_scripts

            for s in includes:
                # double-quoted string
                matches = matches + '"' + s + '",'
            for s in excludes:
                # double-quoted string
                discards = discards + '"' + s + '",'

            inj_scripts = inj_scripts[:-1]
            matches = matches[:-1]
            discards = discards[:-1]
            if debug:
                print(("Injected scripts:" + inj_scripts))
            if not matches:
                # match any page
                matches = '"<all_urls>"'

        jenc = json.JSONEncoder()
        description = jenc.encode(description)
        name = jenc.encode(name)

        manifest = ""
        manifest = '{\n"name": ' + name + ',\n"description": ' + description + ',\n"manifest_version" : 2,\n"version" : "' + version + '",\n"background":{"page":"' + indexfile + '"}'
        if iconfile is not None:
            # any way to include multiple icons if the oex has them?
            manifest += ',\n"icons" : {"128" : "' + iconfile + '"}'
        if has_popup:
            # Let the APIs do their job  #"default_popup" : "popup.html"}'
            manifest += ',\n"browser_action" : {}'
        if has_button and not has_popup:
            manifest += ',\n"browser_action" : {}'
        if has_option:
            manifest += ',\n"options_page" : "options.html"'
        # default_locale should be set in manifest.json *only* if there is a corresponding _locales/foo folder in the input
        if default_locale:
            manifest += ',\n"default_locale" : "' + default_locale + '"'
        if has_injscrs:
            # create separate entries for all injected scripts
            content_scripts = ""
            for cs in injscrlist:
                content_scripts += '\n{"js": ["' + oex_injscr_shim + '", ' + jenc.encode(cs["file"]) + '], "matches": ["<all_urls>"], "include_globs": ' + jenc.encode(cs["includes"]) + ', "exclude_globs": ' + jenc.encode(cs["excludes"]) + ', "run_at": "document_start", "all_frames" : true},'
            content_scripts = content_scripts[:-1]
            manifest += ',\n"content_scripts": [' + content_scripts + ']'

        # add web_accessible_resources
        # all files except the following: manifest.json, indexdoc, popupdoc, optionsdoc, anything else?
        if resources:
            resources = resources[:-1]
            if debug:
                print(("Loadable resources:", resources))
            manifest += ',\n"web_accessible_resources" : [' + resources + ']'

        manifest += ',\n"permissions" : [' + self._get_permissions() + ']'
        manifest += '\n}\n'

        if debug:
            print(("Manifest: ", manifest))
        crx.writestr("manifest.json", manifest)
        if debug:
            print("Adding resource_loader files")
        crx.writestr(oex_resource_loader + ".html", """<!DOCTYPE html>
<style>body { margin: 0; padding: 0; min-width: 300px; min-height:
 200px; }</style>
<iframe seamless width="100%" height="100%" style="display: block;
 position: absolute;"></iframe>
<script src="/oex_shim/popup_resourceloader.js"></script>""")
        crx.writestr(oex_resource_loader + ".js", """function getParam( key ) {
   key = key.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
   var regexS = "[\\?&]" + key + "=([^&#]*)";
   var regex = new RegExp(regexS);
   var results = regex.exec(window.location.search);
   return results == null ? "" :
 window.decodeURIComponent(results[1].replace(/\+/g, " "));
 }

 var s = getParam('href'), w = getParam('w'), h = getParam('h');
 if(s !== "") { document.querySelector('iframe').src = window.atob(s); }
 if(w !== "") { document.body.style.minWidth = w.replace(/\D/g,'') + "px"; }
 if(h !== "") { document.body.style.minHeight = h.replace(/\D/g,'') + "px"; }""")

    def _update_scopes(self, scriptdata):
        """ Attempt to parse the script text and do some variable scoping fixes
        so that the scripts used in the oex work with the shim """
        try:
            jstree = JSParser().parse(scriptdata)
        except SyntaxError:
            try:
                jstree = JSParser().parse(str(scriptdata, 'UTF-8'))
            except Exception as ex:
                print("ERROR: script parsing failed. This script might need manual fixing.\nFile: %s\n" % self._zih_file)
                return ex

        walker = ASTWalker(debug)
        aliases = {"window": ["window"], "opera": ["opera", "window.opera"], "widget": ["widget", "window.widget"], "extension": ["opera.extension"], "preferences": ["widget.preferences", "window.widget.preferences"], "toolbar": ["opera.contexts.toolbar", "window.opera.contexts.toolbar"]}
        scriptdata = jstree.to_ecma()
        for rval in walker._get_replacements(jstree, aliases):
            # if debug: print(('walker ret:', rval))
            if isinstance(rval, list) and rval != [] and isinstance(rval[0], dict):
                rdict = rval[0]
            elif isinstance(rval, dict):
                rdict = rval
            else:
                rdict = []
            try:
                for key in rdict:
                    if 'text' in rdict[key] and 'textnew' in rdict[key]:
                        scriptdata = scriptdata.replace(rdict[key]['text'], rdict[key]['textnew'])
            except Exception as e:
                print ("Exception while fixing script:", e, key, scriptdata)
                pass

        # defining this in here so we can share the jstree and walker instances
        def find_permissions(tree):
            """Looks for possible permissions to be added to manifest.json"""
            self._add_permission(walker.find_apicall(jstree, 'addItem'))
            self._add_permission(walker.find_apicall(jstree, 'create',
                                                             'getAll',
                                                             'getFocused',
                                                             'getSelected',
                                                             'getFocused'))
            self._add_permission(walker.find_apicall(jstree, 'add', 'remove'))

        find_permissions(jstree)
        if walker.find_button(jstree):
            global has_button
            has_button = True
        return scriptdata

    def convert(self):
        """ Public method which does the real work """
        self.readoex()
        self._convert()
        # extract file to the specified directory
        if self._is_dir:
            if debug:
                print(("Extracting .crx file to:", self._out_file))
            try:
                self._crx.extractall(self._out_file)
            except IOError as e:
                print(("ERROR: Threw exception while extracting crx file to the directory: ",
                    self._out_file, "\nGot:", e, "\nIs there a file by the same name?"))
        self._oex.close()
        self._crx.close()
        # Let us not sign if the output requested is for directory
        if self._key_file and not self._is_dir:
            self.signcrx()
        print("Done!")

    def _shim_wrap(self, html, file_type="index", prefs=None, merge_scripts=False):
        """
        Applies certain corrections to the HTML source passed to this method.
        Specifically adds the relevant shim script, wraps all script text
        within opera.isReady() methods etc. """

        htmlparser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("dom"))
        domwalker = html5lib.treewalkers.getTreeWalker("dom")
        serializer = html5lib.serializer.HTMLSerializer(omit_optional_tags=False, quote_attr_values=True, strip_whitespace=True, use_trailing_solidus=True)
        doc = htmlparser.parse(html, "utf-8")
        scriptdata = ""
        inlinescrdata = ""
        oex = self._oex
        crx = self._crx
        # FIXME: use the correct base for the @src (mostly this is the root [''])
        # Remove scripts only if we are merging all of them

        def add_dom_prefs(doc, prefs):
            """ Add an external script with the data taken from preference
            elements in config.xml. Returns a tuple of doc, prefs script and
            script src"""
            if isinstance(prefs, dict):
                pref_str = ""
                for key in prefs:
                    pref_str += 'widget.preferences["' + key + '"] = "' + prefs[key] + '";\n'
                if debug:
                    print("Preferences stringified: " + pref_str)
                if pref_str:
                    p_scr = doc.createElement("script")
                    p_scr_src = "exported_prefs.js"
                    p_scr.setAttribute("src", p_scr_src)
                    head = doc.getElementsByTagName("head")
                    if head is not None and head != []:
                        head = head[0]
                        head.insertBefore(p_scr, head.firstChild)
                    else:
                        doc.documentElement.insertBefore(p_scr, doc.documentElement.firstChild)

                return (doc, pref_str, p_scr_src)

            return (doc, None, None)

        if merge_scripts:
            for script in doc.getElementsByTagName("script"):
                script_name = script.getAttribute("src")
                if debug:
                    print('Script from ' + file_type + ' document:' + script_name)
                if script_name:
                    if debug:
                        print(('reading script data:', script_name))
                    try:
                        scriptdata += (oex.read(script_name)).encode("utf-8")
                    except KeyError:
                        print(("The file " + script_name + " was not found in archive."))
                    self._zih_file = script_name
                # could be an inline script
                else:
                    # but popups could not use inline scripts in crx packages
                    if (script.childNodes != []):
                        inlinescrdata = ""
                        for cnode in script.childNodes:
                            inlinescrdata += cnode.nodeValue
                        inlinescrdata += script.childNodes[0].nodeValue
                script.parentNode.removeChild(script)
        else:
            # move inline scripts into a new external script
            script_count = 0
            for script in doc.getElementsByTagName("script"):
                script_name = script.getAttribute("src")
                if not script_name:
                    if (script.childNodes != []):
                        script_data = ""
                        for cnode in script.childNodes:
                            script_data += cnode.nodeValue
                        script_data = script_data.strip()
                        if script_data:
                            rv_scopefix = self._update_scopes(script_data)
                            if isinstance(rv_scopefix, basestring):
                                script_data = "opera.isReady(function ()\n{\n" + rv_scopefix + "\n});\n"
                            else:
                                script_data = "opera.isReady(function ()\n{\n" + script_data + "\n});\n"
                            script_count += 1
                            iscr = doc.createElement("script")
                            iscr_src = "inline_script_" + file_type + "_" + str(script_count) + ".js"
                            iscr.setAttribute("src", iscr_src)
                            script.parentNode.replaceChild(iscr, script)
                            try:
                                crx.writestr(iscr_src, script_data)
                            except UnicodeEncodeError:
                                # oops non-ASCII bytes found. *Presumably* we have Unicode already at
                                # this point so we can just encode it as UTF-8..
                                # If we at this point somehow end up with data that's already UTF-8
                                # encoded, we'll be in trouble.. will that throw or just create mojibake
                                # in the resulting extension, I wonder?
                                crx.writestr(iscr_src, script_data.encode('utf-8'))

        shim = doc.createElement("script")
        if file_type == "index":
            if merge_scripts:
                oscr = "allscripts_background.js"
            shim.setAttribute("src", oex_bg_shim)
            bgdata = self._get_shim_data(oex_bg_shim)
            if oex_bg_shim not in crx.namelist():
                crx.writestr(oex_bg_shim, bgdata)
            if prefs:
                (doc, pref_sdata, pref_src) = add_dom_prefs(doc, prefs)
                pref_sdata = "opera.isReady(function ()\n{\n" + pref_sdata + "\n});\n"
                crx.writestr(pref_src, pref_sdata)
        # add the 'anypage.shim' to all content we receive here:
        else:
            #NOT : file_type == "popup" or file_type == "option":
            # Hopefully there would be only one popup.html or options.html in
            # the package (Localisation ~!~!~!~)
            if merge_scripts:
                oscr = "allscripts_" + file_type + ".js"

            shim.setAttribute("src", oex_anypage_shim)
            ppdata = self._get_shim_data(oex_anypage_shim)
            # add popup shim only if it hasn't been added already
            if oex_anypage_shim not in crx.namelist():
                crx.writestr(oex_anypage_shim, ppdata)

        if merge_scripts:
            allscr = doc.createElement("script")
            allscr.setAttribute("src", oscr)
            tx1 = doc.createTextNode(" ")
            allscr.appendChild(tx1)
        tx2 = doc.createTextNode(" ")
        shim.appendChild(tx2)

        if inlinescrdata:
            inscr = doc.createElement("script")
            inscr.setAttribute("src", "allinlines_" + file_type + ".js")
            ti = doc.createTextNode(" ")
            inscr.appendChild(ti)

        # add scripts as necessary
        head = doc.getElementsByTagName("head")
        if head is not None and head != []:
            head = head[0]
            head.insertBefore(shim, head.firstChild)
            if merge_scripts:
                head.appendChild(allscr)
            if inlinescrdata:
                head.appendChild(inscr)
        else:
            doc.documentElement.insertBefore(shim, doc.documentElement.firstChild)
            if merge_scripts:
                doc.documentElement.appendChild(allscr)
            if inlinescrdata:
                doc.documentElement.appendChild(inscr)
        # scripts are read and written here only if they are merged
        # if not, they are varscopefixed and added in the routine where other files are added.
        if merge_scripts:
            rval = self._update_scopes(unicoder(scriptdata))
            # Some scripts might not parse, so don't try to wrap them.
            # just use the original data
            if isinstance(rval, basestring):
                scriptdata = "opera.isReady(function ()\n{\n" + rval + "\n});\n"
            crx.writestr(oscr, scriptdata)
        return serializer.render(domwalker(doc))

    def signcrx(self):
        """ Sign the crx file using the provided private key"""
        out_file = self._out_file
        key_file = self._key_file
        signedcrx = crxheader
        publen = 0
        siglen = 0
        try:
            import subprocess
            import shlex
            import struct
            password = ""
            print('Signing CRX package:\nProvide password to load private key:')
            password = sys.stdin.readline()
            if password[-1] == "\n":
                password = password[:-1]
            args = shlex.split('openssl pkey -outform DER -pubout -out pubkey.der -in "' + key_file + '" -passin "pass:' + password + '"')
            if debug:
                print(args)
            subprocess.call(args)
            args = shlex.split('openssl dgst -sha1 -binary -sign "' + key_file + '" -passin "pass:' + password + '" -out "' + out_file + '.sig" "' + out_file + '"')
            if debug:
                print(args)
            subprocess.call(args)
            try:
                pfh = open("pubkey.der", 'rb')
                sfh = open(out_file + '.sig', 'rb')
                if self._is_dir:
                    ofh = open(out_file + '.crx', 'rb')
                else:
                    ofh = open(out_file, 'rb')
            except Exception as e:
                print(('Failed to open required files to create signature.', e))

            if sfh and pfh and ofh:
                pubdata = pfh.read()
                sigdata = sfh.read()
                crxdata = ofh.read()
                ofh.close()
                ofh = open(out_file + '.signed.crx', 'wb')
                publen = struct.pack("<L", len(pubdata))
                siglen = struct.pack("<L", len(sigdata))
                signedcrx += (publen + siglen + pubdata + sigdata + crxdata)
                ofh.write(signedcrx)
                sfh.close()
                pfh.close()
                ofh.close()
                os.unlink("pubkey.der")
                os.unlink(out_file + '.sig')
        except Exception as e:
            print(("Signing of " + out_file + " failed, ", e))

    def _get_shim_data(self, shim):
        data = None
        try:
            sfh = open(shim, 'r')
            if sfh is not None:
                data = sfh.read()
                sfh.close()
        except IOError:
            print(("ERROR: Could not open " + shim + "\nDo you have the shim files in directory oex_shim/ under working directory?"))
            sys.exit(4)
        return data


def fetch_shims():
    """ Download shim files from remote server """
    import urllib.request
    import urllib.error
    import urllib.parse
    attempts = 0
    shims = iter(("operaextensions_background.js", "operaextensions_popup.js", "operaextensions_injectedscript.js"))
    shim = next(shims)
    url = shim_remote + shim
    while attempts < 10:
        attempts += 1
        try:
            res = urllib.request.urlopen(url)
            if res.code == 200:
                try:
                    if not os.path.exists(shim_dir):
                        os.mkdir(shim_dir)
                    elif os.path.isdir(shim_dir):
                        fh = open(shim_dir + shim, 'w')
                        fh.write(res.read())
                        fh.close()
                except Exception as e:
                    sys.exit(e)
            else:
                if debug:
                    print(('Response:', res.code))
            try:
                shim = next(shims)
            except StopIteration:
                break
            url = shim_remote + shim
        except urllib.error.HTTPError as ex:
            if ex.code == 401:
                if debug:
                    print(('HTTP Authentication required:', ex.code, ex.msg, ex.hdrs))
                auth_type = ex.hdrs["WWW-Authenticate"].split()[0]
                realm = ex.hdrs["WWW-Authenticate"].split('=')[1]
                realm = realm.strip('"')
                if auth_type == "Basic":
                    auth_handler = urllib.request.HTTPBasicAuthHandler()
                    print(("Basic auth: Realm: ", realm))
                    print("Enter username:")
                    usr = sys.stdin.readline()
                    usr = usr.strip("\n")
                    print("Enter password:")
                    pwd = sys.stdin.readline()
                    pwd = pwd.strip("\n")
                    auth_handler.add_password(realm=realm, uri=shim_remote, user=usr, passwd=pwd)
                    opener = urllib.request.build_opener(auth_handler)
                    urllib.request.install_opener(opener)
                    continue
            else:
                print(('Threw :', ex, ' when fetching ', url))

class UnicodingError: pass

utf8_detector = re.compile(r"""^(?:
     [\x09\x0A\x0D\x20-\x7E]            # ASCII
   | [\xC2-\xDF][\x80-\xBF]             # non-overlong 2-byte
   |  \xE0[\xA0-\xBF][\x80-\xBF]        # excluding overlongs
   | [\xE1-\xEC\xEE\xEF][\x80-\xBF]{2}  # straight 3-byte
   |  \xED[\x80-\x9F][\x80-\xBF]        # excluding surrogates
   |  \xF0[\x90-\xBF][\x80-\xBF]{2}     # planes 1-3
   | [\xF1-\xF3][\x80-\xBF]{3}          # planes 4-15
   |  \xF4[\x80-\x8F][\x80-\xBF]{2}     # plane 16
  )*$""", re.X)

cp1252_detector = re.compile(r'^(?:[\x80-\xBF])*$', re.X)
xa4_detector = re.compile(r'^(?:\xA4)*$', re.X)

def unicoder(string):
    '''make unicode. This method is copied from http://pastebin.com/f76609aec'''
    
    try:
        if re.match(utf8_detector, string):
            if string[:3] == codecs.BOM_UTF8 : # remove any BOM from UTF-8 data
                string= string[3:]
            return string.decode('utf-8')
        if re.match(cp1252_detector, string):
            if re.match(xa4_detector, string):
                return unicode(string, 'iso8859_15')
            else:
                return unicode(string, 'cp1252')
        return unicode(string, 'latin_1')
        
    except UnicodingError:
        raise UnicodingError("still don't recognise encoding after trying do guess common english encodings")

def main(args=None):
    import argparse
    if len(sys.argv) < 3:
        sys.argv.append('-h')
    argparser = argparse.ArgumentParser(description="Convert an Opera extension into a Chrome extension")
    argparser.add_argument('-s', '--key', help="Sign the crx package with the provided key (PEM) file. The signed package is named <file>.signed.crx.")
    argparser.add_argument('in_file', nargs='?', help="Path to the .oex file")
    argparser.add_argument('out_file', nargs='?', help="Output file path (a .crx file or a directory)")
    argparser.add_argument('-x', '--isdir', action='store_true', default=False, help="Output path is a directory")
    argparser.add_argument('-d', '--debug', default=False, action='store_true', help="Debug mode; quite verbose")
    argparser.add_argument('-f', '--fetch', default=False, action='store_true', help="Fetch the latest oex_shim scripts and put them in oex_shim directory.")

    args = argparser.parse_args()
    global debug
    if args.debug:
        debug = True
    if args.fetch:
        fetch_shims()
    convertor = Oex2Crx(args.in_file, args.out_file, args.key, args.isdir)
    convertor.convert()
    sys.exit(0)


if __name__ == "__main__":
    main()

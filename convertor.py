#!python
import os, sys

debug = False

# Only the default if we don't find any from content element
# Yeah, this could be index.{htm,html,xhtm,xhtml,svg}
indexdoc = "index.html"
# The best place to get the popup file is where it is added in the background
# process as a toolbaritem, but ...
popupdoc = "popup.html"
optionsdoc = "options.html"
shimDir = "oex_shim/"
oexBgShim =  shimDir + "operaextensions_background.js"
oexPPShim = shimDir + "operaextensions_popup.js"
oexInjShim = shimDir + "operaextensions_injectedscript.js"

#Header for Chrome 24(?) compatible .crx package
crxheader = "\x43\x72\x32\x34\x02\x00\x00\x00";

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
		self._is_dir  = is_dir
		self._oex = None
		self._crx = None

	def readoex(self):
		"""
		Reads the input file, creates/overwrites the output file and returns
		the archives to the caller
		"""
		import zipfile
		if debug: print 'Reading oex file.'
		try:
			oex = zipfile.ZipFile(self._in_file, "r")
			if self._is_dir is True:
				crx = zipfile.ZipFile(self._out_file + '.crx', "w", zipfile.ZIP_DEFLATED)
			else:
				crx = zipfile.ZipFile(self._out_file, "w", zipfile.ZIP_DEFLATED)
		except Exception as e:
			print "Error reading/writing the given files.", e
			sys.exit(2)

		self._oex, self._crx = oex, crx
		if debug: print 'Oex:', oex, ", Crx:", crx

	def _convert(self):
		"""
		Reads the oex file, parses its config.xml, includes/, does the
		necessary conversion to prepare the manifest.json of the crx file, add
		wrappers and shims to make the crx work and writes the crx package.
		"""
		import xml.etree.ElementTree as etree
		# parse config.xml to generate the suitable manifest entries
		oex = self._oex
		crx = self._crx
		configStr = oex.read("config.xml")
		if debug: print "Config.xml", configStr
		root = etree.fromstring(configStr)
		#TODO: Handle localisation (xml:lang), defaultLocale, locales folder etc.
		name = root.find("{http://www.w3.org/ns/widgets}name")
		if name is not None:
			name = name.text.encode("utf-8")
		version = root.find("[@version]")
		if version is not None:
			version = root.attrib["version"]
		else:
			version = "1.0.0.1"
		id = root.find("[@id]")
		if id is not None:
			id = root.attrib["id"]
		description = root.find("{http://www.w3.org/ns/widgets}description")
		if description is not None:
			description = description.text.encode("utf-8")
		else:
			description = "No description found in config.xml."
		accesslist = root.findall("{http://www.w3.org/ns/widgets}access")
		accessorigins = []
		for acs in accesslist:
			if (acs.find("[@subdomains]")) is not None:
				accessorigins.append([acs.attrib["origin"], acs.attrib["subdomains"]])
			else:
				accessorigins.append([acs.attrib["origin"], "false"])
		if debug: print "Access origins:" , accessorigins
		featurelist = root.findall("{http://www.w3.org/ns/widgets}feature")
		featurenames = []
		for feat in featurelist:
			featurenames.append(feat.attrib["name"])
		if debug: print "Feature names: ", featurenames
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

		shimWrap = self._shimWrap
		# parsing includes and excludes from the included scripts
		# Can excludes be used somewhere in manifest.json?
		includes = []
		excludes = []
		injscrData = ""
		inj_scripts  = ""
		hasPopup = False
		hasOption = False
		hasInjScrs = False
		resources = ""
		merge_scripts = False
		for it in oex.infolist():
			if debug: print it.filename
			data = oex.read(it.filename)
			# for the background process file (most likely index.html)
			# we need to parse config.xml to get the correct index.html file
			# then there can be many index files scattered across the locales folders
			# note that this also need to take care of localisation, which it doesn't now
			if it.filename == indexfile:
				# all scripts in indexdoc need to be combined into a single .js
				# file and wrapped in an opera.isReady() function. Also this new
				# file needs to be put in the indexdoc as a script and others
				# removed
				data = shimWrap(data, "index", oex, crx)
			elif it.filename == popupdoc:
				# same as with indexdoc
				hasPopup = True
				data = shimWrap(data, "popup", oex, crx)
			elif it.filename == optionsdoc:
				# same as with indexdoc
				hasOption = True
				data = shimWrap(data, "option", oex, crx)
			elif it.filename.find("includes/") == 0 and it.filename.endswith(".js"):
				hasInjScrs = True
				# add individual file names to the content_scripts value
				if not merge_scripts:
					inj_scripts += ('"' + it.filename + '"')
				# store the script file name to add it to manifest's content_scripts section
				if merge_scripts is True:
					injscrData += unicode(oex.read(it.filename), "utf-8")
				if debug: print 'Included script:', it.filename
				pos = data.find("==/UserScript==")
				if pos != -1:
					ijsProlog = data[:pos]
					if debug: print "user script prolog: " , ijsProlog
					lines = ijsProlog.split("\n")
					for line in lines:
						ipos = line.find("@include ")
						if ipos != -1:
							includes.append((line[ipos + 9:]).strip())
						epos = line.find("@exclude ")
						if epos != -1:
							excludes.append((line[epos + 9:]).strip())
					if debug: print "Includes: " , includes, " Excludes: ", excludes
				# wrap the script, but we should also combine all included scripts to one
				data = "opera.isReady(function ()\n{\n" + data + "\n});\n"
			elif not merge_scripts and it.filename.endswith(".js"):
				# wrap all scripts inside opera.isReady()
				data = "opera.isReady(function ()\n{\n" + data + "\n});\n"
			elif it.filename not in ["config.xml", indexdoc, popupdoc, optionsdoc]:
				resources += ('"' + it.filename + '",')

			# Do not add config.xml or .js files to the crx package.
			# All needed .js files referenced by index/popup/etc. are merged
			# and that merged file is added
			# BUT: the js files could be referenced by a different file that we
			# did not touch. So just bundle all the files.
			if ((not it.filename == "config.xml")): #and (not it.filename.endswith(".js"))):
				try:
					crx.writestr(it.filename, data)
				except UnicodeEncodeError:
					crx.writestr(it.filename, data.encode("utf-8"))

		if hasInjScrs:
			if debug: print 'Has injected scripts'
			# Merged injected scripts
			if merge_scripts and injscrData:
				injscrData = "opera.isReady(function ()\n{\n" + injscrData + "\n});\n"
				crx.writestr("allscripts_injected.js", injscrData.encode("utf-8"))
			# add injected script shim if we have any includes or excludes
			try:
				crx.getinfo(oexInjShim)
			except KeyError:
				injfh = open(oexInjShim, 'r')
				if injfh:
					injData = injfh.read()
					crx.writestr(oexInjShim, injData)
					injfh.close()
				else:
					print "Could not open " + oexInjShim

			if merge_scripts:
				inj_scripts = '"' + oexInjShim  + '", "allscripts_injected.js"'
			else:
				inj_scripts = '"' + oexInjShim  + '", ' + inj_scripts
			if debug: print "Injected scripts:" + inj_scripts
			matches = ""
			discards = ""
			for s in includes:
				matches = matches + '"' + s + '",'
			for s in excludes:
				discards = discards + '"' + s + '",'

			matches = matches[:-1]
			discards = discards[:-1]
			if not matches:
				# match any page
				matches = '"http://*/*", "https://*/*"'

		manifest = ""
		manifest = '{\n"name": "' + name + '",\n"description": "' + description + '",\n"manifest_version" : 2,\n"version" : "' + version + '",\n"background":{"page":"' + indexfile + '"}'
		if iconfile is not None:
			manifest += ',\n"icons" : {"128" : "' + iconfile + '"}';
		if hasPopup:
			manifest += ',\n"browser_action" : {"default_popup" : "popup.html"}';
		if hasOption:
			manifest += ',\n"options_page" : "options.html"';
		if hasInjScrs:
			manifest += ',\n"content_scripts" : [{"matches" : [' + matches + '], "js": [' + inj_scripts + ']'
			if discards:
				manifest += ', "exclude_matches": [' + discards + ']'
			manifest += ', "run_at": "document_start"}]'

		# add web_accessible_resources
		# all files except the following: manifest.json, indexdoc, popupdoc, optionsdoc, anything else?
		if resources:
			resources = resources[:-1]
			if debug: print "Loadable resources:", resources
			manifest += ',\n"web_accessible_resources" : [' + resources + ']'

		manifest += ',\n"permissions" : ["contextMenus", "webRequest", "webRequestBlocking", "storage", "cookies", "tabs", "http://*/*", "https://*/*"]'
		manifest += '\n}\n'

		if debug: print "Manifest: ", manifest
		crx.writestr("manifest.json", manifest)

	def _fixVarScoping(self, scriptdata):
		""" Attempt to parse the script text and do some variable scoping fixes
		so that the scripts used in the oex work with the shim """
		try:
			from slimit.parser import Parser
			from slimit import ast
		except ImportError:
			print "ERROR: Could not import slimit module\nIf the module is not installed please install it.\ne.g. by running the command 'easy_install slimit'. Note that the crx package created might not work correctly."
			return scriptdata

		try:
			jstree = Parser().parse(scriptdata)
			# List the functions that are supposed to be in global scope
			globalfuncs = {}
			for node in jstree.children():
				if isinstance(node, ast.VarStatement):
					# print 'isvar?:', c, c.children(), c.to_ecma()
					vdecls = node.children()
					for vd in vdecls:
						# export the statement into global scope
						# E.g. -
						# var foo = function () {....} is converted to var foo = window["foo"] = function () { ... }
						# var foo = 43; is converted to var foo = window["foo"] = 43
						# function baz(arg1,...) {} is converted into window["baz"] = function baz (args) {}
						if debug: print 'Variable declaration:', vd, ', identifier:', vd.identifier.value , ',initialiser:', vd.initializer #, ',ecma:' , vd.to_ecma()
						if isinstance(vd, ast.VarDecl):
							idv = vd.identifier.value
							# ugly hack to export into global scope, but it works!
							vd.identifier.value += (' = window["' + vd.identifier.value + '"]')
				if isinstance(node, ast.FuncDecl):
					globalfuncs[node.identifier.value] = node.to_ecma()
					if debug: print 'Func declaration', node, ', identifier:', node.identifier.value, ',elems:', node.elements #, ', ecma:', node.to_ecma()

			# Fix global functions in script text
			scriptdata = jstree.to_ecma()
			for gf in globalfuncs:
				try:
					scriptdata = scriptdata.replace(globalfuncs[gf], 'window["' + gf + '"] = ' + globalfuncs[gf], 1)
				except Exception as e:
					print "Threw exception in func. scope fixer:", e

		except Exception as e:
			print 'ERROR: Threw exception in global scope mangler. The scripts in the crx package might not work correctly.', e

		return scriptdata

	def convert(self):
		""" Public method which does the real work """
		self.readoex()
		self._convert()
		# extract file to the specified directory
		if self._is_dir:
			if debug: print "Extracting .crx file to:", self._out_file
			try:
				self._crx.extractall(self._out_file)
			except IOError as e:
				print "ERROR: Threw exception while extracting crx file to the directory: ", self._out_file, "\nGot:", e , "\nIs there a file by the same name?"
		self._oex.close()
		self._crx.close()
		# Let us not sign if the output requested is for directory
		if self._key_file and not self._is_dir:
			self.signcrx()
		print "Done!"


	def _shimWrap(self, html, type="index", oex=None,crx=None,merge_scripts=False):
		"""
		Applies certain corrections to the HTML source passed to this method.
		Specifically adds the relevant shim script, wraps all script text
		within opera.isReady() methods etc. """
		try:
			import html5lib
		except ImportError:
			print """\nERROR:\nYou need to install module html5lib to get this working.\nThe easy way to do this is to run\neasy_install html5lib\nwhere easy_install is available as part of your Python installation."""
			sys.exit(3)

		htmlparser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("dom"))
		domwalker = html5lib.treewalkers.getTreeWalker("dom")
		serializer = html5lib.serializer.HTMLSerializer(omit_optional_tags=False,quote_attr_values=True,strip_whitespace=True,use_trailing_solidus=True)
		doc = htmlparser.parse(html, "utf-8")
		scriptdata = u""
		# FIXME: use the correct base for the @src (mostly this is the root [''])
		# Remove scripts only if we are merging all of them
		if merge_scripts:
			for scr in doc.getElementsByTagName("script"):
				sname = scr.getAttribute("src")
				if debug: 'Script from ' + type + ' document:' + sname
				if sname:
					if debug: print 'reading script data:', sname
					try:
						scriptdata += unicode(oex.read(sname), "utf-8")
					except KeyError:
						print "The file " + sname + " was not found in archive."
				else: # could be an inline script
					# but popups could not use inline scripts in crx packages
					if (scr.childNodes[0]):
						scriptdata += scr.childNodes[0].nodeValue
				scr.parentNode.removeChild(scr)
		shim = doc.createElement("script")
		if type == "index":
			if merge_scripts:
				oscr = "allscripts_background.js"
			shim.setAttribute("src", oexBgShim)
			bgdata = self._getShimData(oexBgShim)
			try:
				crx.getinfo(oexBgShim)
			except KeyError:
				crx.writestr(oexBgShim, bgdata)
		elif type == "popup" or type == "option":
			# Hopefully there would be only one popup.html or options.html in
			# the package (Localisation ~!~!~!~)
			if merge_scripts:
				oscr = "allscripts_" + type + ".js"
			shim.setAttribute("src", oexPPShim)
			ppdata = self._getShimData(oexPPShim)
			# add popup shim only if it hasn't been added already
			try:
				crx.getinfo(oexPPShim)
			except KeyError:
				crx.writestr(oexPPShim, ppdata)

		if merge_scripts:
			allscr = doc.createElement("script")
			allscr.setAttribute("src", oscr)
			tx1 = doc.createTextNode(" ")
			allscr.appendChild(tx1)
		tx2 = doc.createTextNode(" ")
		shim.appendChild(tx2)
		head = doc.getElementsByTagName("head")
		if head is not None:
			head = head[0]
			head.insertBefore(shim, head.firstChild)
			if merge_scripts:
				head.appendChild(allscr)
		else:
			doc.documentElement.insertBefore(shim, doc.documentElement.firstChild)
			if merge_scripts:
				doc.documentElement.appendChild(allscr)
		scriptdata = self._fixVarScoping(scriptdata.encode("utf-8", "backslashreplace"))
		scriptdata = "opera.isReady(function ()\n{\n" + scriptdata + "\n});\n"
		if merge_scripts:
			crx.writestr(oscr, scriptdata)
		return serializer.render(domwalker(doc))

	def signcrx(self):
		in_file = self._in_file
		out_file = self._out_file
		key_file = self._key_file
		signedcrx = crxheader
		publen = 0
		siglen = 0
		try:
			import subprocess, shlex
			password = ""
			print 'Signing CRX package:\nProvide password to load private key:'
			password = sys.stdin.readline()
			if password[-1] == "\n":
				password = password[:-1]
			args = shlex.split('openssl pkey -outform DER -pubout -out pubkey.der -in "' + key_file + '" -passin "pass:' + password + '"')
			if debug: print args
			subprocess.call(args)
			args = shlex.split('openssl dgst -sha1 -binary -sign "' + key_file + '" -passin "pass:' + password + '" -out "' + out_file + '.sig" "' + out_file + '"')
			if debug: print args
			subprocess.call(args)
			try:
				pfh = open("pubkey.der", 'rb')
				sfh = open(out_file + '.sig', 'rb')
				if self._is_dir is True:
					ofh = open(out_file + '.crx', 'rb')
				else:
					ofh = open(out_file, 'rb')
			except Exception as e:
				print 'Failed to open required files to create signature.', e

			if sfh and pfh and ofh:
				pubdata = pfh.read()
				sigdata = sfh.read()
				crxdata = ofh.read()
				ofh.close()
				ofh = open(out_file + '.signed.crx', 'wb')
				import struct
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
				print "Signing of " + out_file + " failed, ", e

	def _getShimData(self, shim):
		data = None
		try:
			sfh = open(shim,'r')
			if sfh is not None:
				data = sfh.read()
				sfh.close()
		except IOError:
			print "ERROR: Could not open " + shim + "\nDo you have the shim files in directory oex_shim/ under working directory?"
			sys.exit(4)
		return data

def main(args = None):
	import argparse
	if len(sys.argv) < 3:
		sys.argv.append('-h')
	argparser = argparse.ArgumentParser(description="Convert an Opera extension into a Chrome extension")
	argparser.add_argument('-s', '--key', help="Sign the crx package with the provided key (PEM) file. The signed package is named <file>.signed.crx.")
	argparser.add_argument('in_file', nargs='?', help="Path to the .oex file")
	argparser.add_argument('out_file', nargs='?', help="Output file path (a .crx file or a directory)")
	argparser.add_argument('-x', '--isdir', action='store_true', default=False, help="Output path is a directory")
	argparser.add_argument('-d', '--debug', default=False, action='store_true', help="Debug mode; quite verbose")
	#TODO: argparser.add_argument('-u', '--update-check', default=False, action='store_true', help="Fetch the latest oex_shim scripts and put them in oex_shim directory.")

	args = argparser.parse_args()
#	print args
#	exit()

#	args = sys.argv[1:]
#	in_file = None
#	out_file = None
#	key_file = None
#
#	if len(args) > 3:
#		key_file = args[1]
#		in_file = args[2]
#		out_file = args[3]
#	elif len(args) == 2:
#		in_file = args[0]
#		out_file = args[1]
#		key_file = None
#	else:
#		print USAGE
#		sys.exit(1)

	#TODO: Handle the case where out_file path is a directory
	global debug
	if args.debug is True:
		debug = True
	convertor = Oex2Crx(args.in_file, args.out_file, args.key, args.isdir)
	convertor.convert();
	sys.exit(0)


if __name__ == "__main__":
	main()

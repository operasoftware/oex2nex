#!python

try:
	from slimit.parser import Parser
	from slimit import ast
	from slimit.visitors.nodevisitor import NodeVisitor
except ImportError:
	print("ERROR: Could not import slimit module\nIf the module is not installed please install it.\ne.g. by running the command 'easy_install slimit'. Note that the crx package created might not work correctly.")
	sys.exit(1)

import re

class ASTWalker(NodeVisitor):
	"""Walk a javascript AST and return some interesting nodes"""
	# Find variable statements (variable declarations)
	# we are interested in a few things
	# variable, function declarations in the global scope
	# aliases for opera, window, window.widget (direct and through aliases)
	# e.g. a declaration like
	# var w = window, o = w.opera;
	# var prefs = w.widget.preferences
	# var ext = o.extensions
	# Plan -
	# - as we traverse the first level of program find if there are any aliases to window or opera or window.widget or window.opera
	# - look for widget.preferences, window.widget.preferences
	# repeat this pattern for opera.contexts.toolbar
	
	def __init__(self, debug=False):
		self._debug = debug

	def _get_replacements(self, node=None, aliases={}, scope=0):
		debug = self._debug
		if isinstance(node, ast.Node):
			ne = node.to_ecma()
		else:
			return
		try:
			for child in node:
				if isinstance(child, ast.Node):
					ce = child.to_ecma()
				else:
					return
				if debug: yield ['reg:', scope, child, child.to_ecma()]
				# The replacements need to be done at VarStatement level
				if isinstance(child, ast.VarStatement):
					ve = vef = child.to_ecma()
					for vd in child:
						if isinstance(vd, ast.VarDecl):
							if vd.initializer is not None:
								cie = vd.initializer.to_ecma()
								if cie == "window":
									aliases["window"].append(vd.identifier.value)
								elif cie == "opera":
									aliases["opera"].append(vd.identifier.value)
								elif (cie == "widget") or (cie == "window.widget"):
									aliases["widget"].append(vd.identifier.value)
								# In the following case we also need to handle declarations like
								# var op = opera; ...; var exx = op.extension;
								elif (cie.find(".extension") > -1):
									aliases["extension"].append(vd.identifier.value)
								elif (cie.find(".preferences") > -1):
									aliases["preferences"].append(vd.identifier.value)
								elif (cie.find(".toolbar") > -1):
									aliases["toolbar"].append(vd.identifier.value)
							# top level variable declarations
							if (scope == 0):
								# export on to window object
								vd.identifier.value += (' = window["' + vd.identifier.value + '"]')
					if (scope == 0):
						# the new source text
						vef = child.to_ecma()
						yield [{"topvar": {"scope": scope, "node": child, "text": ve, "textnew": vef, "aliases": aliases}}]
					if debug: yield ['check:var:', scope, 'aliases:', aliases, 'child:', child, child.to_ecma()]
				# assignments for widget.preferences and .toolbar
				
				if isinstance(child, ast.Assign):
					if debug: print('>>>----> ast.Assign: ', child.to_ecma())
					# also need to check for things like;
					# var prefs = widget.preferences; ...; prefs.foo = 34; (we need to convert the .foo to setItem('foo', 34)
					for label in aliases["preferences"]:
						if (ce.find(label) > -1):
							if debug: print('pref label:', label)
							datf = dada = daid = val = None
							for da in child:
								if isinstance(da, ast.DotAccessor):
									dat = da.to_ecma()
									for dac in da:
										if isinstance(dac, ast.Identifier) and dac.to_ecma() != label:
											daid = dac.to_ecma()
										else:
											dada = dac.to_ecma()
								else:
									val = da.to_ecma()
							if dada and daid and val:
								datf = dada + '.setItem("' + daid + '", ' + val + ');'
								yield [{"prefs": {"scope": scope, "node": child, "text": child.to_ecma(), "textnew" : datf, "aliases": aliases}}]
							elif debug:
								print("Entered preferences finder but failed to find one; code", child.to_ecma())
							# not much chance that we would again match at the same place
							break
				# can we remove this code?
				if isinstance(child, ast.FunctionCall) and isinstance(child.identifier, ast.DotAccessor):
					if debug: print('>>>----> FunctionCall and DotAccessor: ', child.to_ecma())
					# var tb = opera.contexts.toolbar; ... ; tb.addItem(props);
					if ('addItem' in child.identifier.to_ecma().split('.')):
						if debug: print('>>>----> toolbar.addItem:', child.identifier.to_ecma())
						# TODO: exactly what?
						yield [{"toolbar": {"scope": scope, "node": child, "text": child.to_ecma(), "aliases": aliases}}]
				elif (scope == 0) and isinstance(child, ast.FuncDecl):
					# replace as follows -
					# function foo() {} -> var foo = window['foo'] = function () { }
					fe = child.to_ecma()
					fef = re.sub(r'function\s+(\w+)\s*\(', 'function (', fe)
					fef = 'var ' + child.identifier.value + ' = window["' + child.identifier.value + '"] = '  + fef
					yield [{"function": {"scope": scope, "node": child, "text": fe, "textnew": fef}}]
				# Descend
				for subchild in self._get_replacements(child, aliases, scope+1):
					yield subchild
		except Exception as e:
			print('ERROR: Threw exception in script fixer. The scripts in the crx package might not work correctly.', e)

	def find_apicall(self, node, apicall, permission):
		"""
		Traverses JS source and looks for hints about what APIs are being used.
		If it finds something, it returns the "permission" argument (to be used with)
		_add_permission. Calls _find, which will return None if nothing is found.
		"""
		if self._find(node, apicall):
			return permission
		elif debug: 
			print('No match for ' + apicall + 'found')

	def _find(self, node=None, apicall=""):
		"""
		_find does the real work for find_apicall. Returns True in case of a match
		or None if nothing is found.
		"""
		debug = self._debug
		#best guesses at an API that requires permission is being used
		lhs_shortcut = ["menu", "block", "allow", "tabs"]
		found = False

		try:
			for child in self.visit(node):
				if isinstance(child, ast.FunctionCall) and isinstance(child.identifier, ast.DotAccessor):
					method_call = child.identifier.to_ecma()
					context = method_call.split('.')
					if context[-1] == apicall:
						#context looks like ['opera', 'contexts', 'toolbar', 'addItem']
						if context[-2] in lhs_shortcut:
							if debug: print('API call found (maybe):', method_call)
							found = True
					#else:
						#	do_it_the_hardway()
						#search to see if the lhs value is defined up the tree
				if found:
					return found
		except Exception as e:
			print('ERROR: Exception thrown in api call finder.', e)

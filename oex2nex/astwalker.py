#!python
""" Walks JavaScript AST and does some fixes for adapting the code to be used
with Opera Extension shims"""

import sys
import re
try:
    from slimit.parser import Parser
    from slimit import ast
    from slimit.visitors.nodevisitor import NodeVisitor
except ImportError:
    sys.exit("ERROR: Could not import slimit module\nIf the module is not"
             "installed please install it.\ne.g. by running the command "
             "'easy_install slimit'.")


class ASTWalker(NodeVisitor):
    """
    Walk a javascript AST and return some interesting nodes
    """
    # Find variable statements (variable declarations)
    # we are interested in a few things
    # variable, function declarations in the global scope
    # aliases for opera, window, window.widget (direct and through aliases)
    # e.g. a declaration like
    # var w = window, o = w.opera;
    # var prefs = w.widget.preferences
    # var ext = o.extensions
    # Plan -
    # - as we traverse the first level of program find if there are any aliases
    #   to window or opera or window.widget or window.opera
    # - look for widget.preferences, window.widget.preferences

    def __init__(self, debug=False):
        self._debug = debug

    def _get_replacements(self, node=None, aliases={}, scope=0):
        debug = self._debug
        expr_root = False
        if not isinstance(node, ast.Node):
            return
        try:
            expr_root = isinstance(node, ast.ExprStatement)
            # if debug:
            #     print(">>>--- root is expression statement? :", node, expr_root)
            for child in node:
                if isinstance(child, ast.Node):
                    ce = child.to_ecma()
                else:
                    return
                if debug:
                    yield ['reg:', scope, child, child.to_ecma()]
                # if debug:
                #     print(">>>--- child under exprstatement node? :", expr_root, node, child)
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
                            # top level variable declarations
                            if (scope == 0):
                                # export on to window object
                                vd.identifier.value += (' = window["' + vd.identifier.value + '"]')
                    if (scope == 0):
                        # the new source text
                        vef = child.to_ecma()
                        yield [{"topvar": {"scope": scope, "node": child,
                                "text": ve, "textnew": vef,
                                "aliases": aliases}}]
                    if debug:
                        yield ['check:var:', scope, 'aliases:', aliases, 'child:', child, child.to_ecma()]
                # assignments for widget.preferences
                if isinstance(node, ast.ExprStatement) and isinstance(child, ast.Assign):
                    # also need to check for things like;
                    # var prefs = widget.preferences; ...; prefs.foo = 34;
                    # (we need to convert the .foo to setItem('foo', 34)
                    for label in aliases["preferences"]:
                        if (ce.find(label) > -1):
                            if debug:
                                print('pref label:', label)
                            datf = dada = daid = val = None
                            for da in child:
                                # The following exercise is to not randomly do the setItem conversion in code like:
                                # document.getElementById(widget.preferences.type).checked = true;
                                # document.getElementById("speed").value = widget.preferences.interval;
                                skip = None
                                if len(da.children()) > 1:
                                    for sc in da.children():
                                        if type(sc) in [ast.BracketAccessor, ast.DotAccessor, ast.Identifier, ast.String]:
                                            if skip is None:
                                                skip = False
                                            else:
                                                skip = skip or False
                                        else:
                                            skip = True
                                    if skip is True:
                                        if debug:
                                            print (">>> Skipping a pref label match: node child:", child.to_ecma())
                                        continue
                                # Handle the following:
                                # widget.preferences.token = event.data.token;
                                # widget.preferences.secret = event.data.secret;
                                # widget.preferences["foo"] = bar;
                                # var prefs = widget.preferences;
                                # prefs.cat = meow;
                                # prefs["coo"] = ceow;
                                if (isinstance(da, ast.DotAccessor) or isinstance(da, ast.BracketAccessor)) and da.to_ecma().find(label) > -1:
                                    for dac in da:
                                        if isinstance(dac, ast.Identifier) and dac.to_ecma() != label:
                                            daid = dac.to_ecma()
                                            daid = "'" + daid + "'"
                                        elif isinstance(dac, ast.String):
                                            daid = dac.to_ecma()
                                        else:
                                            dada = dac.to_ecma()
                                else:
                                    val = da.to_ecma()

                            if dada and daid and val:
                                datf = dada + '.setItem(' + daid + ', ' + val + ')'
                                yield [{"prefs": {"scope": scope,
                                        "node": child, "text": child.to_ecma(),
                                        "textnew": datf, "aliases": aliases}}]
                            elif debug:
                                print("Entered preferences finder but failed to find one; code: prefix:", dada, ", key:", daid, ":value:", val, child.to_ecma())
                            # not much chance that we would again match at the same place
                            break
                if (scope == 0) and isinstance(child, ast.FuncDecl):
                    # replace as follows -
                    # function foo() {} -> var foo = window['foo'] = function () { }
                    fe = child.to_ecma()
                    # Replace only the first (else risk removing function identifiers inside the main function)
                    # fef = re.sub(r'function\s+(\w+)\s*\(', 'function (', fe, count=1)
                    # fef = 'var ' + child.identifier.value + ' = window["' + child.identifier.value + '"] = '  + fef
                    # NOTE: This tries to fix some issue where a function
                    # assignment or call would throw The solution being
                    # attempted below is to leave the function as it is but
                    # also export it to global scope
                    fef = fe + '\nvar ' + child.identifier.value + ' = window["' + child.identifier.value + '"] = ' + child.identifier.value + ';'
                    yield [{"function-id": {"scope": scope, "node": child,
                            "text": fe, "textnew": fef}}]
                # Descend
                for subchild in self._get_replacements(child, aliases, scope + 1):
                    yield subchild
        except Exception as e:
            print("ERROR: Threw exception in script fixer. The scripts in the"
                  "nex package might not work correctly.", e)

    def find_apicall(self, node, *apicalls):
        """
        Traverses JS source and looks for hints about what APIs are being used.
        Returns the associated permission (to be used by _add_permission) if
        found. Calls _find, which will return None if nothing is found.
        """
        debug = self._debug
        permission = {
            'create': 'tabs',
            'getAll': 'tabs',
            'getFocused': 'tabs',
            'getSelected': 'tabs',
            'add': ('webRequest', 'webRequestBlocking'),
            'remove': ('webRequest', 'webRequestBlocking')}

        for call in apicalls:
            if self._find(node, call):
                return permission[call]
            elif debug:
                print('No match for ' + call + ' found')

    def find_button(self, tree):
        """
        Look for opera.contexts.toolbar.addItem() so we can add the
        'browser_action' directive to manfest.json
        """
        debug = self._debug
        if self._find(tree, 'addItem', ["toolbar"]):
            return True
        else:
            if debug:
                print('toolbar.addItem() not found.')

    def _find(self, node=None, apicall="", lhs_shortcut=["menu", "block",
                                                         "allow", "tabs"]):
        """
        _find does the real work for find_apicall. Optional lsh_shortcut arg
        allows for a quick short-circuit. Returns True in case of a match or
        None if nothing is found.
        """
        debug = self._debug
        found = False

        #lhs is probably actually a parent object or container
        def lhs_finder(node, lh_object):
            """
            For a given node, determines if it contains a "lh_object", which
            should be an ancestor object to an API method call.
            """
            # var is either a VarStatement or VarDecl (which
            # could be an implicit global declaration)
            var = node.to_ecma()
            if lh_object in var:
                if debug:
                    print('Aliased API call found (maybe)', node.to_ecma())
                return True

        try:
            for child in self.visit(node):
                if isinstance(child, ast.FunctionCall) and isinstance(child.identifier, ast.DotAccessor):
                    method_call = child.identifier.to_ecma()
                    object_chain = method_call.split('.')
                    lh_object = object_chain[-2]
                    if object_chain[-1] == apicall:
                        #object_chain looks like ['opera', 'contexts', 'toolbar', 'addItem']
                        if lh_object in lhs_shortcut:
                            if debug:
                                print('API call found (maybe):', method_call)
                            found = True
                        else:
                            for child in self.visit(node):
                                if isinstance(child, ast.VarStatement):
                                    found = lhs_finder(child, lh_object)

                                elif isinstance(child, ast.ExprStatement):
                                    found = lhs_finder(child, lh_object)

                if found:
                    return found
        except Exception as e:
            print('ERROR: Exception thrown in api call finder.', e, child.to_ecma())

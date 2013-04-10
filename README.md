# oex2nex Convertor

The oex2nex convertor converts an Opera oex extension into an Opera 14 nex extension, using the [oex-shim](I assume this will be on GitHub too?) library. Extension authors can use this tool as a stopgap solution to bring existing content to the [new Opera extension architecture](link to dev.opera article explaining this).

## What does this actually do?

oex2nex parses the `config.xml` file of an `oex` extension and creates a `manifest.json` file containing the relevant metadata, API permissions, and references to assets. It also parses extension code making scope fixes and generally performs all other black magic required to create a compatibility layer between the two extension models.

## Usage

You can run oex2nex as a simple command-line utility, or install it as a package.

### Command-line

`convertor.py [-h] [-s KEY] [-x] [-d] [-f] [in_file] [out_file]`

```
positional arguments:
  in_file            Path to an .oex file or a directory where its extracted
                     contents are available
  out_file           Output file path (a .nex file or a directory)

optional arguments:
  -h, --help         show this help message and exit
  -s KEY, --key KEY  Sign the nex package with the provided key (PEM) file.
                     The signed package is named <file>.signed.nex.
  -x, --outdir       Create or use a directory for output
  -d, --debug        Debug mode; quite verbose
  -f, --fetch        Fetch the latest oex_shim scripts and put them in
                     oex_shim directory.                                          
```

For example, to convert an Opera `oex` extension dino-comics.oex into a `nex` compatible with Opera 14, but output the exension's contents as a directory (useful for tweaking things):

```
$ python oex2nex/convertor.py -xd path/to/dino-comics.oex path/to/put/dino-comics
```

### Installing as a package

```
$ python setup.py install
```

Anything else to include here?

## Tests

Currently we have a handful of tests in oex2nex/tests. You can run them like so:

```
$ python oex2nex/test.py
```
Better test coverage is always a good thing, so feel free to contribute back tests with any improvements.

## Prerequisites

oex2nex works in Python 2.7 (anyone know if it works in 3? 2.6?)

## Known Issues

(list things that we know won't work here)

APIs that don't work?

icon issues

Parsing JS issues (possible there are bugs we haven't encountered yet)
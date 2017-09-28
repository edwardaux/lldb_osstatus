###########################################################################################################
# osstatus.py -  a custom LLDB command called `osstatus` that uses the awesome osstatus.com service to 
# query what various iOS/macOS/tvOS/watchOS error codes mean. 
#
# See https://github.com/edwardaux/lldb_osstatus
#
# Author's note: Please forgive my python code crimes. It has been a while...
###########################################################################################################

from HTMLParser import HTMLParser
from urllib2 import urlopen, URLError, Request
import textwrap
import os
import json
import argparse
import shlex

###########################################################################################################
# General logic
###########################################################################################################

### returns a string that is a particular color (sadly, Xcode ignores
### colors, but if you use lldb from the command line, it looks nice)
def cstr(msg, color='black'):
    if isXcode():
        return msg

    clr = {
    'cyan' : '\033[36m',
    'grey' : '\033[2m',
    'blink' : '\033[5m',
    'redd' : '\033[41m',
    'greend' : '\033[42m',
    'yellowd' : '\033[43m',
    'pinkd' : '\033[45m',
    'cyand' : '\033[46m',
    'greyd' : '\033[100m',
    'blued' : '\033[44m',
    'whiteb' : '\033[7m',
    'pink' : '\033[95m',
    'blue' : '\033[94m',
    'green' : '\033[92m',
    'yellow' : '\x1b\x5b33m',
    'red' : '\033[91m',
    'bold' : '\033[1m',
    'underline' : '\033[4m'
    }[color]
    return clr + msg + ('\x1b\x5b39m' if clr == 'yellow' else '\033[0m')

### Have we been invoked from Xcode?
def isXcode():
    if "unknown" == os.environ.get("TERM", "unknown"):
        return True
    else:
        return False

### Convert to UTF-8 encoded string, and coalesces null strings into empty string
def ustr(s):
    return '' if s is None else s.encode('utf-8')

### hits the remote API to lookup results. 
def fetchResults(code, platform):
    suffix = '' if platform is None else '&platform='+platform

    # Sadly, because macOS ships with python 2.7.x we are stuck using urllib2 instead
    # of something more modern. A consequence of this, though, is that if we try to
    # hit the osstatus.com server directly, we get back an error because osstatus.com
    # has (quite rightly) enabled SNI - however, the combo of Python 2.7 and macOS
    # openSSL bindings mean SNI is not supported. Argh!  What this means is that we
    # have to go via an AWS instance (wthout SNI) that simply proxies the request through 
    # to the real osstatus API. Such a horrible hack, but we're stuck with the lousy 
    # tooling that Apple has foisted upon us. The direct URL is:
    #     'https://osstatus.com/api/search/errors.json?search=' + str(code) + suffix
    url = 'https://jzcbid2qol.execute-api.us-east-2.amazonaws.com/prod?search=' + str(code) + suffix
    try:
        print(url)
        headers = {'User-Agent': 'lldb_osstatus'}
        request = Request(url, headers=headers)
        rawJSON = urlopen(request).read()
    except URLError as e:
        if hasattr(e, 'reason'):
            raise Exception("Unable to connect to server: " + str(e.reason))
        elif hasattr(e, 'code'):
            raise Exception("Server returned HTTP status code: " + str(e.code))
    else:
        return json.loads(rawJSON)

### Given an array of dictionaries, convert into an array of strings that are consumable by humans
def createResults(results, verbose):
    longestNameLength = 0
    for result in results:
        name = ustr(result["name"])
        longestNameLength = max(longestNameLength, len(name))

    lines = []
    for result in results:
        name = ustr(result["name"])
        desc = ustr(result["description"])
        fwk = ustr(result["framework"])
        header = ustr(result["header_file"])

        formattedName = cstr('{message: <{width}}'.format(message=name, width=longestNameLength), 'red')
        formattedSource = cstr(" " + fwk, 'cyan') + cstr("(" + header + ")", 'bold')
        lines.append(formattedName + formattedSource)
        if verbose and len(desc) != 0:
            lines.append(textwrap.fill(desc, initial_indent='    ', subsequent_indent='    '))
    return lines

### Perform a search and return an array of formatted lines
def search(code, platform, verbose):
    results = fetchResults(code, platform)
    return createResults(results, verbose)

###########################################################################################################
# LLDB specific logic
###########################################################################################################
def lldbsearch(debugger, command, result, internal_dict):
    description = "Commands for fetching status codes from osstatus.com"
    parser = argparse.ArgumentParser(prog="osstatus", description=description)
    parser.add_argument("code", help="The code to lookup")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    #parser.add_argument("-p", "--platform", help="Filter by platform. Possible values: [ iOS | macOS | tvOS | watchOS ]")
    shlexArgs = shlex.split(command)

    if len(shlexArgs) == 0:
        parser.print_help()
        return

    try:
        args = parser.parse_args(shlexArgs)
    except:
        return

    try:
        lines = search(args.code, args.platform, args.verbose)
        for line in lines:
            result.AppendMessage(line)
    except Exception as e:
        result.SetError(str(e))

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand("command script add -f " + __name__ + ".lldbsearch osstatus")

###########################################################################################################
# Command line (for testing)
###########################################################################################################
def terminalSearch():
    try:
        lines = search(1009, None, True)
        for line in lines:
            print(line)
    except Exception as e:
        print(e)

# terminalSearch()

#!/usr/bin/env python3

import sys

from beaconlib.lex import parselines
from beaconlib.compile import compileall

srclines = None

def parse(filename):
    global srclines
    
    fl = open(filename)
    parsetrees, srclines = parselines(fl)
    fl.close()

    #for term in parsetrees:
    #    term.dump()
        
    return compileall(parsetrees)


program = parse(sys.argv[1])
program.post()
if False:
    program.dump()
print('// ' + sys.argv[1])
if False:
    for ln in srclines:
        print('// ' + ln)
    print()
program.write()

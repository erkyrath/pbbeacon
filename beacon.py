#!/usr/bin/env python3

import sys
import argparse

from beaconlib.lex import parselines
from beaconlib.compile import compileall

parser = argparse.ArgumentParser()

parser.add_argument('filename')
parser.add_argument('--showterms', action='store_true')
parser.add_argument('--shownodes', action='store_true')

args = parser.parse_args()

srclines = None

def parse(filename):
    global srclines
    
    fl = open(filename)
    parsetrees, srclines = parselines(fl)
    fl.close()

    if args.showterms:
        for term in parsetrees:
            term.dump()
        
    return compileall(parsetrees)


program = parse(args.filename)
program.post()
if args.shownodes:
    program.dump()

print('// ' + args.filename)
if False:
    for ln in srclines:
        print('// ' + ln)
    print()
program.write()

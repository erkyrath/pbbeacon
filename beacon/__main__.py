import sys
import argparse

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


if __name__ == '__main__':
    from .lex import parselines
    from .compile import compileall

    parser = argparse.ArgumentParser()

    parser.add_argument('filename')
    parser.add_argument('--showterms', action='store_true')
    parser.add_argument('--shownodes', action='store_true')
    
    args = parser.parse_args()


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

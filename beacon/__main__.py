import sys
import argparse

def parse(filename):
    fl = open(filename)
    parsetrees, srclines = parselines(fl)
    fl.close()

    if args.showterms:
        for term in parsetrees:
            term.dump()
        
    program = compileall(parsetrees, srclines=srclines)
    program.post()
    return program


if __name__ == '__main__':
    from .lex import parselines
    from .compile import compileall

    parser = argparse.ArgumentParser()

    parser.add_argument('filename')
    parser.add_argument('--showterms', action='store_true')
    parser.add_argument('--shownodes', action='store_true')
    parser.add_argument('--source', action='store_true')
    
    args = parser.parse_args()

    program = parse(args.filename)
    if args.shownodes:
        program.dump()
    
    print('// ' + args.filename)
    if args.source:
        for ln in program.srclines:
            print('// ' + ln)
        print()
    if not args.showterms and not args.shownodes:
        program.write()

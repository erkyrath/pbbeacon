import re
from enum import StrEnum

pat_white = re.compile('^[ \t]+')
pat_symbol = re.compile('^[a-zA-Z_][a-zA-Z_0-9]*')
pat_number = re.compile('^[-]?[0-9]*[.]?[0-9]+')
pat_color = re.compile('^[$][0-9a-fA-F]+')

def parselines(fl):
    lines = []
    trees = []
    stack = [ (0, trees ) ]
    
    for ln in fl.readlines():
        ln = ln.rstrip()
        lines.append(ln)
        
        match = pat_white.match(ln)
        if not match:
            indent = 0
        else:
            val = match.group(0)
            indent = len(val.replace('\t', '    '))
            cut = len(val)
            ln = ln[ cut : ]
        if not ln or ln.startswith('#'):
            continue
        ls = lex(ln)

        lnterms = parseline(ls)

        (curindent, curls) = stack[-1]
        
        while indent < curindent:
            del stack[-1]
            curindent, curls = stack[-1]
            if indent > curindent:
                raise Exception('indent mismatch')

        if indent > curindent:
            lastindent, lastls = stack[-1]
            if not lastls:
                raise Exception('indenting on nothing')
            lastitem = lastls[-1]
            if lnterms:
                if lastitem.tok.typ != TokType.SYMBOL:
                    raise Exception('only symbols can have args')
                lastitem.args.extend(lnterms)
            stack.append( (indent, lastitem.args) )
            continue
        
        curls.extend(lnterms)

    return (trees, lines)


class TokType(StrEnum):
    SYMBOL = 'SYMBOL'
    NUM = 'NUM'
    COLOR = 'COLOR'
    COMMA = 'COMMA'
    EQUALS = 'EQUALS'
    COLON = 'COLON'
    QUOTE = 'QUOTE'

class Token:
    def __init__(self, typ, val=None):
        self.typ = typ
        self.val = val

    def __repr__(self):
        if self.val is None:
            return '<Token %s>' % (self.typ,)
        else:
            return '<Token %s %r>' % (self.typ, self.val,)

    def __str__(self):
        match self.typ:
            case TokType.COMMA:
                return '='
            case TokType.COLON:
                return ':'
            case TokType.EQUALS:
                return '='
            case TokType.QUOTE:
                return '\''
            case _:
                return str(self.val)

def lex(ln):
    res = []
    while ln:
        match = pat_white.match(ln)
        if match:
            val = match.group(0)
            ln = ln[ len(val) : ]
        if not ln:
            break

        if ln.startswith(':'):
            tok = Token(TokType.COLON)
            res.append(tok)
            ln = ln[ 1 : ]
            continue
            
        if ln.startswith(','):
            tok = Token(TokType.COMMA)
            res.append(tok)
            ln = ln[ 1 : ]
            continue
            
        if ln.startswith('='):
            tok = Token(TokType.EQUALS)
            res.append(tok)
            ln = ln[ 1 : ]
            continue
            
        match = pat_symbol.match(ln)
        if match:
            val = match.group(0)
            tok = Token(TokType.SYMBOL, val)
            res.append(tok)
            ln = ln[ len(val) : ]
            continue

        match = pat_number.match(ln)
        if match:
            val = match.group(0)
            fval = float(val)
            tok = Token(TokType.NUM, fval)
            res.append(tok)
            ln = ln[ len(val) : ]
            continue

        match = pat_color.match(ln)
        if match:
            val = match.group(0)
            if len(val) not in [ 4, 7 ]:
                raise Exception('invalid color length: ' + val)
            tok = Token(TokType.COLOR, val)
            res.append(tok)
            ln = ln[ len(val) : ]
            continue

        raise Exception('invalid character: ' + ln)
        
    return res


class Term:
    def __init__(self, tok, name=None):
        self.tok = tok
        self.name = name
        self.args = []

    def __repr__(self):
        namestr = ''
        if self.name:
            namestr = self.name+'='
        argstr = ''
        if self.args:
            ls = [ repr(arg) for arg in self.args ]
            argstr = '(' + ', '.join(ls) + ')'
        return '<Term %s%s%s>' % (namestr, self.tok, argstr)

    def dump(self, indent=0):
        namestr = ''
        if self.name:
            namestr = self.name+'='
        colon = ':' if self.args else ''
        print('%s%s%s%s' % ('  '*indent, namestr, self.tok, colon))
        if self.args:
            for arg in self.args:
                arg.dump(indent+1)
        

def parseline(ln):
    res = []
    
    pos = comma_or_colon(ln)
    if pos is not None and ln[pos].typ is TokType.COMMA:
        head = ln[ : pos ]
        ln = ln[ pos+1 : ]
        term = bareterm(head)
        res.append(term)
        restls = parseline(ln)
        res.extend(restls)
        return res

    argterms = None
    if pos is not None and ln[pos].typ is TokType.COLON:
        args = ln[ pos+1 : ]
        ln = ln[ : pos ]
        if args:
            argterms = parseline(args)
        
    term = bareterm(ln)
    if argterms:
        if term.tok.typ != TokType.SYMBOL:
            raise Exception('only symbols can have args')
        term.args.extend(argterms)
    res.append(term)
    return res

def comma_or_colon(ln):
    for ix, tok in enumerate(ln):
        if tok.typ is TokType.COMMA:
            return ix
        if tok.typ is TokType.COLON:
            return ix
    return None

def bareterm(ln):
    nodname = None
    if len(ln) >= 2 and ln[1].typ is TokType.EQUALS:
        if ln[0].typ is not TokType.SYMBOL:
            raise Exception('not SYMBOL before =')
        nodname = ln[0].val
        ln = ln[ 2 : ]
    if len(ln) != 1:
        raise Exception('bareterm must be one token')
    tok = ln[0]
    if tok.typ not in [ TokType.SYMBOL, TokType.NUM, TokType.COLOR ]:
        raise Exception('invalid bareterm')
    term = Term(tok, name=nodname)
    return term


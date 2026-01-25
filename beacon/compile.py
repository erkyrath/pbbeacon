from collections import namedtuple

from .defs import Implicit, Dim, Color, WaveShape, AxisDep, axisdepname
from .lex import Term, TokType

def wave_sample(shape, var):
    # We can assume var is between 0 and 1
    match shape:
        case WaveShape.FLAT:
            return '1'
        case WaveShape.SQUARE:
            return '1'
        case WaveShape.HALFSQUARE:
            return '(%s < 0.5 ? 1 : 0)' % (var,)
        case WaveShape.SAWTOOTH:
            return '%s' % (var,)
        case WaveShape.SAWDECAY:
            return '(1-%s)' % (var,)
        case WaveShape.SQRTOOTH:
            return '%s*%s' % (var, var,)
        case WaveShape.SQRDECAY:
            return '(1-%s)*(1-%s)' % (var, var,)
        case WaveShape.TRIANGLE:
            return 'triangle(%s)' % (var,)
        case WaveShape.SINE:
            return 'sin(%s*PI)' % (var,)
        case _:
            raise NotImplementedError('wave_sample: %s' % (shape,))
    
class ArgFormat:
    def __init__(self, name, typ, anon=False, multiple=False, default=None):
        self.name = name
        self.typ = typ
        self.anon = anon
        self.multiple = multiple
        self.default = default
        self.isoptional = (default is not None)

    def __repr__(self):
        defaultstr = ' = %s' if self.default else ''
        return '<ArgFormat "%s" %s%s>' % (self.name, self.typ, defaultstr,)
    
class Node:
    classname = '???'
    idcount = 0

    argformat = None
    argformatmap = None
    argclass = None

    usesimplicit = False

    allclassmap = {}

    @staticmethod
    def prepclasses():
        if Node.allclassmap:
            return
        from .nodes import nodeclasses
        for cla in nodeclasses:
            Node.allclassmap[cla.classname] = cla
            cla.argformatmap = dict([(argf.name, argf) for argf in cla.argformat])
            cla.argclass = namedtuple('Args_'+cla.classname, [ argf.name for argf in cla.argformat ])
    
    def __init__(self, ctx):
        self.id = '%s_%d' % (self.classname, Node.idcount,)
        Node.idcount += 1

        self.implicit = ctx
        self.depend = AxisDep.NONE
        self.dim = Dim.NONE
        self.buffered = False

    def __repr__(self):
        return '<%s>' % (self.id,)

    def parseargs(self, args, defmap):
        map = {}
        for arg in args:
            if arg.name:
                argf = self.argformatmap[arg.name]
            else:
                pos = 0
                lastmultiple = None
                while pos < len(self.argformat):
                    argf = self.argformat[pos]
                    if argf.name not in map:
                        break
                    if argf.multiple:
                        lastmultiple = pos
                    pos += 1
                if pos >= len(self.argformat):
                    if lastmultiple is None:
                        raise Exception('%s: too many arguments' % (self.classname,))
                    pos = lastmultiple
                argf = self.argformat[pos]
            if not argf.multiple and argf.name in map:
                raise Exception('%s: duplicate arg: %s' % (self.classname, argf.name))

            argval = None
            
            if argf.typ is float:
                if arg.tok.typ is not TokType.NUM:
                    raise Exception('%s: %s must be numeric' % (self.classname, argf.name))
                argval = arg.tok.val
            elif argf.typ is int:
                if arg.tok.typ is not TokType.NUM:
                    raise Exception('%s: %s must be numeric' % (self.classname, argf.name))
                argval = int(arg.tok.val)
            elif argf.typ is Color:
                if arg.tok.typ is not TokType.COLOR:
                    raise Exception('%s: %s must be color' % (self.classname, argf.name))
                argval = Color(arg.tok.val)
            elif argf.typ is WaveShape:
                if arg.tok.typ is not TokType.SYMBOL:
                    raise Exception('%s: unrecognized waveshape' % (argf.name,))
                argval = WaveShape.__members__[arg.tok.val.upper()]
            elif argf.typ is Node:
                argval = compile(arg, implicit=self.implicit, defmap=defmap)
            elif argf.typ is Implicit.TIME:
                argval = compile(arg, implicit=Implicit.TIME, defmap=defmap)
            elif argf.typ is Implicit.SPACE:
                argval = compile(arg, implicit=Implicit.SPACE, defmap=defmap)
            else:
                raise Exception('%s: unimplemented arg type: %s (%s)' % (self.classname, argf.typ, argf.name))

            if not argf.multiple:
                map[argf.name] = argval
            else:
                if argf.name not in map:
                    map[argf.name] = []
                map[argf.name].append(argval)

        for argf in self.argformat:
            if argf.name not in map and argf.isoptional:
                if not (isinstance(argf.default, int) or isinstance(argf.default, float)):
                    raise Exception('%s: arg default is not numeric: %s' % (self.classname, argf.name))
                map[argf.name] = NodeConstant(Implicit.TIME, asnum=argf.default)

        self.args = self.argclass(**map)

    def getarg(self, key):
        return getattr(self.args, key)

    def getargls(self, key, multiple=False):
        arg = getattr(self.args, key)
        if not multiple:
            return [ arg ]
        else:
            return arg

    def finddim(self):
        raise NotImplementedError('finddim: ' + self.__class__.__name__)

    def constantval(self):
        return None
        
    def printstaticvars(self, outfl):
        pass
    
    def generateimplicit(self, ctx):
        if not self.usesimplicit:
            raise Exception('usesimplicit not set')
        if self.implicit is Implicit.TIME:
            if not ctx.timebase:
                return 'clock'
            else:
                return ctx.timebase
        if self.implicit is Implicit.SPACE:
            return '(ix/pixelCount)'
        raise Exception('implicit not set')

    def generatedata(self, ctx, component=None):
        id = self.id
        ### dim
        if self.buffered:
            if not (self.depend & AxisDep.SPACE):
                return f'{id}_scalar'
            else:
                return f'{id}_vector[ix]'
        return self.generateexpr(ctx, component=component)

    def generateexpr(self, ctx, component=None):
        raise NotImplementedError('generateexpr: %s' % (self.classname,))
    
    def dump(self, indent=0, name=None):
        indentstr = '  '*indent
        namestr = name+'=' if name else ''
        impstr = str(self.implicit)[0]
        dimstr = str(self.dim) if self.dim else '???'
        depstr = axisdepname(self.depend)
        bufstr = ' (BUF)' if self.buffered else ''
        print(f'{indentstr}{namestr}<{self.id}> ({impstr}:{dimstr}) dep={depstr}{bufstr}')
        for argf in self.argformat:
            argls = self.getargls(argf.name, argf.multiple)
            for arg in argls:
                if isinstance(arg, Node):
                    arg.dump(indent+1, name=argf.name)
                else:
                    print(f'{indentstr}  {argf.name}={arg}')
            


def compileall(trees, srclines=None):
    Node.prepclasses()
    Node.idcount = 0
    
    roots = []
    defmap = {}
    for term in trees:
        root = compile(term, implicit=Implicit.SPACE, defmap=defmap)
        roots.append(( root, term.name ))
        if term.name is not None:
            if term.name in defmap:
                raise Exception('duplicate def: %s' % (term.name,))
            defmap[term.name.lower()] = root

    startnod = None
    for (nod, name) in roots:
        if name is None:
            if startnod is not None:
                raise Exception('more than one start')
            startnod = nod
    return Program(startnod, defmap, srclines=srclines)

def compile(term, implicit, defmap):
    if term.tok.typ == TokType.NUM:
        if term.args:
            raise Exception('number cannot have args')
        return NodeConstant(implicit, asnum=term.tok.val)
    if term.tok.typ == TokType.COLOR:
        if term.args:
            raise Exception('color cannot have args')
        return NodeColor(implicit, ascol=term.tok.val)
    if term.tok.typ != TokType.SYMBOL:
        raise Exception('non-symbol')
    key = term.tok.val.lower()
    if key in defmap:
        if term.args:
            raise Exception('variable name cannot have args: %s' % (key,))
        return defmap[key]
    cla = Node.allclassmap.get(key)
    if not cla:
        raise Exception('unknown term: %s' % (key,))
    nod = cla(implicit)
    nod.parseargs(term.args, defmap=defmap)
    return nod

# Late imports
from .program import Program, Stanza
from .nodes import NodeConstant, NodeColor

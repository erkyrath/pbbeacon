from enum import StrEnum
from collections import namedtuple

from .lex import Term, TokType

class Implicit(StrEnum):
    TIME  = 'TIME'
    SPACE = 'SPACE'

class WaveShape(StrEnum):
    FLAT = 'FLAT'
    SQUARE = 'SQUARE'
    HALFSQUARE = 'HALFSQUARE'
    TRIANGLE = 'TRIANGLE'
    TRAPEZOID = 'TRAPEZOID'
    SAWTOOTH = 'SAWTOOTH'
    SQRTOOTH = 'SQRTOOTH'
    SAWDECAY = 'SAWDECAY'
    SQRDECAY = 'SQRDECAY'
    SINE = 'SINE'

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
    def prepclasses(classls):
        for cla in classls:
            Node.allclassmap[cla.classname] = cla
            cla.argformatmap = dict([(argf.name, argf) for argf in cla.argformat])
            cla.argclass = namedtuple('Args_'+cla.classname, [ argf.name for argf in cla.argformat ])
    
    def __init__(self, ctx):
        self.id = '%s_%d' % (self.classname, Node.idcount,)
        Node.idcount += 1

        self.implicit = ctx
        self.depend = AxisDep.NONE
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

    def constantval(self):
        return None
        
    def printstaticvars(self):
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

    def generatedata(self, ctx):
        if self.buffered:
            if not (self.depend & AxisDep.SPACE):
                return '%s_scalar' % (self.id,)
            else:
                return '%s_pixels[ix]' % (self.id,)
        return self.generateexpr(ctx)

    def generateexpr(self, ctx):
        raise NotImplementedError('generateexpr: %s' % (self.classname,))
    
    def dump(self, indent=0, name=None):
        indentstr = '  '*indent
        namestr = name+'=' if name else ''
        impstr = str(self.implicit)[0]
        depstr = axisdepname(self.depend)
        bufstr = ' (BUF)' if self.buffered else ''
        print('%s%s<%s> (%s) dep=%s%s' % (indentstr, namestr, self.id, impstr, depstr, bufstr))
        for argf in self.argformat:
            argls = self.getargls(argf.name, argf.multiple)
            for arg in argls:
                if isinstance(arg, Node):
                    arg.dump(indent+1, name=argf.name)
                else:
                    print('%s  %s=%s' % (indentstr, argf.name, arg,))
            

class NodeConstant(Node):
    classname = 'constant'

    argformat = [
        ArgFormat('value', float)
    ]

    def __init__(self, ctx, asnum=None):
        Node.__init__(self, ctx)
        if asnum is not None:
            self.args = self.argclass(value=asnum)

    def constantval(self):
        return self.args.value
        
    def generateexpr(self, ctx):
        return str(self.args.value)

class NodeQuote(Node):
    classname = 'quote'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node),
    ]

    def generateexpr(self, ctx):
        raise Exception('cannot use quote directly')

class NodeTime(Node):
    classname = 'time'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Implicit.TIME),
    ]

    def generateexpr(self, ctx):
        argdata = self.args.arg.generatedata(ctx=ctx)
        return argdata

class NodeSpace(Node):
    classname = 'space'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Implicit.SPACE),
    ]

    def generateexpr(self, ctx):
        argdata = self.args.arg.generatedata(ctx=ctx)
        return argdata

class NodeLinear(Node):
    classname = 'linear'

    usesimplicit = True
    argformat = [
        ArgFormat('start', Implicit.TIME),
        ArgFormat('velocity', Implicit.TIME),
    ]

    def generateexpr(self, ctx):
        param = self.generateimplicit(ctx)
        startdata = self.args.start.generatedata(ctx=ctx)
        veldata = self.args.velocity.generatedata(ctx=ctx)
        return '(%s + %s * %s)' % (startdata, param, veldata,)

class NodeRandFlat(Node):
    classname = 'randflat'

    usesimplicit = True
    argformat = [
        ArgFormat('min', Implicit.TIME),
        ArgFormat('max', Implicit.TIME),
    ]

    def generateexpr(self, ctx):
        # Don't actually use generateimplicit
        mindata = self.args.min.generatedata(ctx=ctx)
        maxdata = self.args.max.generatedata(ctx=ctx)
        minval = ctx.store_val(self, 'min', mindata)
        diffval = ctx.store_val(self, 'diff', '(%s-%s)' % (maxdata, minval,))
        return '(random(%s)+%s)' % (diffval, minval,)
    
class NodeRandNorm(Node):
    classname = 'randnorm'

    usesimplicit = True
    argformat = [
        ArgFormat('mean', Implicit.TIME, default=0.5),
        ArgFormat('stdev', Implicit.TIME, default=0.25),
    ]

    def generateexpr(self, ctx):
        # Don't actually use generateimplicit
        meandata = self.args.mean.generatedata(ctx=ctx)
        stdevdata = self.args.stdev.generatedata(ctx=ctx)
        ### constant-fold the stdev/0.522 part if possible?
        return '(((random(1)+random(1)+random(1)-1.5)*%s/0.522)+%s)' % (stdevdata, meandata,)
    
class NodeClamp(Node):
    classname = 'clamp'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node),
        ArgFormat('min', Implicit.TIME, default=0),
        ArgFormat('max', Implicit.TIME, default=1),
    ]

    def generateexpr(self, ctx):
        argdata = self.args.arg.generatedata(ctx=ctx)
        mindata = self.args.min.generatedata(ctx=ctx)
        maxdata = self.args.max.generatedata(ctx=ctx)
        return 'clamp(%s, %s, %s)' % (argdata, mindata, maxdata,)

class NodeSum(Node):
    classname = 'sum'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node, multiple=True),
    ]

    ### constantval if needed...

    def generateexpr(self, ctx):
        argdata = []
        for arg in self.args.arg:
            argdata.append(arg.generatedata(ctx=ctx))
        if len(argdata) == 1:
            return argdata[0]
        return '(%s)' % (' + '.join(argdata),)
    
class NodeMean(Node):
    classname = 'mean'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node, multiple=True),
    ]

    def generateexpr(self, ctx):
        argdata = []
        for arg in self.args.arg:
            argdata.append(arg.generatedata(ctx=ctx))
        if len(argdata) == 1:
            return argdata[0]
        return '(%s) / %s' % (' + '.join(argdata), len(argdata),)
    
class NodeMul(Node):
    classname = 'mul'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node, multiple=True),
    ]

    ### constantval if needed...

    def generateexpr(self, ctx):
        argdata = []
        for arg in self.args.arg:
            argdata.append(arg.generatedata(ctx=ctx))
        if len(argdata) == 1:
            return argdata[0]
        return '(%s)' % (' * '.join(argdata),)
    
class NodeWave(Node):
    classname = 'wave'

    usesimplicit = True
    argformat = [
        ArgFormat('shape', WaveShape),
        ArgFormat('min', Implicit.TIME, default=0),
        ArgFormat('max', Implicit.TIME, default=1),
        ArgFormat('period', Implicit.TIME, default=1),
        ### offset?
    ]

    def generateexpr(self, ctx):
        param = self.generateimplicit(ctx)
        mindata = self.args.min.generatedata(ctx=ctx)
        maxdata = self.args.max.generatedata(ctx=ctx)
        perioddata = self.args.period.generatedata(ctx=ctx)
        if self.implicit is Implicit.SPACE:
            theta = '((%s-0.5)/%s+0.5)' % (param, perioddata,)
        else:
            theta = '%s/%s' % (param, perioddata,)
            
        match self.args.shape:
            case WaveShape.FLAT:
                return maxdata
            case WaveShape.SAWTOOTH:
                minval = ctx.store_val(self, 'min', mindata)
                diffval = ctx.store_val(self, 'diff', '(%s-%s)' % (maxdata, minval,))
                return '(%s+%s*(mod(%s, 1)))' % (minval, diffval, theta)
            case WaveShape.SAWDECAY:
                minval = ctx.store_val(self, 'min', mindata)
                diffval = ctx.store_val(self, 'diff', '(%s-%s)' % (maxdata, minval,))
                return '(%s+%s*(1-mod(%s, 1)))' % (minval, diffval, theta)
            case WaveShape.SQRTOOTH:
                minval = ctx.store_val(self, 'min', mindata)
                diffval = ctx.store_val(self, 'diff', '(%s-%s)' % (maxdata, minval,))
                return '(%s+%s*(pow(mod(%s, 1), 2)))' % (minval, diffval, theta)
            case WaveShape.SQRDECAY:
                minval = ctx.store_val(self, 'min', mindata)
                diffval = ctx.store_val(self, 'diff', '(%s-%s)' % (maxdata, minval,))
                return '(%s+%s*(pow(1-mod(%s, 1), 2)))' % (minval, diffval, theta)
            case WaveShape.TRIANGLE:
                minval = ctx.store_val(self, 'min', mindata)
                diffval = ctx.store_val(self, 'diff', '(%s-%s)' % (maxdata, minval,))
                return '(%s+%s*(triangle(%s)))' % (minval, diffval, theta)
            case WaveShape.HALFSQUARE:
                minval = ctx.store_val(self, 'min', mindata)
                diffval = ctx.store_val(self, 'diff', '(%s-%s)' % (maxdata, minval,))
                return '(%s+%s*(square(%s, 0.5)))' % (minval, diffval, theta)
            case WaveShape.SINE:
                minval = ctx.store_val(self, 'min', mindata)
                hdiffval = ctx.store_val(self, 'hdiff', '((%s-%s)*0.5)' % (maxdata, minval,))
                return '(%s+%s*(1-cos(PI2*%s)))' % (minval, hdiffval, theta)
            case _:
                raise Exception('unimplemented WaveShape')

class NodePulser(Node):
    classname = 'pulser'
    
    usesimplicit = False
    argformat = [
        ArgFormat('maxcount', int),
        ArgFormat('spaceshape', WaveShape, default=WaveShape.TRIANGLE),
        ArgFormat('timeshape', WaveShape, default=WaveShape.SQRDECAY),
        ArgFormat('interval', Implicit.TIME, default=1),
        ArgFormat('pos', Implicit.TIME, default=0.5),
        ArgFormat('duration', Implicit.TIME, default=1),
        ArgFormat('width', Implicit.TIME, default=0.5),
    ]

    def parseargs(self, args, defmap):
        Node.parseargs(self, args, defmap)
        self.quote_pos = None
        self.quote_width = None
        self.quote_duration = None
        ### We could auto-quote constants to save the array space
        if isinstance(self.args.pos, NodeQuote):
            self.quote_pos = self.args.pos.args.arg
        if isinstance(self.args.width, NodeQuote):
            self.quote_width = self.args.width.args.arg
        if isinstance(self.args.duration, NodeQuote):
            self.quote_duration = self.args.duration.args.arg
    
    def printstaticvars(self):
        maxcount = self.args.maxcount
        print('var %s_live = array(%d)' % (self.id, maxcount,))
        print('var %s_birth = array(%d)' % (self.id, maxcount,))
        print('var %s_livecount = 0' % (self.id,))
        print('var %s_nextstart = 0' % (self.id,))
        if not self.quote_pos:
            print('var %s_arg_pos = array(%d)' % (self.id, maxcount,))
        if not self.quote_width:
            print('var %s_arg_width = array(%d)' % (self.id, maxcount,))
        if not self.quote_duration:
            print('var %s_arg_duration = array(%d)' % (self.id, maxcount,))
    
    def generateexpr(self, ctx):
        assert self.buffered
        maxcount = self.args.maxcount
        ctx.after('if (clock >= %s_nextstart && %s_livecount < %d) {' % (self.id, self.id, maxcount,))
        ctx.after('  for (var px=0; px<%d; px++) {' % (maxcount,))
        ctx.after('    if (!%s_live[px]) { break }' % (self.id,))
        ctx.after('  }')
        ctx.after('  if (px < %d) {' % (maxcount,))
        ctx.after('    %s_live[px] = 1' % (self.id,))
        ctx.after('    livecount += 1')
        if not self.quote_pos:
            qctx = Stanza(self)
            iposdata = self.args.pos.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=2)
            ctx.after('    %s_arg_pos[px] = %s' % (self.id, iposdata))
        if not self.quote_width:
            qctx = Stanza(self)
            iwidthdata = self.args.width.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=2)
            ctx.after('    %s_arg_width[px] = %s' % (self.id, iwidthdata))
        if not self.quote_duration:
            qctx = Stanza(self)
            idurationdata = self.args.duration.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=2)
            ctx.after('    %s_arg_duration[px] = %s' % (self.id, idurationdata))
        qctx = Stanza(self)
        intervaldata = self.args.interval.generatedata(ctx=qctx)
        qctx.transfer(ctx, indent=2)
        ctx.after('    %s_nextstart = clock + %s' % (self.id, intervaldata,))
        ctx.after('    %s_birth[px] = clock' % (self.id,))
        ctx.after('  }')

        ctx.after('}')
        ctx.after('for (var px=0; px<%d; px++) {' % (maxcount,))
        ctx.after('  if (!%s_live[px]) { break }' % (self.id,))
        ctx.after('  age = clock - %s_birth[px]' % (self.id,))
        if self.args.timeshape is WaveShape.FLAT:
            ctx.after('  timeval = 1')
        else:
            if not self.quote_duration:
                ctx.after('  relage = age / %s_arg_duration[px]' % (self.id,))
            else:
                qctx = Stanza(self, timebase='age')
                durationdata = self.quote_duration.generatedata(ctx=qctx)
                qctx.transfer(ctx, indent=1)
                ctx.after('  relage = age / %s' % (durationdata,))
            ctx.after('  if (relage > 1.0) {\n      %s_live[px] = 0\n      livecount -= 1\n      continue\n    }' % (self.id,))
            ctx.after('  timeval = %s' % (wave_sample(self.args.timeshape, 'relage'),))
        ### minpos, maxpos, and check if pulse has flown off the edge
        
        if not self.quote_pos:
            ctx.after('  ppos = %s_arg_pos[px]' % (self.id,))
        else:
            qctx = Stanza(self, timebase='age')
            posdata = self.quote_pos.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=1)
            ctx.after('  ppos = %s' % (posdata,))
            
        if not self.quote_width:
            ctx.after('  pwidth = %s_arg_width[px]' % (self.id,))
        else:
            qctx = Stanza(self, timebase='age')
            widthdata = self.quote_width.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=1)
            ctx.after('  pwidth = %s' % (widthdata,))
            
        if self.args.spaceshape is WaveShape.FLAT:
            ctx.after('  minpos = 0')
            ctx.after('  maxpos = pixelCount')
        else:
            ctx.after('  minpos = max(0, pixelCount*(ppos-pwidth/2))')
            ctx.after('  maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))')
        ctx.after('  for (var ix=minpos; ix<maxpos; ix++) {')
        if self.args.spaceshape is WaveShape.FLAT:
            ctx.after('    spaceval = 1')
        else:
            ctx.after('    relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth')
            ctx.after('    spaceval = %s' % (wave_sample(self.args.spaceshape, 'relpos'),))
        ctx.after('    %s_pixels[ix] += (timeval * spaceval)' % (self.id,))
        ctx.after('  }')
        ctx.after('}')
        
        # This is just the initial buffer-clear.
        return '0'

nodeclasses = [
    NodeConstant,
    NodeQuote,
    NodeTime,
    NodeSpace,
    NodeLinear,
    NodeRandFlat,
    NodeRandNorm,
    NodeClamp,
    NodeSum,
    NodeMean,
    NodeMul,
    NodeWave,
    NodePulser,
]

Node.prepclasses(nodeclasses)

def compileall(trees):
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
    return Program(startnod, defmap)

def compile(term, implicit, defmap):
    if term.tok.typ == TokType.NUM:
        if term.args:
            raise Exception('number cannot have args')
        return NodeConstant(implicit, asnum=term.tok.val)
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
from .program import Program, Stanza, AxisDep, axisdepname

from .defs import Implicit, Dim, Color, WaveShape
from .compile import Node, ArgFormat, wave_sample
from .program import Stanza

class NodeConstant(Node):
    classname = 'constant'

    argformat = [
        ArgFormat('value', float)
    ]

    def __init__(self, ctx, asnum=None):
        Node.__init__(self, ctx)
        if asnum is not None:
            self.args = self.argclass(value=asnum)

    def finddim(self):
        return Dim.ONE
    
    def constantval(self):
        return self.args.value
        
    def generateexpr(self, ctx):
        return str(self.args.value)

class NodeColor(Node):
    classname = 'color'

    argformat = [
        ArgFormat('value', Color)
    ]

    def __init__(self, ctx, ascol=None):
        Node.__init__(self, ctx)
        if ascol is not None:
            self.args = self.argclass(value=Color(ascol))

    def finddim(self):
        return Dim.THREE
    
    def generateexpr(self, ctx):
        return '###'

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

    def finddim(self):
        return self.args.arg.dim
    
    def generateexpr(self, ctx):
        argdata = self.args.arg.generatedata(ctx=ctx)
        return argdata

class NodeSpace(Node):
    classname = 'space'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Implicit.SPACE),
    ]

    def finddim(self):
        return self.args.arg.dim
    
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

    def finddim(self):
        return Dim.ONE
    
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

    def finddim(self):
        return Dim.ONE
    
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

    def finddim(self):
        return Dim.ONE
    
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

    def finddim(self):
        return max([ arg.dim for arg in self.args.arg ])
        
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

    def finddim(self):
        return max([ arg.dim for arg in self.args.arg ])
        
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

    def finddim(self):
        return max([ arg.dim for arg in self.args.arg ])
        
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

    def finddim(self):
        return Dim.ONE
    
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

        # We treat constant args as quoted because it makes simpler code.
        
        if isinstance(self.args.pos, NodeQuote):
            self.quote_pos = self.args.pos.args.arg
        elif isinstance(self.args.pos, NodeConstant):
            self.quote_pos = self.args.pos

        if isinstance(self.args.width, NodeQuote):
            self.quote_width = self.args.width.args.arg
        elif isinstance(self.args.width, NodeConstant):
            self.quote_width = self.args.width
            
        if isinstance(self.args.duration, NodeQuote):
            self.quote_duration = self.args.duration.args.arg
        elif isinstance(self.args.duration, NodeConstant):
            self.quote_duration = self.args.duration
    
    def finddim(self):
        return Dim.ONE
    
    def printstaticvars(self, outfl):
        id = self.id
        maxcount = self.args.maxcount
        outfl.write(f'var {id}_live = array({maxcount})\n')
        outfl.write(f'var {id}_birth = array({maxcount})\n')
        outfl.write(f'var {id}_livecount = 0\n')
        outfl.write(f'var {id}_nextstart = 0\n')
        if not self.quote_pos:
            outfl.write(f'var {id}_arg_pos = array({maxcount})\n')
        if not self.quote_width:
            outfl.write(f'var {id}_arg_width = array({maxcount})\n')
        if not self.quote_duration:
            outfl.write(f'var {id}_arg_duration = array({maxcount})\n')
    
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
        ctx.after('    %s_vector[ix] += (timeval * spaceval)' % (self.id,))
        ctx.after('  }')
        ctx.after('}')
        
        # This is just the initial buffer-clear.
        return '0'

nodeclasses = [
    NodeConstant,
    NodeColor,
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




from .defs import Implicit, Dim, Color, WaveShape, AxisDep
from .compile import Node, ArgFormat, wave_sample, compile, find_unquoted_children
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
    
    def isconstant(self):
        return True
    
    def iszpositive(self):
        return (self.args.value >= 0)
    
    def isznegative(self):
        return (self.args.value <= 0)
    
    def isnondecreasing(self):
        return True
    
    def isnonincreasing(self):
        return True
    
    def generateexpr(self, ctx, component=None):
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
    
    def isconstant(self):
        return True
    
    def generateexpr(self, ctx, component):
        if component == 'r':
            return str(self.args.value.red)
        if component == 'g':
            return str(self.args.value.green)
        if component == 'b':
            return str(self.args.value.blue)
        raise Exception('color: no component')

class NodeQuote(Node):
    classname = 'quote'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node),
    ]

    def finddim(self):
        return self.args.arg.dim
    
    def generateexpr(self, ctx, component=None):
        raise Exception('cannot use quote directly')

class NodeTime(Node):
    classname = 'time'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Implicit.TIME),
    ]

    def finddim(self):
        return self.args.arg.dim
    
    def generateexpr(self, ctx, component=None):
        argdata = self.args.arg.generatedata(ctx=ctx, component=component)
        return argdata

class NodeSpace(Node):
    classname = 'space'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Implicit.SPACE),
    ]

    def finddim(self):
        return self.args.arg.dim
    
    def generateexpr(self, ctx, component=None):
        argdata = self.args.arg.generatedata(ctx=ctx, component=component)
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
    
    def iszpositive(self):
        return self.args.start.iszpositive() and self.args.velocity.iszpositive()
    
    def isznegative(self):
        return self.args.start.isznegative() and self.args.velocity.isznegative()
    
    def isnondecreasing(self):
        return self.args.velocity.iszpositive()

    def isnonincreasing(self):
        return self.args.velocity.isznegative()

    def generateexpr(self, ctx, component=None):
        param = self.generateimplicit(ctx)
        startdata = self.args.start.generatedata(ctx=ctx)
        veldata = self.args.velocity.generatedata(ctx=ctx)
        return f'({startdata} + {param} * {veldata})'

class NodeChanging(Node):
    classname = 'changing'

    usesimplicit = True
    argformat = [
        ArgFormat('start', Implicit.TIME),
        ArgFormat('velocity', Implicit.TIME),
    ]

    ### args cannot be SPACE

    def finddim(self):
        return Dim.ONE
    
    def iszpositive(self):
        return self.args.start.iszpositive() and self.args.velocity.iszpositive()
    
    def isznegative(self):
        return self.args.start.isznegative() and self.args.velocity.isznegative()
    
    def isnondecreasing(self):
        return self.args.velocity.iszpositive()

    def isnonincreasing(self):
        return self.args.velocity.isznegative()

    def printstaticvars(self, outfl, first=False):
        id = self.id
        outfl.write(f'var {id}_val_accum = 0\n')
        
    def generateexpr(self, ctx, component=None):
        if self.implicit is Implicit.SPACE:
            raise Exception('changing cannot be SPACE')
        id = self.id
        param = self.generateimplicit(ctx)
        startdata = self.args.start.generatedata(ctx=ctx)
        veldata = self.args.velocity.generatedata(ctx=ctx)
        # hacky: "accum" lines up with our staticvar
        ctx.store_val(self, 'accum', f'({id}_val_accum + (delta/1000)*{veldata})')
        return f'({startdata} + {id}_val_accum)'

class NodeRandFlat(Node):
    classname = 'randflat'

    # We set usesimplicit because the value will vary across time or space;
    # we don't want the compiler to precompute a single "random" value.
    
    usesimplicit = True
    argformat = [
        ArgFormat('min', Implicit.TIME),
        ArgFormat('max', Implicit.TIME),
    ]

    def finddim(self):
        return Dim.ONE

    def iszpositive(self):
        return self.args.min.iszpositive() and self.args.max.iszpositive()
    
    def isznegative(self):
        return self.args.min.isznegative() and self.args.max.isznegative()
    
    def generateexpr(self, ctx, component=None):
        # Don't actually use generateimplicit
        mindata = self.args.min.generatedata(ctx=ctx)
        maxdata = self.args.max.generatedata(ctx=ctx)
        minval = ctx.store_val(self, 'min', mindata)
        diffval = ctx.store_val(self, 'diff', f'({maxdata}-{minval})')
        return f'(random({diffval})+{minval})'
    
class NodeRandNorm(Node):
    classname = 'randnorm'

    # We set usesimplicit because the value will vary across time or space;
    # we don't want the compiler to precompute a single "random" value.
    
    usesimplicit = True
    argformat = [
        ArgFormat('mean', Implicit.TIME, default=0.5),
        ArgFormat('stdev', Implicit.TIME, default=0.25),
    ]

    def finddim(self):
        return Dim.ONE
    
    def generateexpr(self, ctx, component=None):
        # Don't actually use generateimplicit
        meandata = self.args.mean.generatedata(ctx=ctx)
        stdevdata = self.args.stdev.generatedata(ctx=ctx)
        ### constant-fold the stdev/0.522 part if possible?
        return f'(((random(1)+random(1)+random(1)-1.5)*{stdevdata}/0.522)+{meandata})'
    
class NodeClamp(Node):
    classname = 'clamp'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node),
        ArgFormat('min', Implicit.TIME, default=0),
        ArgFormat('max', Implicit.TIME, default=1),
    ]

    def finddim(self):
        assert self.args.arg.dim is self.args.min.dim
        assert self.args.arg.dim is self.args.max.dim
        return self.args.arg.dim
    
    def generateexpr(self, ctx, component=None):
        argdata = self.args.arg.generatedata(ctx=ctx, component=component)
        mindata = self.args.min.generatedata(ctx=ctx, component=component)
        maxdata = self.args.max.generatedata(ctx=ctx, component=component)
        return 'clamp(%s, %s, %s)' % (argdata, mindata, maxdata,)

class NodeLerp(Node):
    classname = 'lerp'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg1', Node),
        ArgFormat('arg2', Node),
        ArgFormat('weight', Node),
    ]

    def finddim(self):
        assert self.args.weight.dim is Dim.ONE
        assert self.args.arg1.dim is self.args.arg2.dim
        return self.args.arg1.dim
    
    def generateexpr(self, ctx, component=None):
        weightdata = self.args.weight.generatedata(ctx=ctx)
        if self.dim is Dim.ONE:
            arg1data = self.args.arg1.generatedata(ctx=ctx)
            arg2data = self.args.arg2.generatedata(ctx=ctx)
            return f'mix({arg1data}, {arg2data}, {weightdata})'
        elif self.dim is Dim.THREE:
            argdata = []
            for arg in [self.args.arg1, self.args.arg2]:
                if arg.dim is Dim.ONE:
                    if arg.isconstant():
                        argval = arg.generatedata(ctx=ctx)
                    else:
                        argval = ctx.find_val(self, 'common')
                        if argval is None:
                            argval = ctx.store_val(self, 'common', arg.generatedata(ctx=ctx))
                    argdata.append(argval)
                elif arg.dim is Dim.THREE:
                    argdata.append(arg.generatedata(ctx=ctx, component=component))
                else:
                    raise Exception('bad dim')
            return f'mix({argdata[0]}, {argdata[1]}, {weightdata})'
        else:
            raise Exception('bad dim')

class NodeSum(Node):
    classname = 'sum'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node, multiple=True),
    ]

    def finddim(self):
        return max([ arg.dim for arg in self.args.arg ])
        
    def generateexpr(self, ctx, component=None):
        argdata = []
        if self.dim is Dim.ONE:
            for arg in self.args.arg:
                argdata.append(arg.generatedata(ctx=ctx))
        elif self.dim is Dim.THREE:
            argdata = self.generatelistas3(self.args.arg, ctx, component=component)
        else:
            raise Exception('bad dim')
        if len(argdata) == 1:
            return argdata[0]
        argls = ' + '.join(argdata)
        return f'({argls})'
    
class NodeMean(Node):
    classname = 'mean'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node, multiple=True),
    ]

    def finddim(self):
        return max([ arg.dim for arg in self.args.arg ])
        
    def generateexpr(self, ctx, component=None):
        argdata = []
        if self.dim is Dim.ONE:
            for arg in self.args.arg:
                argdata.append(arg.generatedata(ctx=ctx))
        elif self.dim is Dim.THREE:
            argdata = self.generatelistas3(self.args.arg, ctx, component=component)
        else:
            raise Exception('bad dim')
        if len(argdata) == 1:
            return argdata[0]
        argls = ' + '.join(argdata)
        return f'({argls}) / {len(argdata)}'
    
class NodeMul(Node):
    classname = 'mul'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node, multiple=True),
    ]

    def finddim(self):
        return max([ arg.dim for arg in self.args.arg ])
        
    def generateexpr(self, ctx, component=None):
        argdata = []
        if self.dim is Dim.ONE:
            for arg in self.args.arg:
                argdata.append(arg.generatedata(ctx=ctx))
        elif self.dim is Dim.THREE:
            argdata = self.generatelistas3(self.args.arg, ctx, component=component)
        else:
            raise Exception('bad dim')
        if len(argdata) == 1:
            return argdata[0]
        argls = ' * '.join(argdata)
        return f'({argls})'
    
class NodeMax(Node):
    classname = 'max'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node, multiple=True),
    ]

    def finddim(self):
        return max([ arg.dim for arg in self.args.arg ])
        
    def generateexpr(self, ctx, component=None):
        argdata = []
        if self.dim is Dim.ONE:
            for arg in self.args.arg:
                argdata.append(arg.generatedata(ctx=ctx))
        elif self.dim is Dim.THREE:
            argdata = self.generatelistas3(self.args.arg, ctx, component=component)
        else:
            raise Exception('bad dim')
        res = argdata[0]
        for dat in argdata[ 1 : ]:
            res = f'max({res}, {dat})'
        return res
    
class NodeMin(Node):
    classname = 'min'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node, multiple=True),
    ]

    def finddim(self):
        return max([ arg.dim for arg in self.args.arg ])
        
    def generateexpr(self, ctx, component=None):
        argdata = []
        if self.dim is Dim.ONE:
            for arg in self.args.arg:
                argdata.append(arg.generatedata(ctx=ctx))
        elif self.dim is Dim.THREE:
            argdata = self.generatelistas3(self.args.arg, ctx, component=component)
        else:
            raise Exception('bad dim')
        res = argdata[0]
        for dat in argdata[ 1 : ]:
            res = f'min({res}, {dat})'
        return res
    
class NodeWave(Node):
    classname = 'wave'

    usesimplicit = True
    argformat = [
        ArgFormat('shape', WaveShape),
        ArgFormat('min', Implicit.TIME, default=0),
        ArgFormat('max', Implicit.TIME, default=1),
        ArgFormat('period', Implicit.TIME, default=1),
        ArgFormat('shift', Implicit.TIME, default=0),
    ]

    def finddim(self):
        return Dim.ONE

    def iszpositive(self):
        return self.args.min.iszpositive() and self.args.max.iszpositive()
    
    def isznegative(self):
        return self.args.min.isznegative() and self.args.max.isznegative()
    
    def generateexpr(self, ctx, component=None):
        param = self.generateimplicit(ctx)
        mindata = self.args.min.generatedata(ctx=ctx)
        maxdata = self.args.max.generatedata(ctx=ctx)
        perioddata = self.args.period.generatedata(ctx=ctx)
        shiftdata = self.args.shift.generatedata(ctx=ctx)
        hasshift = (shiftdata not in ('0', '0.0'))   # hacky
        if self.implicit is Implicit.SPACE:
            if not hasshift:
                theta = f'(({param}-0.5)/{perioddata}+0.5)'
            else:
                ### could constant-fold if shiftdata is constant
                theta = f'(({param}-(0.5+{shiftdata}))/{perioddata}+0.5)'
        else:
            if not hasshift:
                theta = f'{param}/{perioddata}'
            else:
                theta = f'({param} - {shiftdata})/{perioddata}'
            
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

class NodeRGB(Node):
    classname = 'rgb'

    usesimplicit = False
    argformat = [
        ArgFormat('r', Node),
        ArgFormat('g', Node),
        ArgFormat('b', Node),
    ]

    def finddim(self):
        assert self.args.r.dim is Dim.ONE
        assert self.args.g.dim is Dim.ONE
        assert self.args.b.dim is Dim.ONE
        return Dim.THREE

    def generateexpr(self, ctx, component=None):
        if component == 'r':
            return self.args.r.generatedata(ctx=ctx, component=None)
        if component == 'g':
            return self.args.g.generatedata(ctx=ctx, component=None)
        if component == 'b':
            return self.args.b.generatedata(ctx=ctx, component=None)

class NodeBrightness(Node):
    classname = 'brightness'

    usesimplicit = False
    argformat = [
        ArgFormat('value', Node),
    ]

    def finddim(self):
        assert self.args.value.dim is Dim.THREE
        return Dim.ONE

    def generateexpr(self, ctx, component=None):
        argdatar = self.args.value.generatedata(ctx=ctx, component='r')
        argdatag = self.args.value.generatedata(ctx=ctx, component='g')
        argdatab = self.args.value.generatedata(ctx=ctx, component='b')
        return f'(0.299 * {argdatar} + 0.587 * {argdatag} + 0.114 * {argdatab})'

eval_gradient_func = '''
function evalGradient(val, posls, colls, count)
{
  if (val <= posls[0]) {
    return colls[0]
  }
  if (val >= posls[count-1]) {
    return colls[count-1]
  }
  for (var ix=0; ix<count-1; ix++) {
    if (val < posls[ix+1]) {
      return mix(colls[ix], colls[ix+1], (val-posls[ix])/(posls[ix+1]-posls[ix]))
    }
  }
  return colls[count-1]
}
'''
    
class NodeGradient(Node):
    classname = 'gradient'

    usesimplicit = False
    argformat = [
        ArgFormat('stops', Node, multiple=True),
        ArgFormat('arg', Node),
    ]

    def parseargs(self, args, defmap):
        stops = []
        mainval = None
        for arg in args:
            if arg.tok.val == 'stop':
                stop = compile(arg, implicit=self.implicit, defmap=defmap)
                stops.append( (stop.args.value, stop.args.color) )
                continue
            if mainval is not None:
                raise Exception('%s: duplicate arg' % (self.classname,))
            mainval = compile(arg, implicit=self.implicit, defmap=defmap)
        if not stops:
            raise Exception('%s: missing stops' % (self.classname,))
        stops.sort()
        self.args = self.argclass(stops=stops, arg=mainval)
    
    def finddim(self):
        assert self.args.arg.dim is Dim.ONE
        return Dim.THREE

    def printstaticvars(self, outfl, first=False):
        if first:
            outfl.write(eval_gradient_func)
        id = self.id
        posls = []
        colrs = []
        colgs = []
        colbs = []
        for pos, col in self.args.stops:
            posls.append(pos)
            colrs.append(col.red)
            colgs.append(col.green)
            colbs.append(col.blue)
        ls = ', '.join([ str(val) for val in posls ])
        outfl.write(f'var {id}_grad_pos = [{ls}]\n')
        ls = ', '.join([ str(val) for val in colrs ])
        outfl.write(f'var {id}_grad_r = [{ls}]\n')
        ls = ', '.join([ str(val) for val in colgs ])
        outfl.write(f'var {id}_grad_g = [{ls}]\n')
        ls = ', '.join([ str(val) for val in colbs ])
        outfl.write(f'var {id}_grad_b = [{ls}]\n')
        
    def generateexpr(self, ctx, component=None):
        id = self.id
        count = len(self.args.stops)
        argdata = self.args.arg.generatedata(ctx=ctx)
        return f'evalGradient({argdata}, {id}_grad_pos, {id}_grad_{component}, {count})'
    
class NodeStop(Node):
    classname = 'stop'
    
    argformat = [
        ArgFormat('value', float),
        ArgFormat('color', Color),
    ]

    def finddim(self):
        raise Exception('stop can only be used in a gradient')


class NodeDecay(Node):
    classname = 'decay'

    usesimplicit = False
    argformat = [
        ArgFormat('halflife', float),
        ArgFormat('arg', Node),
    ]
    
    def finddim(self):
        return self.args.arg.dim

    def generateexpr(self, ctx, component=None):
        assert self.buffered
        halflife = self.args.halflife
        argdata = self.args.arg.generatedata(ctx=ctx, component=component)
        id = self.id
        last = '???'
        if self.dim is Dim.ONE:
            if not (self.depend & AxisDep.SPACE):
                last = f'{id}_scalar'
            else:
                last = f'{id}_vector[ix]'
        elif self.dim is Dim.THREE:
            if not (self.depend & AxisDep.SPACE):
                last = f'{id}_scalar_{component}'
            else:
                last = f'{id}_vector_{component}[ix]'
        return f'max({last}*pow(2, -delta/{1000*halflife}), {argdata})'

### NodePulse?
### with spaceshape, pos, width

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

        self.unquotedargs = {}
        for key in ['pos', 'width', 'duration']:
            ls = find_unquoted_children(getattr(self.args, key))
            self.unquotedargs[key] = ls
    
    def finddim(self):
        return Dim.ONE
    
    def printstaticvars(self, outfl, first=False):
        id = self.id
        maxcount = self.args.maxcount
        outfl.write(f'var {id}_live = array({maxcount})\n')
        outfl.write(f'var {id}_birth = array({maxcount})\n')
        outfl.write(f'var {id}_livecount = 0\n')
        outfl.write(f'var {id}_nextstart = 0\n')
        for key in ['pos', 'width', 'duration']:
            for nod in self.unquotedargs[key]:
                outfl.write(f'var {id}_{key}_{nod.id} = array({maxcount})\n')
    
    def generateexpr(self, ctx, component=None):
        assert self.buffered
        assert component is None
        id = self.id
        maxcount = self.args.maxcount
        ctx.after('if (clock >= %s_nextstart && %s_livecount < %d) {' % (self.id, self.id, maxcount,))
        ctx.after('  for (var px=0; px<%d; px++) {' % (maxcount,))
        ctx.after('    if (!%s_live[px]) { break }' % (self.id,))
        ctx.after('  }')
        ctx.after('  if (px < %d) {' % (maxcount,))
        ctx.after('    %s_live[px] = 1' % (self.id,))
        ctx.after('    livecount += 1')
        for nod in self.unquotedargs['pos']:
            qctx = Stanza(self)
            unqdata = nod.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=2)
            ctx.after('    %s_pos_%s[px] = %s' % (self.id, nod.id, unqdata))
        for nod in self.unquotedargs['width']:
            qctx = Stanza(self)
            unqdata = nod.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=2)
            ctx.after('    %s_width_%s[px] = %s' % (self.id, nod.id, unqdata))
        for nod in self.unquotedargs['duration']:
            qctx = Stanza(self)
            unqdata = nod.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=2)
            ctx.after('    %s_duration_%s[px] = %s' % (self.id, nod.id, unqdata))
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
            qctx = Stanza(self, timebase='age', quoteparent=self, quotekey='duration')
            durationdata = self.args.duration.generatedata(ctx=qctx)
            qctx.transfer(ctx, indent=1)
            ctx.after(f'  relage = age / {durationdata}')
            ctx.after('  if (relage > 1.0) {\n      %s_live[px] = 0\n      livecount -= 1\n      continue\n    }' % (self.id,))
            ctx.after('  timeval = %s' % (wave_sample(self.args.timeshape, 'relage'),))

        qctx = Stanza(self, timebase='age', quoteparent=self, quotekey='pos')
        posdata = self.args.pos.generatedata(ctx=qctx)
        qctx.transfer(ctx, indent=1)
        ctx.after(f'  ppos = {posdata}')
            
        qctx = Stanza(self, timebase='age', quoteparent=self, quotekey='pos')
        widthdata = self.args.width.generatedata(ctx=qctx)
        qctx.transfer(ctx, indent=1)
        ctx.after(f'  pwidth = {widthdata}')

        if isinstance(self.args.pos, NodeQuote):
            quotepos = self.args.pos.args.arg
            ### This is probably still wrong
            if quotepos.isnondecreasing():
                ctx.after('  if (ppos-pwidth/2 > 1.0) {')
                ctx.after(f'    {id}_live[px] = 0\n      livecount -= 1\n      continue')
                ctx.after('  }')
            if quotepos.isnonincreasing():
                ctx.after('  if (ppos+pwidth/2 < 0.0) {')
                ctx.after(f'    {id}_live[px] = 0\n      livecount -= 1\n      continue')
                ctx.after('  }')
        
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
    NodeChanging,
    NodeRandFlat,
    NodeRandNorm,
    NodeClamp,
    NodeLerp,
    NodeSum,
    NodeMean,
    NodeMul,
    NodeMax,
    NodeMin,
    NodeWave,
    NodeRGB,
    NodeBrightness,
    NodeGradient,
    NodeStop,
    NodeDecay,
    NodePulser,
]




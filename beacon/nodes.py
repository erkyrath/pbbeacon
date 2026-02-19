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

    def isclamped(self):
        return (self.args.value >= 0 and self.args.value <= 1)
    
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
    
    def isclamped(self):
        return (self.args.value.red >= 0 and self.args.value.red <= 1
                and self.args.value.green >= 0 and self.args.value.green <= 1
                and self.args.value.blue >= 0 and self.args.value.blue <= 1)
    
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

    def isclamped(self):
        return self.args.arg.isclamped()
    
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
    
    def isclamped(self):
        return self.args.arg.isclamped()
    
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
    
    def isclamped(self):
        return self.args.min.isclamped() and self.args.max.isclamped()
    
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

    def isclamped(self):
        return all([ self.args.weight.isclamped(), self.args.arg1.isclamped(), self.args.arg2.isclamped() ])
    
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
        
    def isclamped(self):
        return all([ arg.isclamped() for arg in self.args.arg ])
        
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
        
    def isclamped(self):
        return all([ arg.isclamped() for arg in self.args.arg ])
        
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

    def isclamped(self):
        return all([ arg.isclamped() for arg in self.args.arg ])
        
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
        
    def isclamped(self):
        return all([ arg.isclamped() for arg in self.args.arg ])
        
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
    
class NodeMod(Node):
    classname = 'mod'
    
    usesimplicit = False
    argformat = [
        ArgFormat('arg1', Node),
        ArgFormat('arg2', Node),
    ]

    def finddim(self):
        return max([ self.args.arg1.dim, self.args.arg2.dim ])
        
    def isclamped(self):
        return self.args.arg2.isclamped()
        
    def generateexpr(self, ctx, component=None):
        argdata = []
        if self.dim is Dim.ONE:
            for arg in [self.args.arg1, self.args.arg2]:
                argdata.append(arg.generatedata(ctx=ctx))
        elif self.dim is Dim.THREE:
            argdata = self.generatelistas3([self.args.arg1, self.args.arg2], ctx, component=component)
        else:
            raise Exception('bad dim')
        assert len(argdata) == 2
        return f'mod({argdata[0]}, {argdata[1]})'
    
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

    def isclamped(self):
        return self.args.min.isclamped() and self.args.max.isclamped()
    
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

class NodeRed(Node):
    classname = 'red'

    usesimplicit = False
    argformat = [
        ArgFormat('value', Node),
    ]

    def finddim(self):
        assert self.args.value.dim is Dim.THREE
        return Dim.ONE

    def generateexpr(self, ctx, component=None):
        argdatar = self.args.value.generatedata(ctx=ctx, component='r')
        return argdatar

class NodeGreen(Node):
    classname = 'green'

    usesimplicit = False
    argformat = [
        ArgFormat('value', Node),
    ]

    def finddim(self):
        assert self.args.value.dim is Dim.THREE
        return Dim.ONE

    def generateexpr(self, ctx, component=None):
        argdatag = self.args.value.generatedata(ctx=ctx, component='g')
        return argdatag

class NodeBlue(Node):
    classname = 'blue'

    usesimplicit = False
    argformat = [
        ArgFormat('value', Node),
    ]

    def finddim(self):
        assert self.args.value.dim is Dim.THREE
        return Dim.ONE

    def generateexpr(self, ctx, component=None):
        argdatab = self.args.value.generatedata(ctx=ctx, component='b')
        return argdatab

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
                stops.append( (stop.args.pos, stop.args.color) )
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

    def isclamped(self):
        for pos, col in self.args.stops:
            if col.red < 0 or col.red > 1:
                return False
            if col.green < 0 or col.green > 1:
                return False
            if col.blue < 0 or col.blue > 1:
                return False
        return True

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
    
class NodeNGradient(Node):
    classname = 'ngradient'

    usesimplicit = False
    argformat = [
        ArgFormat('nstops', Node, multiple=True),
        ArgFormat('arg', Node),
    ]

    def parseargs(self, args, defmap):
        nstops = []
        mainval = None
        for arg in args:
            if arg.tok.val == 'nstop':
                stop = compile(arg, implicit=self.implicit, defmap=defmap)
                nstops.append( (stop.args.pos, stop.args.value) )
                continue
            if mainval is not None:
                raise Exception('%s: duplicate arg' % (self.classname,))
            mainval = compile(arg, implicit=self.implicit, defmap=defmap)
        if not nstops:
            raise Exception('%s: missing nstops' % (self.classname,))
        nstops.sort()
        self.args = self.argclass(nstops=nstops, arg=mainval)
    
    def finddim(self):
        assert self.args.arg.dim is Dim.ONE
        return Dim.ONE

    def isclamped(self):
        for pos, val in self.args.nstops:
            if val < 0 or val > 1:
                return False
        return True

    def printstaticvars(self, outfl, first=False):
        if first:
            outfl.write(eval_gradient_func)
        id = self.id
        posls = []
        cols = []
        for pos, val in self.args.nstops:
            posls.append(pos)
            cols.append(val)
        ls = ', '.join([ str(val) for val in posls ])
        outfl.write(f'var {id}_grad_pos = [{ls}]\n')
        ls = ', '.join([ str(val) for val in cols ])
        outfl.write(f'var {id}_grad_v = [{ls}]\n')
        
    def generateexpr(self, ctx, component=None):
        id = self.id
        count = len(self.args.nstops)
        argdata = self.args.arg.generatedata(ctx=ctx)
        return f'evalGradient({argdata}, {id}_grad_pos, {id}_grad_v, {count})'
    
class NodeStop(Node):
    classname = 'stop'
    
    argformat = [
        ArgFormat('pos', float),
        ArgFormat('color', Color),
    ]

    def finddim(self):
        raise Exception('stop can only be used in a gradient')

class NodeNStop(Node):
    classname = 'nstop'
    
    argformat = [
        ArgFormat('pos', float),
        ArgFormat('value', float),
    ]

    def finddim(self):
        raise Exception('nstop can only be used in an ngradient')


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

class NodeDiff(Node):
    classname = 'diff'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node),
    ]
    
    def finddim(self):
        return self.args.arg.dim

    def generateexpr(self, ctx, component=None):
        assert self.buffered
        assert self.args.arg.buffered
        assert (self.depend & AxisDep.SPACE)
        arg = self.args.arg
        assert self.dim is arg.dim
        if not (arg.depend & AxisDep.SPACE):
            return '0'
        suffix = '_'+component if self.dim is Dim.THREE else ''
        ctx.instead('var diffratio = pixelCount/2')
        ctx.instead('for (var ix=1; ix<pixelCount-1; ix++) {')
        ctx.instead(f'  {self.id}_vector{suffix}[ix] = diffratio*({arg.id}_vector{suffix}[ix+1] - {arg.id}_vector{suffix}[ix-1])')
        ctx.instead('}')
        return None
        
class NodeShift(Node):
    classname = 'shift'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node),
        ArgFormat('by', Implicit.TIME),
    ]
    
    def finddim(self):
        assert self.args.by.dim is Dim.ONE
        return self.args.arg.dim

    def isclamped(self):
        return self.args.arg.isclamped()

    def generateexpr(self, ctx, component=None):
        assert self.buffered
        assert self.args.arg.buffered
        assert (self.depend & AxisDep.SPACE)
        arg = self.args.arg
        assert self.dim is arg.dim
        if not (arg.depend & AxisDep.SPACE):
            argdata = self.args.arg.generatedata(ctx=ctx, component=component)
            return argdata
        bydata = self.args.by.generatedata(ctx=ctx, component=component)
        suffix = '_'+component if self.dim is Dim.THREE else ''
        ctx.instead('for (var ix=0; ix<pixelCount; ix++) {')
        ctx.instead(f'  var shiftpos = ix - {bydata} * pixelCount')
        ctx.instead('  if (shiftpos <= 0) {')
        ctx.instead(f'    {self.id}_vector{suffix}[ix] = {arg.id}_vector{suffix}[0]')
        ctx.instead('  } else if (shiftpos >= pixelCount-1) {')
        ctx.instead(f'    {self.id}_vector{suffix}[ix] = {arg.id}_vector{suffix}[pixelCount-1]')
        ctx.instead('  } else {')
        ctx.instead(f'    {self.id}_vector{suffix}[ix] = mix({arg.id}_vector{suffix}[floor(shiftpos)], {arg.id}_vector{suffix}[floor(shiftpos)+1], frac(shiftpos))')
        ctx.instead('  }')
        ctx.instead('}')
        return None
        
class NodeShiftDecay(Node):
    classname = 'shiftdecay'

    usesimplicit = False
    argformat = [
        ArgFormat('arg', Node),
        ArgFormat('by', Implicit.TIME),
        ArgFormat('halflife', float),
    ]
    
    def finddim(self):
        assert self.args.by.dim is Dim.ONE
        return self.args.arg.dim

    def isclamped(self):
        return self.args.arg.isclamped()

    def generateexpr(self, ctx, component=None):
        assert self.buffered
        halflife = self.args.halflife
        assert self.args.arg.buffered
        assert (self.depend & AxisDep.SPACE)
        assert (self.depend & AxisDep.TIME)
        arg = self.args.arg
        assert self.dim is arg.dim
        bydata = self.args.by.generatedata(ctx=ctx, component=component)
        suffix = '_'+component if self.dim is Dim.THREE else ''
        ctx.instead('for (var ix=0; ix<pixelCount; ix++) {')
        ctx.instead(f'  {self.id}_previous{suffix}[ix] = pow(2, -delta/{1000*halflife}, {self.id}_vector{suffix}[ix])')
        ctx.instead('}')
        ctx.instead('for (var ix=0; ix<pixelCount; ix++) {')
        ctx.instead(f'  var shiftpos = ix - {bydata} * pixelCount')
        if not (arg.depend & AxisDep.SPACE):
            ctx.instead(f'  var argval = {arg.id}_scalar{suffix}')
        else:
            ctx.instead(f'  var argval = {arg.id}_vector{suffix}[ix]')
        ctx.instead('  if (shiftpos <= 0) {')
        ctx.instead(f'    {self.id}_vector{suffix}[ix] = max(argval, {self.id}_previous{suffix}[0])')
        ctx.instead('  } else if (shiftpos >= pixelCount-1) {')
        ctx.instead(f'    {self.id}_vector{suffix}[ix] = max(argval, {self.id}_previous{suffix}[pixelCount-1])')
        ctx.instead('  } else {')
        ctx.instead(f'    {self.id}_vector{suffix}[ix] = max(argval, mix({self.id}_previous{suffix}[floor(shiftpos)], {self.id}_previous{suffix}[floor(shiftpos)+1], frac(shiftpos)))')
        ctx.instead('  }')
        ctx.instead('}')
        return None
        
class NodeNoise(Node):
    classname = 'noise'

    usesimplicit = True
    argformat = [
        ArgFormat('shift', Implicit.TIME, default=0),
        ArgFormat('morph', Implicit.TIME, default=0),
        ArgFormat('grain', float, default=16),
        ArgFormat('octaves', int, default=1),
    ]
    
    def finddim(self):
        return Dim.ONE

    def printstaticvars(self, outfl, first=False):
        if first:
            grain = self.args.grain
            outfl.write(f'setPerlinWrap({grain}, {grain}, {grain})\n')
            
    def generateexpr(self, ctx, component=None):
        grain = self.args.grain
        octaves = self.args.octaves
        assert octaves >= 1
        param = self.generateimplicit(ctx)
        shiftdata = self.args.shift.generatedata(ctx=ctx)
        morphdata = self.args.morph.generatedata(ctx=ctx)
        return f'perlinTurbulence(({param}-{shiftdata})*{grain}, {morphdata}, 0, 2, 0.5, {octaves})'
    
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
            
        qctx = Stanza(self, timebase='age', quoteparent=self, quotekey='width')
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
            ### temp var for (ppos-pwidth/2)?
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
    NodeMod,
    NodeWave,
    NodeRGB,
    NodeBrightness,
    NodeRed,
    NodeGreen,
    NodeBlue,
    NodeGradient,
    NodeNGradient,
    NodeStop,
    NodeNStop,
    NodeDecay,
    NodeDiff,
    NodeShift,
    NodeShiftDecay,
    NodeNoise,
    NodePulser,
]




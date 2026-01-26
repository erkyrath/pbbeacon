import sys

from .defs import Implicit, AxisDep, Dim
from .compile import Node

class Stanza:
    def __init__(self, nod, timebase=None):
        self.nod = nod
        self.depend = nod.depend
        self.storedvals = []
        self.storedvalkeys = {}
        self.bottomline = None
        self.afterlines = []
        self.timebase = timebase
    
    def store_val(self, nod, key, expr):
        varname = f'{nod.id}_val_{key}'
        self.storedvals.append( (varname, expr) )
        self.storedvalkeys[varname] = expr
        return varname

    def find_val(self, nod, key):
        varname = f'{nod.id}_val_{key}'
        if varname in self.storedvalkeys:
            return varname

    def after(self, ln):
        self.afterlines.append(ln)

    def transfer(self, other, indent=0):
        indentstr = indent * '  '
        for varname, expr in self.storedvals:
            other.after('%s%s = %s' % (indentstr, varname, expr,))

    def generatebuffer(self):
        if self.nod.dim is Dim.ONE:
            self.bottomline = self.nod.generateexpr(ctx=self)
        elif self.nod.dim is Dim.THREE:
            self.bottomline = (
                self.nod.generateexpr(ctx=self, component='r'),
                self.nod.generateexpr(ctx=self, component='g'),
                self.nod.generateexpr(ctx=self, component='b'),
            )
        else:
            raise Exception('bad dim')

    def printlines(self, outfl, indent=0):
        indentstr = indent * '  '
        id = self.nod.id
        if self.nod.dim is Dim.ONE:
            if not (self.depend & AxisDep.SPACE):
                for varname, expr in self.storedvals:
                    outfl.write(f'{indentstr}var {varname} = {expr}  // for {id}\n')
                outfl.write(f'{indentstr}{id}_scalar = ({self.bottomline})\n')
            else:
                outfl.write(f'{indentstr}for (var ix=0; ix<pixelCount; ix++) {{\n')
                for varname, expr in self.storedvals:
                    outfl.write(f'{indentstr}  var {varname} = {expr}  // for {id}\n')
                outfl.write(f'{indentstr}  {id}_vector[ix] = ({self.bottomline})\n')
                outfl.write(f'{indentstr}}}\n')
        elif self.nod.dim is Dim.THREE:
            if not (self.depend & AxisDep.SPACE):
                for varname, expr in self.storedvals:
                    outfl.write(f'{indentstr}var {varname} = {expr}  // for {id}\n')
                outfl.write(f'{indentstr}{id}_scalar_r = ({self.bottomline[0]})\n')
                outfl.write(f'{indentstr}{id}_scalar_g = ({self.bottomline[1]})\n')
                outfl.write(f'{indentstr}{id}_scalar_b = ({self.bottomline[2]})\n')
            else:
                outfl.write(f'{indentstr}for (var ix=0; ix<pixelCount; ix++) {{\n')
                for varname, expr in self.storedvals:
                    outfl.write(f'{indentstr}  var {varname} = {expr}  // for {id}\n')
                outfl.write(f'{indentstr}  {id}_vector_r[ix] = ({self.bottomline[0]})\n')
                outfl.write(f'{indentstr}  {id}_vector_g[ix] = ({self.bottomline[1]})\n')
                outfl.write(f'{indentstr}  {id}_vector_b[ix] = ({self.bottomline[2]})\n')
                outfl.write(f'{indentstr}}}\n')
        else:
            raise Exception('bad dim')
        for ln in self.afterlines:
            outfl.write(f'{indentstr}{ln}\n')

class Program:
    def __init__(self, start, defs, srclines=None):
        self.start = start
        self.defs = defs
        self.srclines = srclines

        self.nodes = []
        self.nodeidset = set()

        self.stanzas = []

    def post(self):
        if self.start is None:
            raise Exception('no root')
        
        self.postiter(self.start)
        assert(self.start is self.nodes[-1])
        self.start.buffered = True
        self.start.id = 'root'
        for key, nod in self.defs.items():
            if not nod.isconstant():
                nod.buffered = True

        for nod in self.nodes:
            if nod.buffered:
                stanza = Stanza(nod)
                self.stanzas.append(stanza)
                stanza.generatebuffer()

    def postiter(self, nod):
        if nod.id in self.nodeidset:
            return
        self.nodes.insert(0, nod)
        self.nodeidset.add(nod.id)

        if isinstance(nod, NodePulser):
            nod.depend = AxisDep.SPACETIME
            nod.buffered = True

        subdeps = AxisDep.NONE
        
        for argf in nod.argformat:
            argls = nod.getargls(argf.name, argf.multiple)
            for arg in argls:
                if isinstance(arg, Node):
                    self.postiter(arg)
                    subdeps |= arg.depend

        if nod.usesimplicit:
            if nod.implicit == Implicit.TIME:
                nod.depend = AxisDep.TIME
            if nod.implicit == Implicit.SPACE:
                nod.depend = AxisDep.SPACE
        nod.depend |= subdeps

        for argf in nod.argformat:
            argls = nod.getargls(argf.name, argf.multiple)
            for arg in argls:
                if isinstance(arg, Node):
                    if isinstance(nod, NodePulser):
                        if (arg.depend & AxisDep.SPACE):
                            raise Exception('pulser arg cannot be SPACE')
                        continue
                    if arg.depend != nod.depend and not isinstance(arg, NodeConstant):
                        arg.buffered = True

        nod.dim = nod.finddim()
        
    def dump(self):
        for name in self.defs:
            self.defs[name].dump(name=name)
        self.start.dump()

    def write(self, outfl=None):
        if outfl is None:
            outfl = sys.stdout
            
        outfl.write('var clock = 0   // seconds\n')
        outfl.write('\n')
        outfl.write('// stanza buffers:\n')
        for stanza in self.stanzas:
            id = stanza.nod.id
            if stanza.nod.dim is Dim.ONE:
                if not (stanza.depend & AxisDep.SPACE):
                    outfl.write(f'var {id}_scalar\n')
                else:
                    outfl.write(f'var {id}_vector = array(pixelCount)\n')
            elif stanza.nod.dim is Dim.THREE:
                if not (stanza.depend & AxisDep.SPACE):
                    outfl.write(f'var {id}_scalar_r\n')
                    outfl.write(f'var {id}_scalar_g\n')
                    outfl.write(f'var {id}_scalar_b\n')
                else:
                    outfl.write(f'var {id}_vector_r = array(pixelCount)\n')
                    outfl.write(f'var {id}_vector_g = array(pixelCount)\n')
                    outfl.write(f'var {id}_vector_b = array(pixelCount)\n')
            else:
                raise Exception('bad dim')
            stanza.nod.printstaticvars(outfl)
        outfl.write('\n')

        outfl.write('// startup calculations:\n')
        for stanza in self.stanzas:
            if not (stanza.depend & AxisDep.TIME):
                stanza.printlines(outfl=outfl, indent=0)
        outfl.write('\n')
        
        outfl.write('export function beforeRender(delta) {\n')
        # delta is ms since last call
        ### we'll want an accuracy hack here
        outfl.write('  clock += (delta / 1000)\n')
        
        for stanza in self.stanzas:
            if stanza.depend & AxisDep.TIME:
                stanza.printlines(outfl=outfl, indent=1)
        outfl.write('}\n')
        outfl.write('\n')

        id = self.start.id
        outfl.write('export function render(index) {\n')
        if self.start.dim is Dim.ONE:
            if not (self.start.depend & AxisDep.SPACE):
                outfl.write(f'  var val = {id}_scalar\n')
            else:
                outfl.write(f'  var val = {id}_vector[index]\n')
            outfl.write('  rgb(val*val, val*val, val*val)\n')
        elif self.start.dim is Dim.THREE:
            if not (self.start.depend & AxisDep.SPACE):
                outfl.write(f'  var valr = {id}_scalar_r\n')
                outfl.write(f'  var valg = {id}_scalar_g\n')
                outfl.write(f'  var valb = {id}_scalar_b\n')
            else:
                outfl.write(f'  var valr = {id}_vector_r[index]\n')
                outfl.write(f'  var valg = {id}_vector_g[index]\n')
                outfl.write(f'  var valb = {id}_vector_b[index]\n')
            outfl.write('  rgb(valr*valr, valg*valg, valb*valb)\n')
        else:
            raise Exception('bad dim')
        outfl.write('}\n')
        outfl.write('\n')
        


# Late imports
from .nodes import NodeConstant, NodePulser



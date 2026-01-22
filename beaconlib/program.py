from .defs import Implicit, AxisDep
from .compile import Node

class Stanza:
    def __init__(self, nod, timebase=None):
        self.nod = nod
        self.depend = nod.depend
        self.storedvals = []
        self.bottomline = None
        self.afterlines = []
        self.timebase = timebase
    
    def store_val(self, nod, key, expr):
        varname = '%s_val_%s' % (nod.id, key,)
        self.storedvals.append( (varname, expr) )
        return varname

    def after(self, ln):
        self.afterlines.append(ln)

    def transfer(self, other, indent=0):
        indentstr = indent * '  '
        for varname, expr in self.storedvals:
            other.after('%s%s = %s' % (indentstr, varname, expr,))

    def generatebuffer(self):
        self.bottomline = self.nod.generateexpr(ctx=self)

    def printlines(self, indent=0):
        indentstr = indent * '  '
        if not (self.depend & AxisDep.SPACE):
            for varname, expr in self.storedvals:
                print('%svar %s = %s  // for %s' % (indentstr, varname, expr, self.nod.id,))
            print('%s%s_scalar = (%s)' % (indentstr, self.nod.id, self.bottomline,))
        else:
            print('%sfor (var ix=0; ix<pixelCount; ix++) {' % (indentstr,))
            for varname, expr in self.storedvals:
                print('%s  var %s = %s  // for %s' % (indentstr, varname, expr, self.nod.id,))
            print('%s  %s_pixels[ix] = (%s)' % (indentstr, self.nod.id, self.bottomline,))
            print('%s}' % (indentstr,))
        for ln in self.afterlines:
            print('%s%s' % (indentstr, ln,))

class Program:
    def __init__(self, start, defs):
        self.start = start
        self.defs = defs

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
            if not isinstance(nod, NodeConstant):
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
                    ### (arg.depend | nod.depend) != nod.depend?
                    ### do we really want to buffer lower-dep cases?
                    ### if we do, Pulser needs an exception
                    if arg.depend != nod.depend and not isinstance(arg, NodeConstant):
                        arg.buffered = True
        
    def dump(self):
        for name in self.defs:
            self.defs[name].dump(name=name)
        self.start.dump()

    def write(self):
        print('var clock = 0   // seconds')
        print()
        print('// stanza buffers:')
        for stanza in self.stanzas:
            if not (stanza.depend & AxisDep.SPACE):
                print('var %s_scalar' % (stanza.nod.id,))
            else:
                print('var %s_pixels = array(pixelCount)' % (stanza.nod.id,))
            stanza.nod.printstaticvars()
        print()

        print('// startup calculations:')
        for stanza in self.stanzas:
            if not (stanza.depend & AxisDep.TIME):
                stanza.printlines(indent=0)
        print()
        
        print('export function beforeRender(delta) {')
        # delta is ms since last call
        ### we'll want an accuracy hack here
        print('  clock += (delta / 1000)')
        
        for stanza in self.stanzas:
            if stanza.depend & AxisDep.TIME:
                stanza.printlines(indent=1)
        print('}')
        print()

        print('export function render(index) {')
        if not (self.start.depend & AxisDep.SPACE):
            print('  var val = %s_scalar' % (self.start.id,))
        else:
            print('  var val = %s_pixels[index]' % (self.start.id,))
        print('  rgb(val*val, val*val, 0.1)')
        print('}')
        print()
        


# Late imports
from .nodes import NodeConstant, NodePulser



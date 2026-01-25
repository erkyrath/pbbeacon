from enum import StrEnum, IntEnum

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

class Dim(IntEnum):
    NONE  = 0
    ONE   = 1
    THREE = 3
    
class AxisDep(IntEnum):
    NONE  = 0
    TIME  = 1
    SPACE = 2
    SPACETIME = 3

def axisdepname(dep):
    match dep:
        case AxisDep.NONE:
            return 'NONE'
        case AxisDep.TIME:
            return 'TIME'
        case AxisDep.SPACE:
            return 'SPACE'
        case AxisDep.SPACETIME:
            return 'SPACETIME'
        case _:
            return '???%s' % (dep,)

class Color:
    def __init__(self, val):
        assert val.startswith('$') and len(val) in (4, 7)
        val = val[ 1 : ]
        if len(val) == 3:
            val = val[0]+val[0]+val[1]+val[1]+val[2]+val[2]
        self.red   = int(val[0:2], 16) / 255.0
        self.green = int(val[2:4], 16) / 255.0
        self.blue  = int(val[4:6], 16) / 255.0

    def __repr__(self):
        rval = int(self.red   * 255.0)
        gval = int(self.green * 255.0)
        bval = int(self.blue  * 255.0)
        return '$%02X%02X%02X' % (rval, gval, bval,)

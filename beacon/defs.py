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


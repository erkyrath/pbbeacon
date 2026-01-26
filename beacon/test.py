import unittest
import re
from io import StringIO

from .lex import parselines
from .compile import compileall

pat_indent = re.compile('^[ ]*')

def deindent(text):
    lines = text.rstrip().split('\n')
    if lines[0] == '':
        del lines[0]
    match = pat_indent.match(lines[0])
    if not match:
        return text
    indent = len(match.group(0))
    if not indent:
        return text
    newlines = []
    for val in lines:
        match = pat_indent.match(val)
        if not match or len(match.group(0)) < indent:
            raise Exception('deindented line')
        newlines.append(val[ indent : ])
    return '\n'.join(newlines) + '\n'

def stripdown(text):
    lines = text.rstrip().split('\n')
    newlines = []
    for val in lines:
        if not val:
            continue
        if val.startswith('//'):
            continue
        if val == 'var clock = 0   // seconds':
            continue
        newlines.append(val)
    return '\n'.join(newlines)

class TestCompile(unittest.TestCase):

    def compile(self, src):
        fl = StringIO(src)
        parsetrees, srclines = parselines(fl)
        fl.close()

        program = compileall(parsetrees, srclines=srclines)
        program.post()
        return program

    def compare(self, src, template):
        prog = self.compile(src)
        outfl = StringIO()
        prog.write(outfl)
        res = outfl.getvalue()
        
        res = stripdown(res)
        template = template.strip()
        self.assertEqual(res, template)

    def test_constant(self):
        src = deindent('''
        0.5
        ''')

        self.compare(src, '''
var root_scalar
root_scalar = (0.5)
export function beforeRender(delta) {
  clock += (delta / 1000)
}
export function render(index) {
  var val = root_scalar
  rgb(val*val, val*val, val*val)
}
        ''')

    def test_color(self):
        src = deindent('''
        $03F
        ''')

        self.compare(src, '''
var root_scalar_r
var root_scalar_g
var root_scalar_b
root_scalar_r = (0.0)
root_scalar_g = (0.2)
root_scalar_b = (1.0)
export function beforeRender(delta) {
  clock += (delta / 1000)
}
export function render(index) {
  var valr = root_scalar_r
  var valg = root_scalar_g
  var valb = root_scalar_b
  rgb(valr*valr, valg*valg, valb*valb)
}
        ''')

    def test_spacewave(self):
        src = deindent('''
        wave: sine
        ''')

        self.compare(src, '''
var root_vector = array(pixelCount)
for (var ix=0; ix<pixelCount; ix++) {
  var root_val_min = 0  // for root
  var root_val_hdiff = ((1-root_val_min)*0.5)  // for root
  root_vector[ix] = ((root_val_min+root_val_hdiff*(1-cos(PI2*(((ix/pixelCount)-0.5)/1+0.5)))))
}
export function beforeRender(delta) {
  clock += (delta / 1000)
}
export function render(index) {
  var val = root_vector[index]
  rgb(val*val, val*val, val*val)
}
        ''')

    def test_timewave(self):
        src = deindent('''
        time: wave: sine
        ''')

        self.compare(src, '''
var root_scalar
export function beforeRender(delta) {
  clock += (delta / 1000)
  var wave_1_val_min = 0  // for root
  var wave_1_val_hdiff = ((1-wave_1_val_min)*0.5)  // for root
  root_scalar = ((wave_1_val_min+wave_1_val_hdiff*(1-cos(PI2*clock/1))))
}
export function render(index) {
  var val = root_scalar
  rgb(val*val, val*val, val*val)
}
        ''')

    def test_spacetimewaves(self):
        src = deindent('''
        sum:
          space: wave: triangle
          time: wave: sqrdecay
        ''')

        self.compare(src, '''
var time_6_scalar
var space_1_vector = array(pixelCount)
var root_vector = array(pixelCount)
for (var ix=0; ix<pixelCount; ix++) {
  var wave_2_val_min = 0  // for space_1
  var wave_2_val_diff = (1-wave_2_val_min)  // for space_1
  space_1_vector[ix] = ((wave_2_val_min+wave_2_val_diff*(triangle((((ix/pixelCount)-0.5)/1+0.5)))))
}
export function beforeRender(delta) {
  clock += (delta / 1000)
  var wave_7_val_min = 0  // for time_6
  var wave_7_val_diff = (1-wave_7_val_min)  // for time_6
  time_6_scalar = ((wave_7_val_min+wave_7_val_diff*(pow(1-mod(clock/1, 1), 2))))
  for (var ix=0; ix<pixelCount; ix++) {
    root_vector[ix] = ((space_1_vector[ix] + time_6_scalar))
  }
}
export function render(index) {
  var val = root_vector[index]
  rgb(val*val, val*val, val*val)
}
        ''')

    def test_sumcolor(self):
        src = deindent('''
        sum:
          $F30
          rgb:
            r=0.1
            g=0.2
            b=time: wave: sine
          ''')

        self.compare(src, '''
var root_scalar_r
var root_scalar_g
var root_scalar_b
export function beforeRender(delta) {
  clock += (delta / 1000)
  var wave_6_val_min = 0  // for root
  var wave_6_val_hdiff = ((1-wave_6_val_min)*0.5)  // for root
  root_scalar_r = ((1.0 + 0.1))
  root_scalar_g = ((0.2 + 0.2))
  root_scalar_b = ((0.0 + (wave_6_val_min+wave_6_val_hdiff*(1-cos(PI2*clock/1)))))
}
export function render(index) {
  var valr = root_scalar_r
  var valg = root_scalar_g
  var valb = root_scalar_b
  rgb(valr*valr, valg*valg, valb*valb)
}
        ''')

    def test_sumcolor2(self):
        src = deindent('''
        sum:
          rgb:
            r=time: wave: triangle
            g=0.5
            b=0.5
          rgb:
            r=0.1
            g=0.2
            b=time: wave: sine
          ''')

        self.compare(src, '''
var root_scalar_r
var root_scalar_g
var root_scalar_b
export function beforeRender(delta) {
  clock += (delta / 1000)
  var wave_3_val_min = 0  // for root
  var wave_3_val_diff = (1-wave_3_val_min)  // for root
  var wave_13_val_min = 0  // for root
  var wave_13_val_hdiff = ((1-wave_13_val_min)*0.5)  // for root
  root_scalar_r = (((wave_3_val_min+wave_3_val_diff*(triangle(clock/1))) + 0.1))
  root_scalar_g = ((0.5 + 0.2))
  root_scalar_b = ((0.5 + (wave_13_val_min+wave_13_val_hdiff*(1-cos(PI2*clock/1)))))
}
export function render(index) {
  var valr = root_scalar_r
  var valg = root_scalar_g
  var valb = root_scalar_b
  rgb(valr*valr, valg*valg, valb*valb)
}
        ''')

    def test_sumscalarcolor(self):
        src = deindent('''
        sum:
          0.5
          rgb:
            r=0.1
            g=0.2
            b=time: wave: sine
          ''')

        self.compare(src, '''
var root_scalar_r
var root_scalar_g
var root_scalar_b
export function beforeRender(delta) {
  clock += (delta / 1000)
  var wave_6_val_min = 0  // for root
  var wave_6_val_hdiff = ((1-wave_6_val_min)*0.5)  // for root
  root_scalar_r = ((0.5 + 0.1))
  root_scalar_g = ((0.5 + 0.2))
  root_scalar_b = ((0.5 + (wave_6_val_min+wave_6_val_hdiff*(1-cos(PI2*clock/1)))))
}
export function render(index) {
  var valr = root_scalar_r
  var valg = root_scalar_g
  var valb = root_scalar_b
  rgb(valr*valr, valg*valg, valb*valb)
}
        ''')

    def test_sumscalarcolor2(self):
        src = deindent('''
        sum:
          space: wave: sine
          rgb:
            r=0.1
            g=0.2
            b=space: wave: sine
          ''')

        self.compare(src, '''
var root_vector_r = array(pixelCount)
var root_vector_g = array(pixelCount)
var root_vector_b = array(pixelCount)
for (var ix=0; ix<pixelCount; ix++) {
  var wave_2_val_min = 0  // for root
  var wave_2_val_hdiff = ((1-wave_2_val_min)*0.5)  // for root
  var root_val_common = (wave_2_val_min+wave_2_val_hdiff*(1-cos(PI2*(((ix/pixelCount)-0.5)/1+0.5))))  // for root
  var wave_10_val_min = 0  // for root
  var wave_10_val_hdiff = ((1-wave_10_val_min)*0.5)  // for root
  root_vector_r[ix] = ((root_val_common + 0.1))
  root_vector_g[ix] = ((root_val_common + 0.2))
  root_vector_b[ix] = ((root_val_common + (wave_10_val_min+wave_10_val_hdiff*(1-cos(PI2*(((ix/pixelCount)-0.5)/1+0.5))))))
}
export function beforeRender(delta) {
  clock += (delta / 1000)
}
export function render(index) {
  var valr = root_vector_r[index]
  var valg = root_vector_g[index]
  var valb = root_vector_b[index]
  rgb(valr*valr, valg*valg, valb*valb)
}
        ''')

    def test_pulser_decayinplace(self):
        src = deindent('''
        pulser:
          maxcount=4
          spaceshape=triangle
          width=0.3
          timeshape=sawdecay
          duration=0.2
        ''')

        self.compare(src, '''
var root_vector = array(pixelCount)
var root_live = array(4)
var root_birth = array(4)
var root_livecount = 0
var root_nextstart = 0
export function beforeRender(delta) {
  clock += (delta / 1000)
  for (var ix=0; ix<pixelCount; ix++) {
    root_vector[ix] = (0)
  }
  if (clock >= root_nextstart && root_livecount < 4) {
    for (var px=0; px<4; px++) {
      if (!root_live[px]) { break }
    }
    if (px < 4) {
      root_live[px] = 1
      livecount += 1
      root_nextstart = clock + 1
      root_birth[px] = clock
    }
  }
  for (var px=0; px<4; px++) {
    if (!root_live[px]) { break }
    age = clock - root_birth[px]
    relage = age / 0.2
    if (relage > 1.0) {
      root_live[px] = 0
      livecount -= 1
      continue
    }
    timeval = (1-relage)
    ppos = 0.5
    pwidth = 0.3
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = triangle(relpos)
      root_vector[ix] += (timeval * spaceval)
    }
  }
}
export function render(index) {
  var val = root_vector[index]
  rgb(val*val, val*val, val*val)
}
        ''')

    def test_pulser_randpos(self):
        src = deindent('''
        pulser:
          maxcount=4
          spaceshape=triangle
          width=0.3
          timeshape=sawdecay
          duration=0.2
          pos=randflat: 0.2, 0.8
        ''')

        self.compare(src, '''
var root_vector = array(pixelCount)
var root_live = array(4)
var root_birth = array(4)
var root_livecount = 0
var root_nextstart = 0
var root_arg_pos = array(4)
export function beforeRender(delta) {
  clock += (delta / 1000)
  for (var ix=0; ix<pixelCount; ix++) {
    root_vector[ix] = (0)
  }
  if (clock >= root_nextstart && root_livecount < 4) {
    for (var px=0; px<4; px++) {
      if (!root_live[px]) { break }
    }
    if (px < 4) {
      root_live[px] = 1
      livecount += 1
      randflat_3_val_min = 0.2
      randflat_3_val_diff = (0.8-randflat_3_val_min)
      root_arg_pos[px] = (random(randflat_3_val_diff)+randflat_3_val_min)
      root_nextstart = clock + 1
      root_birth[px] = clock
    }
  }
  for (var px=0; px<4; px++) {
    if (!root_live[px]) { break }
    age = clock - root_birth[px]
    relage = age / 0.2
    if (relage > 1.0) {
      root_live[px] = 0
      livecount -= 1
      continue
    }
    timeval = (1-relage)
    ppos = root_arg_pos[px]
    pwidth = 0.3
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = triangle(relpos)
      root_vector[ix] += (timeval * spaceval)
    }
  }
}
export function render(index) {
  var val = root_vector[index]
  rgb(val*val, val*val, val*val)
}
        ''')

    def test_pulser_quoterandpos(self):
        src = deindent('''
        pulser:
          maxcount=4
          spaceshape=triangle
          width=0.3
          timeshape=sawdecay
          duration=0.2
          pos=quote:randflat: 0.2, 0.8
        ''')

        self.compare(src, '''
var root_vector = array(pixelCount)
var root_live = array(4)
var root_birth = array(4)
var root_livecount = 0
var root_nextstart = 0
export function beforeRender(delta) {
  clock += (delta / 1000)
  for (var ix=0; ix<pixelCount; ix++) {
    root_vector[ix] = (0)
  }
  if (clock >= root_nextstart && root_livecount < 4) {
    for (var px=0; px<4; px++) {
      if (!root_live[px]) { break }
    }
    if (px < 4) {
      root_live[px] = 1
      livecount += 1
      root_nextstart = clock + 1
      root_birth[px] = clock
    }
  }
  for (var px=0; px<4; px++) {
    if (!root_live[px]) { break }
    age = clock - root_birth[px]
    relage = age / 0.2
    if (relage > 1.0) {
      root_live[px] = 0
      livecount -= 1
      continue
    }
    timeval = (1-relage)
    randflat_4_val_min = 0.2
    randflat_4_val_diff = (0.8-randflat_4_val_min)
    ppos = (random(randflat_4_val_diff)+randflat_4_val_min)
    pwidth = 0.3
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = triangle(relpos)
      root_vector[ix] += (timeval * spaceval)
    }
  }
}
export function render(index) {
  var val = root_vector[index]
  rgb(val*val, val*val, val*val)
}
        ''')



if __name__ == '__main__':
    unittest.main()

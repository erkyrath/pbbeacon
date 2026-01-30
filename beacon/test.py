import unittest
import os.path
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
        newlines.append(val)
    return '\n'.join(newlines)

class TestCompile(unittest.TestCase):

    def checkfile(self, filename):
        path = os.path.join(os.path.dirname(__file__), 'testfiles', filename)
        
        srcls = []
        resls = []
        
        fl = open(path)
        for ln in fl.readlines():
            ln = ln.rstrip()
            if ln.startswith('///'):
                srcls.append(ln[ 3 : ])
            elif ln.startswith('//') or not ln:
                pass
            else:
                resls.append(ln)
        fl.close()

        res = '\n'.join(resls)
        src = deindent('\n'.join(srcls))

        program = self.compile(src)

        outfl = StringIO()
        program.write(outfl)
        output = stripdown(outfl.getvalue())

        self.assertEqual(output, res)

    def compile(self, src):
        fl = StringIO(src)
        parsetrees, srclines = parselines(fl)
        fl.close()

        program = compileall(parsetrees, srclines=srclines)
        program.post()
        return program

    def test_constant(self):
        self.checkfile('constant.pbb')

    def test_color(self):
        self.checkfile('color.pbb')

    def test_spacewave(self):
        self.checkfile('spacewave.pbb')

    def test_timewave(self):
        self.checkfile('timewave.pbb')

    def test_spacetimewaves(self):
        self.checkfile('spacetimewaves.pbb')

    def test_sumcolor(self):
        self.checkfile('sumcolor.pbb')

    def test_sumcolor2(self):
        self.checkfile('sumcolor2.pbb')

    def test_sumscalarcolor(self):
        self.checkfile('sumscalarcolor.pbb')
        
    def test_sumscalarcolor2(self):
        self.checkfile('sumscalarcolor2.pbb')
        
    def test_pulser_randpos(self):
        self.checkfile('pulser_randpos.pbb')
        
    def test_pulser_quoterandpos(self):
        self.checkfile('pulser_quoterandpos.pbb')
        
    def test_pulser_quotelinear(self):
        self.checkfile('pulser_quotelinear.pbb')
        
    def test_gradient(self):
        self.checkfile('gradient.pbb')
        

if __name__ == '__main__':
    unittest.main()

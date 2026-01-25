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

class TestCompile(unittest.TestCase):

    def compile(self, prog):
        fl = StringIO(prog)
        parsetrees, srclines = parselines(fl)
        fl.close()

        return compileall(parsetrees, srclines=srclines)

    def compare(self, res, template):
        pass

    def test_simple(self):
        src = deindent('''
        0.5
        ''')
        
        prog = self.compile(src)
        outfl = StringIO()
        prog.write(outfl)
        res = outfl.getvalue()

        self.compare(res, '''
export function beforeRender(delta) {
  clock += (delta / 1000)
}

export function render(index) {
  var val = constant_0_scalar
  rgb(val*val, val*val, 0.1)
}
        ''')

if __name__ == '__main__':
    unittest.main()

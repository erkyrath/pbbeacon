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
  rgb(val*val, val*val, 0.1)
}
        ''')



if __name__ == '__main__':
    unittest.main()

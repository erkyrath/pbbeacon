import unittest
import re

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
        

    def test_simple(self):
        prog = deindent('''
        0.5
        ''')
        
        res = self.compile(prog)



if __name__ == '__main__':
    unittest.main()

import re
import itertools

re_tokenize = re.compile(r"""
    (?P<newline>\r\n | \n | \r)
    | (?P<quoted>'.*?(?!>\\)'|".*?(?<!\\)")
    | (?P<paren>\$\(\( | \)\)
      | \$\{
      | \$\( | \)
      | [\(\)\[\]{}])
    | (?P<var>\$[_a-zA-Z][a-zA-Z0-9_]*)
    | (?P<op>[=|>&])
    | (?P<ws>\s+ | \\\n | \\\r\n | \\\r)
    | (?P<word>[^\s$=|>&()]+)
    """, re.X)

class Token(object):
    __slots__ = ('typ', 'value', 'lineno', 'offset')

    def __init__(self, typ, value, lineno, offset):
        self.typ = typ
        self.value = value
        self.lineno = lineno
        self.offset = offset

    def __repr__(self):
        return '<{0} at {1}:{2} {3!r}>'.format(self.typ,
            self.lineno, self.offset, self.value)

class Node(object):
    __slots__ = ()

class CmdLine(Node):
    __slots__ = ('args',)
    def __init__(self, args):
        self.args = args

    @classmethod
    def parse(cls, *tokens):
        cur = []
        args = []
        for i in tokens:
            if i.typ in {'ws', 'newline'}:
                if cur:
                    args.append(cur)
                    cur = []
            else:
                cur.append(i)
        if cur:
            args.append(cur)
        return cls(args)

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__, self.args)

class VarValue(Node):
    __slots__ = ('name', 'value')

    def __init__(self, name, value):
        self.name = name
        self.value = value

    @classmethod
    def parse(cls, name, *value):
        return cls(name, value)

    def __repr__(self):
        return '<{0} {1}={2}>'.format(self.__class__.__name__,
            self.name, self.value)

    def interpolate(self, vars):
        if not self.value:
            return ""
        result = ""
        for i in self.value:
            if i.typ == 'var':
                result += vars[i.value[1:]]
            elif i.typ == 'quoted':
                result += i.value[1:-1]
            else:
                result += i.value
        return result

class VarArray(VarValue):

    def interpolate(self, vars):
        if not self.value:
            return ""
        result = []
        cur = ""
        for i in self.value:
            if i.typ == 'var':
                cur += vars[i.value[1:]]
            elif i.typ in {'ws', 'newline'}:
                if cur:
                    result.append(cur)
                    cur = ""
            elif i.typ == 'quoted':
                cur += i.value[1:-1]
            else:
                cur += i.value
        if cur:
            result.append(cur)
        return result

class Function(Node):
    __slots__ = ('name', 'body')

    def __init__(self, name, body):
        self.name = name
        self.body = body

    def __repr__(self):
        return '<{0}[{1}]>'.format(self.__class__.__name__, len(self.body))

    @classmethod
    def parse(cls, name, body):
        return cls(name, list(body))

def tokenize(file):
    last_token = 0
    last_line = 0
    data = file.read().decode('ascii')
    for m in re_tokenize.finditer(data):
        val = m.group(0)
        typ = next(iter(k for k, v in m.groupdict().items() if v is not None))
        last_line += data[last_token:m.start(0)].count('\n')
        last_token = m.start(0)
        try:
            pos = last_token - data.rindex('\n', 0, last_token)
        except ValueError:
            pos = last_token  # first line
        yield Token(typ, val, last_line, pos)

def parse(file):
    tok = tokenize(file)
    return list(_parse(tok))

def _parse(tok):
    while True:
        name = next(tok)
        if name.typ in ('newline', 'ws'):
            continue
        if name.value == '{':
            break
        oper = next(tok)
        if name.typ == 'word':
            if oper.typ == 'op':
                if oper.value == '=':
                    firstarg = next(tok)
                    if firstarg.value == '(':
                        yield VarArray.parse(name,
                            *itertools.takewhile(
                                lambda x: x.value != ')', tok))
                        ntok = next(tok)
                        assert ntok.typ == 'newline', ntok
                    else:
                        yield VarValue.parse(name, firstarg,
                            *itertools.takewhile(
                                lambda x: x.typ != 'newline', tok))
                    continue
            elif oper.value == '(':
                assert next(tok).value == ')'
                ntok = next(tok)
                if ntok.typ == 'ws':
                    ntok = next(tok)
                assert ntok.value == '{'
                yield Function.parse(name, _parse(tok))
                continue

        yield CmdLine.parse(name, oper,
            *itertools.takewhile(lambda x: x.typ != 'newline', tok))


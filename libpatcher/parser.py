# This is a parser for assembler listings (?)

import asm
from itertools import chain

class SyntaxError(Exception):
    def __init__(self, msg, f, line):
        self.msg = msg
        self.file = f
        self.line = line
    def __str__(self):
        return "%s@%s: %s" % (self.file.name, self.line, self.msg)

def uncomment(line):
    """ Removes comment, if any, from line. Also strips line """
    linewoc = '' # line without comment
    in_str = ''
    for c in line:
        if in_str:
            if c == in_str:
                in_str = ''
        else:
            if c in '#;': # our comment characters
                break
            elif c in '"\'':
                in_str = c
        linewoc += c
    return linewoc.strip() # remove leading and trailing spaces

def parseAsm(f, prev=()):
    """
    Usage: pass it file after you encounter { (block beginning)
    and optionally pass everything after that character as prev arg.
    After it encounter }, it will return list of instructions:
        [
            ("opcode", [arg1,arg2...]),
            ...
        ]
    """
    if prev:
        prev = (prev,) # to be iterable

    instructions = []
    for line in chain(prev, f):
        line = uncomment(line)

        # ignore empty lines
        if not line:
            continue

        # end of block?
        if line.startswith('}'):
            # FIXME: what to do with remainder?
            remainder = line[1:]
            if remainder:
                print "Warning: spare characters after '}', will ignore"
            break

        try:
            opcode, arg = line.split(None,1)
        except ValueError: # only one token
            opcode = line
            arg = ''

        # now parse args
        args = []
        s = '' # string repr of current arg
        t = None # type of current arg: None (no current), n(numeric), ',"(quoted str), l(reg or label)
        br = False # whether we are in [] block
        for c in arg+'\n': # \n will be processed as last character
            domore = False # if current character needs to be processed further
            if t == None: # state: no current arg
                domore = True
            elif t in "'\"": # quoted string
                if c == t: # end of string
                    args.append(asm.Str(s))
                    s = ''
                    t = None
                elif c == '\\': # backslash in string
                    t += '\\'
                else:
                    s += c
            elif t in ['"\\', "'\\"]: # state: backslash in quoted string
                s += c
                t=t[0]
            elif t == 'n': # number, maybe hex
                if c.isdigit() or c in 'xXbB':
                    s.append(c)
                else:
                    domore = True # need to process current character further
                    args.append(asm.Num(int(s, 0)))
                    s = ''
                    t = None
            elif t == 'l': # label or reg
                if c.isalnum() or c == '_':
                    s += c
                else:
                    domore = True
                    if asm.Reg.is_reg(s):
                        a = asm.Reg(s)
                    else:
                        a = asm.Label(s)
                    args.append(a)
                    s = ''
                    t = None
            else:
                raise ValueError("Internal error: illegal type state %s" % t)

            if domore: # current character was not processed yet
                if c.isdigit():
                    s += c
                    t = 'n'
                elif c.isalpha() or c == '_':
                    s += c
                    t = 'l' # label
                elif c in "'\"": # quoted str
                    t = c
                elif c.isspace(): # including last \n
                    continue # skip
                elif c == ',':
                    continue # skip - is it a good approach? allows both "MOV R0,R1" and "MOV R1 R1"
                elif c == '[':
                    if br:
                        raise SyntaxError("Nested [] are not supported", f, line)
                    br = True
                    gargs = args
                    args = asm.List()
                elif c == ']':
                    if not br:
                        raise SyntaxError("Unmatched ]", f, line)
                    gargs.append(args)
                    args = gargs
                    br = False
                else:
                    raise SyntaxError("Bad character: %c" % c, f, line)
        # now let's check that everything went clean
        if t:
            raise SyntaxError("Unterminated string? %c" % t, f, line)
        if br:
            raise SyntaxError("Unmatched '['", f, line)

        # now we have a good instruction
        instructions.append((opcode, args))
    return instructions

def parsePatch(f):
    """
    Parses patch file
    """
    # list of masks and corresponding instruction listings
    blocks = []

    # current mask
    mask = []
    # current mask item (bytestring)
    bstr = ''
    # current mask item (integer, number of bytes to skip)
    bskip = 0
    for line in f:
        line = uncomment(line)
        if not line:
            continue

        # read mask: it consists of 00 f7 items, ? ?4 items, and "strings"
        tokens = line.split('"')
        if len(tokens) % 2 == 0:
            raise SyntaxError("Unterminated string", f, line)
        is_str = False
        for tnum, token in enumerate(tokens):
            if is_str:
                if bskip:
                    mask.append(bskip)
                    bskip = 0
                bstr += token
            else:
                ts = token.split()
                for t in ts:
                    if len(t) == 2 and t.isalnum():
                        if bskip:
                            mask.append(bskip)
                            bskip = 0
                        try:
                            c = chr(int(t, 16))
                        except ValueError:
                            raise SyntaxError("Bad token: %s" % t, f, line)
                        bstr += c
                    elif t[0] == '?':
                        if len(t) == 1:
                            count = 1
                        else:
                            try:
                                count = int(t[1:])
                            except ValueError:
                                raise SyntaxError("Bad token: %s" % t, f, line)
                        if bstr:
                            mask.append(bstr)
                            bstr = ''
                        bskip += count
                    elif t == '{':
                        if bstr:
                            mask.append(bstr)
                            bstr = ''
                            if bskip:
                                print mask
                                print bstr
                                print bskip
                                raise SyntaxError("Internal error: both bstr and bskip used", f, line)
                        if bskip:
                            mask.append(bskip)
                            bskip = 0
                        remainder = '"'.join(tokens[tnum+1:])
                        # debug:
                        print remainder
                        content = parseAsm(f, remainder)
                        # TODO: save mask and content
                        mask = []
                    else:
                        raise SyntaxError("Bad token: %s" % t, f, line)
            is_str = not is_str
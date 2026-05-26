import math
import random as _random

_BUILTINS = {
    # I/O
    'printf', 'putchar', 'getchar', 'puts', 'scanf',
    # 字串
    'strlen', 'strcpy', 'strcat', 'strcmp', 'atoi', 'itoa',
    # 數學
    'abs', 'max', 'min', 'pow', 'sqrt', 'mod', 'rand', 'srand',
    # 工具
    'memset', 'sizeof_int', 'sizeof_char', 'exit',
}

def is_builtin(name: str) -> bool:
    return name in _BUILTINS

def _read_str(memory, addr: int) -> str:
    chars = []
    while True:
        c = memory.read(addr)
        if c == 0:
            break
        chars.append(chr(c & 0xFF))
        addr += 1
    return ''.join(chars)

def _write_str(memory, addr: int, s: str):
    for i, c in enumerate(s + '\0'):
        memory.write(addr + i, ord(c))

def _format(fmt: str, args: list, memory) -> str:
    result = []
    i  = 0
    ai = 0
    while i < len(fmt):
        if fmt[i] == '%' and i + 1 < len(fmt):
            spec = fmt[i + 1]
            if spec == 'd':
                result.append(str(args[ai] if ai < len(args) else 0))
                ai += 1; i += 2
            elif spec == 'c':
                result.append(chr(args[ai] & 0xFF) if ai < len(args) else '')
                ai += 1; i += 2
            elif spec == 's':
                result.append(_read_str(memory, args[ai]) if ai < len(args) else '')
                ai += 1; i += 2
            elif spec == 'x':
                result.append(hex(args[ai])[2:] if ai < len(args) else '0')
                ai += 1; i += 2
            elif spec == '%':
                result.append('%'); i += 2
            else:
                result.append(fmt[i]); i += 1
        else:
            result.append(fmt[i]); i += 1
    return ''.join(result)

def call_builtin(name: str, args: list, memory, output_fn=print):
    """呼叫內建函式，回傳整數結果。"""

    if name == 'printf':
        fmt = _read_str(memory, args[0])
        output_fn(_format(fmt, args[1:], memory), end='')
        return 0

    if name == 'putchar':
        output_fn(chr(args[0] & 0xFF), end='')
        return args[0]

    if name == 'puts':
        output_fn(_read_str(memory, args[0]))
        return 0

    if name == 'getchar':
        try:
            c = input()[:1]
            return ord(c) if c else -1
        except EOFError:
            return -1

    if name == 'scanf':
        fmt = _read_str(memory, args[0])
        specs = [c for c in fmt if c in 'dc']
        for idx, spec in enumerate(specs):
            if idx + 1 >= len(args):
                break
            dest_addr = args[idx + 1]
            try:
                raw = input()
                if spec == 'd':
                    memory.write(dest_addr, int(raw.strip()))
                elif spec == 'c':
                    memory.write(dest_addr, ord(raw[0]) if raw else 0)
            except (ValueError, EOFError):
                pass
        return len(specs)

    if name == 'strlen':
        return len(_read_str(memory, args[0]))

    if name == 'strcpy':
        _write_str(memory, args[0], _read_str(memory, args[1]))
        return args[0]

    if name == 'strcat':
        dest = _read_str(memory, args[0])
        src  = _read_str(memory, args[1])
        _write_str(memory, args[0], dest + src)
        return args[0]

    if name == 'strcmp':
        a = _read_str(memory, args[0])
        b = _read_str(memory, args[1])
        return 0 if a == b else (-1 if a < b else 1)

    if name == 'atoi':
        s = _read_str(memory, args[0]).strip()
        try:
            return int(s)
        except ValueError:
            return 0

    if name == 'itoa':
        _write_str(memory, args[1], str(args[0]))
        return 0

    if name == 'abs':
        return abs(args[0])

    if name == 'max':
        return max(args[0], args[1])

    if name == 'min':
        return min(args[0], args[1])

    if name == 'pow':
        if args[1] < 0:
            return 0   
        return int(args[0] ** args[1])

    if name == 'sqrt':
        if args[0] < 0:
            raise Exception("Runtime error: sqrt() argument must be non-negative")
        return int(math.isqrt(args[0]))

    if name == 'mod':
        if args[1] == 0:
            raise Exception("Runtime error: mod() division by zero")
        return args[0] % args[1]

    if name == 'rand':
        return _random.randint(0, 32767)

    if name == 'srand':
        _random.seed(args[0])
        return 0

    if name == 'sizeof_int':
        return 4

    if name == 'sizeof_char':
        return 1

    if name == 'memset':
        ptr, val, size = args[0], args[1], args[2]
        for i in range(size):
            memory.write(ptr + i, val & 0xFF)
        return 0

    if name == 'exit':
        raise SystemExit(args[0])

    return 0

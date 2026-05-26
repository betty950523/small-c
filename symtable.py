class ReturnException(Exception):
    def __init__(self, value): self.value = value

class BreakException(Exception): pass
class ContinueException(Exception): pass

class ParseError(Exception):
    def __init__(self, msg, line):
        super().__init__(f'[Parser] Line {line}: {msg}')
        self.line = line

class RuntimeError_(Exception):
    def __init__(self, msg, line=0):
        super().__init__(f'[Runtime] {msg}' if not line else f'[Runtime] Line {line}: {msg}')


class Memory:
    def __init__(self):
        self._mem: dict[int, int] = {}
        self._next_addr = 1000

    def alloc(self, size=1) -> int:
        addr = self._next_addr
        for i in range(size):
            self._mem[addr + i] = 0
        self._next_addr += size
        return addr

    def read(self, addr: int) -> int:
        if addr not in self._mem:
            raise RuntimeError_(f"Invalid memory access at address {addr}")
        return self._mem[addr]

    def write(self, addr: int, value: int):
        if addr not in self._mem:
            raise RuntimeError_(f"Invalid memory access at address {addr}")
        self._mem[addr] = self._to_int32(value)

    @staticmethod
    def _to_int32(v: int) -> int:
        v = int(v) & 0xFFFFFFFF
        return v if v < 0x80000000 else v - 0x100000000

    def reset(self):
        self._mem.clear()
        self._next_addr = 1000

class Symbol:
    def __init__(self, name, type_, addr, size=1, is_array=False, is_pointer=False):
        self.name       = name
        self.type_      = type_
        self.addr       = addr
        self.size       = size
        self.is_array   = is_array
        self.is_pointer = is_pointer

class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self._syms: dict[str, Symbol] = {}

    def declare(self, name, type_, addr, size=1, is_array=False, is_pointer=False):
        self._syms[name] = Symbol(name, type_, addr, size, is_array, is_pointer)

    def lookup(self, name) -> Symbol:
        if name in self._syms:
            return self._syms[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def all_symbols(self):
        return list(self._syms.values())

    def reset(self):
        self._syms.clear()

class FuncDef:
    def __init__(self, name, ret_type, params, body_tokens, start_line):
        self.name        = name
        self.ret_type    = ret_type
        self.params      = params
        self.body_tokens = body_tokens
        self.start_line  = start_line

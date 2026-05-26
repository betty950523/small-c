from parser import make_interpreter
from symtable import Memory, SymbolTable


class Interpreter:
    def __init__(self, output_fn=None, trace=False):
        self.output_fn = output_fn or print
        self.trace     = trace
        self._memory   = Memory()
        self._st       = SymbolTable()
        self._funcs    = {}
        self._defines  = {}

    def run_program(self, code: str):
        
        try:
            interp = make_interpreter(
                code,
                self._memory,
                self._st,
                self._funcs,
                self._defines,
                trace=self.trace,
                output_fn=self.output_fn,
            )
            interp.parse_program()
        except SystemExit:
            pass
        except Exception as e:
            self.output_fn(str(e))

    def check_program(self, code: str) -> list[str]:
        errors = []
        try:
            interp = make_interpreter(
                code,
                Memory(),  
                SymbolTable(),
                dict(self._funcs),
                dict(self._defines),
                output_fn=lambda *a, **kw: None,
            )
            interp.executing = False
            interp.parse_program()
        except Exception as e:
            errors.append(str(e))
        return errors

    def get_vars(self) -> list:
        
        result = []
        for sym in self._st.all_symbols():
            if sym.is_array:
                vals = [self._memory.read(sym.addr + i)
                        for i in range(min(sym.size, 10))]
                result.append((sym.name, sym.type_, vals, sym.size))
            else:
                result.append((sym.name, sym.type_,
                                self._memory.read(sym.addr), 1))
        return result

    def get_funcs(self) -> list:
        
        result = []
        for name, f in self._funcs.items():
            params_str = ', '.join(f'{t} {n}' for n, t in f.params)
            result.append((name, f.ret_type, params_str, f.start_line))
        return result

    def set_trace(self, on: bool):
        self.trace = on

    def reset(self):
        
        self._memory  = Memory()
        self._st      = SymbolTable()
        self._funcs   = {}
        self._defines = {}

from interpreter import Interpreter

program_buffer = []
_interp = Interpreter(output_fn=print)

def append_line(line):
    program_buffer.append(line)


def list_lines(start=None, end=None):
    if len(program_buffer) == 0:
        print("Buffer is empty.")
        return
    s = (start - 1) if start else 0
    e = end if end else len(program_buffer)
    for i, line in enumerate(program_buffer[s:e], start=s + 1):
        print(f"  {i:3}: {line}")


def delete_line(n, n2=None):
    if n2 is None:
        if n < 1 or n > len(program_buffer):
            print("Invalid line number.")
            return
        program_buffer.pop(n - 1)
    else:
        if n < 1 or n2 > len(program_buffer) or n > n2:
            print("Invalid line range.")
            return
        del program_buffer[n - 1:n2]


def clear_buffer():
    program_buffer.clear()
    _interp.reset()
    print("All cleared.")


def edit_line(n, new_text):
    if n < 1 or n > len(program_buffer):
        print("Invalid line number.")
        return
    program_buffer[n - 1] = new_text


def insert_line(n, text):
    if n < 1 or n > len(program_buffer) + 1:
        print("Invalid line number.")
        return
    program_buffer.insert(n - 1, text)


def save_file(filename):
    try:
        with open(filename, 'w') as f:
            for line in program_buffer:
                f.write(line + '\n')
        print(f"Saved {len(program_buffer)} lines to '{filename}'.")
    except Exception as e:
        print(f"Error saving file: {e}")


def load_file(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.read().splitlines()
        program_buffer.clear()
        _interp.reset()
        program_buffer.extend(lines)
        print(f"Loaded {len(program_buffer)} lines from '{filename}'.")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print(f"Error loading file: {e}")


def run_program():
    if not program_buffer:
        print("Buffer is empty.")
        return
    code = '\n'.join(program_buffer)
    _interp.reset()
    _interp.run_program(code)


def run_code(code):
    _interp.run_program(code, auto_run_main=False)


def check_program():
    if not program_buffer:
        print("Buffer is empty.")
        return
    code = '\n'.join(program_buffer)
    errors = _interp.check_program(code)
    if not errors:
        print("No errors found.")
    else:
        for e in errors:
            print(e)


def show_vars():
    vars_ = _interp.get_vars()
    if not vars_:
        print("No variables.")
        return
    for name, type_, val, size in vars_:
        if size > 1:
            preview = val[:10]
            suffix = ', ...' if size > 10 else ''
            print(f"  {type_} {name}[{size}] = {{{', '.join(map(str, preview))}{suffix}}}")
        else:
            char_hint = f" ('{chr(val)}')" if type_ == 'char' and 32 <= val <= 126 else ''
            print(f"  {type_} {name} = {val}{char_hint}")


def show_funcs():
    funcs = _interp.get_funcs()
    if not funcs:
        print("No user-defined functions.")
    for name, ret, params, line in funcs:
        print(f"  {ret} {name}({params})  line {line}")
    # 內建函式
    print("  --- built-in functions ---")
    builtins = [
        "int putchar(int ch)", "int getchar()", "void printf(char *fmt, ...)",
        "void puts(char *s)", "int scanf(char *fmt, ...)",
        "int strlen(char *s)", "void strcpy(char *dst, char *src)",
        "void strcat(char *dst, char *src)", "int strcmp(char *s1, char *s2)",
        "int atoi(char *s)", "void itoa(int val, char *str)",
        "int abs(int x)", "int max(int a, int b)", "int min(int a, int b)",
        "int pow(int base, int exp)", "int sqrt(int x)", "int mod(int a, int b)",
        "int rand()", "void srand(int seed)",
        "void memset(char *ptr, int val, int size)",
        "int sizeof_int()", "int sizeof_char()", "void exit(int code)",
    ]
    for b in builtins:
        print(f"  {b}  [built-in]")


def trace_on():
    _interp.set_trace(True)
    print("Trace mode enabled.")


def trace_off():
    _interp.set_trace(False)
    print("Trace mode disabled.")

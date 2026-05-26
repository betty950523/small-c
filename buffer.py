program_buffer = []
trace_mode = False


def append_line(line):
    program_buffer.append(line)


def list_lines():
    if len(program_buffer) == 0:
        print("No program loaded.")
        return

    for i, line in enumerate(program_buffer, start=1):
        print(f"{i}: {line}")


def delete_line(n):
    if n < 1 or n > len(program_buffer):
        print("Invalid line number.")
        return

    program_buffer.pop(n - 1)
    print(f"Deleted line {n}")


def clear_buffer():
    program_buffer.clear()
    print("All cleared.")


def edit_line(n, new_text):
    if n < 1 or n > len(program_buffer):
        print("Invalid line number.")
        return

    program_buffer[n - 1] = new_text
    print(f"Edited line {n}")


def insert_line(n, text):
    if n < 1 or n > len(program_buffer) + 1:
        print("Invalid line number.")
        return

    program_buffer.insert(n - 1, text)
    print(f"Inserted line {n}")


def save_file(filename):
    with open(filename, "w") as f:
        for line in program_buffer:
            f.write(line + "\n")

    print(f"Saved {len(program_buffer)} lines to '{filename}'")


def load_file(filename):
    global program_buffer

    try:
        with open(filename, "r") as f:
            program_buffer = []

            for line in f:
                program_buffer.append(line.rstrip("\n"))

        print(f"Loaded {len(program_buffer)} lines from '{filename}'")

    except FileNotFoundError:
        print("File not found.")


def check_program():
    if len(program_buffer) == 0:
        print("No program loaded.")
    else:
        print("No errors found.")


def run_program():
    if len(program_buffer) == 0:
        print("No program loaded.")
        return

    print("Running program...")
    print("----------------")

    for i, line in enumerate(program_buffer, start=1):
        if trace_mode:
            print(f"[line {i}] {line}")
        else:
            print(line)

    print("----------------")
    print("Program finished.")


def show_vars():
    print("No variables.")


def show_funcs():
    print("No functions.")


def trace_on():
    global trace_mode
    trace_mode = True
    print("Trace mode enabled.")


def trace_off():
    global trace_mode
    trace_mode = False
    print("Trace mode disabled.")
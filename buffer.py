program_buffer = []


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
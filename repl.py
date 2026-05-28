from buffer import (
    append_line,
    list_lines,
    delete_line,
    clear_buffer,
    edit_line,
    insert_line,
    save_file,
    load_file,
    check_program,
    run_program,
    show_vars,
    show_funcs,
    trace_on,
    trace_off,
    run_code,
    get_line_count, 
)


def start_repl():
    print("Small-C Interpreter")
    print("Type HELP for commands.")

    while True:
        cmd = input("sc> ")

        if cmd.upper() == "QUIT" or cmd.upper() == "EXIT":
            print("Goodbye.")
            break

        elif cmd.upper() == "HELP":
            print("Commands:")
            print("HELP")
            print("ABOUT")
            print("APPEND")
            print("LIST")
            print("DELETE n")
            print("NEW")
            print("EDIT n")
            print("INSERT n")
            print("SAVE file")
            print("LOAD file")
            print("CHECK")
            print("RUN")
            print("CLEAR")
            print("VARS")
            print("FUNCS")
            print("TRACE ON")
            print("TRACE OFF")
            print("QUIT / EXIT")

        elif cmd.upper() == "ABOUT":
            print("Small-C Interpreter")
            print("Version 1.0")
            print("Author: 李忻倍,王辰禕")
            print("Spring 2026")

        elif cmd.upper() == "APPEND":
            print("Enter program lines. Type . to finish.")
            line_num = get_line_count() + 1
            while True:
                line = input(f"{line_num:4}> ")
                if line == ".":
                    break
                append_line(line)
                line_num += 1

        elif cmd.upper().startswith("LIST"):
            parts = cmd.split()
            if len(parts) == 1:
                list_lines()
            elif len(parts) == 2:
                if '-' in parts[1]:
                    n1, n2 = parts[1].split('-')
                    list_lines(int(n1), int(n2))
                else:
                    list_lines(int(parts[1]), int(parts[1]))

        elif cmd.upper().startswith("DELETE"):
            parts = cmd.split()

            if len(parts) != 2:
                print("Usage: DELETE n")
            else:
                delete_line(int(parts[1]))

        elif cmd.upper() == "NEW":
            if get_line_count() > 0:
                confirm = input("Unsaved changes. Clear anyway? (Y/N): ")
                if confirm.upper() == "Y":
                    clear_buffer()
            else:
                clear_buffer()
                
        elif cmd.upper().startswith("EDIT"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: EDIT n")
            else:
                n = int(parts[1])
                list_lines(n, n)
                new_text = input("New line: ")
                if new_text:
                    edit_line(n, new_text)

        elif cmd.upper().startswith("INSERT"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: INSERT n")
            else:
                n = int(parts[1])
                line_num = n
                while True:
                    line = input(f"{line_num:4}> ")
                    if line == ".":
                        break
                    insert_line(n + (line_num - n), line)
                    line_num += 1

        elif cmd.upper().startswith("SAVE"):
            parts = cmd.split()

            if len(parts) != 2:
                print("Usage: SAVE filename")
            else:
                save_file(parts[1])

        elif cmd.upper().startswith("LOAD"):
            parts = cmd.split()

            if len(parts) != 2:
                print("Usage: LOAD filename")
            else:
                load_file(parts[1])

        elif cmd.upper() == "CHECK":
            check_program()

        elif cmd.upper() == "RUN":
            run_program()

        elif cmd.upper() == "CLEAR":
            print("\033[2J\033[H", end="")

        elif cmd.upper() == "VARS":
            show_vars()

        elif cmd.upper() == "FUNCS":
            show_funcs()

        elif cmd.upper() == "TRACE ON":
            trace_on()

        elif cmd.upper() == "TRACE OFF":
            trace_off()

        else:
            code = cmd
            open_braces = cmd.count('{') - cmd.count('}')
            while open_braces > 0:
                line = input("  > ")
                code += '\n' + line
                open_braces += line.count('{') - line.count('}')
                if open_braces == 0 and code.lstrip().startswith('do'):
                    stripped = line.strip()
                    if not (stripped.startswith('}') and 'while' in stripped and stripped.endswith(';')):
                        open_braces = 1
            run_code(code)

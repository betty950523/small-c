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
    trace_off
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
            print("VARS")
            print("FUNCS")
            print("TRACE ON")
            print("TRACE OFF")
            print("QUIT / EXIT")

        elif cmd.upper() == "ABOUT":
            print("Small-C Interpreter")
            print("Version 1.0")
            print("Author: Betty Team")
            print("Spring 2026")

        elif cmd.upper() == "APPEND":
            print("Enter program lines. Type . to finish.")

            while True:
                line = input()

                if line == ".":
                    break

                append_line(line)

        elif cmd.upper() == "LIST":
            list_lines()

        elif cmd.upper().startswith("DELETE"):
            parts = cmd.split()

            if len(parts) != 2:
                print("Usage: DELETE n")
            else:
                delete_line(int(parts[1]))

        elif cmd.upper() == "NEW":
            clear_buffer()

        elif cmd.upper().startswith("EDIT"):
            parts = cmd.split()

            if len(parts) != 2:
                print("Usage: EDIT n")
            else:
                n = int(parts[1])
                new_text = input("New line: ")
                edit_line(n, new_text)

        elif cmd.upper().startswith("INSERT"):
            parts = cmd.split()

            if len(parts) != 2:
                print("Usage: INSERT n")
            else:
                n = int(parts[1])
                text = input("Insert line: ")
                insert_line(n, text)

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

        elif cmd.upper() == "VARS":
            show_vars()

        elif cmd.upper() == "FUNCS":
            show_funcs()

        elif cmd.upper() == "TRACE ON":
            trace_on()

        elif cmd.upper() == "TRACE OFF":
            trace_off()

        else:
            print("Unknown command")
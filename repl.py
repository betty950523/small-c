from buffer import (
    append_line,
    list_lines,
    delete_line,
    clear_buffer,
    edit_line,
    save_file,
    load_file
)


def start_repl():
    print("Small-C Interpreter")
    print("Type HELP for commands.")

    while True:
        cmd = input("sc> ")

        if cmd.upper() == "QUIT":
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
            print("SAVE file")
            print("LOAD file")
            print("QUIT")

        elif cmd.upper() == "ABOUT":
            print("Small-C Interpreter")
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

        else:
            print("Unknown command")
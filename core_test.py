# small-c-main/core_test.py
from lexer import Lexer
from parser import Parser
from symtable import SymbolTable
from interpreter import SmallCInterpreter

if __name__ == '__main__':
    interpreter = SmallCInterpreter()
    ultimate_code = """
    int my_array[3];
    my_array[0] = 10;
    my_array[1] = 20;
    my_array[2] = my_array[0] + my_array[1];
    
    int square(int x) {
        return x * x;
    }
    
    int result;
    result = square(5);
    """
    
    print("--- 開始進行 Small-C 終極核心整合測試 ---")
    interpreter.run_program(ultimate_code)
    
    print("\n--- 1. 檢查變數與陣列儲存狀態 ---")
    print(interpreter.get_vars())
    
    print("\n--- 2. 檢查組員 B 需要的 get_funcs() 函式表狀態 ---")
    print(interpreter.get_funcs())
# small-c-main/main.py
from lexer import Lexer
from parser import Parser
from symtable import SymbolTable

class SmallCInterpreter:
    def __init__(self):
        self.shared_symtable = SymbolTable()

    def run_program(self, code_string: str) -> str:
        try:
            lexer = Lexer(code_string)
            parser = Parser(lexer, symtable=self.shared_symtable)
            result = parser.parse()
            return str(result)
        except Exception as e:
            return f"Runtime Error: {e}"

    def get_vars(self) -> dict:
        return self.shared_symtable.get_all()

    def get_funcs(self) -> dict:
        """
        API 接口：當組員 B 輸入 FUNCS 指令時，直接打包回傳目前的函式清單
        """
        return self.shared_symtable.get_all_funcs()


if __name__ == '__main__':
    interpreter = SmallCInterpreter()
    
    # 撰寫一段涵蓋 陣列操作、函式定義 與 函式呼叫的終極綜合測試
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

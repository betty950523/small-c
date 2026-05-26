# small-c-main/symtable.py

class SymbolTable:
    def __init__(self):
        # 用來存變數。格式：{'x': {'type': 'int', 'value': 10}}
        self.symbols = {}

    def declare(self, name, var_type):
        """宣告變數，例如 int x;（初始值先給 0）"""
        if name in self.symbols:
            raise Exception(f"Semantic error: 變數 '{name}' 已經被宣告過了！")
        self.symbols[name] = {'type': var_type, 'value': 0}

    def set_value(self, name, value):
        """給變數賦值，例如 x = 20;"""
        if name not in self.symbols:
            raise Exception(f"Semantic error: 變數 '{name}' 尚未宣告，無法賦值！")
        self.symbols[name]['value'] = value

    def get_value(self, name):
        """拿取變數的值，例如計算 x + 5 時"""
        if name not in self.symbols:
            raise Exception(f"Name error: 變數 '{name}' 尚未宣告！")
        return self.symbols[name]['value']

    def get_all(self):
        """用來打包吐出目前所有的變數資訊"""
        return self.symbols
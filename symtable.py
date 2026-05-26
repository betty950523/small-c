# small-c-main/symtable.py
class SymbolTable:
    def __init__(self):
        # 變數表：{'x': {'type': 'int', 'value': 10}, 'arr': {'type': 'int_array', 'value': [0, 0, 0]}}
        self.symbols = {}
        # 函式表：{'add': {'return_type': 'int', 'params': [('x', 'int')], 'body_node': <ParserNode>}}
        self.functions = {}

    def declare(self, name, var_type, size=None):
        """宣告變數，支援基本型態與一維陣列"""
        if name in self.symbols:
            raise Exception(f"Semantic error: 變數 '{name}' 已經被宣告過！")
        
        if size is not None: # 陣列宣告，例如 int a[5];
            self.symbols[name] = {'type': f'{var_type}_array', 'value': [0] * size}
        else: # 普通變數或指標
            self.symbols[name] = {'type': var_type, 'value': 0}

    def set_value(self, name, value, index=None):
        """指定數值，支援陣列索引與指標模擬"""
        if name not in self.symbols:
            raise Exception(f"Semantic error: 變數 '{name}' 尚未宣告！")
        
        if index is not None: # 陣列賦值：a[2] = 10;
            if 'array' not in self.symbols[name]['type']:
                raise Exception(f"Type error: '{name}' 不是陣列型態！")
            if index < 0 or index >= len(self.symbols[name]['value']):
                raise Exception(f"Runtime Error: 陣列 '{name}' 索引值 {index} 超出邊界！")
            self.symbols[name]['value'][index] = value
        else:
            if self.symbols[name]['type'] == 'char':
                value = (value + 128) % 256 - 128
            self.symbols[name]['value'] = value

    def get_value(self, name, index=None):
        """讀取數值，支援陣列索引取值"""
        if name not in self.symbols:
            raise Exception(f"Name error: 變數 '{name}' 尚未宣告！")
        
        if index is not None: # 陣列取值：a[2]
            if 'array' not in self.symbols[name]['type']:
                raise Exception(f"Type error: '{name}' 不是陣列型態！")
            if index < 0 or index >= len(self.symbols[name]['value']):
                raise Exception(f"Runtime Error: 陣列 '{name}' 索引值 {index} 超出邊界！")
            return self.symbols[name]['value'][index]
            
        return self.symbols[name]['value']

    def declare_func(self, name, return_type, params, body_text):
        """註冊函式，以便後面呼叫"""
        self.functions[name] = {
            'return_type': return_type,
            'params': params, # 格式: [('param_name', 'type')]
            'body': body_text # 存下函式主體的原始碼字串，呼叫時再動態解析
        }

    def get_func(self, name):
        if name not in self.functions:
            raise Exception(f"Name error: 函式 '{name}' 尚未定義！")
        return self.functions[name]

    def get_all(self):
        return self.symbols

    def get_all_funcs(self):
        """這給組員 B 的 FUNCS 指令用的接口"""
        return self.functions

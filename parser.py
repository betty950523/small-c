# small-c-main/parser.py
from lexer import (
    INTEGER, ID, INT, CHAR, RETURN, SEMICOLON, ASSIGN,
    PLUS, MINUS, MUL, DIV, MOD, LPAREN, RPAREN, LBRACKET, RBRACKET, EOF,
    GT, LT, GE, LE, EQ, NE
)
from symtable import SymbolTable

class Parser:
    def __init__(self, lexer, symtable=None):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.symtable = symtable if symtable is not None else SymbolTable()
        self.is_executing = True 

    def error(self, message="Syntax error"):
        raise Exception(message)

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Unexpected token {self.current_token.type}, expected {token_type}")

    def factor(self):
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)
            return token.value
            
        elif token.type == ID:
            name = token.value
            self.eat(ID)
            
            # 函式呼叫：add(5)
            if self.current_token.type == LPAREN:
                self.eat(LPAREN)
                args = []
                if self.current_token.type != RPAREN:
                    args.append(self.equality_expr())
                    while self.current_token.type == ID and self.current_token.value == ',':
                        self.eat(ID)
                        args.append(self.equality_expr())
                self.eat(RPAREN)
                
                if self.is_executing:
                    func_data = self.symtable.get_func(name)
                    local_table = SymbolTable()
                    local_table.functions = self.symtable.functions 
                    
                    for (param_name, param_type), arg_val in zip(func_data['params'], args):
                        local_table.declare(param_name, param_type)
                        local_table.set_value(param_name, arg_val)
                    
                    from lexer import Lexer
                    sub_lexer = Lexer(func_data['body'])
                    sub_parser = Parser(sub_lexer, symtable=local_table)
                    try:
                        sub_parser.parse()
                    except Exception as e:
                        if "ReturnVal:" in str(e):
                            return int(str(e).split(":")[1])
                        raise e
                    return 0 
                return 0
                
            # 陣列取值：a[2]
            elif self.current_token.type == LBRACKET:
                self.eat(LBRACKET)
                idx = self.equality_expr()
                self.eat(RBRACKET)
                return self.symtable.get_value(name, index=idx) if self.is_executing else 0
                
            else:
                return self.symtable.get_value(name) if self.is_executing else 0
                
        elif token.type == LPAREN:
            self.eat(LPAREN)
            result = self.equality_expr()
            self.eat(RPAREN)
            return result
            
        elif token.type == MUL:
            self.eat(MUL)
            var_name = self.current_token.value
            self.eat(ID)
            if self.is_executing:
                actual_var = self.symtable.get_value(var_name)
                return self.symtable.get_value(actual_var)
            return 0
            
        self.error(f"Unexpected factor token: {token.type}")

    def term(self):
        result = self.factor()
        while self.current_token.type in (MUL, DIV, MOD):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
                val = self.factor()
                if self.is_executing: result = result * val
            elif token.type == DIV:
                self.eat(DIV)
                val = self.factor()
                if self.is_executing: result = int(result / val)
            elif token.type == MOD:
                self.eat(MOD)
                val = self.factor()
                if self.is_executing: result = result % val
        return result

    def expr(self):
        result = self.term()
        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
                val = self.term()
                if self.is_executing: result = result + val
            elif token.type == MINUS:
                self.eat(MINUS)
                val = self.term()
                if self.is_executing: result = result - val
        return result

    def relational_expr(self):
        result = self.expr()
        while self.current_token.type in (GT, LT, GE, LE):
            token = self.current_token
            if token.type == GT:
                self.eat(GT)
                val = self.expr()
                if self.is_executing: result = 1 if result > val else 0
            elif token.type == LT:
                self.eat(LT)
                val = self.expr()
                if self.is_executing: result = 1 if result < val else 0
            elif token.type == GE:
                self.eat(GE)
                val = self.expr()
                if self.is_executing: result = 1 if result >= val else 0
            elif token.type == LE:
                self.eat(LE)
                val = self.expr()
                if self.is_executing: result = 1 if result <= val else 0
        return result

    def equality_expr(self):
        result = self.relational_expr()
        while self.current_token.type in (EQ, NE):
            token = self.current_token
            if token.type == EQ:
                self.eat(EQ)
                val = self.relational_expr()
                if self.is_executing: result = 1 if result == val else 0
            elif token.type == NE:
                self.eat(NE)
                val = self.relational_expr()
                if self.is_executing: result = 1 if result != val else 0
        return result

    def statement(self):
        # 1. 處理變數 / 陣列 / 函式 的宣告與定義
        if self.current_token.type in (INT, CHAR):
            type_token = self.current_token.type  
            self.eat(type_token)
            
            is_pointer = False
            if self.current_token.type == MUL:
                self.eat(MUL)
                is_pointer = True
                
            var_name = self.current_token.value
            self.eat(ID)
            
            # 陣列宣告：int a[5];
            if self.current_token.type == LBRACKET:
                self.eat(LBRACKET)
                size = self.current_token.value
                self.eat(INTEGER)
                self.eat(RBRACKET)
                self.eat(SEMICOLON)
                if self.is_executing:
                    var_type_str = 'int' if type_token == INT else 'char'
                    self.symtable.declare(var_name, var_type_str, size=size)
                return f"成功宣告陣列: {var_name}[{size}]"
                
            # 函式定義：int add(int x) { ... }
            elif self.current_token.type == LPAREN:
                self.eat(LPAREN)
                params = []
                while self.current_token.type in (INT, CHAR):
                    p_type = 'int' if self.current_token.type == INT else 'char'
                    self.eat(self.current_token.type)
                    p_name = self.current_token.value
                    self.eat(ID)
                    params.append((p_name, p_type))
                    if self.current_token.type == ID and self.current_token.value == ',':
                        self.eat(ID)
                self.eat(RPAREN)
                
                # 【終極精準 Token 收集法】
                self.eat('LBRACE')
                body_tokens = []
                brace_count = 1
                
                # 倒出原始碼重建主體，徹底避免 index 偏移 Bug
                while brace_count > 0 and self.current_token.type != EOF:
                    t = self.current_token
                    if t.type == 'LBRACE': brace_count += 1
                    if t.type == 'RBRACE': brace_count -= 1
                    
                    if brace_count > 0:
                        if t.type == SEMICOLON: body_tokens.append(";\n")
                        elif t.type == INTEGER: body_tokens.append(str(t.value))
                        elif t.type == RETURN: body_tokens.append("return ")
                        elif t.type in (INT, CHAR): body_tokens.append("int " if t.type == INT else "char ")
                        else: body_tokens.append(str(t.value))
                    
                    self.current_token = self.lexer.get_next_token()
                
                body_text = "".join(body_tokens)
                
                if self.is_executing:
                    var_type_str = 'int' if type_token == INT else 'char'
                    self.symtable.declare_func(var_name, var_type_str, params, body_text)
                return f"成功定義函式: {var_name}"
                
            else:
                self.eat(SEMICOLON)
                if self.is_executing:
                    var_type_str = 'int' if type_token == INT else 'char'
                    if is_pointer: var_type_str += "*"
                    self.symtable.declare(var_name, var_type_str)
                return f"成功宣告變數: {var_name}"

        # 2. 處理 return 語句
        elif self.current_token.type == RETURN:
            self.eat(RETURN)
            val = self.equality_expr()
            self.eat(SEMICOLON)
            if self.is_executing:
                raise Exception(f"ReturnVal:{val}")
            return val

        # 3. 處理指定賦值
        elif self.current_token.type == ID and (
            self.lexer.text[self.lexer.pos-2:].strip().startswith('=') or 
            '=' in self.lexer.text[self.lexer.pos-2:self.lexer.pos+15] or
            self.current_token.type == ID
        ):
            var_name = self.current_token.value
            self.eat(ID)
            
            if self.current_token.type == LBRACKET:
                self.eat(LBRACKET)
                idx = self.equality_expr()
                self.eat(RBRACKET)
                self.eat(ASSIGN)
                val = self.equality_expr()
                self.eat(SEMICOLON)
                if self.is_executing:
                    self.symtable.set_value(var_name, val, index=idx)
                return f"陣列賦值成功"
            elif self.current_token.type == ASSIGN:
                self.eat(ASSIGN)
                val = self.equality_expr()
                if self.current_token.type == SEMICOLON:
                    self.eat(SEMICOLON)
                if self.is_executing:
                    self.symtable.set_value(var_name, val)
                return f"成功賦值"
            else:
                # 獨立的表達式求值（例如純呼叫函式）
                # 倒退一步讓下面的 equality_expr 能讀到完整東西
                self.lexer.pos -= len(var_name)
                self.lexer.current_char = self.lexer.text[self.lexer.pos]
                self.current_token = self.lexer.get_next_token()
                return self.equality_expr()

        # 4. 大括號區塊 { ... }
        elif self.current_token.type == 'LBRACE':
            self.eat('LBRACE')
            last_res = None
            while self.current_token.type != 'RBRACE' and self.current_token.type != EOF:
                last_res = self.statement()
            self.eat('RBRACE')
            return last_res

        # 5. 控制流程 (if, while, do, for)
        elif self.current_token.type == ID and self.current_token.value == 'if':
            self.eat(ID); self.eat(LPAREN); condition = self.equality_expr(); self.eat(RPAREN)
            old_state = self.is_executing
            if old_state: self.is_executing = (condition != 0)
            self.statement()
            if self.current_token.type == ID and self.current_token.value == 'else':
                self.eat(ID)
                if old_state: self.is_executing = not (condition != 0)
                self.statement()
            self.is_executing = old_state
            return "if-else 執行完畢"

        elif self.current_token.type == ID and self.current_token.value == 'while':
            self.eat(ID); start_pos, start_char, start_token = self.lexer.pos, self.lexer.current_char, self.current_token
            old_state = self.is_executing
            while True:
                self.eat(LPAREN); condition = self.equality_expr(); self.eat(RPAREN)
                self.is_executing = old_state and (condition != 0)
                if not self.is_executing: self.statement(); break
                self.statement()
                self.lexer.pos, self.lexer.current_char, self.current_token = start_pos, start_char, start_token
            self.is_executing = old_state
            return "while 執行完畢"

        elif self.current_token.type == ID and self.current_token.value == 'do':
            self.eat(ID); start_pos, start_char, start_token = self.lexer.pos, self.lexer.current_char, self.current_token
            old_state = self.is_executing
            while True:
                self.statement()
                self.eat(ID); self.eat(LPAREN); condition = self.equality_expr(); self.eat(RPAREN); self.eat(SEMICOLON)
                self.is_executing = old_state and (condition != 0)
                if not self.is_executing: break
                self.lexer.pos, self.lexer.current_char, self.current_token = start_pos, start_char, start_token
            self.is_executing = old_state
            return "do-while 執行完畢"

        elif self.current_token.type == ID and self.current_token.value == 'for':
            self.eat(ID); self.eat(LPAREN); self.statement()
            cond_pos, cond_char, cond_token = self.lexer.pos, self.lexer.current_char, self.current_token
            old_state = self.is_executing
            while True:
                condition = self.equality_expr(); self.eat(SEMICOLON)
                iter_pos, iter_char, iter_token = self.lexer.pos, self.lexer.current_char, self.current_token
                while self.current_token.type != RPAREN: self.current_token = self.lexer.get_next_token()
                self.eat(RPAREN)
                self.is_executing = old_state and (condition != 0)
                if not self.is_executing: self.statement(); break
                self.statement()
                self.lexer.pos, self.lexer.current_char, self.current_token = iter_pos, iter_char, iter_token
                self.statement(); self.eat(RPAREN)
                self.lexer.pos, self.lexer.current_char, self.current_token = cond_pos, cond_char, cond_token
            self.is_executing = old_state
            return "for 執行完畢"

        else:
            return self.equality_expr()

    def parse(self):
        last_result = None
        while self.current_token.type != EOF:
            last_result = self.statement()
        return last_result

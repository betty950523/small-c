# small-c-main/lexer.py

# 新增 Token 類型
INTEGER = 'INTEGER'
ID      = 'ID'       # 變數名稱 (例如 x, score)
INT     = 'INT'      # 關鍵字 int
SEMICOLON = 'SEMICOLON' # 分號 ;
ASSIGN  = 'ASSIGN'   # 指定運算子 =
PLUS, MINUS, MUL, DIV, MOD, LPAREN, RPAREN = 'PLUS', 'MINUS', 'MUL', 'DIV', 'MOD', 'LPAREN', 'RPAREN'
GT, LT, GE, LE, EQ, NE = 'GT', 'LT', 'GE', 'LE', 'EQ', 'NE'
EOF     = 'EOF'

# 關鍵字字典
KEYWORDS = {
    'int': INT,
}

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __str__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if text else None

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos > len(self.text) - 1:
            return None
        return self.text[peek_pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def _id(self):
        """處理變數名稱與關鍵字"""
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        # 如果這個字在關鍵字字典裡，就回傳關鍵字 Token（例如 INT）；否則一律當成變數 ID
        token_type = KEYWORDS.get(result, ID)
        return Token(token_type, result)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # 如果是字母或底線開頭，代表是變數名或關鍵字
            if self.current_char.isalpha() or self.current_char == '_':
                return self._id()

            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())

            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+')
            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-')
            if self.current_char == '*':
                self.advance()
                return Token(MUL, '*')
            if self.current_char == '/':
                self.advance()
                return Token(DIV, '/')
            if self.current_char == '%':
                self.advance()
                return Token(MOD, '%')
            if self.current_char == '(':
                self.advance()
                return Token(LPAREN, '(')
            if self.current_char == ')':
                self.advance()
                return Token(RPAREN, ')')
            if self.current_char == ';':
                self.advance()
                return Token(SEMICOLON, ';')

            if self.current_char == '=':
                if self.peek() == '=':
                    self.advance()
                    self.advance()
                    return Token(EQ, '==')
                self.advance()
                return Token(ASSIGN, '=')

            if self.current_char == '!':
                if self.peek() == '=':
                    self.advance()
                    self.advance()
                    return Token(NE, '!=')
                self.advance()
                return Token('NOT', '!')

            if self.current_char == '>':
                if self.peek() == '=':
                    self.advance()
                    self.advance()
                    return Token(GE, '>=')
                self.advance()
                return Token(GT, '>')

            if self.current_char == '<':
                if self.peek() == '=':
                    self.advance()
                    self.advance()
                    return Token(LE, '<=')
                self.advance()
                return Token(LT, '<')

            raise Exception(f"Syntax error: unexpected character '{self.current_char}'")

        return Token(EOF, None)

INTEGER = 'INTEGER'  
CHAR_LIT = 'CHAR_LIT' 
STRING  = 'STRING'    

ID = 'ID'

INT      = 'INT'
CHAR     = 'CHAR'
VOID     = 'VOID'
IF       = 'IF'
ELSE     = 'ELSE'
WHILE    = 'WHILE'
FOR      = 'FOR'
DO       = 'DO'
BREAK    = 'BREAK'
CONTINUE = 'CONTINUE'
RETURN   = 'RETURN'
SWITCH   = 'SWITCH'
CASE     = 'CASE'
DEFAULT  = 'DEFAULT'

# 前處理器
DEFINE = 'DEFINE'   # #define

# 算術運算子
PLUS    = 'PLUS'    # +
MINUS   = 'MINUS'   # -
MUL     = 'MUL'     # *
DIV     = 'DIV'     # /
MOD     = 'MOD'     # %

# 位元運算子
AMP     = 'AMP'     # &
PIPE    = 'PIPE'    # |
CARET   = 'CARET'   # ^
TILDE   = 'TILDE'   # ~
LSHIFT  = 'LSHIFT'  # <<
RSHIFT  = 'RSHIFT'  # >>

# 邏輯運算子
AND     = 'AND'     # &&
OR      = 'OR'      # ||
NOT     = 'NOT'     # !

# 關係運算子
EQ      = 'EQ'      # ==
NE      = 'NE'      # !=
LT      = 'LT'      # <
GT      = 'GT'      # >
LE      = 'LE'      # <=
GE      = 'GE'      # >=

# 指定運算子
ASSIGN      = 'ASSIGN'      # =
PLUS_ASSIGN = 'PLUS_ASSIGN' # +=
MINUS_ASSIGN= 'MINUS_ASSIGN'# -=
MUL_ASSIGN  = 'MUL_ASSIGN'  # *=
DIV_ASSIGN  = 'DIV_ASSIGN'  # /=
MOD_ASSIGN  = 'MOD_ASSIGN'  # %=

# 遞增 / 遞減
INC = 'INC'  # ++
DEC = 'DEC'  # --

# 括號 / 標點
LPAREN   = 'LPAREN'   # (
RPAREN   = 'RPAREN'   # )
LBRACE   = 'LBRACE'   # {
RBRACE   = 'RBRACE'   # }
LBRACKET = 'LBRACKET' # [
RBRACKET = 'RBRACKET' # ]
SEMICOLON = 'SEMICOLON' # ;
COMMA    = 'COMMA'    # ,

EOF = 'EOF'

KEYWORDS = {
    'int':      INT,
    'char':     CHAR,
    'void':     VOID,
    'if':       IF,
    'else':     ELSE,
    'while':    WHILE,
    'for':      FOR,
    'do':       DO,
    'break':    BREAK,
    'continue': CONTINUE,
    'return':   RETURN,
    'switch':   SWITCH,
    'case':     CASE,
    'default':  DEFAULT,
}

class Token:
    def __init__(self, type_, value, line=1):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, line={self.line})'


class LexerError(Exception):
    def __init__(self, msg, line):
        super().__init__(f'[Lexer] Line {line}: {msg}')
        self.line = line


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos  = 0
        self.line = 1
        self.current_char = text[0] if text else None

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self, offset=1):
        i = self.pos + offset
        return self.text[i] if i < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_line_comment(self):
        """跳過 // 到行尾"""
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def skip_block_comment(self):
        """跳過 /* ... */"""
        start_line = self.line
        self.advance(); self.advance()  # 跳過 /*
        while self.current_char is not None:
            if self.current_char == '*' and self.peek() == '/':
                self.advance(); self.advance()  # 跳過 */
                return
            self.advance()
        raise LexerError("Unterminated block comment", start_line)

    def read_escape(self):
        """pos 指向 \\ 後面的字元，讀取並回傳對應的字元。"""
        mapping = {
            'n': '\n', 't': '\t', '0': '\0',
            '\\': '\\', "'": "'", '"': '"', 'r': '\r',
        }
        ch = self.current_char
        if ch is None:
            raise LexerError("Unexpected end in escape sequence", self.line)
        self.advance()
        if ch in mapping:
            return mapping[ch]
        raise LexerError(f"Unknown escape sequence: \\{ch}", self.line)

    def read_number(self):
        line = self.line
        text = ''
        # 十六進位
        if self.current_char == '0' and self.peek() in ('x', 'X'):
            text += self.current_char; self.advance()
            text += self.current_char; self.advance()
            while self.current_char is not None and self.current_char in '0123456789abcdefABCDEF':
                text += self.current_char; self.advance()
            return Token(INTEGER, int(text, 16), line)
        # 十進位
        while self.current_char is not None and self.current_char.isdigit():
            text += self.current_char; self.advance()
        return Token(INTEGER, int(text), line)

    def read_char_literal(self):
        line = self.line
        self.advance()  # 跳過開頭 '
        if self.current_char == '\\':
            self.advance()
            ch = self.read_escape()
        elif self.current_char is not None and self.current_char != "'":
            ch = self.current_char
            self.advance()
        else:
            raise LexerError("Empty char literal", line)
        if self.current_char != "'":
            raise LexerError("Unterminated char literal", line)
        self.advance()  # 跳過結尾 '
        return Token(CHAR_LIT, ord(ch), line)

    def read_string(self):
        line = self.line
        self.advance()  # 跳過開頭 "
        chars = []
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                chars.append(self.read_escape())
            elif self.current_char == '\n':
                chars.append('\n')
                self.advance()
            else:
                chars.append(self.current_char)
                self.advance()
        if self.current_char != '"':
            raise LexerError("Unterminated string literal", line)
        self.advance()  # 跳過結尾 "
        return Token(STRING, ''.join(chars), line)

    def read_id_or_keyword(self):
        line = self.line
        text = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            text += self.current_char
            self.advance()
        ttype = KEYWORDS.get(text, ID)
        return Token(ttype, text, line)

    def read_define(self):
        """讀 #define NAME VALUE（整行）"""
        line = self.line
        # 已在 #，往後讀識別字
        self.advance()  # 跳過 #
        word = ''
        while self.current_char is not None and self.current_char.isalpha():
            word += self.current_char
            self.advance()
        if word != 'define':
            raise LexerError(f"Unknown preprocessor directive: #{word}", line)
        return Token(DEFINE, '#define', line)

    def get_next_token(self) -> Token:
        while self.current_char is not None:
            # 空白
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # 註解
            if self.current_char == '/' and self.peek() == '/':
                self.skip_line_comment()
                continue
            if self.current_char == '/' and self.peek() == '*':
                self.skip_block_comment()
                continue

            line = self.line

            # 數字
            if self.current_char.isdigit():
                return self.read_number()

            # 字元常數
            if self.current_char == "'":
                return self.read_char_literal()

            # 字串常數
            if self.current_char == '"':
                return self.read_string()

            # 識別字 / 關鍵字
            if self.current_char.isalpha() or self.current_char == '_':
                return self.read_id_or_keyword()

            # 前處理器
            if self.current_char == '#':
                return self.read_define()

            two = self.current_char + (self.peek() or '')

            if two == '&&': self.advance(); self.advance(); return Token(AND,          '&&', line)
            if two == '||': self.advance(); self.advance(); return Token(OR,           '||', line)
            if two == '==': self.advance(); self.advance(); return Token(EQ,           '==', line)
            if two == '!=': self.advance(); self.advance(); return Token(NE,           '!=', line)
            if two == '<=': self.advance(); self.advance(); return Token(LE,           '<=', line)
            if two == '>=': self.advance(); self.advance(); return Token(GE,           '>=', line)
            if two == '<<': self.advance(); self.advance(); return Token(LSHIFT,       '<<', line)
            if two == '>>': self.advance(); self.advance(); return Token(RSHIFT,       '>>', line)
            if two == '++': self.advance(); self.advance(); return Token(INC,          '++', line)
            if two == '--': self.advance(); self.advance(); return Token(DEC,          '--', line)
            if two == '+=': self.advance(); self.advance(); return Token(PLUS_ASSIGN,  '+=', line)
            if two == '-=': self.advance(); self.advance(); return Token(MINUS_ASSIGN, '-=', line)
            if two == '*=': self.advance(); self.advance(); return Token(MUL_ASSIGN,   '*=', line)
            if two == '/=': self.advance(); self.advance(); return Token(DIV_ASSIGN,   '/=', line)
            if two == '%=': self.advance(); self.advance(); return Token(MOD_ASSIGN,   '%=', line)

            ch = self.current_char
            self.advance()
            single = {
                '+': PLUS,  '-': MINUS, '*': MUL,   '/': DIV,
                '%': MOD,   '&': AMP,   '|': PIPE,  '^': CARET,
                '~': TILDE, '!': NOT,   '<': LT,    '>': GT,
                '=': ASSIGN,'(': LPAREN,')': RPAREN,'{': LBRACE,
                '}': RBRACE,'[': LBRACKET,']': RBRACKET,
                ';': SEMICOLON, ',': COMMA,
            }
            if ch in single:
                return Token(single[ch], ch, line)

            raise LexerError(f"Unexpected character: {ch!r}", line)

        return Token(EOF, None, self.line)


if __name__ == '__main__':
    samples = [
        ("整數",       "42",              INTEGER),
        ("十六進位",   "0xFF",            INTEGER),
        ("字元",       "'A'",             CHAR_LIT),
        ("跳脫字元",   "'\\n'",           CHAR_LIT),
        ("字串",       '"hello\\n"',      STRING),
        ("關鍵字 int", "int",             INT),
        ("關鍵字 if",  "if",              IF),
        ("識別字",     "myVar",           ID),
        ("==",         "==",              EQ),
        ("!=",         "!=",              NE),
        ("&&",         "&&",              AND),
        ("||",         "||",              OR),
        ("<<",         "<<",             LSHIFT),
        ("+=",         "+=",             PLUS_ASSIGN),
        ("++",         "++",             INC),
        ("逗號",       ",",              COMMA),
        ("單行註解",   "// hi\n42",      INTEGER),
        ("區塊註解",   "/* hi */42",     INTEGER),
        ("#define",    "#define N 10",   DEFINE),
    ]

    all_ok = True
    for desc, src, expected in samples:
        try:
            tok = Lexer(src).get_next_token()
            ok  = tok.type == expected
            print(f"  {'✓' if ok else '✗'} {desc:15s}  期望={expected:15s}  得到={tok.type}")
            if not ok: all_ok = False
        except Exception as e:
            print(f"  ✗ {desc:15s}  錯誤: {e}")
            all_ok = False

    print()
    print("全部通過！" if all_ok else "有測試失敗。")

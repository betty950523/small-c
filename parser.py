# parser.py — Small-C 語法分析器 + 執行器（遞迴下降 + Tree-walking）

from lexer import (
    Lexer, Token,
    INTEGER, CHAR_LIT, STRING, ID, EOF,
    INT, CHAR, VOID,
    IF, ELSE, WHILE, FOR, DO, BREAK, CONTINUE, RETURN,
    DEFINE,
    PLUS, MINUS, MUL, DIV, MOD,
    AMP, PIPE, CARET, TILDE, LSHIFT, RSHIFT,
    AND, OR, NOT,
    EQ, NE, LT, GT, LE, GE,
    ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, MUL_ASSIGN, DIV_ASSIGN, MOD_ASSIGN,
    INC, DEC,
    LPAREN, RPAREN, LBRACE, RBRACE, LBRACKET, RBRACKET,
    SEMICOLON, COMMA,
)
from symtable import (
    ReturnException, BreakException, ContinueException,
    ParseError, RuntimeError_,
    Memory, Symbol, SymbolTable, FuncDef,
)


class Interpreter:
    """
    遞迴下降 Parser + Tree-walking Interpreter。
    同一個 class 負責解析與執行，以 self.executing 旗標控制是否真正執行。
    """

    def __init__(self, source: str, memory: Memory = None,
                 global_symtable: SymbolTable = None,
                 functions: dict = None,
                 defines: dict = None,
                 trace: bool = False,
                 output_fn=None):
        self.lexer      = Lexer(source)
        self.cur        = self.lexer.get_next_token()
        self.memory     = memory or Memory()
        self.symtable   = global_symtable or SymbolTable()
        self.functions  = functions if functions is not None else {}   # name -> FuncDef
        self.defines    = defines  if defines  is not None else {}    # name -> int
        self.trace      = trace
        self.output_fn  = output_fn or print   # 輸出函式（REPL 可替換）
        self.executing  = True

    def _next_token(self):
        return self.lexer.get_next_token()

    # ── token 操作 ────────────────────────────────────────────────
    def peek_type(self):
        return self.cur.type

    def peek_val(self):
        return self.cur.value

    def eat(self, expected_type):
        if self.cur.type != expected_type:
            raise ParseError(
                f"Expected {expected_type}, got {self.cur.type} ({self.cur.value!r})",
                self.cur.line)
        tok = self.cur
        self.cur = self.lexer.get_next_token()
        return tok

    def match(self, *types):
        return self.cur.type in types

    # ── 頂層解析 ──────────────────────────────────────────────────
    def parse_program(self, auto_run_main=True):
        while not self.match(EOF):
            self.parse_top_level()
        if auto_run_main and 'main' in self.functions:
            self._invoke_func('main', [])

    def _invoke_func(self, name, args, caller_symtable=None):
        """直接呼叫函式（不從 token stream 讀引數）。"""
        if not self.executing: return 0
        from builtin import call_builtin, is_builtin
        if is_builtin(name):
            return call_builtin(name, args, self.memory, self.output_fn)
        if name not in self.functions:
            raise RuntimeError_(f"Undefined function: {name}")
        func = self.functions[name]
        # 函式的局部符號表：parent 指向全域（讓函式能存取全域變數）
        # 注意：不繼承呼叫者的局部變數（C 的作用域規則）
        global_st = self.symtable
        while global_st.parent is not None:
            global_st = global_st.parent
        local_st = SymbolTable(parent=global_st)
        for (p_name, p_type), arg_val in zip(func.params, args):
            addr = self.memory.alloc(1)
            local_st.declare(p_name, p_type, addr, is_pointer=p_type.endswith('*'))
            self.memory.write(addr, arg_val)
        sub = _TokenListInterpreter(
            func.body_tokens, self.memory, local_st,
            self.functions, self.defines, self.trace, self.output_fn)
        try:
            sub.parse_statement()
        except ReturnException as e:
            return e.value
        return 0

    def parse_top_level(self):
        """解析頂層宣告：#define、函式定義、全域變數。"""
        if self.match(DEFINE):
            self.parse_define()
        elif self.match(INT, CHAR, VOID):
            self.parse_decl_or_func()
        else:
            # 互動模式：直接執行語句
            self.parse_statement()

    def parse_define(self):
        line = self.cur.line
        self.eat(DEFINE)
        name = self.eat(ID).value
        val  = self.eat(INTEGER).value
        if self.executing:
            self.defines[name] = val

    def parse_decl_or_func(self):
        """int/char/void 開頭，判斷是函式定義還是變數宣告。"""
        line     = self.cur.line
        ret_type = self._parse_type_spec()   # 'int' / 'char' / 'void' / 'int*' / 'char*'

        name = self.eat(ID).value

        if self.match(LPAREN):
            # 函式定義
            self._parse_func_def(ret_type, name, line)
        elif self.match(LBRACKET):
            # 陣列宣告
            self._parse_array_decl(ret_type, name, line)
        else:
            # 純量變數宣告
            self._parse_var_decl(ret_type, name, line)

    def _parse_type_spec(self):
        """解析型別（含指標 *），回傳型別字串。"""
        base = self.cur.value   # 'int' / 'char' / 'void'
        self.eat(self.cur.type)
        if self.match(MUL):
            self.eat(MUL)
            return base + '*'
        return base

    def _parse_func_def(self, ret_type, name, line):
        self.eat(LPAREN)
        params = []
        while not self.match(RPAREN):
            p_type = self._parse_type_spec()
            p_name = self.eat(ID).value
            params.append((p_name, p_type))
            if self.match(COMMA):
                self.eat(COMMA)
        self.eat(RPAREN)

        # 收集函式主體的 token（含 { }）
        body_tokens = self._collect_block_tokens()

        if self.executing:
            self.functions[name] = FuncDef(name, ret_type, params, body_tokens, line)

    def _collect_block_tokens(self):
        """把 { ... } 之間的 token 全部收集起來（含大括號）。"""
        tokens = []
        depth  = 0
        while not self.match(EOF):
            tok = self.cur
            if tok.type == LBRACE: depth += 1
            elif tok.type == RBRACE:
                depth -= 1
                tokens.append(tok)
                self.cur = self._next_token()
                if depth == 0:
                    break
                continue
            tokens.append(tok)
            self.cur = self._next_token()
        tokens.append(Token(EOF, None))
        return tokens

    def _parse_array_decl(self, type_, name, line):
        self.eat(LBRACKET)
        if self.match(INTEGER):
            size = self.eat(INTEGER).value
        elif self.match(ID):
            id_name = self.eat(ID).value
            if id_name in self.defines:
                size = self.defines[id_name]
            else:
                raise ParseError(f"Undefined constant: {id_name}", self.cur.line)
        else:
            raise ParseError("Expected array size (integer constant)", self.cur.line)
        self.eat(RBRACKET)
        init_val = None
        if self.match(ASSIGN):
            self.eat(ASSIGN)
            init_val = self.parse_expr()
        self.eat(SEMICOLON)
        if self.executing:
            addr = self.memory.alloc(size)
            base_type = type_.rstrip('*')
            self.symtable.declare(name, base_type, addr, size=size, is_array=True)

    def _parse_var_decl(self, type_, name, line, local_symtable=None):
        is_ptr = type_.endswith('*')
        init_val = None
        if self.match(ASSIGN):
            self.eat(ASSIGN)
            init_val = self.parse_expr()
        self.eat(SEMICOLON)
        if self.executing:
            st = local_symtable or self.symtable
            addr = self.memory.alloc(1)
            st.declare(name, type_, addr, is_pointer=is_ptr)
            if init_val is not None:
                self.memory.write(addr, init_val)

    # ── 語句解析 ──────────────────────────────────────────────────
    def parse_statement(self, local_st=None):
        line = self.cur.line
        if self.trace and self.executing:
            self.output_fn(f'[line {line}] {self._cur_stmt_preview()}')

        if self.match(LBRACE):
            self.parse_block(local_st)
        elif self.match(INT, CHAR):
            self._stmt_local_decl(local_st)
        elif self.match(IF):
            self._stmt_if(local_st)
        elif self.match(WHILE):
            self._stmt_while(local_st)
        elif self.match(FOR):
            self._stmt_for(local_st)
        elif self.match(DO):
            self._stmt_do_while(local_st)
        elif self.match(BREAK):
            self.eat(BREAK); self.eat(SEMICOLON)
            if self.executing: raise BreakException()
        elif self.match(CONTINUE):
            self.eat(CONTINUE); self.eat(SEMICOLON)
            if self.executing: raise ContinueException()
        elif self.match(RETURN):
            self._stmt_return()
        elif self.match(SEMICOLON):
            self.eat(SEMICOLON)   # 空語句
        elif self.match(MUL):
            # *ptr = val;  指標寫入
            self._stmt_ptr_assign()
        else:
            self.parse_expr_stmt()

    def _cur_stmt_preview(self):
        """回傳目前 token 的簡短預覽（用於 TRACE）。"""
        return f'{self.cur.value}'

    def parse_block(self, outer_st=None):
        self.eat(LBRACE)
        block_st = SymbolTable(parent=outer_st or self.symtable)
        old_st = self.symtable
        self.symtable = block_st   # 切換到 block 作用域
        while not self.match(RBRACE) and not self.match(EOF):
            self.parse_statement(block_st)
        self.symtable = old_st     # 還原
        self.eat(RBRACE)

    def _stmt_local_decl(self, local_st):
        line     = self.cur.line
        type_str = self._parse_type_spec()
        name     = self.eat(ID).value
        st       = local_st or self.symtable
        if self.match(LBRACKET):
            self.eat(LBRACKET)
            if self.match(INTEGER):
                size = self.eat(INTEGER).value
            elif self.match(ID):
                id_name = self.eat(ID).value
                size = self.defines.get(id_name, 0)
                if size == 0:
                    raise ParseError(f"Undefined constant: {id_name}", self.cur.line)
            else:
                raise ParseError("Expected array size", self.cur.line)
            self.eat(RBRACKET)
            self.eat(SEMICOLON)
            if self.executing:
                addr = self.memory.alloc(size)
                st.declare(name, type_str.rstrip('*'), addr, size=size, is_array=True)
        else:
            self._parse_var_decl(type_str, name, line, local_symtable=st)

    def _stmt_if(self, local_st):
        self.eat(IF); self.eat(LPAREN)
        cond = self.parse_expr()
        self.eat(RPAREN)
        old_exec = self.executing
        # then
        self.executing = old_exec and bool(cond)
        self.parse_statement(local_st)
        # else
        if self.match(ELSE):
            self.eat(ELSE)
            self.executing = old_exec and not bool(cond)
            self.parse_statement(local_st)
        self.executing = old_exec

    def _stmt_while(self, local_st):
        self.eat(WHILE)
        # 記下 while 起點的 token 串（需要能重複求值條件）
        saved_tokens = self._snapshot_until_end_of_loop()
        if not self.executing:
            return

        while True:
            sub = self._make_sub_interpreter(saved_tokens)
            sub.eat(LPAREN)
            cond = sub.parse_expr()
            sub.eat(RPAREN)
            if not cond:
                # 跳過 body
                self_skip = self._make_sub_interpreter(saved_tokens)
                self_skip.eat(LPAREN); self_skip.parse_expr(); self_skip.eat(RPAREN)
                self_skip.executing = False
                self_skip.parse_statement()
                break
            try:
                sub.parse_statement()
            except BreakException:
                break
            except ContinueException:
                continue

    def _stmt_for(self, local_st):
        self.eat(FOR)
        saved = self._snapshot_for()
        if not self.executing:
            return

        # 執行 init
        init_sub = self._make_sub_interpreter(saved['init'])
        init_sub.parse_statement()

        while True:
            # 求值條件
            cond_sub = self._make_sub_interpreter(saved['cond'])
            cond = cond_sub.parse_expr()
            if not cond:
                break
            # 執行 body
            try:
                body_sub = self._make_sub_interpreter(saved['body'])
                body_sub.parse_statement()
            except BreakException:
                break
            except ContinueException:
                pass
            # 執行 iter
            iter_sub = self._make_sub_interpreter(saved['iter'])
            iter_sub.parse_expr_stmt()

    def _stmt_do_while(self, local_st):
        self.eat(DO)
        saved_body  = self._snapshot_block()
        self.eat(WHILE); self.eat(LPAREN)
        saved_cond_tokens = []
        depth = 1
        while not self.match(EOF):
            tok = self.cur
            self.cur = self._next_token()
            if tok.type == RPAREN:
                depth -= 1
                if depth == 0: break
            elif tok.type == LPAREN:
                depth += 1
            saved_cond_tokens.append(tok)
        saved_cond_tokens.append(Token(EOF, None))
        self.eat(SEMICOLON)

        if not self.executing:
            return

        while True:
            try:
                body_sub = self._make_sub_interpreter(saved_body)
                body_sub.parse_statement()
            except BreakException:
                break
            except ContinueException:
                pass
            cond_sub = self._make_sub_interpreter(saved_cond_tokens)
            if not cond_sub.parse_expr():
                break

    def _stmt_return(self):
        self.eat(RETURN)
        val = 0
        if not self.match(SEMICOLON):
            val = self.parse_expr()
        self.eat(SEMICOLON)
        if self.executing:
            raise ReturnException(val)

    def _stmt_ptr_assign(self):
        """*ptr = expr;"""
        self.eat(MUL)
        name = self.eat(ID).value
        # 可能有陣列索引：*(ptr + i) 不支援，只支援 *name
        op = self.cur.type
        if op in (ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, MUL_ASSIGN, DIV_ASSIGN, MOD_ASSIGN):
            self.eat(op)
            rhs = self.parse_expr()
            self.eat(SEMICOLON)
            if self.executing:
                sym = self.symtable.lookup(name)
                if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                ptr_addr = self.memory.read(sym.addr)
                if op == ASSIGN: val = rhs
                else:
                    old = self.memory.read(ptr_addr)
                    val = {PLUS_ASSIGN:old+rhs,MINUS_ASSIGN:old-rhs,
                           MUL_ASSIGN:old*rhs}.get(op, rhs)
                self.memory.write(ptr_addr, val)
        else:
            # 當表達式語句處理
            val = self.memory.read(self.memory.read(self.symtable.lookup(name).addr)) if self.executing else 0
            self.eat(SEMICOLON)

    def parse_expr_stmt(self):
        self.parse_expr()
        self.eat(SEMICOLON)

    # ── snapshot 工具（把剩餘 token 複製給子解譯器用）──────────────
    def _drain_tokens(self):
        """把目前 lexer 剩餘的 token 全部讀出來。"""
        tokens = [self.cur]
        while tokens[-1].type != EOF:
            tokens.append(self._next_token())
        self.cur = Token(EOF, None)
        return tokens

    def _snapshot_block(self):
        """收集一個完整的 { ... } block token 串（含大括號）。"""
        tokens = []
        depth  = 0
        while not self.match(EOF):
            tok = self.cur
            self.cur = self._next_token()
            if tok.type == LBRACE: depth += 1
            elif tok.type == RBRACE:
                depth -= 1
                tokens.append(tok)
                if depth == 0: break
                continue
            tokens.append(tok)
        tokens.append(Token(EOF, None))
        return tokens

    def _snapshot_until_end_of_loop(self):
        """收集 while 的 (cond) body 部分的 token 串。"""
        tokens = []
        # 先讀 (cond)
        depth = 0
        while not self.match(EOF):
            tok = self.cur
            self.cur = self._next_token()
            tokens.append(tok)
            if tok.type == LPAREN: depth += 1
            elif tok.type == RPAREN:
                depth -= 1
                if depth == 0: break
        # 再讀 body（一個語句或 block）
        body_tokens = self._snapshot_one_stmt()
        tokens.extend(body_tokens)
        tokens.append(Token(EOF, None))
        return tokens

    def _snapshot_one_stmt(self):
        """收集一個語句（可能是 block 或單行）。"""
        tokens = []
        if self.match(LBRACE):
            depth = 0
            while not self.match(EOF):
                tok = self.cur
                self.cur = self._next_token()
                if tok.type == LBRACE: depth += 1
                elif tok.type == RBRACE:
                    depth -= 1
                    tokens.append(tok)
                    if depth == 0: break
                    continue
                tokens.append(tok)
        else:
            while not self.match(EOF):
                tok = self.cur
                self.cur = self._next_token()
                tokens.append(tok)
                if tok.type == SEMICOLON: break
        return tokens

    def _snapshot_for(self):
        """收集 for 的 (init; cond; iter) body，分別回傳。"""
        self.eat(LPAREN)
        init_tokens = []
        # init（到第一個 ;）
        while not self.match(EOF) and not self.match(SEMICOLON):
            init_tokens.append(self.cur)
            self.cur = self._next_token()
        if self.match(SEMICOLON):
            init_tokens.append(self.cur)   # 包含 ;
            self.cur = self._next_token()
        init_tokens.append(Token(EOF, None))

        # cond（到第二個 ;）
        cond_tokens = []
        while not self.match(EOF) and not self.match(SEMICOLON):
            cond_tokens.append(self.cur)
            self.cur = self._next_token()
        self.eat(SEMICOLON)
        cond_tokens.append(Token(EOF, None))

        # iter（到 )）
        iter_tokens = []
        depth = 1
        while not self.match(EOF):
            tok = self.cur
            self.cur = self._next_token()
            if tok.type == LPAREN: depth += 1
            elif tok.type == RPAREN:
                depth -= 1
                if depth == 0: break
            iter_tokens.append(tok)
        iter_tokens.append(Token(SEMICOLON, ';'))
        iter_tokens.append(Token(EOF, None))

        # body
        body_tokens = self._snapshot_one_stmt()
        body_tokens.append(Token(EOF, None))

        return {'init': init_tokens, 'cond': cond_tokens,
                'iter': iter_tokens, 'body': body_tokens}

    def _make_sub_interpreter(self, token_list):
        """建立一個子解譯器，共用同一塊記憶體與符號表。"""
        sub = _TokenListInterpreter(
            token_list, self.memory, self.symtable,
            self.functions, self.defines, self.trace, self.output_fn)
        return sub

    # ── 表達式解析（遞迴下降，依優先順序由低到高）────────────────
    def parse_expr(self):
        """最低優先：指定運算子（右結合）。
        
        指定判斷策略：先解析 logical_or，若結果是單純 lval 且下一個 token 是指定運算子，
        才執行指定；否則直接回傳右值。
        """
        return self._parse_assign()

    def _parse_assign(self):
        # 先記住目前位置，嘗試看是否為指定語句
        # 策略：解析左側（可能是 ID 或 ID[expr]），再看是否有 = 系列運算子
        if self.match(ID):
            name = self.cur.value
            name_line = self.cur.line
            self.eat(ID)
            
            # 函式呼叫 → 不是 lval
            if self.match(LPAREN):
                val = self._call_func(name, name_line)
                # 繼續解析後面可能的運算
                return self._continue_lor(val)
            
            # 陣列元素
            if self.match(LBRACKET):
                self.eat(LBRACKET)
                idx = self._parse_assign()
                self.eat(RBRACKET)
                if self.match(ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN,
                               MUL_ASSIGN, DIV_ASSIGN, MOD_ASSIGN):
                    return self._do_assign({'kind':'array','name':name,'idx':idx})
                # 不是指定，當右值繼續
                val = self._lval_read({'kind':'array','name':name,'idx':idx}) if self.executing else 0
                return self._continue_lor(val)
            
            # 普通變數
            if self.match(ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN,
                           MUL_ASSIGN, DIV_ASSIGN, MOD_ASSIGN):
                return self._do_assign({'kind':'var','name':name})
            
            # 不是指定，當右值繼續（先讀變數值，再接後面運算）
            if self.match(INC):
                self.eat(INC)
                if self.executing:
                    sym = self.symtable.lookup(name)
                    if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                    v = self.memory.read(sym.addr)
                    self.memory.write(sym.addr, v+1)
                    return self._continue_lor(v)
                return 0
            if self.match(DEC):
                self.eat(DEC)
                if self.executing:
                    sym = self.symtable.lookup(name)
                    if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                    v = self.memory.read(sym.addr)
                    self.memory.write(sym.addr, v-1)
                    return self._continue_lor(v)
                return 0
            
            # 純右值
            if self.executing:
                if name in self.defines:
                    val = self.defines[name]
                else:
                    sym = self.symtable.lookup(name)
                    if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                    # 陣列名稱 → 回傳首地址（模擬 C 的 array decay）
                    if sym.is_array:
                        val = sym.addr
                    else:
                        val = self.memory.read(sym.addr)
            else:
                val = 0
            return self._continue_lor(val)
        
        # 非 ID 開頭，直接走 lor
        return self.parse_lor()

    def _do_assign(self, lval_info):
        op = self.cur.type
        self.eat(op)
        rhs = self._parse_assign()
        if self.executing:
            old = self._lval_read(lval_info)
            if op == ASSIGN:         val = rhs
            elif op == PLUS_ASSIGN:  val = old + rhs
            elif op == MINUS_ASSIGN: val = old - rhs
            elif op == MUL_ASSIGN:   val = old * rhs
            elif op == DIV_ASSIGN:
                if rhs == 0: raise RuntimeError_("division by zero")
                val = int(old / rhs)
            elif op == MOD_ASSIGN:
                if rhs == 0: raise RuntimeError_("modulo by zero")
                val = old % rhs
            else: val = rhs
            self._lval_write(lval_info, val)
            return val
        return 0

    def _continue_lor(self, left_val):
        """已有一個左值，繼續解析後面可能的雙元運算子（lor 層以下）。"""
        # 模擬從 parse_lor 開始，但左側已有值
        return self._continue_land(left_val)

    def _continue_land(self, left):
        left = self._continue_bor(left)
        while self.match(AND):
            self.eat(AND)
            if self.executing and not left:
                self._skip_bor(); continue
            right = self.parse_bor()
            if self.executing: left = 1 if (left and right) else 0
        # lor
        while self.match(OR):
            self.eat(OR)
            if self.executing and left:
                self._skip_bor(); continue
            right = self.parse_land()
            if self.executing: left = 1 if (left or right) else 0
        return left

    def _continue_bor(self, left):
        left = self._continue_xor(left)
        while self.match(PIPE):
            self.eat(PIPE); right = self.parse_xor()
            if self.executing: left = left | right
        return left

    def _continue_xor(self, left):
        left = self._continue_band(left)
        while self.match(CARET):
            self.eat(CARET); right = self.parse_band()
            if self.executing: left = left ^ right
        return left

    def _continue_band(self, left):
        left = self._continue_eq(left)
        while self.match(AMP):
            self.eat(AMP); right = self.parse_eq()
            if self.executing: left = left & right
        return left

    def _continue_eq(self, left):
        left = self._continue_rel(left)
        while self.match(EQ, NE):
            op = self.cur.type; self.eat(op); right = self.parse_rel()
            if self.executing:
                left = (1 if left == right else 0) if op == EQ else (1 if left != right else 0)
        return left

    def _continue_rel(self, left):
        left = self._continue_shift(left)
        while self.match(LT, GT, LE, GE):
            op = self.cur.type; self.eat(op); right = self.parse_shift()
            if self.executing:
                left = {LT:left<right,GT:left>right,LE:left<=right,GE:left>=right}[op]
                left = 1 if left else 0
        return left

    def _continue_shift(self, left):
        left = self._continue_add(left)
        while self.match(LSHIFT, RSHIFT):
            op = self.cur.type; self.eat(op); right = self.parse_add()
            if self.executing:
                left = (left << right) if op == LSHIFT else (left >> right)
        return left

    def _continue_add(self, left):
        left = self._continue_mul(left)
        while self.match(PLUS, MINUS):
            op = self.cur.type; self.eat(op); right = self.parse_mul()
            if self.executing:
                left = left + right if op == PLUS else left - right
        return left

    def _continue_mul(self, left):
        while self.match(MUL, DIV, MOD):
            op = self.cur.type; self.eat(op); right = self.parse_unary()
            if self.executing:
                if op == MUL: left = left * right
                elif op == DIV:
                    if right == 0: raise RuntimeError_("division by zero")
                    left = int(left / right)
                else:
                    if right == 0: raise RuntimeError_("modulo by zero")
                    left = left % right
        return left

    def _skip_bor(self):
        """短路求值時跳過一個 bor 層（不執行）。"""
        old = self.executing
        self.executing = False
        self.parse_bor()
        self.executing = old

    def _parse_lor_from_cur(self):
        return self.parse_lor()

    def parse_lor(self):
        left = self.parse_land()
        while self.match(OR):
            self.eat(OR)
            if self.executing:
                if left: self.parse_land(); continue   # 短路
            right = self.parse_land()
            if self.executing: left = 1 if (left or right) else 0
        return left

    def parse_land(self):
        left = self.parse_bor()
        while self.match(AND):
            self.eat(AND)
            if self.executing:
                if not left: self.parse_bor(); continue  # 短路
            right = self.parse_bor()
            if self.executing: left = 1 if (left and right) else 0
        return left

    def parse_bor(self):
        left = self.parse_xor()
        while self.match(PIPE):
            self.eat(PIPE); right = self.parse_xor()
            if self.executing: left = left | right
        return left

    def parse_xor(self):
        left = self.parse_band()
        while self.match(CARET):
            self.eat(CARET); right = self.parse_band()
            if self.executing: left = left ^ right
        return left

    def parse_band(self):
        left = self.parse_eq()
        while self.match(AMP):
            self.eat(AMP); right = self.parse_eq()
            if self.executing: left = left & right
        return left

    def parse_eq(self):
        left = self.parse_rel()
        while self.match(EQ, NE):
            op = self.cur.type; self.eat(op); right = self.parse_rel()
            if self.executing:
                left = (1 if left == right else 0) if op == EQ else (1 if left != right else 0)
        return left

    def parse_rel(self):
        left = self.parse_shift()
        while self.match(LT, GT, LE, GE):
            op = self.cur.type; self.eat(op); right = self.parse_shift()
            if self.executing:
                left = {LT: left < right, GT: left > right,
                        LE: left <= right, GE: left >= right}[op]
                left = 1 if left else 0
        return left

    def parse_shift(self):
        left = self.parse_add()
        while self.match(LSHIFT, RSHIFT):
            op = self.cur.type; self.eat(op); right = self.parse_add()
            if self.executing:
                left = (left << right) if op == LSHIFT else (left >> right)
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.match(PLUS, MINUS):
            op = self.cur.type; self.eat(op); right = self.parse_mul()
            if self.executing:
                left = left + right if op == PLUS else left - right
        return left

    def parse_mul(self):
        left = self.parse_unary()
        while self.match(MUL, DIV, MOD):
            op = self.cur.type; self.eat(op); right = self.parse_unary()
            if self.executing:
                if op == MUL: left = left * right
                elif op == DIV:
                    if right == 0: raise RuntimeError_("division by zero")
                    left = int(left / right)
                else:
                    if right == 0: raise RuntimeError_("modulo by zero")
                    left = left % right
        return left

    def parse_unary(self):
        if self.match(MINUS):
            self.eat(MINUS); val = self.parse_unary()
            return -val if self.executing else 0
        if self.match(NOT):
            self.eat(NOT); val = self.parse_unary()
            return (0 if val else 1) if self.executing else 0
        if self.match(TILDE):
            self.eat(TILDE); val = self.parse_unary()
            return (~val) if self.executing else 0
        if self.match(INC):
            self.eat(INC)
            lval = self._try_parse_lval()
            if lval and self.executing:
                v = self._lval_read(lval) + 1
                self._lval_write(lval, v); return v
            return 0
        if self.match(DEC):
            self.eat(DEC)
            lval = self._try_parse_lval()
            if lval and self.executing:
                v = self._lval_read(lval) - 1
                self._lval_write(lval, v); return v
            return 0
        # 取址 &var
        if self.match(AMP):
            self.eat(AMP)
            name = self.eat(ID).value
            if self.match(LBRACKET):
                self.eat(LBRACKET); idx = self.parse_expr(); self.eat(RBRACKET)
                if self.executing:
                    sym = self.symtable.lookup(name)
                    if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                    # 指標參數：基底位址存在 sym.addr 裡，需要先讀出來再加 idx
                    if sym.is_pointer:
                        base_addr = self.memory.read(sym.addr)
                        return base_addr + idx
                    return sym.addr + idx
                return 0
            if self.executing:
                sym = self.symtable.lookup(name)
                if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                return sym.addr
            return 0
        # 指標取值 *ptr
        if self.match(MUL):
            self.eat(MUL); name = self.eat(ID).value
            if self.executing:
                sym = self.symtable.lookup(name)
                if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                ptr_addr = self.memory.read(sym.addr)
                return self.memory.read(ptr_addr)
            return 0
        return self.parse_postfix()

    def parse_postfix(self):
        val = self.parse_primary()
        # 後綴 ++ --（簡化：先回傳舊值再改）
        if self.match(INC):
            self.eat(INC); return val   # 已在 primary 讀過，這裡只吃掉符號
        if self.match(DEC):
            self.eat(DEC); return val
        return val

    def parse_primary(self):
        tok = self.cur

        # 整數常數
        if self.match(INTEGER):
            self.eat(INTEGER)
            return tok.value if self.executing else 0

        # 字元常數
        if self.match(CHAR_LIT):
            self.eat(CHAR_LIT)
            return tok.value if self.executing else 0

        # 字串常數（只在函式呼叫參數中出現，回傳位址）
        if self.match(STRING):
            self.eat(STRING)
            if self.executing:
                s = tok.value + '\0'
                addr = self.memory.alloc(len(s))
                for i, c in enumerate(s):
                    self.memory.write(addr + i, ord(c))
                return addr
            return 0

        # 括號
        if self.match(LPAREN):
            self.eat(LPAREN); val = self.parse_expr(); self.eat(RPAREN)
            return val

        # 識別字（變數 / 函式呼叫 / #define）
        if self.match(ID):
            name = self.eat(ID).value

            # #define 替換
            if name in self.defines:
                return self.defines[name] if self.executing else 0

            # 函式呼叫
            if self.match(LPAREN):
                return self._call_func(name, tok.line)

            # 陣列索引
            if self.match(LBRACKET):
                self.eat(LBRACKET); idx = self.parse_expr(); self.eat(RBRACKET)
                if self.executing:
                    sym = self.symtable.lookup(name)
                    if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                    # 指標參數：base_addr + idx
                    if sym.is_pointer:
                        base_addr = self.memory.read(sym.addr)
                        return self.memory.read(base_addr + idx)
                    if idx < 0 or idx >= sym.size:
                        raise RuntimeError_(f"Array index out of bounds (index {idx}, size {sym.size})")
                    return self.memory.read(sym.addr + idx)
                return 0

            # 普通變數
            if self.executing:
                sym = self.symtable.lookup(name)
                if sym is None: raise RuntimeError_(f"Undefined variable: {name}")
                return self.memory.read(sym.addr)
            return 0

        raise ParseError(f"Unexpected token: {tok.type} ({tok.value!r})", tok.line)

    # ── lval 輔助（解析左值以支援指定運算）──────────────────────
    def _try_parse_lval(self):
        """嘗試解析一個左值，回傳 lval_info dict 或 None。"""
        if not self.match(ID):
            return None
        name = self.eat(ID).value

        # 排除函式呼叫
        if self.match(LPAREN):
            # 不是左值，退回處理：先呼叫函式再當右值
            val = self._call_func(name, self.cur.line)
            # 包成假的 lval_info（不可寫入）
            return {'kind': 'rval', 'value': val}

        # 陣列元素
        if self.match(LBRACKET):
            self.eat(LBRACKET); idx = self.parse_expr(); self.eat(RBRACKET)
            return {'kind': 'array', 'name': name, 'idx': idx}

        # 指標取值 *name（已在 unary 處理，這裡不重複）
        return {'kind': 'var', 'name': name}

    def _lval_read(self, info):
        if info['kind'] == 'rval': return info['value']
        if info['kind'] == 'var':
            sym = self.symtable.lookup(info['name'])
            if sym is None: raise RuntimeError_(f"Undefined variable: {info['name']}")
            return self.memory.read(sym.addr)
        if info['kind'] == 'array':
            sym = self.symtable.lookup(info['name'])
            if sym is None: raise RuntimeError_(f"Undefined variable: {info['name']}")
            idx = info['idx']
            # 指標參數（is_pointer）：addr 存的是基底位址，直接用 base_addr + idx
            if sym.is_pointer:
                base_addr = self.memory.read(sym.addr)
                return self.memory.read(base_addr + idx)
            if idx < 0 or idx >= sym.size:
                raise RuntimeError_(f"Array index out of bounds (index {idx}, size {sym.size})")
            return self.memory.read(sym.addr + idx)
        return 0

    def _lval_write(self, info, val):
        if info['kind'] == 'rval': return
        if info['kind'] == 'var':
            sym = self.symtable.lookup(info['name'])
            if sym is None: raise RuntimeError_(f"Undefined variable: {info['name']}")
            self.memory.write(sym.addr, val)
        elif info['kind'] == 'array':
            sym = self.symtable.lookup(info['name'])
            if sym is None: raise RuntimeError_(f"Undefined variable: {info['name']}")
            idx = info['idx']
            # 指標參數（is_pointer）：addr 存的是基底位址，直接用 base_addr + idx
            if sym.is_pointer:
                base_addr = self.memory.read(sym.addr)
                self.memory.write(base_addr + idx, val)
                return
            if idx < 0 or idx >= sym.size:
                raise RuntimeError_(f"Array index out of bounds (index {idx}, size {sym.size})")
            self.memory.write(sym.addr + idx, val)

    def _lval_as_rval(self, info):
        return self._lval_read(info) if self.executing else 0

    # ── 函式呼叫 ──────────────────────────────────────────────────
    def _call_func(self, name, line):
        self.eat(LPAREN)
        args = []
        while not self.match(RPAREN):
            args.append(self.parse_expr())
            if self.match(COMMA): self.eat(COMMA)
        self.eat(RPAREN)

        if not self.executing:
            return 0

        # 內建函式
        from builtin import call_builtin, is_builtin
        if is_builtin(name):
            return call_builtin(name, args, self.memory, self.output_fn)

        if name not in self.functions:
            raise RuntimeError_(f"Undefined function: {name}", line)
        func = self.functions[name]

        return self._invoke_func(name, args, caller_symtable=self.symtable)

    def get_vars(self):
        result = []
        for sym in self.symtable.all_symbols():
            if sym.is_array:
                vals = [self.memory.read(sym.addr + i) for i in range(min(sym.size, 10))]
                result.append((sym.name, sym.type_, vals, sym.size))
            else:
                result.append((sym.name, sym.type_, self.memory.read(sym.addr), 1))
        return result

    def get_funcs(self):
        result = []
        for name, f in self.functions.items():
            params_str = ', '.join(f'{t} {n}' for n, t in f.params)
            result.append((name, f.ret_type, params_str, f.start_line))
        return result


class _TokenListInterpreter(Interpreter):
    def __init__(self, token_list, memory, symtable, functions, defines, trace, output_fn):
        self._token_list = token_list
        self._tok_pos    = 0
        self.memory      = memory
        self.symtable    = symtable
        self.functions   = functions
        self.defines     = defines
        self.trace       = trace
        self.output_fn   = output_fn
        self.executing   = True
        self.cur         = token_list[0] if token_list else Token(EOF, None)

    def _next_token(self):
        self._tok_pos += 1
        return self._token_list[self._tok_pos] if self._tok_pos < len(self._token_list) else Token(EOF, None)

    def eat(self, expected_type):
        if self.cur.type != expected_type:
            raise ParseError(
                f"Expected {expected_type}, got {self.cur.type} ({self.cur.value!r})",
                self.cur.line)
        tok = self.cur
        self.cur = self._next_token()
        return tok

    def _make_sub_interpreter(self, token_list):
        return _TokenListInterpreter(
            token_list, self.memory, self.symtable,
            self.functions, self.defines, self.trace, self.output_fn)

def make_interpreter(source: str, memory=None, global_st=None,
                     functions=None, defines=None,
                     trace=False, output_fn=None) -> Interpreter:
    return Interpreter(source, memory, global_st, functions, defines, trace, output_fn)

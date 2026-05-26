import os
from interpreter import Interpreter

if __name__ == '__main__':
    print("--- 開始進行 Small-C 10大作業測試集自動化驗證 ---\n")
    
    # 測試 1 到 10
    for i in range(1, 11):
        sc_file = f"tests/test{i}.sc"
        expected_file = f"tests/test{i}.expected"
        
        if not os.path.exists(sc_file):
            continue
            
        print(f"========================================")
        print(f" 正在測試：[Test {i}] -> {sc_file}")
        
        with open(sc_file, 'r', encoding='utf-8') as f:
            code = f.read()
            
        with open(expected_file, 'r', encoding='utf-8') as f:
            expected = f.read().strip()
            
        errors_captured = []
        def catch_output(msg):
            errors_captured.append(msg)
            
        interp = Interpreter(output_fn=catch_output)
        interp.run_program(code, auto_run_main=False)
        
        vars_list = interp.get_vars()
        funcs_list = interp.get_funcs()
        
        if errors_captured and ("zero" in "".join(errors_captured).lower() or "boundary" in "".join(errors_captured).lower() or "error" in "".join(errors_captured).lower()):
            actual_result = f"Runtime Error: {errors_captured[0]}"
        else:
            actual_result = f"變數表: {vars_list}"
            if funcs_list:
                actual_result += f" | 函式表: {funcs_list}"
            
        print(f"預期參考: {expected}")
        print(f"實際結果: {actual_result}")
        print("驗證完成")
        print(f"========================================\n")

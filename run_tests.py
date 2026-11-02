import os
from parser import parse_source
from interpreter import Interpreter

def run_all_tests():
    test_dir = "tests"
    
    # Fallback if tests are in the current working directory
    if not os.path.exists(test_dir):
        os.makedirs(test_dir, exist_ok=True)
        print(f"Created '{test_dir}' directory. Place your test files there!")
        return

    test_files = [f for f in os.listdir(test_dir) if f.endswith(".txt") or f.endswith(".ox")]
    
    if not test_files:
        print(f"No test files found in '{test_dir}/'. Add at least 5 test files.")
        return

    print("=" * 50)
    print("RUNNING ONYX TEST SUITE")
    print("=" * 50)

    for file_name in sorted(test_files):
        file_path = os.path.join(test_dir, file_name)
        print(f"\n--- Running Test: {file_name} ---")
        
        with open(file_path, "r") as f:
            source_code = f.read()
            
        print("Source Code:")
        print(source_code.strip())
        print("Output:")
        
        try:
            ast = parse_source(source_code)
            interpreter = Interpreter()
            output_buffer = interpreter.interpret(ast)
            print("Successfully executed. Output buffer:", output_buffer)
        except Exception as e:
            print(f"Runtime/Parser Error Caught: {e}")

if __name__ == "__main__":
    run_all_tests()
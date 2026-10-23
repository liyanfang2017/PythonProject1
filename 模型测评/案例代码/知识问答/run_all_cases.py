import os
import sys

def main():
    print("开始运行知识问答评估案例...")
    
    # 运行 fact_check 案例
    exit_code = os.system("python3 case_fact_check.py")
    
    if exit_code == 0:
        print("\n所有案例执行完成。")
    else:
        print("\n执行过程中出现错误。")

if __name__ == "__main__":
    main()


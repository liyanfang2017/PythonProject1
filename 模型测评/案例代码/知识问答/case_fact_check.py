# -*- coding: utf-8 -*-
"""
案例：事实性知识问答评估
评估模型对历史、科学等事实性知识的掌握程度，重点检测幻觉。
"""

import json
from knowledge_judge import KnowledgeJudge

def main():
    print("=" * 60)
    print("案例：事实性知识问答评估 (Fact Checking)")
    print("=" * 60)
    
    judge = KnowledgeJudge(use_mock=True)
    
    # 案例1: 历史知识 (准确回答)
    case1 = {
        "test_case_id": "HIST_001",
        "question": "第二次世界大战是哪一年结束的？主要参战国有哪些？",
        "model_output": "第二次世界大战于1945年结束。主要参战国分为同盟国（如美国、苏联、英国、中国）和轴心国（如德国、日本、意大利）。",
        "required_facts": [
            "1945",
            "美国|USA", "苏联|USSR", "英国|UK", "中国|China", 
            "德国|Germany", "日本|Japan"
        ],
        "negative_keywords": ["1944", "1946", "法国属于轴心国"]
    }
    
    # 案例2: 科学知识 (包含幻觉)
    case2 = {
        "test_case_id": "SCI_001",
        "question": "请解释为什么天空是蓝色的？",
        "model_output": "天空之所以是蓝色的，是因为大气层中的氧气分子吸收了红光，反射了蓝光。这被称为廷德尔效应。",
        "required_facts": ["散射", "瑞利散射|Rayleigh"],
        "negative_keywords": ["反射", "吸收", "氧气分子", "廷德尔效应"] # 这里模型回答错误，把瑞利散射说成了反射/廷德尔效应
    }
    
    cases = [case1, case2]
    
    for case in cases:
        print(f"\n[测试用例 {case['test_case_id']}]")
        print(f"问题: {case['question']}")
        print(f"回答: {case['model_output']}")
        print("-" * 30)
        
        result = judge.evaluate(case)
        
        print(f"综合评分: {result['final_verdict']['overall_score']} ({result['final_verdict']['grade']})")
        print("事实核查:")
        for fact in result['reasoning']['facts_check']:
            status = "✓" if fact['met'] else "✗"
            print(f"  {status} {fact['fact']}")
            
        if result['reasoning']['hallucinations_found']:
            print("⚠️ 发现幻觉/错误:")
            for h in result['reasoning']['hallucinations_found']:
                print(f"  - {h}")
        else:
            print("✓ 未发现明显幻觉")
            
        # 保存结果
        with open(f"{case['test_case_id']}_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()


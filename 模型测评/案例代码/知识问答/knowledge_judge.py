# -*- coding: utf-8 -*-
"""
AI裁判模型 - 知识问答评估核心类
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# 尝试加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 处理openai导入
try:
    from openai import OpenAI  # type: ignore
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None  # type: ignore
    print("警告: 未安装openai库，将使用模拟模式")


class KnowledgeJudge:
    """知识问答评估的AI裁判模型"""
    
    def __init__(
        self, 
        judge_model: str = "gpt-4", 
        api_key: Optional[str] = None,
        use_mock: bool = True
    ):
        self.judge_model = judge_model
        self.use_mock = use_mock
        
        if use_mock or not HAS_OPENAI:
            self.client = None
            if not use_mock:
                print("未检测到OpenAI库或API Key，强制启用Mock模式")
                self.use_mock = True
        else:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("未提供API Key，强制启用Mock模式")
                self.use_mock = True
                self.client = None
            else:
                self.client = OpenAI(api_key=api_key)
    
    def evaluate(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """执行评估"""
        if self.use_mock:
            return self._mock_evaluate(test_case)
        
        # 真实API调用逻辑 (简化版，类似指令遵循)
        return self._api_evaluate(test_case)

    def _mock_evaluate(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock评估逻辑：基于关键词匹配的事实核查
        """
        question = test_case.get("question", "")
        model_output = test_case.get("model_output", "")
        required_facts = test_case.get("required_facts", [])  # 必需的事实关键词
        negative_keywords = test_case.get("negative_keywords", [])  # 幻觉/错误关键词
        
        # 1. 事实核查 (Accuracy & Coverage)
        facts_met = []
        output_lower = model_output.lower()
        
        for fact in required_facts:
            # 支持多选一： "A|B" 表示包含A或B均可
            keywords = fact.lower().split("|")
            is_met = any(k.strip() in output_lower for k in keywords)
            facts_met.append({
                "fact": fact,
                "met": is_met
            })
            
        fact_coverage = sum(1 for f in facts_met if f["met"]) / len(facts_met) if required_facts else 1.0
        
        # 2. 幻觉检测 (Hallucination)
        hallucinations = []
        for kw in negative_keywords:
            if kw.lower() in output_lower:
                hallucinations.append(kw)
        
        has_hallucination = len(hallucinations) > 0
        
        # 3. 完整性检查 (Completeness)
        # 简单根据长度判断，假设回答长度应与问题复杂度相关，这里简化为 > 20字符
        is_complete = len(model_output) > 20
        
        # 计算得分
        # 准确性 (40%): 事实覆盖率 * (1 - 幻觉惩罚)
        accuracy_score = fact_coverage * 5.0
        if has_hallucination:
            accuracy_score = max(1.0, accuracy_score - 2.5) # 发现幻觉重罚
            
        # 覆盖度 (30%): 与准确性强相关，这里简化为事实覆盖率
        coverage_score = fact_coverage * 5.0
        
        # 清晰度 (20%): 默认给高分，除非太短
        clarity_score = 5.0 if len(model_output) > 50 else 3.0
        
        # 幻觉 (10%): 
        hallucination_score = 1.0 if has_hallucination else 5.0
        
        # 综合评分
        overall_score = (accuracy_score * 0.4) + (coverage_score * 0.3) + (clarity_score * 0.2) + (hallucination_score * 0.1)
        
        # 生成评级
        if overall_score >= 4.5: grade = "优秀"
        elif overall_score >= 4.0: grade = "良好"
        elif overall_score >= 3.0: grade = "中等"
        else: grade = "较差"
        
        return {
            "test_case_id": test_case.get("test_case_id", "UNKNOWN"),
            "evaluation_timestamp": datetime.now().isoformat(),
            "judge_model": "KnowledgeMockJudge",
            "scores": {
                "accuracy": round(accuracy_score, 1),
                "coverage": round(coverage_score, 1),
                "clarity": round(clarity_score, 1),
                "no_hallucination": round(hallucination_score, 1)
            },
            "reasoning": {
                "facts_check": facts_met,
                "hallucinations_found": hallucinations,
                "summary": f"事实覆盖率 {fact_coverage:.0%}，发现 {len(hallucinations)} 个幻觉点。"
            },
            "final_verdict": {
                "overall_score": round(overall_score, 1),
                "grade": grade,
                "suggestions": "存在幻觉，请修正事实错误。" if has_hallucination else "回答准确且全面。"
            }
        }

    def _api_evaluate(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """真实API评估逻辑 (Stub)"""
        # 这里应构建Prompt调用GPT-4
        # 为保持示例简单，此处略过
        return self._mock_evaluate(test_case)

if __name__ == "__main__":
    # 简单测试
    judge = KnowledgeJudge()
    case = {
        "test_case_id": "TEST_001",
        "question": "光合作用的产物是什么？",
        "model_output": "光合作用主要产生氧气和葡萄糖。",
        "required_facts": ["氧气|O2", "葡萄糖|有机物|C6H12O6"],
        "negative_keywords": ["二氧化碳作为产物", "消耗氧气"]
    }
    print(json.dumps(judge.evaluate(case), indent=2, ensure_ascii=False))


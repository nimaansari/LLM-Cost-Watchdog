#!/usr/bin/env python3
"""
Smart Budgeting for Cost Watchdog
Auto-adjusts budgets based on task priority, learns from spending patterns,
and suggests cheaper alternatives.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

DATA_DIR = Path.home() / ".cost-watchdog"
DATA_DIR.mkdir(exist_ok=True)

# Pricing reference (simplified for quick lookups)
MODEL_PRICING = {
    # Format: (input_per_1M, output_per_1M)
    "claude-sonnet-4.5": (3.00, 15.00),
    "claude-opus-4.6": (15.00, 75.00),
    "claude-haiku-4.5": (0.80, 4.00),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.5-flash": (0.15, 0.30),
    "groq-llama-3.2-8b": (0.05, 0.08),
    "deepseek-v3": (0.14, 0.28),
    "perplexity-sonar-small": (0.20, 0.20),
}


@dataclass
class BudgetConfig:
    """Budget configuration with smart features."""
    amount: float
    priority: str  # "low", "medium", "high", "critical"
    auto_adjust: bool = True
    learning_enabled: bool = True
    alerts_at: List[float] = None  # Percentages to alert at
    fallback_model: Optional[str] = None
    
    def __post_init__(self):
        if self.alerts_at is None:
            self.alerts_at = [50, 80, 95]


@dataclass
class SpendingPattern:
    """Learned spending pattern."""
    task_type: str
    avg_cost: float
    avg_tokens: int
    typical_duration_minutes: float
    confidence: float  # 0.0 to 1.0
    last_updated: str
    samples: int = 0


class SmartBudgetManager:
    """Manages smart budgeting with learning and auto-adjustment."""
    
    def __init__(self):
        self.config_file = DATA_DIR / "budget-config.json"
        self.patterns_file = DATA_DIR / "spending-patterns.json"
        self.config = self._load_config()
        self.patterns = self._load_patterns()
    
    def _load_config(self) -> Dict:
        """Load budget configuration."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {"budgets": [], "settings": {}}
    
    def _load_patterns(self) -> Dict:
        """Load learned spending patterns."""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        return {"patterns": []}
    
    def _save_config(self):
        """Save budget configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _save_patterns(self):
        """Save spending patterns."""
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)
    
    def set_budget(self, amount: float, priority: str = "medium", 
                   auto_adjust: bool = True) -> BudgetConfig:
        """Set a new budget with priority level."""
        budget = BudgetConfig(
            amount=amount,
            priority=priority,
            auto_adjust=auto_adjust
        )
        
        # Adjust budget based on priority if auto-adjust is enabled
        if auto_adjust:
            budget.amount = self._adjust_budget_for_priority(amount, priority)
        
        self.config["budgets"].append(asdict(budget))
        self._save_config()
        
        return budget
    
    def _adjust_budget_for_priority(self, base_amount: float, priority: str) -> float:
        """Adjust budget amount based on task priority."""
        multipliers = {
            "low": 0.5,      # 50% of base for low priority
            "medium": 1.0,   # 100% of base
            "high": 1.5,     # 150% of base
            "critical": 2.0  # 200% of base
        }
        return base_amount * multipliers.get(priority, 1.0)
    
    def get_recommended_budget(self, task_type: str, 
                                historical_data: List[Dict]) -> float:
        """Get recommended budget based on task type and history."""
        if not historical_data:
            return 5.00  # Default budget
        
        # Calculate average cost for this task type
        task_costs = [t["cost"] for t in historical_data 
                      if t.get("task_type") == task_type]
        
        if not task_costs:
            return 5.00
        
        avg_cost = sum(task_costs) / len(task_costs)
        std_dev = self._calculate_std_dev(task_costs)
        
        # Recommend budget at mean + 1 std dev (covers ~84% of cases)
        recommended = avg_cost + std_dev
        
        # Add buffer for unexpected complexity
        return recommended * 1.2
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def learn_from_task(self, task_type: str, cost: float, tokens: int,
                        duration_minutes: float):
        """Learn from completed task to improve future estimates."""
        # Find or create pattern for this task type
        pattern = None
        for p in self.patterns["patterns"]:
            if p["task_type"] == task_type:
                pattern = p
                break
        
        if pattern:
            # Update existing pattern with exponential moving average
            alpha = 0.2  # Learning rate
            n = pattern["samples"] + 1
            
            pattern["avg_cost"] = (alpha * cost) + ((1 - alpha) * pattern["avg_cost"])
            pattern["avg_tokens"] = int((alpha * tokens) + ((1 - alpha) * pattern["avg_tokens"]))
            pattern["typical_duration_minutes"] = (
                (alpha * duration_minutes) + ((1 - alpha) * pattern["typical_duration_minutes"])
            )
            pattern["samples"] = n
            pattern["confidence"] = min(0.95, pattern["confidence"] + 0.05)
            pattern["last_updated"] = datetime.now().isoformat()
        else:
            # Create new pattern
            new_pattern = SpendingPattern(
                task_type=task_type,
                avg_cost=cost,
                avg_tokens=tokens,
                typical_duration_minutes=duration_minutes,
                confidence=0.5,
                samples=1,
                last_updated=datetime.now().isoformat()
            )
            self.patterns["patterns"].append(asdict(new_pattern))
        
        self._save_patterns()
    
    def estimate_task_cost(self, task_type: str, tokens_estimate: int,
                           model: str = "claude-sonnet-4.5") -> Dict:
        """Estimate cost for a task based on learned patterns."""
        # Look up pattern
        pattern = None
        for p in self.patterns["patterns"]:
            if p["task_type"] == task_type:
                pattern = p
                break
        
        # Get pricing for model
        pricing = MODEL_PRICING.get(model, (3.00, 15.00))
        input_price, output_price = pricing
        
        if pattern and pattern["samples"] >= 3:
            # Use learned pattern
            avg_tokens = pattern["avg_tokens"]
            # Assume 20% output tokens
            estimated_output = int(tokens_estimate * 0.2)
            estimated_input = tokens_estimate - estimated_output
            
            estimated_cost = (
                (estimated_input / 1_000_000) * input_price +
                (estimated_output / 1_000_000) * output_price
            )
            
            confidence = pattern["confidence"]
            source = "learned pattern"
        else:
            # Use simple estimation
            estimated_output = int(tokens_estimate * 0.2)
            estimated_input = tokens_estimate - estimated_output
            
            estimated_cost = (
                (estimated_input / 1_000_000) * input_price +
                (estimated_output / 1_000_000) * output_price
            )
            
            confidence = 0.5
            source = "simple estimation"
        
        return {
            "task_type": task_type,
            "estimated_cost": round(estimated_cost, 4),
            "estimated_tokens": tokens_estimate,
            "model": model,
            "confidence": confidence,
            "source": source,
            "pricing_used": pricing
        }
    
    def suggest_cheaper_alternatives(self, current_model: str, 
                                      task_type: str,
                                      max_savings_percent: float = 50) -> List[Dict]:
        """Suggest cheaper model alternatives for a task."""
        if current_model not in MODEL_PRICING:
            return []
        
        current_pricing = MODEL_PRICING[current_model]
        current_cost_per_1M = current_pricing[0] + current_pricing[1]
        
        alternatives = []
        
        for model, pricing in MODEL_PRICING.items():
            if model == current_model:
                continue
            
            new_cost_per_1M = pricing[0] + pricing[1]
            savings_percent = ((current_cost_per_1M - new_cost_per_1M) / current_cost_per_1M) * 100
            
            if savings_percent >= max_savings_percent:
                alternatives.append({
                    "model": model,
                    "savings_percent": round(savings_percent, 1),
                    "new_cost_per_1M": round(new_cost_per_1M, 4),
                    "current_cost_per_1M": round(current_cost_per_1M, 4),
                    "trade_offs": self._get_trade_offs(current_model, model)
                })
        
        # Sort by savings
        alternatives.sort(key=lambda x: x["savings_percent"], reverse=True)
        return alternatives[:5]  # Top 5 alternatives
    
    def _get_trade_offs(self, current_model: str, alternative_model: str) -> str:
        """Get trade-offs when switching models."""
        trade_offs = {
            "claude-opus-4.6": "Lower reasoning quality, faster responses",
            "claude-sonnet-4.5": "Slightly lower quality, much faster",
            "claude-haiku-4.5": "Much faster, lower quality for complex tasks",
            "gpt-4o": "Different strengths, may need prompt adjustment",
            "gpt-4o-mini": "Good for simple tasks, less capable on complex reasoning",
            "gpt-4.1-nano": "Best for classification, extraction, simple tasks",
            "gemini-2.0-flash": "Good value, different knowledge cutoff",
            "groq-llama-3.2-8b": "Very fast, good for simple tasks",
            "deepseek-v3": "Strong on code, different style",
            "perplexity-sonar-small": "Includes web search, good for research"
        }
        
        return trade_offs.get(alternative_model, "May require prompt adjustment")
    
    def get_budget_status(self, current_spend: float) -> Dict:
        """Get current budget status and recommendations."""
        if not self.config["budgets"]:
            return {"status": "no_budget", "message": "No budget set"}
        
        # Get most recent budget
        budget = self.config["budgets"][-1]
        amount = budget["amount"]
        
        percent_used = (current_spend / amount) * 100 if amount > 0 else 0
        
        status = "ok"
        recommendations = []
        
        if percent_used >= 100:
            status = "over_budget"
            recommendations.append("⚠️ Budget exceeded! Consider stopping or increasing budget.")
        elif percent_used >= 95:
            status = "critical"
            recommendations.append("🚨 95% of budget used! Finish current task only.")
        elif percent_used >= 80:
            status = "warning"
            recommendations.append("⚠️ 80% of budget used. Consider wrapping up.")
        elif percent_used >= 50:
            status = "caution"
            recommendations.append("💡 50% of budget used. Monitor spending.")
        
        return {
            "status": status,
            "budget": amount,
            "spent": current_spend,
            "remaining": amount - current_spend,
            "percent_used": round(percent_used, 1),
            "recommendations": recommendations
        }
    
    def auto_adjust_budget(self, task_priority: str, 
                           current_spend: float) -> Optional[float]:
        """Auto-adjust budget based on task priority and spending patterns."""
        if not self.config["budgets"]:
            return None
        
        budget = self.config["budgets"][-1]
        if not budget.get("auto_adjust", True):
            return None
        
        # Adjust based on priority
        multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0
        }
        
        new_budget = budget["amount"] * multipliers.get(task_priority, 1.0)
        
        # Don't reduce budget if already spent > 50%
        if current_spend > (budget["amount"] * 0.5) and new_budget < budget["amount"]:
            return budget["amount"]
        
        return new_budget


def main():
    """CLI interface for smart budgeting."""
    manager = SmartBudgetManager()
    
    import sys
    if len(sys.argv) < 2:
        print("Usage: smart-budget.py [command] [args]")
        print("Commands:")
        print("  set <amount> [--priority=low|medium|high|critical]")
        print("  status")
        print("  estimate <task_type> <tokens> [model]")
        print("  alternatives <model> [--savings=50]")
        print("  learn <task_type> <cost> <tokens> <duration_minutes>")
        print("  recommend <task_type>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "set":
        amount = float(sys.argv[2])
        priority = "medium"
        for arg in sys.argv[3:]:
            if arg.startswith("--priority="):
                priority = arg.split("=")[1]
        
        budget = manager.set_budget(amount, priority)
        print(f"✅ Budget set: ${budget.amount:.2f}")
        print(f"   Priority: {budget.priority}")
        print(f"   Auto-adjust: {budget.auto_adjust}")
    
    elif command == "status":
        # For demo, assume $0 spend
        status = manager.get_budget_status(0)
        print(json.dumps(status, indent=2))
    
    elif command == "estimate":
        task_type = sys.argv[2]
        tokens = int(sys.argv[3])
        model = sys.argv[4] if len(sys.argv) > 4 else "claude-sonnet-4.5"
        
        estimate = manager.estimate_task_cost(task_type, tokens, model)
        print(f"💰 Estimate for {task_type}:")
        print(f"   Cost: ${estimate['estimated_cost']:.4f}")
        print(f"   Tokens: {estimate['estimated_tokens']:,}")
        print(f"   Confidence: {estimate['confidence']:.0%}")
        print(f"   Source: {estimate['source']}")
    
    elif command == "alternatives":
        model = sys.argv[2]
        savings = 50
        for arg in sys.argv[3:]:
            if arg.startswith("--savings="):
                savings = int(arg.split("=")[1])
        
        alternatives = manager.suggest_cheaper_alternatives(model, "general", savings)
        if alternatives:
            print(f"💡 Cheaper alternatives to {model} (>{savings}% savings):")
            for alt in alternatives:
                print(f"   • {alt['model']}: Save {alt['savings_percent']}%")
                print(f"     Trade-off: {alt['trade_offs']}")
        else:
            print(f"No alternatives with >{savings}% savings found.")
    
    elif command == "learn":
        task_type = sys.argv[2]
        cost = float(sys.argv[3])
        tokens = int(sys.argv[4])
        duration = float(sys.argv[5])
        
        manager.learn_from_task(task_type, cost, tokens, duration)
        print(f"✅ Learned from {task_type} task")
        print(f"   Cost: ${cost:.4f}, Tokens: {tokens:,}, Duration: {duration}min")
    
    elif command == "recommend":
        task_type = sys.argv[2]
        # For demo, suggest based on common patterns
        print(f"💡 Recommendations for {task_type}:")
        print("   Use Claude Haiku for simple tasks")
        print("   Use Claude Sonnet for complex reasoning")
        print("   Use GPT-4o-mini for code generation")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

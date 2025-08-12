#!/usr/bin/env python3
"""
TRADING SYSTEM OPTIMIZER
Implement fixes to reduce losses and improve performance
"""

import json
from datetime import datetime

def create_optimized_config():
    """Create optimized configuration to fix trading issues"""
    
    print("🔧 CREATING OPTIMIZED TRADING CONFIG")
    print("=" * 50)
    
    # Current problematic settings analysis
    current_issues = {
        "trades_per_day": 54,
        "max_position_size": 10002,
        "symbols_overtrade": 16,
        "charges_per_day": 1336,  # 2672/2 days
        "win_rate": 90.2,  # Good but offset by charges
        "stop_loss_rate": 9.8  # Acceptable
    }
    
    # Optimized settings
    optimized_config = {
        "trading_limits": {
            "max_trades_per_day": 10,
            "max_position_size": 2500,
            "max_symbols_per_day": 8,
            "min_gap_between_trades": 15,  # minutes
            "daily_loss_limit": 500,
            "weekly_loss_limit": 1500
        },
        
        "position_sizing": {
            "base_position_size": 1500,
            "max_position_percentage": 2.5,  # % of capital
            "reduce_size_after_loss": True,
            "increase_size_after_wins": False
        },
        
        "risk_management": {
            "stop_loss_percentage": 1.5,
            "take_profit_percentage": 2.0,
            "max_open_positions": 5,
            "avoid_news_hours": True,
            "avoid_volatile_symbols": True
        },
        
        "symbol_rotation": {
            "daily_symbol_limit": 8,
            "weekly_rotation": True,
            "avoid_previous_day_losers": True,
            "cooldown_period_hours": 24
        },
        
        "timing_optimization": {
            "preferred_hours": ["09:30-10:30", "14:30-15:00"],
            "avoid_hours": ["12:00-13:00"],
            "pre_market_analysis": True,
            "market_sentiment_check": True
        }
    }
    
    # Calculate projected improvements
    print("📊 PROJECTED IMPROVEMENTS:")
    print("-" * 30)
    
    current_daily_charges = current_issues["charges_per_day"]
    optimized_daily_charges = (optimized_config["trading_limits"]["max_trades_per_day"] * 
                              optimized_config["position_sizing"]["base_position_size"] * 0.001)
    
    charge_reduction = current_daily_charges - optimized_daily_charges
    monthly_savings = charge_reduction * 22  # Trading days
    
    print(f"   Current daily charges: ₹{current_daily_charges:,.0f}")
    print(f"   Optimized daily charges: ₹{optimized_daily_charges:,.0f}")
    print(f"   Daily savings: ₹{charge_reduction:,.0f}")
    print(f"   Monthly savings: ₹{monthly_savings:,.0f}")
    
    # Risk reduction
    current_daily_risk = current_issues["trades_per_day"] * current_issues["max_position_size"] * 0.02
    optimized_daily_risk = (optimized_config["trading_limits"]["max_trades_per_day"] * 
                           optimized_config["position_sizing"]["base_position_size"] * 0.015)
    
    risk_reduction = current_daily_risk - optimized_daily_risk
    
    print(f"\n🛡️ RISK REDUCTION:")
    print(f"   Current daily risk exposure: ₹{current_daily_risk:,.0f}")
    print(f"   Optimized daily risk: ₹{optimized_daily_risk:,.0f}")
    print(f"   Risk reduction: ₹{risk_reduction:,.0f} ({(risk_reduction/current_daily_risk)*100:.1f}%)")
    
    return optimized_config

def create_implementation_plan():
    """Create step-by-step implementation plan"""
    
    print(f"\n🚀 IMPLEMENTATION PLAN")
    print("=" * 50)
    
    plan = {
        "phase_1_immediate": {
            "timeline": "Today",
            "actions": [
                "🛑 Stop all trading for today",
                "📊 Review and close losing open positions",
                "⚙️ Update config.yml with new limits",
                "🔧 Implement position size limits in strategies",
                "📝 Add daily trade counter"
            ]
        },
        
        "phase_2_tomorrow": {
            "timeline": "Tomorrow morning",
            "actions": [
                "🌅 Run pre-market analysis",
                "🎯 Select max 8 symbols for the day",
                "📐 Set position size to ₹1500-2500 range",
                "⏰ Trade only during optimal hours",
                "📊 Monitor daily P&L closely"
            ]
        },
        
        "phase_3_weekly": {
            "timeline": "This week",
            "actions": [
                "🔄 Implement symbol rotation",
                "📈 Track performance daily",
                "🎯 Optimize entry conditions",
                "🛡️ Fine-tune stop loss levels",
                "📊 Weekly performance review"
            ]
        }
    }
    
    for phase, details in plan.items():
        print(f"\n{phase.upper().replace('_', ' ')}:")
        print(f"Timeline: {details['timeline']}")
        for action in details['actions']:
            print(f"   {action}")
    
    return plan

def create_monitoring_system():
    """Create monitoring system to track improvements"""
    
    print(f"\n📊 MONITORING SYSTEM")
    print("=" * 50)
    
    monitoring_config = {
        "daily_metrics": [
            "total_trades",
            "total_charges",
            "largest_position",
            "symbols_traded",
            "realized_pnl",
            "stop_loss_count"
        ],
        
        "alerts": {
            "max_trades_exceeded": "🚨 Daily trade limit exceeded",
            "large_position_warning": "⚠️ Position size too large",
            "daily_loss_limit": "🛑 Daily loss limit reached",
            "overtrading_symbol": "🔄 Symbol traded too frequently"
        },
        
        "weekly_review": [
            "total_pnl_vs_charges",
            "win_rate_analysis",
            "best_performing_symbols",
            "worst_performing_symbols",
            "strategy_efficiency"
        ]
    }
    
    print("Daily tracking metrics:")
    for metric in monitoring_config["daily_metrics"]:
        print(f"   • {metric}")
    
    print(f"\nAlert system:")
    for alert, message in monitoring_config["alerts"].items():
        print(f"   • {alert}: {message}")
    
    return monitoring_config

def main():
    """Main function to create complete optimization plan"""
    
    optimized_config = create_optimized_config()
    implementation_plan = create_implementation_plan()
    monitoring_system = create_monitoring_system()
    
    # Save complete optimization package
    complete_plan = {
        "timestamp": datetime.now().isoformat(),
        "current_issues_identified": {
            "overtrading": "54 trades/day vs recommended 10-15",
            "high_charges": "₹2672 in 2 days",
            "large_positions": "₹10,000+ positions",
            "symbol_concentration": "16 symbols traded heavily"
        },
        "optimized_config": optimized_config,
        "implementation_plan": implementation_plan,
        "monitoring_system": monitoring_system,
        "expected_results": {
            "daily_charge_reduction": "₹1300+ savings",
            "risk_reduction": "70%+ lower exposure",
            "improved_consistency": "More predictable returns",
            "better_win_rate": "Maintain 90%+ with lower costs"
        }
    }
    
    with open('trading_optimization_plan.json', 'w') as f:
        json.dump(complete_plan, f, indent=2, default=str)
    
    print(f"\n💾 Complete optimization plan saved to: trading_optimization_plan.json")
    
    # Summary
    print(f"\n🎯 EXECUTIVE SUMMARY")
    print("=" * 50)
    print(f"✅ Problem identified: Overtrading causing high charges")
    print(f"✅ Solution created: Reduce trades from 54 to 10 per day")
    print(f"✅ Expected benefit: ₹1300+ daily savings")
    print(f"✅ Implementation: Ready to deploy immediately")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"1. Update config.yml with new limits")
    print(f"2. Modify strategy files to implement position sizing")
    print(f"3. Add daily monitoring system")
    print(f"4. Test with reduced parameters tomorrow")

if __name__ == "__main__":
    main()

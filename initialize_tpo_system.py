#!/usr/bin/env python3
"""
TPO系統初始化腳本
執行此腳本來初始化完整的Koolearn TPO系統
"""

from app import app, db
from services.tpo_management_system import TPOManagementSystem

def initialize_system():
    """初始化TPO系統"""
    
    with app.app_context():
        print("🚀 開始初始化TPO聽力練習系統...")
        
        # 創建管理系統實例
        tpo_manager = TPOManagementSystem()
        
        # 執行初始化
        result = tpo_manager.initialize_tpo_system()
        
        if result['status'] == 'success':
            print("✅ TPO系統初始化成功！")
            print(f"📊 匯入統計：")
            stats = result['import_statistics']
            print(f"   - 匯入測試數量：{stats['imported_tests']}")
            print(f"   - 匯入題目數量：{stats['imported_questions']}")
            
            validation = result['validation_results']
            print(f"📋 系統驗證：")
            print(f"   - TPO內容總數：{validation['tpo_content_count']}")
            print(f"   - 總題目數量：{validation['total_questions']}")
            print(f"   - 難度分佈：{validation['difficulty_distribution']}")
            
        else:
            print(f"❌ 系統初始化失敗：{result['message']}")
            
        return result

if __name__ == "__main__":
    initialize_system()
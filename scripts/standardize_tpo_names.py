#!/usr/bin/env python
"""
統一TPO命名格式腳本
將所有TPO內容標準化為統一的命名格式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import ContentSource
import logging
import re

# 設置日誌
logging.basicConfig(level=logging.INFO)

def standardize_audio_labs_tpo():
    """標準化Audio Labs TPO命名"""
    with app.app_context():
        try:
            # 獲取所有Audio Labs TPO項目
            items = ContentSource.query.filter_by(type='smallstation_tpo').all()
            updated_count = 0
            
            for item in items:
                # 解析原始名稱: "Audio Labs TPO 75 S2P3"
                name_match = re.search(r'TPO (\d+) S(\d+)P(\d+)', item.name)
                if name_match:
                    tpo_num = int(name_match.group(1))
                    section = int(name_match.group(2))
                    passage = int(name_match.group(3))
                    
                    # 創建新的標準名稱
                    new_name = f"TPO {tpo_num:02d} Section {section} Passage {passage}"
                    
                    # 更新名稱和描述
                    if item.name != new_name:
                        old_name = item.name
                        item.name = new_name
                        
                        # 更新描述，保持主題信息
                        if item.topic:
                            item.description = f"TOEFL TPO {tpo_num} 聽力練習 - {item.topic}"
                        else:
                            item.description = f"TOEFL TPO {tpo_num} 聽力練習"
                        
                        updated_count += 1
                        logging.info(f"Updated: {old_name} -> {new_name}")
            
            db.session.commit()
            logging.info(f"Successfully updated {updated_count} Audio Labs TPO items")
            return updated_count
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error standardizing Audio Labs TPO: {e}")
            raise

def standardize_koolearn_official():
    """標準化新東方Official命名"""
    with app.app_context():
        try:
            # 獲取所有新東方Official項目
            items = ContentSource.query.filter_by(type='koolearn_official').all()
            updated_count = 0
            
            for item in items:
                # 解析原始名稱: "新東方 Official 75 Con1"
                name_match = re.search(r'Official (\d+) (Con|Lec)(\d+)', item.name)
                if name_match:
                    official_num = int(name_match.group(1))
                    item_type = name_match.group(2)  # Con 或 Lec
                    item_num = int(name_match.group(3))
                    
                    # 創建新的標準名稱
                    type_name = "對話" if item_type == "Con" else "講座"
                    new_name = f"TPO {official_num:02d} {type_name} {item_num}"
                    
                    # 更新名稱和描述
                    if item.name != new_name:
                        old_name = item.name
                        item.name = new_name
                        
                        # 更新描述
                        if item.topic:
                            item.description = f"TOEFL TPO {official_num} 聽力{type_name} - {item.topic}"
                        else:
                            item.description = f"TOEFL TPO {official_num} 聽力{type_name}"
                        
                        # 更新類型標記，保持原有功能
                        item.type = 'tpo_official'  # 統一類型
                        
                        updated_count += 1
                        logging.info(f"Updated: {old_name} -> {new_name}")
            
            db.session.commit()
            logging.info(f"Successfully updated {updated_count} KooLearn Official items")
            return updated_count
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error standardizing KooLearn Official: {e}")
            raise

def create_complete_tpo_structure():
    """確保完整的TPO 1-75結構"""
    with app.app_context():
        try:
            # 檢查每個TPO的完整性
            missing_items = []
            
            for tpo_num in range(1, 76):  # TPO 1-75
                # 檢查Audio Labs TPO項目 (Section 1-2, Passage 1-3)
                for section in [1, 2]:
                    for passage in [1, 2, 3]:
                        standard_name = f"TPO {tpo_num:02d} Section {section} Passage {passage}"
                        existing = ContentSource.query.filter_by(name=standard_name).first()
                        
                        if not existing:
                            # 檢查是否有舊格式的項目可以轉換
                            old_pattern = f"Audio Labs TPO {tpo_num} S{section}P{passage}"
                            old_item = ContentSource.query.filter(
                                ContentSource.name.like(f"%TPO {tpo_num} S{section}P{passage}")
                            ).first()
                            
                            if old_item:
                                old_item.name = standard_name
                                logging.info(f"Converted: {old_pattern} -> {standard_name}")
                            else:
                                missing_items.append({
                                    'name': standard_name,
                                    'tpo_num': tpo_num,
                                    'section': section,
                                    'passage': passage
                                })
                
                # 檢查對話和講座項目 (TPO 65-75)
                if tpo_num >= 65:
                    for conv_num in [1, 2]:
                        conv_name = f"TPO {tpo_num:02d} 對話 {conv_num}"
                        if not ContentSource.query.filter_by(name=conv_name).first():
                            missing_items.append({
                                'name': conv_name,
                                'tpo_num': tpo_num,
                                'type': 'conversation',
                                'num': conv_num
                            })
                    
                    for lec_num in [1, 2, 3]:
                        lec_name = f"TPO {tpo_num:02d} 講座 {lec_num}"
                        if not ContentSource.query.filter_by(name=lec_name).first():
                            missing_items.append({
                                'name': lec_name,
                                'tpo_num': tpo_num,
                                'type': 'lecture',
                                'num': lec_num
                            })
            
            db.session.commit()
            
            if missing_items:
                logging.warning(f"Found {len(missing_items)} missing TPO items")
                for item in missing_items[:5]:  # 顯示前5個
                    logging.warning(f"Missing: {item['name']}")
            else:
                logging.info("All TPO items are present and accounted for!")
            
            return len(missing_items)
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error checking TPO structure: {e}")
            raise

def main():
    """主函數"""
    print("開始統一TPO命名格式...")
    
    try:
        # 1. 標準化Audio Labs TPO命名
        print("\n1. 標準化Audio Labs TPO命名...")
        audio_labs_updated = standardize_audio_labs_tpo()
        print(f"✅ 更新了 {audio_labs_updated} 個Audio Labs TPO項目")
        
        # 2. 標準化新東方Official命名
        print("\n2. 標準化新東方Official命名...")
        koolearn_updated = standardize_koolearn_official()
        print(f"✅ 更新了 {koolearn_updated} 個新東方Official項目")
        
        # 3. 檢查完整結構
        print("\n3. 檢查TPO完整結構...")
        missing_count = create_complete_tpo_structure()
        if missing_count == 0:
            print("✅ 所有TPO項目都已完整！")
        else:
            print(f"⚠️ 發現 {missing_count} 個缺失項目")
        
        print(f"\n📊 統計結果:")
        print(f"- Audio Labs TPO更新: {audio_labs_updated} 項")
        print(f"- 新東方Official更新: {koolearn_updated} 項")
        print(f"- 缺失項目: {missing_count} 項")
        print(f"- 總覆蓋: TPO 1-75 (完整)")
        
    except Exception as e:
        print(f"❌ 處理失敗: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
import sqlite3
import os

DB_PATH = "/app/knowledge_base/kb.sqlite"

def get_advice_by_condition(condition: str):
    """根据条件查询建议"""
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        return {"error": "数据库不存在"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询规则
        cursor.execute("""
            SELECT 
                rule_id,
                advice_text,
                evidence_id
            FROM rules
            WHERE condition_expr LIKE ? AND is_active = 1
        """, (f"%{condition}%",))
        
        rules = cursor.fetchall()
        results = []
        
        for rule in rules:
            # 处理证据ID（可能是多个，用分号分隔）
            evidence_ids = rule["evidence_id"].split(';') if rule["evidence_id"] else []
            
            evidence_list = []
            source_list = []
            
            # 查询每个证据
            for ev_id in evidence_ids:
                ev_id = ev_id.strip()
                cursor.execute("""
                    SELECT e.evidence_text, s.source_title
                    FROM evidence e
                    LEFT JOIN sources s ON e.source_id = s.source_id
                    WHERE e.evidence_id = ?
                """, (ev_id,))
                
                ev_row = cursor.fetchone()
                if ev_row:
                    if ev_row["evidence_text"]:
                        evidence_list.append(ev_row["evidence_text"])
                    if ev_row["source_title"] and ev_row["source_title"] not in source_list:
                        source_list.append(ev_row["source_title"])
            
            results.append({
                "advice": rule["advice_text"],
                "evidence": "；".join(evidence_list) if evidence_list else "暂无具体依据",
                "source": "、".join(source_list) if source_list else "未知来源"
            })
        
        conn.close()
        return {"advice": results}
        
    except Exception as e:
        print(f"数据库查询错误: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
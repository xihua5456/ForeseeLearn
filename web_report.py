"""学习网页生成器：读取学习数据，生成可视化 HTML 报告

纯标准库实现（零依赖）：
- 读取 knowledge_structure.json（学习目录）
- 读取掌握度状态、学习记录、学习路径进度
- 拼装成自包含的 HTML（内嵌 CSS），存为 learning_report.html
"""

import os
from datetime import datetime
from typing import Dict, Any, List


def _mastery_color(mastery: float) -> str:
    """掌握度 → 颜色（绿=熟练 蓝=掌握 橙=学习中 灰=未开始）"""
    if mastery >= 0.8:
        return "#0F6E56"
    if mastery >= 0.5:
        return "#185FA5"
    if mastery >= 0.2:
        return "#BA7517"
    return "#B4B2A9"


def _mastery_label(mastery: float) -> str:
    if mastery >= 0.8:
        return "熟练"
    if mastery >= 0.5:
        return "掌握"
    if mastery >= 0.2:
        return "学习中"
    return "未开始"


def generate_report(system) -> str:
    """生成学习报告网页，返回 HTML 文件路径"""
    configs = system.configs
    knowledge_structure = configs.get('knowledge_structure', {})
    state = system.data_manager.load_knowledge_state()
    records = system.data_manager.load_records()

    # ---------- 顶部：标题 ----------
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    html = []
    html.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ForeseeLearn 学习报告</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
         background: #f5f6f8; color: #2c2c2a; padding: 24px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #185FA5, #0F6E56);
            color: #fff; border-radius: 16px; padding: 28px 32px; margin-bottom: 20px; }}
  .header h1 {{ font-size: 24px; margin-bottom: 6px; }}
  .header p {{ opacity: 0.85; font-size: 13px; }}
  .card {{ background: #fff; border-radius: 14px; padding: 20px 24px; margin-bottom: 16px;
          box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .card h2 {{ font-size: 16px; margin-bottom: 14px; color: #185FA5;
             border-left: 4px solid #185FA5; padding-left: 10px; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .stat {{ background: #f8f9fb; border-radius: 10px; padding: 14px; text-align: center; }}
  .stat .num {{ font-size: 22px; font-weight: 600; }}
  .stat .label {{ font-size: 12px; color: #888780; margin-top: 4px; }}
  .bar {{ height: 10px; background: #eee; border-radius: 5px; overflow: hidden; margin-top: 10px; }}
  .bar-fill {{ height: 100%; border-radius: 5px; }}
  .subject {{ margin-bottom: 18px; }}
  .subject-name {{ font-size: 14px; font-weight: 600; margin-bottom: 8px; }}
  .chapter {{ margin: 10px 0 4px; font-size: 13px; color: #444441; }}
  .points {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .point {{ padding: 6px 12px; border-radius: 20px; font-size: 12px; color: #fff; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ color: #888780; font-weight: 500; }}
  .review {{ background: #FFF8E6; border-left: 4px solid #BA7517;
            padding: 10px 14px; border-radius: 8px; margin: 6px 0; font-size: 13px; }}
  .footer {{ text-align: center; color: #b4b2a9; font-size: 12px; margin-top: 24px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>ForeseeLearn 学习报告</h1>
    <p>生成时间：{now} · 基于 MPC + 模糊控制的学习路径</p>
  </div>""")

    # ---------- 统计总览 ----------
    total_points = sum(len(points) for chapters in knowledge_structure.values() for points in chapters.values())
    mastered = sum(1 for k in state if state[k] >= 0.6)
    avg_mastery = sum(state.values()) / len(state) if state else 0.0

    html.append(f"""
  <div class="card">
    <h2>学习进度总览</h2>
    <div class="grid">
      <div class="stat"><div class="num" style="color:#185FA5">{total_points}</div><div class="label">知识点总数</div></div>
      <div class="stat"><div class="num" style="color:#0F6E56">{mastered}</div><div class="label">已达标（≥0.6）</div></div>
      <div class="stat"><div class="num" style="color:#BA7517">{avg_mastery:.0%}</div><div class="label">平均掌握度</div></div>
    </div>
    <div class="bar"><div class="bar-fill" style="width:{avg_mastery * 100:.0f}%; background:linear-gradient(90deg,#185FA5,#0F6E56);"></div></div>
  </div>""")

    # ---------- 当前学习单元 ----------
    try:
        unit = system.get_learning_path_status()
        if 'message' not in unit:
            html.append(f"""
  <div class="card">
    <h2>当前学习单元</h2>
    <div class="grid">
      <div class="stat"><div class="num" style="color:#2c2c2a">{unit['current_unit']}</div><div class="label">当前单元</div></div>
      <div class="stat"><div class="num" style="color:#185FA5">{unit['current_mastery']:.0%}</div><div class="label">当前掌握度</div></div>
      <div class="stat"><div class="num" style="color:#BA7517">{unit['estimated_minutes']}分</div><div class="label">预估达标时间</div></div>
    </div>""")
            if unit.get('review_suggestions'):
                html.append('<div style="margin-top:12px;">')
                for item in unit['review_suggestions']:
                    html.append(f'<div class="review">📌 建议复习：{item["knowledge"]}（掌握度 {item["mastery"]:.0%}）</div>')
                html.append('</div>')
            html.append('</div>')
    except Exception:
        pass

    # ---------- 知识点地图 ----------
    html.append("""
  <div class="card">
    <h2>知识点地图</h2>""")
    for subject, chapters in knowledge_structure.items():
        html.append(f'<div class="subject"><div class="subject-name">{subject}</div>')
        for chapter, points in chapters.items():
            html.append(f'<div class="chapter">{chapter}</div><div class="points">')
            for point in points:
                m = state.get(point, 0.0)
                color = _mastery_color(m)
                html.append(f'<span class="point" style="background:{color}">{point} {m:.0%}</span>')
            html.append('</div>')
        html.append('</div>')
    html.append('</div>')

    # ---------- 最近学习记录 ----------
    html.append("""
  <div class="card">
    <h2>最近学习记录</h2>""")
    recent = records[-10:][::-1]  # 最近 10 条，新的在前
    if recent:
        html.append("""<table><tr><th>日期</th><th>知识点</th><th>计划/实际</th><th>正确率</th><th>自评</th></tr>""")
        for r in recent:
            acc = r.get('correct_count', 0) / max(r.get('question_count', 1), 1)
            html.append(f"""<tr>
                <td>{r.get('date', '')}</td>
                <td>{r.get('knowledge_point', '')}</td>
                <td>{r.get('planned_minutes', 0)}/{r.get('actual_minutes', 0)}分</td>
                <td>{acc:.0%}</td>
                <td>{r.get('self_rating', '-')}/5</td></tr>""")
        html.append('</table>')
    else:
        html.append('<p style="color:#888780">还没有学习记录，快去学第一个单元吧！</p>')
    html.append('</div>')

    # ---------- 页脚 ----------
    html.append(f"""
  <div class="footer">ForeseeLearn · 基于模型预测控制与模糊控制 · {now}</div>
</div>
</body>
</html>""")

    # ---------- 写文件 ----------
    output_path = os.path.join(system.base_path, 'learning_report.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    return output_path

"""ForeseeLearn 网页版后端：本地 Web 服务，提供可视化操作界面

纯标准库实现（零依赖）：
- http.server 提供静态页面 + JSON API
- 复用 LearningOptimizationSystem 的全部逻辑
- 启动：python web_app.py → 浏览器自动打开 http://127.0.0.1:8000

API 一览：
- GET  /                      → 网页界面
- GET  /api/overview          → 仪表盘数据（总览+当前单元+知识点地图+最近记录）
- POST /api/record            → 记录学习
- GET  /api/path              → 学习路径状态
- POST /api/skip              → 手动跳过当前单元
- POST /api/deadline_plan     → 截止日期规划（倒排）
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from learning_system import LearningOptimizationSystem
from deadline_planner import DeadlinePlanner

PORT = 8000
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# 全局系统实例
system = LearningOptimizationSystem(BASE_PATH)
planner = DeadlinePlanner(system.learning_path, system.configs)


def _json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler):
    length = int(handler.headers.get('Content-Length', 0))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode('utf-8'))


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # 静默日志

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/' or parsed.path == '/index.html':
            self._serve_static('templates/index.html', 'text/html; charset=utf-8')
        elif parsed.path == '/api/overview':
            _json_response(self, _build_overview())
        elif parsed.path == '/api/path':
            _json_response(self, _get_path_status())
        elif parsed.path == '/api/knowledge':
            _json_response(self, {'knowledge_list': system.knowledge_list})
        elif parsed.path == '/api/importance':
            _json_response(self, {
                'importance_map': system.importance_map,
                'levels': system.importance_levels,
            })
        else:
            _json_response(self, {'error': 'not found'}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/record':
            data = _read_json_body(self)
            _json_response(self, system.add_learning_record(data))
        elif parsed.path == '/api/skip':
            data = _read_json_body(self)
            knowledge = data.get('knowledge', '')
            _json_response(self, system.skip_learning_unit(knowledge))
        elif parsed.path == '/api/set_mastery':
            data = _read_json_body(self)
            _json_response(self, system.set_mastery_manually(
                knowledge=data.get('knowledge', ''),
                mastery=data.get('mastery', 0),
            ))
        elif parsed.path == '/api/set_importance':
            data = _read_json_body(self)
            _json_response(self, system.set_knowledge_importance(
                knowledge=data.get('knowledge', ''),
                level=data.get('level', 'normal'),
            ))
        elif parsed.path == '/api/deadline_plan':
            data = _read_json_body(self)
            result = planner.plan(
                deadline=data.get('deadline', ''),
                knowledge_points=data.get('points', []),
                daily_minutes=int(data.get('daily_minutes', 60)),
            )
            _json_response(self, result)
        else:
            _json_response(self, {'error': 'not found'}, 404)

    def _serve_static(self, rel_path, content_type):
        path = os.path.join(BASE_PATH, rel_path)
        if not os.path.exists(path):
            _json_response(self, {'error': f'{rel_path} not found'}, 404)
            return
        with open(path, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------- 数据组装 ----------

def _build_overview():
    """仪表盘：总览统计 + 当前单元 + 知识点地图 + 最近记录"""
    state = system.data_manager.load_knowledge_state()
    records = system.data_manager.load_records()
    structure = system.configs.get('knowledge_structure', {})

    total = sum(len(p) for ch in structure.values() for p in ch.values())
    mastered = sum(1 for v in state.values() if v >= 0.6)
    avg = sum(state.values()) / len(state) if state else 0.0

    # 当前单元
    path_status = system.get_learning_path_status()
    current_unit = None
    if 'message' not in path_status:
        current_unit = path_status

    # 知识点地图（学科→章节→知识点带掌握度+重要度）
    map_data = []
    for subject, chapters in structure.items():
        chapters_out = []
        for chapter, points in chapters.items():
            points_out = [{
                'name': p,
                'mastery': round(state.get(p, 0.0), 3),
                'importance': system.importance_map.get(p, 'normal'),
            } for p in points]
            chapters_out.append({'name': chapter, 'points': points_out})
        map_data.append({'subject': subject, 'chapters': chapters_out})

    # 最近记录
    recent = []
    for r in records[-8:][::-1]:
        acc = r.get('correct_count', 0) / max(r.get('question_count', 1), 1)
        recent.append({
            'date': r.get('date', ''),
            'knowledge': r.get('knowledge_point', ''),
            'planned': r.get('planned_minutes', 0),
            'actual': r.get('actual_minutes', 0),
            'accuracy': round(acc, 3),
            'self_rating': r.get('self_rating', 0),
        })

    return {
        'total_points': total,
        'mastered': mastered,
        'avg_mastery': round(avg, 3),
        'current_unit': current_unit,
        'map': map_data,
        'recent_records': recent,
    }


def _get_path_status():
    return system.get_learning_path_status()


def main():
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f"ForeseeLearn 网页版已启动： http://127.0.0.1:{PORT}")
    print("按 Ctrl+C 停止服务")

    # 延迟 1 秒自动打开浏览器
    threading.Timer(1.0, lambda: webbrowser.open(f'http://127.0.0.1:{PORT}')).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.shutdown()


if __name__ == '__main__':
    main()

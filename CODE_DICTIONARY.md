# 📖 代码阅读词典（中英对照）

> 改代码时遇到看不懂的变量/函数名，来这里查。
> 用法：`Ctrl+F` 搜英文名，看中文解释。

## 一、高频"后缀"（看到就懂是什么）

| 英文后缀 | 中文意思 | 项目里的例子 |
|---|---|---|
| `_minutes` | 分钟（时长） | `planned_minutes` 计划分钟、`actual_minutes` 实际分钟 |
| `_count` | 数量 | `question_count` 题数、`correct_count` 正确题数 |
| `_rating` | 评分（1-5） | `self_rating` 自评分数 |
| `_weight` | 权重 | `accuracy_weight` 正确率权重 |
| `_mastery` | 掌握度（0-1） | `current_mastery` 当前掌握度 |
| `_threshold` | 阈值/界限 | `min_difficulty_threshold` 最低难度阈值 |
| `_state` | 状态 | `knowledge_state` 知识点状态 |
| `_record` | 记录 | `learning_record` 学习记录 |
| `_plan` | 计划 | `tomorrow_plan` 明日计划 |
| `_score` | 得分 | `average_score` 平均分 |
| `_accuracy` | 正确率 | `avg_accuracy` 平均正确率 |
| `_difficulty` | 难度 | `difficulty_map` 难度表 |
| `_completion` | 完成率 | `avg_completion` 平均完成率 |
| `_trend` | 趋势 | `performance_trend` 表现趋势 |
| `_consistency` | 一致性 | 学习波动程度（越大越稳） |
| `_decay` | 衰减 | `fatigue_decay` 疲劳衰减、`base_decay` 基础遗忘率 |

## 二、高频"前缀"（动词=动作，函数名）

| 英文前缀 | 中文意思 | 项目里的例子 |
|---|---|---|
| `load_` | 读/加载 | `load_records()` 读记录 |
| `save_` | 存/保存 | `save_record()` 存记录 |
| `update_` | 更新 | `update_mastery_state()` 更新掌握度 |
| `generate_` | 生成 | `generate_tomorrow_plan()` 生成明日计划 |
| `calculate_` | 计算 | `calculate_difficulty()` 计算难度 |
| `evaluate_` | 评估 | `evaluate_day()` 评估单日表现 |
| `predict_` | 预测 | `predict_forgetting()` 预测遗忘 |
| `optimize_` | 优化 | `optimize_plan()` 优化计划 |
| `simulate_` | 模拟 | `simulate_forgetting()` 模拟遗忘 |
| `get_` | 获取 | `get_knowledge_status()` 获取知识点状态 |
| `add_` | 添加 | `add_learning_record()` 添加学习记录 |
| `show_` | 显示 | `show_evaluation()` 显示评价 |
| `modify_` | 修改 | `modify_config()` 修改配置 |
| `auto_` | 自动 | `auto_optimize_parameters()` 自动优化参数 |
| `flatten_` | 展平/摊开 | `flatten_knowledge_structure()` 展平知识结构 |

## 三、核心名词（最重要的 30 个）

| 英文 | 中文 | 在系统里代表什么 |
|---|---|---|
| `base_path` | 项目根目录 | 程序运行所在的文件夹 |
| `knowledge_point` | 知识点 | 你要学的一个具体内容（如"一元二次方程"） |
| `knowledge_list` | 知识点列表 | 所有知识点的集合 |
| `mastery` | 掌握度 | 0~1 的数字，越高说明学得越好 |
| `gain` | 提升量 | 学一次涨了多少掌握度 |
| `difficulty` | 难度 | 0~1，越高越难 |
| `priority` | 优先级 | 计划里排在前面的程度，越高越靠前 |
| `horizon` | 预测窗口 | MPC 往前看几天（本项目=7天） |
| `budget` | 预算 | 总共可用的时间 |
| `iteration` | 迭代次数 | 优化时重复试了多少次 |
| `feedback` | 反馈 | 给用户的学习评价文字 |
| `suggestion` | 建议 | 个性化学习建议 |
| `weak_points` | 薄弱点 | 掌握度最低的知识点 |
| `strong_points` | 优势点 | 掌握度最高的知识点 |
| `cache` | 缓存/数据存放处 | 数据文件存放的文件夹 |
| `config` | 配置 | 系统参数设置 |
| `params` | 参数 | 同 config，系统设置 |
| `state` | 状态 | 当前进度情况 |
| `records` | 记录 | 历史学习数据 |
| `tasks` | 任务 | 计划里安排的学习项 |
| `efficiency` | 效率 | 学习效率 |
| `fatigue` | 疲劳 | 学久了效率下降 |
| `forgetting` | 遗忘 | 不复习就会忘 |
| `rest` | 休息 | 休息安排 |
| `motivation` | 动力/激励 | 打卡、成就等激励功能 |
| `flexibility` | 弹性 | 容错、临时调整的空间 |
| `adaptation` | 自适应 | 根据表现自动调整 |
| `completion` | 完成度 | 实际学/计划学的比例 |
| `insights` | 洞察/分析 | 学习分析建议 |
| `overall` | 整体 | 总体情况 |

## 四、英文缩写速查

| 缩写 | 全称 | 意思 |
|---|---|---|
| `acc` | accuracy | 正确率 |
| `avg` | average | 平均 |
| `min` / `max` | minimum / maximum | 最小 / 最大 |
| `iter` | iteration | 迭代 |
| `params` | parameters | 参数 |
| `configs` | configurations | 配置集合 |
| `kp` | knowledge point | 知识点 |
| `eval` | evaluate | 评估 |

## 五、读代码万能公式

遇到任何看不懂的标识符，按这三步走：

1. **按 `_` 拆开**：`generate_tomorrow_plan` → `generate` + `tomorrow` + `plan`
2. **逐段查表**：生成 + 明天 + 计划 = "生成明日计划"
3. **猜不出来就搜**：用编辑器的查找（Ctrl+F）搜这个单词，看它出现在哪个上下文里，上下文会告诉你意思

> 诀窍：程序员命名 90% 是"动词_名词"或"形容词_名词"，掌握了上面几张表，整个项目的代码基本都能读懂。

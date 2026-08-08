# MPC学习系统配置说明

## 配置文件总览

系统包含4个配置文件，都位于 `config/` 目录下：

1. **model_params.json** - 模型参数（核心算法设置）
2. **evaluation_weights.json** - 评价权重（评分标准）
3. **knowledge_structure.json** - 知识结构（知识点定义）
4. **human_settings.json** - 人性化设置（用户体验）

## 配置修改指南

### 1. model_params.json - 模型参数

#### 遗忘曲线参数
- **base_decay**: 基础遗忘率（默认0.1）
  - 每天10%的掌握度会自然衰减
  - 调整建议：0.05-0.2，值越大遗忘越快
- **difficulty_multiplier**: 难度系数（默认0.2）
  - 难度越高的知识点遗忘越快
  - 0.2 = 难度每增加0.1，遗忘率增加2%

#### 学习效率参数
- **base_rate**: 基础学习率（默认0.15）
  - 每分钟学习可提升15%的掌握度
  - 调整建议：0.1-0.25，值越大学习效果越好
- **fatigue_decay**: 疲劳衰减系数（默认0.05）
  - 学习时间越长，效率越低
  - 0.05 = 每分钟学习效率降低5%

#### 时间分配参数
- **min_task_minutes**: 最小任务时长（默认15）
  - 低于15分钟的学习任务会被合并
  - 调整建议：10-30分钟
- **max_task_minutes**: 最大任务时长（默认120）
  - 单个知识点最多学习120分钟
  - 调整建议：60-180分钟
- **balance_new_old**: 新旧知识点平衡（默认0.7）
  - 70%时间给旧知识点，30%给新知识点
  - 调整建议：0.5-0.9，值越大越侧重复习

#### 优化参数
- **horizon_days**: 优化时间窗口（默认7）
  - 预测未来7天的学习效果
  - 调整建议：3-14天
- **max_iterations**: 最大迭代次数（默认100）
  - 优化算法最多运行100次
  - 调整建议：50-200，值越大结果越精确但越慢

### 2. evaluation_weights.json - 评价权重

#### 每日评价参数
- **accuracy_weight**: 准确率权重（默认0.6）
  - 60%的评分来自题目正确率
  - 调整建议：0.4-0.8
- **self_rating_weight**: 自评权重（默认0.3）
  - 30%的评分来自主观自评
  - 调整建议：0.2-0.5
- **completion_weight**: 完成度权重（默认0.1）
  - 10%的评分来自计划完成情况
  - 调整建议：0.05-0.2

#### 长期跟踪参数
- **consistency_bonus**: 一致性奖励（默认0.2）
  - 学习一致性好的额外奖励
  - 调整建议：0.1-0.3
- **improvement_rate**: 进步率（默认0.3）
  - 学习进步速度的权重
  - 调整建议：0.2-0.4
- **knowledge_coverage**: 知识覆盖度（默认0.5）
  - 知识点广度的权重
  - 调整建议：0.3-0.7

### 3. knowledge_structure.json - 知识结构

#### 格式说明
```json
{
  "学科": {
    "章节": ["知识点1", "知识点2", "知识点3"]
  }
}
```

#### 修改方法
1. **添加新学科**：在根级别添加新键
2. **添加新章节**：在学科对象内添加新键
3. **添加新知识点**：在章节数组内添加字符串

#### 示例扩展
```json
{
  "物理": {
    "力学": ["牛顿定律", "动量守恒", "能量守恒"],
    "电磁学": ["电场", "磁场", "电磁感应"]
  }
}
```

### 4. human_settings.json - 人性化设置

#### 休息时间设置
- **weekly_rest_days**: 每周休息日（默认[0,6]）
  - 0=周日, 1=周一, ..., 6=周六
  - 例如：[1,2,3,4,5] 表示工作日学习，周末休息
- **daily_break_minutes**: 每次休息时长（默认10）
  - 单位：分钟
- **break_after_minutes**: 学习多久休息（默认90）
  - 每90分钟学习后休息10分钟

#### 难度适应设置
- **auto_adjust**: 是否自动调整难度（默认true）
  - true: 根据表现自动调整
  - false: 保持固定难度
- **min_difficulty_threshold**: 最小难度阈值（默认0.4）
  - 低于此值会降低难度
- **max_difficulty_threshold**: 最大难度阈值（默认0.8）
  - 高于此值会提高难度

#### 激励系统设置
- **enable_streak_tracking**: 是否启用连续学习追踪（默认true）
  - 记录连续学习天数
- **enable_achievements**: 是否启用成就系统（默认true）
  - 解锁学习成就
- **daily_goal_minimum**: 每日最低学习目标（默认30）
  - 单位：分钟

#### 灵活性设置
- **allow_plan_modification**: 是否允许修改计划（默认true）
  - true: 可以随时修改学习计划
  - false: 计划生成后不可修改
- **emergency_break_minutes**: 紧急休息时长（默认30）
  - 单位：分钟
- **stress_relief_mode**: 压力缓解模式（默认false）
  - true: 启用轻松的学习模式
  - false: 正常学习模式

## 配置修改建议

### 初学者设置
```json
// model_params.json
{
  "learning_efficiency": {"base_rate": 0.1},
  "time_allocation": {"min_task_minutes": 20, "max_task_minutes": 60}
}

// human_settings.json
{
  "rest_schedule": {"break_after_minutes": 60},
  "motivation_system": {"daily_goal_minimum": 20}
}
```

### 进阶者设置
```json
// model_params.json
{
  "learning_efficiency": {"base_rate": 0.2},
  "time_allocation": {"min_task_minutes": 15, "max_task_minutes": 120}
}

// human_settings.json
{
  "rest_schedule": {"break_after_minutes": 120},
  "motivation_system": {"daily_goal_minimum": 60}
}
```

### 专家设置
```json
// model_params.json
{
  "learning_efficiency": {"base_rate": 0.25},
  "time_allocation": {"min_task_minutes": 10, "max_task_minutes": 180}
}

// human_settings.json
{
  "rest_schedule": {"break_after_minutes": 150},
  "motivation_system": {"daily_goal_minimum": 90}
}
```

## 注意事项

1. **备份配置**：修改前请备份原配置文件
2. **逐步调整**：一次只修改一个参数，观察效果
3. **数值范围**：注意参数的有效范围，避免极端值
4. **系统重启**：修改配置后需要重启系统才能生效
5. **数据兼容**：修改知识结构不会影响已有数据

## 故障排除

### 配置文件格式错误
- 检查JSON语法是否正确
- 确保所有键值对都有引号
- 检查逗号使用是否正确

### 参数值无效
- 确保数值在合理范围内
- 检查数据类型是否正确（数字vs字符串）
- 避免空值或null

### 系统不生效
- 重启系统
- 检查文件权限
- 查看系统日志
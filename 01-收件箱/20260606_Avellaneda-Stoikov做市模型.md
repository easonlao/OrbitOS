---

title: "Avellaneda-Stoikov做市模型"
type: card
topic: dev
workspace: "03-知识"
created: "2026-06-06"
modified: "2026-06-06 21:06:03"
tags: ["finance", "market-making", "quantitative", "algorithmic-trading"]
source: manual
status: active
---


# Avellaneda-Stoikov 做市模型

## 定义

Avellaneda-Stoikov（2008）是做市商最优报价的数学基准模型。回答核心问题：给定库存风险和市场波动，做市商应把买卖报价挂在哪里。

## 预约价格（Reservation Price）

做市商根据库存偏离目标值动态调整的"个性化中间价"：

```
r = s - q·γ·σ²·(T-t)
```

- s = 当前中间价，q = 当前库存，γ = 风险厌恶系数
- σ² = 价格波动率，T-t = 剩余交易时间

库存越多，预约价格越低——做市商愿以更便宜的价格卖出以减少库存。

## 最优价差（Optimal Spread）

```
δ = γσ²(T-t) + (2/κ)ln(1 + γ/δ)
```

- κ = 订单到达强度（订单簿密度）

波动越大、时间越长、风险厌恶越高，最优价差越宽。

## 关键参数

- **γ（风险厌恶）**：γ → 0 不关心库存, γ → ∞ 极度厌恶。决定价差宽度
- **κ（订单簿密度）**：κ 大 → 竞争激烈 → 价差窄
- **σ²（波动率）**：波动大 → 库存风险高 → 价差宽

## 相关概念

- [[做市商制度]]
- [[MMXM做市商模型]]
- [[流动性理论]]

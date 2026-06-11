---

title: "ICT Silver Bullet策略"
type: card
topic: dev
workspace: "03-知识"
created: "2026-06-06"
modified: "2026-06-06 21:06:03"
tags: ["finance", "trading", "ict", "market-making", "PYTA"]
source: manual
status: active
---


# ICT Silver Bullet 策略

## 定义

Silver Bullet 是 ICT 方法论中的单小时日内交易模型。在三个特定的 60 分钟窗口内，用低时间框架捕捉 FVG 回踩入场。

## 三个窗口

| 窗口 | 纽约时间 (ET) | 东八区（夏令时） |
|------|-------------|---------------|
| 伦敦 | 3:00 – 4:00 AM | 3:00 – 4:00 PM |
| 纽约 AM | 10:00 – 11:00 AM | 10:00 – 11:00 PM |
| 纽约 PM | 1:30 – 2:30 PM | 1:30 – 2:30 AM |

## 必要条件

- 日线偏差已确立
- 流动性已被猎取（扫了）
- 位移 + FVG 同时出现
- R:R ≥ 1:2

## 相关概念

- [[ICT交易时间窗口KillZones]]
- [[ICT 确认模型Confluence]]
- [[流动性理论]]

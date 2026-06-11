---

title: "ICT 确认模型Confluence"
type: card
topic: dev
workspace: "03-知识"
created: "2026-06-06"
modified: "2026-06-06 21:06:03"
tags: ["finance", "trading", "ict", "market-making", "PYTA"]
source: manual
status: active
---


# ICT 确认模型（Confluence Model）

## 定义

确认模型是 ICT 的三合一入场信号系统。三个条件必须同时满足：Liquidity Sweep + FVG + Order Block。

## 三层确认

**第一层：流动性猎取**。价格突破关键位后迅速反转，表明做市商已完成对手盘获取。无扫流动性 → 不交易。

**第二层：位移 + FVG**。扫流动性后出现强力位移K线，留下三K线不平衡区域（Fair Value Gap）。

**第三层：订单块**。FVG 形成前最后一根反向K线的实体区域，是机构大单集中的入场区。

## 相关概念

- [[ICT OTE最优交易入场]]
- [[机构订单流]]
- [[流动性理论]]

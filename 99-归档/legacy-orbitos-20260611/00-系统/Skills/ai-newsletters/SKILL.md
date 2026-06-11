---
name: ai-newsletters
description: >-
  AI通讯策展。当用户说"AI通讯"、"newsletter"、"订阅摘要"、"ai-newsletters"时触发。
  抓取、去重、排名AI领域通讯内容，生成每日摘要。
triggers:
  - AI通讯
  - newsletter
  - 订阅摘要
  - ai-newsletters
---
# AI Newsletter Curation

Fetch, deduplicate, and rank AI newsletter content into a daily digest.

## RSS Sources

- **TLDR AI**: `https://bullrich.dev/tldr-rss/ai.rss`
- **The Rundown AI**: `https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml`

## Workflow

1. **Check cache**: Look for `05-资源/Newsletters/YYYY-MM/YYYY-MM-DD-摘要.md`. If exists with today's date, return cached content.

2. **Fetch feeds**: Use WebFetch on both RSS URLs. Extract title, link, pubDate, description for each item.

3. **Deduplicate**: Merge items with similar titles (80%+ word overlap). Keep longer description, track both sources.

4. **Rank items** by:
   - AI relevance (LLM, GPT, Claude, agents, ML keywords)
   - Productivity relevance (workflow, automation, tools, PKM)
   - Recency (newer = higher)
   - Novelty (check recent archives, penalize repeats)

5. **Generate digest**: See [TEMPLATE.md](TEMPLATE.md) for format. Include:
   - 精选推荐 (3-5 highest scoring) with content creation angles
   - AI动态 section
   - 生产力工具 section
   - Stats footer

6. **Save files**:
   - `05-资源/Newsletters/YYYY-MM/YYYY-MM-DD-摘要.md` (curated)
   - `05-资源/Newsletters/YYYY-MM/原始数据/YYYY-MM-DD_TLDR-AI-Raw.md`
   - `05-资源/Newsletters/YYYY-MM/原始数据/YYYY-MM-DD_Rundown-AI-Raw.md`

## Output Format

**Manual invocation**: Display full digest with all sections.

**From /start-my-day**: Return condensed list:
```
**内容机会 (5):**
- [标题] - [角度]
...
完整摘要: [[YYYY-MM-DD-摘要]]
```

## Error Handling

- One feed down: Continue with other, note in digest
- Both down: Use yesterday's archive with warning
- Empty feeds: Create minimal digest noting "今日无新内容"

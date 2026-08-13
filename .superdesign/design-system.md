# REDPLAG Notion Report Design System

## Product Context

REDPLAG is a local MVP that detects bullying risk signals in chat conversations. The Notion report is opened by school or organization administrators from an email link. It must help a manager quickly scan risk, understand context, and inspect original evidence without implying a final legal or disciplinary judgment.

## Required Report Content

The report currently contains:

- Title: `REDPLAG` and `[위험 신호 알림]`
- Summary: chat room name, risk level, bullying probability
- Manager summary
- Context reason
- Risk type table with sender labels
- Risk segment table with time, reason, evidence message ids
- Evidence message table with message id, time, sender, content
- Missing context
- Recommended initial actions
- Disclaimer

## Visual Principles

- Tone: serious, calm, administrative, evidence-first.
- Avoid marketing hero layouts, decorative illustrations, and playful styling.
- Preserve clear hierarchy for manager review.
- Use restrained color. Immediate risk should be visible but not alarmist.
- Keep dense information readable with section bands, tables, callouts, and labels.
- Korean text must remain readable, not cramped.

## Tokens

- Font: Pretendard, Noto Sans KR, Apple SD Gothic Neo, Segoe UI, sans-serif.
- Page background: `#f4f7fb`.
- Surface: `#ffffff`.
- Soft surface: `#f8faff`.
- Ink: `#17233f`.
- Muted: `#68738b`.
- Border: `#e3e9f2`.
- Primary: `#3867d6`.
- Immediate/risk: `#d94b56`.
- Warning: `#e09a24`.
- Normal: `#2b9a6f`.
- Radius: 10px for compact controls, 14px for report sections.

## Notion Constraints

Design as if implemented in Notion-compatible Markdown/blocks:

- Headings, paragraphs, bullets, tables, callout-like blocks, dividers, and simple badges are acceptable.
- Do not rely on complex custom CSS, absolute positioning, scripts, or interactive controls.
- Tables should remain readable when converted to native Notion tables.
- The final implementation will be in `ai/notification/notion_markdown.py`.

from __future__ import annotations


def format_retrieval_context(hits: list[dict]) -> str:
    lines: list[str] = []
    for item in hits:
        content = str(item.get("content", "")).strip()
        source = str(item.get("source", "knowledge"))
        score = item.get("score")
        if not content:
            continue
        preview = content if len(content) <= 280 else f"{content[:280]}..."
        if score is None:
            lines.append(f"- [{source}] {preview}")
        else:
            lines.append(f"- [{source}] ({float(score):.3f}) {preview}")
    return "\n".join(lines)


def format_tool_context(tool_trace: list[dict]) -> str:
    lines: list[str] = []
    for trace in tool_trace:
        lines.append(
            f"- tool={trace.get('tool_name')} status={trace.get('status')} result={trace.get('result_preview')}"
        )
    return "\n".join(lines)


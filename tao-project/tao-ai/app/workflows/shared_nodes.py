"""提供与sharednodes相关的实现。"""

from __future__ import annotations


def format_retrieval_context(hits: list[dict]) -> str:
    """把检索结果格式化成可直接拼进 prompt 的文本。

    大模型更容易消费自然语言文本，所以这里会把命中的知识片段
    整理成“来源 + 分数 + 摘要”的列表形式。
    """
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
    """把工具执行记录格式化成 prompt 文本。

    这样模型在生成回答时，不只看知识库证据，也能看到刚刚实时查出来的业务数据。
    """
    lines: list[str] = []
    for trace in tool_trace:
        lines.append(
            f"- tool={trace.get('tool_name')} status={trace.get('status')} result={trace.get('result_preview')}"
        )
    return "\n".join(lines)

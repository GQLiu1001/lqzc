# AI Legacy Archive

本目录存放已下线的 Java 端旧 AI 链路代码（聊天、知识库、手册检索等）。

迁移策略：
- 原始文件已从 `src/main/java` 移出，不再参与主程序编译。
- 文件统一改为 `.java.disabled` 扩展名，作为“注释/冻结”状态保留。
- 当前 Java 端仅保留 MCP 工具提供能力，模型调用与 agent loop 交给 Python 端。

当前仍在主程序中保留：
- `MCP` 工具：`getInventoryByModel`、`getTopSales`

已归档的旧 HTTP 接口：
- `AiToolController`（原 `/mall/ai/tools/**`）

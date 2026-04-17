# 重建索引与发版检查清单

## 新增知识文档后

1. 确认文件落在正确的 `knowledge/` 或 `manuals/` 目录
2. 执行 `python -m app.rag.ingest` 或调用 `POST /rag/reindex`
3. 查看 `rag.summary` / `rag.reindex` trace，确认文档数和 chunk 数增长

## 发版前至少完成

- 回归 4 组 golden dataset
- 检查 `need_approval` 是否能正确返回 `interrupt`
- 检查越权请求是否稳定拒绝
- 检查 `no_hit` 场景是否仍保持谨慎回答

## 失败处理

- 如果检索命中下降，先看知识文档、scene 和 metadata 是否写对
- 如果回答臆造，优先收紧 grounded answer 与提示词
- 如果权限越界，优先排查 auth、tool 注入和过滤规则

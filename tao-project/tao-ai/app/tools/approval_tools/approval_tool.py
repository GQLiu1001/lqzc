"""提供与审批工具相关的实现。"""

from __future__ import annotations

from app.memory.mysql_store import MySQLStore


class ApprovalTool:
    """审批记录封装层。

    它不直接执行审批后的业务动作，而是专门管理“审批这件事本身”的状态：
    - 发起审批
    - 记录审批人决定
    - 查询审批结果
    """
    def __init__(self, mysql_store: MySQLStore) -> None:
        """初始化审批工具，把运行时依赖和基础状态准备好。"""
        self.mysql_store = mysql_store

    def request(self, *, task_id: str, approval_action: str) -> None:
        """创建或更新一条待审批记录。

        当子工作流判断当前请求属于高风险操作时，就会先走这里，
        把任务挂到审批表里，状态标记为 `PENDING`。
        """
        self.mysql_store.create_or_update_approval(
            task_id=task_id,
            approval_action=approval_action,
            status="PENDING",
            approver_id=None,
            comment=None,
        )

    def decide(self, *, task_id: str, approval_action: str, approver_id: str, comment: str | None) -> None:
        """记录审批人的最终决定。

        这里做的是“记录结论”，不是“执行业务动作”。
        真正审批通过后的执行动作，会由更上层工作流继续推进。
        """
        status = "APPROVED" if approval_action in {"approve", "edit_and_approve"} else "REJECTED"
        self.mysql_store.create_or_update_approval(
            task_id=task_id,
            approval_action=approval_action,
            status=status,
            approver_id=approver_id,
            comment=comment,
        )

    def get(self, task_id: str) -> dict | None:
        """查询某个任务当前的审批记录。"""
        return self.mysql_store.get_approval(task_id=task_id)

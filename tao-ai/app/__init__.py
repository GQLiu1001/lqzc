"""TAO AI v3 agent runtime package.

The architecture follows ``TAOAIv3.md``:
FastAPI -> Supervisor -> Mall/Warehouse Agent -> Skill/Tool execution.
"""

RUNTIME_NAME = "TAO AI v3 Agent Runtime"
ARCHITECTURE_OVERVIEW = (
    "FastAPI -> Supervisor -> Mall/Warehouse Agent -> Skill/Tool execution"
)

__all__ = ["ARCHITECTURE_OVERVIEW", "RUNTIME_NAME"]

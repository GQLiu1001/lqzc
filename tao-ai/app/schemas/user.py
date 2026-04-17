from pydantic import BaseModel, Field


class UserContext(BaseModel):
    user_type: str  # customer / staff
    user_id: int
    role: str | None = None
    role_ids: list[int] = Field(default_factory=list)
    tenant_id: str | None = None
    shop_id: str | None = None
    warehouse_scope: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)

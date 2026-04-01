from __future__ import annotations

from app.config import settings


def collection_for_domain(domain: str) -> str:
    mapping = {
        "customer_service": settings.customer_faq_collection,
        "customer_policy": settings.customer_policy_collection,
        "warehouse": settings.warehouse_sop_collection,
        "rules": settings.business_rules_collection,
        "business_rules": settings.business_rules_collection,
        "cases": settings.historical_case_collection,
        "historical_cases": settings.historical_case_collection,
    }
    return mapping.get(domain, settings.business_rules_collection)


def all_collections() -> list[str]:
    return [
        settings.customer_faq_collection,
        settings.customer_policy_collection,
        settings.warehouse_sop_collection,
        settings.business_rules_collection,
        settings.historical_case_collection,
    ]

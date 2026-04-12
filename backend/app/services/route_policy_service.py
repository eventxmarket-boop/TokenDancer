from typing import List

from sqlalchemy.orm import Session

from app.core.constants import VALID_ROUTE_POLICY_TYPES
from app.models.model_route import ModelRoute
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.models.route_policy import RoutePolicy
from app.schemas.route_policy import RoutePolicyCreate, RoutePolicyUpdate


class RoutePolicyService:
    def list_policies(self, db: Session) -> List[RoutePolicy]:
        return db.query(RoutePolicy).order_by(RoutePolicy.created_at.desc()).all()

    def list_enriched(self, db: Session) -> list[dict]:
        return [self.serialize(policy, db) for policy in self.list_policies(db)]

    def get(self, policy_id: int, db: Session) -> RoutePolicy | None:
        return db.query(RoutePolicy).filter(RoutePolicy.id == policy_id).first()

    def get_enriched(self, policy_id: int, db: Session) -> dict | None:
        policy = self.get(policy_id, db)
        if not policy:
            return None
        return self.serialize(policy, db)

    def get_for_model(self, public_model: str, db: Session) -> RoutePolicy | None:
        return (
            db.query(RoutePolicy)
            .filter(
                RoutePolicy.public_model_name == public_model,
                RoutePolicy.is_active == True,
            )
            .first()
        )

    def _normalize_payload(self, payload: dict) -> dict:
        normalized = dict(payload)
        if "name" in normalized and normalized["name"] is not None:
            normalized["name"] = normalized["name"].strip()
        if "public_model_name" in normalized and normalized["public_model_name"] is not None:
            normalized["public_model_name"] = normalized["public_model_name"].strip()
        if "policy_type" in normalized and normalized["policy_type"] is not None:
            normalized["policy_type"] = normalized["policy_type"].strip().lower()
        if "notes" in normalized and normalized["notes"] is not None:
            normalized["notes"] = normalized["notes"].strip() or None
        return normalized

    def _ensure_provider_available(self, provider_id: int | None, field: str, db: Session) -> None:
        if provider_id is None:
            return
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if not provider:
            raise ValueError(f"{field}不存在，请先创建 Provider")
        has_active_key = (
            db.query(ProviderKey)
            .filter(ProviderKey.provider_id == provider_id, ProviderKey.status == "active")
            .first()
            is not None
        )
        if not has_active_key:
            raise ValueError(f"{field}暂无可用源 Key，请先创建并启用 Provider Key")

    def _validate_route_binding(self, payload: dict, db: Session, existing: RoutePolicy | None = None) -> None:
        public_model_name = payload.get("public_model_name") or (existing.public_model_name if existing else None)
        primary_provider_id = payload.get("primary_provider_id", existing.primary_provider_id if existing else None)
        secondary_provider_id = payload.get("secondary_provider_id", existing.secondary_provider_id if existing else None)
        policy_type = payload.get("policy_type") or (existing.policy_type if existing else "fixed")

        if policy_type not in VALID_ROUTE_POLICY_TYPES:
            raise ValueError(f"非法 policy_type，可选: {', '.join(sorted(VALID_ROUTE_POLICY_TYPES))}")
        if primary_provider_id is None:
            raise ValueError("请先选择主渠道")
        if secondary_provider_id and secondary_provider_id == primary_provider_id:
            raise ValueError("主渠道和备渠道不能相同")

        self._ensure_provider_available(primary_provider_id, "主渠道", db)
        if secondary_provider_id:
            self._ensure_provider_available(secondary_provider_id, "备渠道", db)

        route = db.query(ModelRoute).filter(ModelRoute.public_model_name == public_model_name).first()
        if not route:
            raise ValueError("当前公版模型尚未配置模型映射，请先创建 Model Route")

        allowed_provider_ids = {route.provider_id}
        if route.fallback_provider_id:
            allowed_provider_ids.add(route.fallback_provider_id)
        if primary_provider_id not in allowed_provider_ids:
            raise ValueError("主渠道必须来自该模型已配置的路由 Provider")
        if secondary_provider_id and secondary_provider_id not in allowed_provider_ids:
            raise ValueError("备渠道必须来自该模型已配置的路由 Provider")
        if policy_type in {"fallback", "weighted", "cost_first"} and len(allowed_provider_ids) < 2:
            raise ValueError("当前模型仅配置了单路由，无法使用 fallback / weighted / cost_first 策略")
        if policy_type == "fallback" and not secondary_provider_id:
            raise ValueError("fallback 策略必须配置备渠道")

    def create(self, data: RoutePolicyCreate, db: Session) -> RoutePolicy:
        payload = self._normalize_payload(data.model_dump())
        self._validate_route_binding(payload, db)
        policy = RoutePolicy(**payload)
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    def update(self, policy_id: int, data: RoutePolicyUpdate, db: Session) -> RoutePolicy | None:
        policy = self.get(policy_id, db)
        if not policy:
            return None
        update = self._normalize_payload(data.model_dump(exclude_unset=True))
        self._validate_route_binding(update, db, existing=policy)
        for field, value in update.items():
            setattr(policy, field, value)
        db.commit()
        db.refresh(policy)
        return policy

    def serialize(self, policy: RoutePolicy, db: Session) -> dict:
        route = db.query(ModelRoute).filter(ModelRoute.public_model_name == policy.public_model_name).first()
        primary = db.query(Provider).filter(Provider.id == policy.primary_provider_id).first()
        secondary = None
        if policy.secondary_provider_id:
            secondary = db.query(Provider).filter(Provider.id == policy.secondary_provider_id).first()
        allowed_provider_ids = set()
        if route:
            allowed_provider_ids.add(route.provider_id)
            if route.fallback_provider_id:
                allowed_provider_ids.add(route.fallback_provider_id)
        pair_valid = bool(route and policy.primary_provider_id in allowed_provider_ids and (policy.secondary_provider_id is None or policy.secondary_provider_id in allowed_provider_ids))
        return {
            "id": policy.id,
            "name": policy.name,
            "public_model_name": policy.public_model_name,
            "primary_provider_id": policy.primary_provider_id,
            "primary_provider_name": primary.name if primary else None,
            "secondary_provider_id": policy.secondary_provider_id,
            "secondary_provider_name": secondary.name if secondary else None,
            "policy_type": policy.policy_type,
            "retry_count": policy.retry_count,
            "cooldown_seconds": policy.cooldown_seconds,
            "timeout_seconds": policy.timeout_seconds,
            "is_active": policy.is_active,
            "notes": policy.notes,
            "created_at": policy.created_at,
            "linked_route_id": route.id if route else None,
            "route_ready": bool(route),
            "route_provider_pair_valid": pair_valid,
        }


route_policy_service = RoutePolicyService()

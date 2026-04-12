from typing import List

from sqlalchemy.orm import Session

from app.models.model_route import ModelRoute
from app.models.provider import Provider
from app.models.provider_key import ProviderKey
from app.schemas.model_route import ModelRouteCreate, ModelRouteUpdate


class ModelRouteService:
    def list_routes(self, db: Session) -> List[ModelRoute]:
        return db.query(ModelRoute).order_by(ModelRoute.priority.asc()).all()

    def get(self, route_id: int, db: Session) -> ModelRoute | None:
        return db.query(ModelRoute).filter(ModelRoute.id == route_id).first()

    def get_by_public_model(self, public_model: str, db: Session) -> List[ModelRoute]:
        return (
            db.query(ModelRoute)
            .filter(
                ModelRoute.public_model_name == public_model,
                ModelRoute.is_active == True,
            )
            .order_by(ModelRoute.priority.asc())
            .all()
        )

    def _ensure_provider_ready(self, provider_id: int | None, role: str, db: Session) -> None:
        if provider_id is None:
            return
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if not provider:
            raise ValueError(f"{role}不存在，请先创建 Provider")
        has_active_key = (
            db.query(ProviderKey)
            .filter(
                ProviderKey.provider_id == provider_id,
                ProviderKey.status == "active",
            )
            .first()
            is not None
        )
        if not has_active_key:
            raise ValueError(f"{role}暂无可用源 Key，请先创建并启用 Provider Key")

    def _normalize_payload(self, payload: dict, db: Session) -> dict:
        normalized = dict(payload)
        if "public_model_name" in normalized and normalized["public_model_name"] is not None:
            normalized["public_model_name"] = normalized["public_model_name"].strip()
        if "provider_model_name" in normalized and normalized["provider_model_name"] is not None:
            normalized["provider_model_name"] = normalized["provider_model_name"].strip()
        if "fallback_model_name" in normalized and normalized["fallback_model_name"] is not None:
            normalized["fallback_model_name"] = normalized["fallback_model_name"].strip() or None
        if "notes" in normalized and normalized["notes"] is not None:
            normalized["notes"] = normalized["notes"].strip() or None

        provider_id = normalized.get("provider_id")
        fallback_provider_id = normalized.get("fallback_provider_id")
        if provider_id is not None:
            self._ensure_provider_ready(provider_id, "主渠道", db)
        if fallback_provider_id:
            self._ensure_provider_ready(fallback_provider_id, "备用渠道", db)
        if provider_id and fallback_provider_id and provider_id == fallback_provider_id:
            raise ValueError("主渠道和备用渠道不能相同")
        return normalized

    def create(self, data: ModelRouteCreate, db: Session) -> ModelRoute:
        payload = self._normalize_payload(data.model_dump(), db)
        route = ModelRoute(**payload)
        db.add(route)
        db.commit()
        db.refresh(route)
        return route

    def update(self, route_id: int, data: ModelRouteUpdate, db: Session) -> ModelRoute | None:
        route = self.get(route_id, db)
        if not route:
            return None
        update = self._normalize_payload(data.model_dump(exclude_unset=True), db)
        merged_provider_id = update.get("provider_id", route.provider_id)
        merged_fallback_provider_id = update.get("fallback_provider_id", route.fallback_provider_id)
        if merged_provider_id == merged_fallback_provider_id and merged_provider_id is not None:
            raise ValueError("主渠道和备用渠道不能相同")
        for field, value in update.items():
            setattr(route, field, value)
        db.commit()
        db.refresh(route)
        return route

    def resolve(self, public_model: str, db: Session) -> ModelRoute | None:
        routes = self.get_by_public_model(public_model, db)
        return routes[0] if routes else None


model_route_service = ModelRouteService()

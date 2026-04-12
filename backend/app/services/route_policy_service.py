from sqlalchemy.orm import Session
from app.models.route_policy import RoutePolicy
from app.schemas.route_policy import RoutePolicyCreate, RoutePolicyUpdate


class RoutePolicyService:
    def list(self, db: Session) -> list[RoutePolicy]:
        return db.query(RoutePolicy).order_by(RoutePolicy.created_at.desc()).all()

    def get(self, policy_id: int, db: Session) -> RoutePolicy | None:
        return db.query(RoutePolicy).filter(RoutePolicy.id == policy_id).first()

    def get_for_model(
        self, public_model: str, db: Session
    ) -> RoutePolicy | None:
        return (
            db.query(RoutePolicy)
            .filter(
                RoutePolicy.public_model_name == public_model,
                RoutePolicy.is_active == True,
            )
            .first()
        )

    def create(self, data: RoutePolicyCreate, db: Session) -> RoutePolicy:
        policy = RoutePolicy(**data.model_dump())
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    def update(
        self, policy_id: int, data: RoutePolicyUpdate, db: Session
    ) -> RoutePolicy | None:
        policy = self.get(policy_id, db)
        if not policy:
            return None
        update = data.model_dump(exclude_unset=True)
        for field, value in update.items():
            setattr(policy, field, value)
        db.commit()
        db.refresh(policy)
        return policy


route_policy_service = RoutePolicyService()

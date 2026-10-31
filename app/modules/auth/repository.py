"""Repository layer for users, organizations, and authentication tokens."""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.auth import Organization, OrganizationSettings, User, PasswordResetToken, RefreshToken, UserRole


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID) -> Optional[Organization]:
        return self.db.get(Organization, org_id)

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.slug == slug).first()

    def create(self, name: str, slug: str) -> Organization:
        org = Organization(name=name, slug=slug, is_active=True)
        self.db.add(org)
        self.db.flush()
        settings = OrganizationSettings(organization_id=org.id)
        self.db.add(settings)
        self.db.flush()
        return org

    def update(self, org: Organization, name: Optional[str] = None, is_active: Optional[bool] = None) -> Organization:
        if name is not None:
            org.name = name
        if is_active is not None:
            org.is_active = is_active
        self.db.flush()
        return org


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def list_by_organization(self, org_id: uuid.UUID) -> List[User]:
        return self.db.query(User).filter(User.organization_id == org_id).all()

    def create(
        self,
        organization_id: uuid.UUID,
        email: str,
        password_hash: str,
        full_name: str,
        role: UserRole,
        customer_id: Optional[uuid.UUID] = None,
        is_verified: bool = True,
    ) -> User:
        user = User(
            organization_id=organization_id,
            customer_id=customer_id,
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name,
            role=role.value if hasattr(role, "value") else str(role),
            is_active=True,
            is_verified=is_verified,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_password(self, user: User, new_password_hash: str) -> User:
        user.password_hash = new_password_hash
        self.db.flush()
        return user


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_refresh_token(self, user_id: uuid.UUID, token: str, expires_at: datetime) -> RefreshToken:
        th = _hash_token(token)
        rt = RefreshToken(user_id=user_id, token_hash=th, expires_at=expires_at, revoked_at=None)
        self.db.add(rt)
        self.db.flush()
        return rt

    def get_active_refresh_token(self, token: str) -> Optional[RefreshToken]:
        th = _hash_token(token)
        now = datetime.now(timezone.utc)
        return self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == th,
            RefreshToken.revoked_at == None,
            RefreshToken.expires_at > now,
        ).first()

    def revoke_refresh_token(self, token: str) -> bool:
        th = _hash_token(token)
        rt = self.db.query(RefreshToken).filter(RefreshToken.token_hash == th).first()
        if rt:
            rt.revoked_at = datetime.now(timezone.utc)
            self.db.flush()
            return True
        return False

    def create_reset_token(self, user_id: uuid.UUID, token: str, expires_at: datetime) -> PasswordResetToken:
        th = _hash_token(token)
        prt = PasswordResetToken(user_id=user_id, token_hash=th, expires_at=expires_at, used_at=None)
        self.db.add(prt)
        self.db.flush()
        return prt

    def get_valid_reset_token(self, token: str) -> Optional[PasswordResetToken]:
        th = _hash_token(token)
        now = datetime.now(timezone.utc)
        return self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == th,
            PasswordResetToken.used_at == None,
            PasswordResetToken.expires_at > now,
        ).first()

    def mark_reset_token_used(self, prt: PasswordResetToken) -> None:
        prt.used_at = datetime.now(timezone.utc)
        self.db.flush()

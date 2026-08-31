"""
Authentication API schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.core.schemas.user import UserResponseSchema


class UserRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field("ANALYST")


class OrgSignupSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full Name of the Administrator")
    email: EmailStr = Field(..., description="Work Email")
    password: str = Field(..., min_length=8, description="Password (at least 8 chars)")
    organization_name: str = Field(..., min_length=2, max_length=100, description="Lender / Fund Organization Name")
    organization_industry: str = Field("Private Credit", max_length=100, description="Industry sector")


class InviteAcceptSchema(BaseModel):
    token: str = Field(..., description="Invitation token received from administrator")
    name: str = Field(..., min_length=2, max_length=100, description="Full Name")
    password: str = Field(..., min_length=8, description="Account Password")


class MemberInviteSchema(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: str = Field("ANALYST", description="ADMIN, MANAGER, or ANALYST")


class MemberRoleUpdateSchema(BaseModel):
    role: str = Field(..., description="ADMIN, MANAGER, or ANALYST")


class InvitationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    email: EmailStr
    name: Optional[str] = None
    role: str
    token: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    invite_url: Optional[str] = None


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponseSchema] = None


class TokenRefreshSchema(BaseModel):
    refresh_token: str

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum


class ItemType(str, Enum):
    lost = "lost"
    found = "found"


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MatchResult(BaseModel):
    matched_item_id: int
    matched_description: str
    similarity_score: float


class ItemCreateResponse(BaseModel):
    item_id: int
    item_type: ItemType
    description: str
    matches: List[MatchResult]


class ItemOut(BaseModel):
    id: int
    item_type: ItemType
    description: str
    is_flagged: bool

    class Config:
        from_attributes = True

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, ARRAY, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    item_type = Column(String, nullable=False)  # "lost" or "found"
    description = Column(String, nullable=False)

    # Embeddings stored as plain float arrays for now (Phase 2 scope).
    # Swapping this column type to pgvector's Vector(...) later is the
    # Phase 3 upgrade — everything else stays the same.
    text_vec_mpnet = Column(ARRAY(Float), nullable=False)
    text_vec_clip = Column(ARRAY(Float), nullable=False)
    image_vec_clip = Column(ARRAY(Float), nullable=True)

    is_flagged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="items")

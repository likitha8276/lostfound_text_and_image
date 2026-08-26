from typing import List, Optional
import numpy as np
from sqlalchemy.orm import Session

from db_models import Item, User


def create_user(db: Session, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def add_item(
    db: Session,
    owner_id: int,
    item_type: str,
    description: str,
    text_vec_mpnet: np.ndarray,
    text_vec_clip: np.ndarray,
    image_vec_clip: Optional[np.ndarray] = None,
) -> Item:
    item = Item(
        owner_id=owner_id,
        item_type=item_type,
        description=description,
        text_vec_mpnet=text_vec_mpnet.tolist(),
        text_vec_clip=text_vec_clip.tolist(),
        image_vec_clip=image_vec_clip.tolist() if image_vec_clip is not None else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_opposite_category(db: Session, item_type: str) -> List[Item]:
    opposite = "found" if item_type == "lost" else "lost"
    return db.query(Item).filter(Item.item_type == opposite, Item.is_flagged == False).all()  # noqa: E712


def item_to_vec_dict(item: Item) -> dict:
    """Convert a DB row's list columns back into numpy arrays for matching.py."""
    return {
        "text_vec_mpnet": np.array(item.text_vec_mpnet),
        "text_vec_clip": np.array(item.text_vec_clip),
        "image_vec_clip": np.array(item.image_vec_clip) if item.image_vec_clip is not None else None,
    }


def get_user_items(db: Session, owner_id: int) -> List[Item]:
    return db.query(Item).filter(Item.owner_id == owner_id).all()


def get_all_items(db: Session) -> List[Item]:
    return db.query(Item).all()


def set_item_flag(db: Session, item_id: int, flagged: bool) -> Optional[Item]:
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        return None
    item.is_flagged = flagged
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int) -> bool:
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True

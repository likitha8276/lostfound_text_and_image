from fastapi import FastAPI, UploadFile, Form, File, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, List
from PIL import Image
import io

from database import Base, engine, get_db
from db_models import User, Item
import crud
from auth import (
    hash_password, create_access_token, authenticate_user,
    get_current_user, get_current_admin,
)
from embeddings import embed_text, embed_text_clip, embed_image
from matching import compute_match_score
from schemas import (
    UserCreate, UserOut, Token, ItemCreateResponse, MatchResult, ItemOut,
)

# Creates tables on startup if they don't exist yet.
# For real migrations later, swap this for Alembic.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Lost & Found — Phase 2")

SIMILARITY_THRESHOLD = 0.6


# ---------------------------------------------------------------- AUTH -----
@app.post("/auth/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, user_in.email, hash_password(user_in.password))
    return user


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@app.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------------- ITEMS ----
@app.post("/items", response_model=ItemCreateResponse)
async def create_item(
    item_type: str = Form(...),
    description: str = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    text_vec_mpnet = embed_text(description)
    text_vec_clip = embed_text_clip(description)

    image_vec_clip = None
    if image is not None:
        img_bytes = await image.read()
        pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        image_vec_clip = embed_image(pil_img)

    item = crud.add_item(
        db, current_user.id, item_type, description,
        text_vec_mpnet, text_vec_clip, image_vec_clip,
    )

    new_item_vecs = {
        "text_vec_mpnet": text_vec_mpnet,
        "text_vec_clip": text_vec_clip,
        "image_vec_clip": image_vec_clip,
    }

    candidates = crud.get_opposite_category(db, item_type)
    matches = []
    for c in candidates:
        combined = compute_match_score(new_item_vecs, crud.item_to_vec_dict(c))
        # Threshold is now actually applied — this was a no-op bug in the
        # original code (`if True:` let every candidate through).
        if combined >= SIMILARITY_THRESHOLD:
            matches.append(MatchResult(
                matched_item_id=c.id,
                matched_description=c.description,
                similarity_score=round(combined, 4),
            ))

    matches.sort(key=lambda m: m.similarity_score, reverse=True)

    return ItemCreateResponse(
        item_id=item.id,
        item_type=item.item_type,
        description=item.description,
        matches=matches,
    )


@app.get("/items/mine", response_model=List[ItemOut])
def my_items(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dashboard endpoint — a logged-in user's own submitted items."""
    return crud.get_user_items(db, current_user.id)


# ---------------------------------------------------------------- ADMIN ----
@app.get("/admin/items", response_model=List[ItemOut])
def admin_list_items(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return crud.get_all_items(db)


@app.patch("/admin/items/{item_id}/flag", response_model=ItemOut)
def admin_flag_item(item_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    item = crud.set_item_flag(db, item_id, True)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/admin/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_item(item_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    deleted = crud.delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")

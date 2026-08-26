# AI Lost & Found — Phase 2 upgrade

This is your Phase 1 code (embeddings.py, matching.py, main.py) upgraded to
match Phase 2 of your project plan: real persistence, auth, a user
dashboard, and admin moderation.

## What changed from your original code

- **Persistence:** `storage.py`'s in-memory Python list is gone. `db_models.py`
  + `database.py` + `crud.py` replace it with real PostgreSQL tables via
  SQLAlchemy (`users`, `items`). Embeddings are stored as float arrays for now —
  swapping to pgvector's native `Vector` type later (Phase 3) only touches
  `db_models.py` and the query in `crud.get_opposite_category`, nothing else.
- **Auth:** `auth.py` adds signup/login with bcrypt password hashing and JWT
  tokens (`python-jose`), plus `get_current_user` / `get_current_admin`
  FastAPI dependencies to protect routes.
- **Bug fix:** your original `main.py` had `if True:` where the similarity
  threshold check should have been — every candidate was returned regardless
  of score. Fixed to `if combined >= SIMILARITY_THRESHOLD`.
- **Dashboard:** `GET /items/mine` — a logged-in user's own submitted items.
- **Admin moderation:** `GET /admin/items` (list all), `PATCH
  /admin/items/{id}/flag` (flag suspicious item), `DELETE /admin/items/{id}`
  — all require `is_admin=True` on the user.
- Removed the `print()` debug statements from `matching.py` — swap in proper
  `logging` if you want that visibility back in a non-debug way.

## Setup

1. Install Postgres locally (or use a hosted one) and create a database:
   ```bash
   createdb lost_found
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables (or edit the defaults in `database.py` / `auth.py`):
   ```bash
   export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/lost_found"
   export JWT_SECRET_KEY="something-long-and-random"
   ```
4. Run it:
   ```bash
   uvicorn main:app --reload
   ```
5. Tables are auto-created on startup (`Base.metadata.create_all`). For a
   real project going forward, switch to Alembic migrations instead of
   relying on this.

## To make a user an admin

There's no signup flag for this on purpose (you don't want users
self-promoting to admin). After signing up, flip it directly in the DB:

```sql
UPDATE users SET is_admin = true WHERE email = 'you@example.com';
```

## Trying it end-to-end

```bash
# 1. Sign up
curl -X POST localhost:8000/auth/signup -H "Content-Type: application/json" \
  -d '{"email":"a@test.com","password":"pass123"}'

# 2. Log in (form-encoded, not JSON — OAuth2PasswordRequestForm)
curl -X POST localhost:8000/auth/login \
  -d "username=a@test.com&password=pass123"
# -> copy the access_token from the response

# 3. Submit an item (use the token from step 2)
curl -X POST localhost:8000/items \
  -H "Authorization: Bearer <TOKEN>" \
  -F "item_type=lost" -F "description=red backpack with a keychain"

# 4. See your own items
curl localhost:8000/items/mine -H "Authorization: Bearer <TOKEN>"
```

## Still not done (Phase 3, optional stretch)

- pgvector for native in-DB similarity search instead of pulling every
  opposite-category row into Python and looping (fine at small scale, won't
  scale to a real campus-wide dataset).
- Redis caching for repeated similarity computations.
- Geo/time signals blended into the match score.

Don't add these to your resume until they're actually in the code — same
mistake as last time.

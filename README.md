# mental_hospital — shared version

This version keeps the original hand-drawn UI but moves profiles/posts from browser `localStorage` to a shared Django database.

## Features
- Same `name + code` reopens the same profile.
- Same name with a different code creates a separate room.
- Posts are shared across devices.
- Public posts appear in the hospital tour.
- Private posts are visible only in the owner's room.
- Only the logged-in owner can edit their posts.
- Only the logged-in owner can delete their own profile; deleting a profile also deletes its posts.
- Login uses a server-side session cookie.
- The code is hashed for password verification and a separate HMAC key is used to find the profile.

## Local run
```bash
py -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

Open http://127.0.0.1:8000/

## Production
The app is designed for a Python web host such as Render. Use PostgreSQL in production by setting `DATABASE_URL` and set a strong `DJANGO_SECRET_KEY`. Do not rely on SQLite on an ephemeral hosting filesystem.

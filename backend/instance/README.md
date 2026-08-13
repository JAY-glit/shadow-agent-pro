# instance/

This folder holds `shadowagent.db`, the SQLite database — created
automatically the first time you run `python app.py` (via
`db.create_all()` in `app.py`). It's empty in the repository on purpose;
the database is runtime state, not source code.

## Safe to delete

Deleting `shadowagent.db` and restarting the app gives you a fresh, empty
threat history. This is the correct fix if:

- You've upgraded to a version of the project with a changed `Threat`
  model (SQLAlchemy's `db.create_all()` only creates missing tables, it
  never alters an existing one — so a schema change like an added column
  needs a fresh database file, not a migration, at this project's scale).
- The database is in a confusing state during development and you'd
  rather start clean than debug stale data.

## Not meant for production

SQLite is fine for a demo/capstone project but has real limits under
concurrent writes (the Flask API and the Celery worker both write to it).
See the "Known limitations" section of the main README — a real
deployment would use PostgreSQL instead.

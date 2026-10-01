# MySQL Database Setup

This guide sets up the local MySQL database for Smart Inventory Market. The database engine is **MySQL Server 8.x**. **MySQL Workbench** is the visual administration and ERD tool; it does not store the database by itself.

## 1. Install Software

Install MySQL Server 8.x and MySQL Workbench. Start the MySQL Server service, then open Workbench and confirm that a local administrative connection works.

## 2. Create the Database and Recommended App User

In Workbench, connect with an administrative account and open `scripts/db/bootstrap_database.sql`. Replace `CHANGE_ME` only in the Workbench editor with a strong local password, then run it. The tracked script creates:

- database: `smart_inventory_market`
- recommended local application account: `smart_inventory_app`
- database character set: `utf8mb4`

Do not commit the password or an edited copy of the script.

## 3. Configure the Ignored Local Environment

Copy `.env.example` to `.env`, then replace the placeholder locally:

```dotenv
APP_ENV=development
DATABASE_URL=mysql+pymysql://smart_inventory_app:YOUR_LOCAL_PASSWORD@localhost:3306/smart_inventory_market?charset=utf8mb4
SECRET_KEY=YOUR_LOCAL_DEVELOPMENT_SECRET
```

`.env` is ignored by Git. Never put a real password in Markdown, source code, tests, or commits.

## 4. Install Python Dependencies

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The application uses PyMySQL through the `mysql+pymysql://` URL scheme.

## 5. Apply and Inspect the Migration

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe heads
.\.venv\Scripts\alembic.exe check
```

P13's initial revision is `f86d36b27719`. Do not create application tables manually in Workbench; SQLAlchemy models and Alembic own the schema.

## 6. Start and Check FastAPI

```powershell
.\.venv\Scripts\uvicorn.exe backend.app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/health` — process health.
- `http://127.0.0.1:8000/health/db` — executes a lightweight database `SELECT 1` and returns either connected or a non-secret unavailable response.

## 7. Create a Workbench ERD from the Real Schema

After `alembic upgrade head` succeeds:

1. In MySQL Workbench select **Database → Reverse Engineer**.
2. Select the local MySQL connection.
3. Select schema `smart_inventory_market`.
4. Import the schema and arrange the EER diagram.
5. Save/export the diagram only as a visualization of the Alembic-managed schema.

Do not manually maintain a separate Workbench-only schema. Capture a clear ERD screenshot for thesis evidence after reverse engineering.

## Common Errors

| Symptom | Likely cause and safe response |
| --- | --- |
| Access denied | Check the user/password in your local `.env`; use Workbench as an admin to create/grant the recommended app user. Do not publish the password. |
| Unknown database | Run `scripts/db/bootstrap_database.sql` in Workbench, then retry Alembic. |
| MySQL service stopped | Start the MySQL Server service in Windows Services, then reconnect in Workbench. |
| Wrong port | Confirm the MySQL Server port (normally `3306`) and update only local `.env`. |
| Missing PyMySQL | Run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. |
| Migration revision mismatch | Run `alembic current`, inspect the migration files, and never drop unrelated databases to resolve it. |

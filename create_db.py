"""

    Only need to call this once to initialize the database with schema.sql.
    - Will wipe all data (as def. in schema.sql)

    The compose volume will persist db on disk through future container creations.

    Ensure hostname is "localhost" in init.py when running this outside a container.

"""

from website import create_app, get_db

app = create_app()

with app.app_context():  # ensures session and g are available
    with open("schema.sql", "r") as f:
        sql_script = f.read()

    db = get_db()
    cur = db.cursor()
    cur.execute(sql_script)
    db.commit()

    print("Database schema successfully created.")
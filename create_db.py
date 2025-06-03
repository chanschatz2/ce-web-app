"""

    Only need to call this once to initialize the database with schema.sql.
    The compose volume will have it persist on disk through future container creations.

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
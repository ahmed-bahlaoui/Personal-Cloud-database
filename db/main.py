from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cloud_storage"

engine = create_engine(DATABASE_URL)

query = '''
 SELECT original_name, size_bytes
    FROM files
    WHERE owner_id = 1 AND is_deleted = FALSE
'''

with engine.connect() as connection:
    result = connection.execute(text(query))

    print("Users table:")
    for row in result:
        print(row)

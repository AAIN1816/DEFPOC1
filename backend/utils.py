import uuid

def generate_run_id():
    return str(uuid.uuid4())

def get_dummy_columns():
    return ["id", "name", "age", "email", "salary"]

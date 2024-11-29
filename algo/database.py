import firebase_admin
from firebase_admin import credentials, firestore


def init_db():
    cred = credentials.Certificate("db_config.json")
    firebase_admin.initialize_app(cred)


def get_users(db):
    users_ref = db.collection("users")
    return users_ref.stream()


def get_history(db):
    history_ref = db.collection("history")
    return history_ref.stream()


def get_data():
    init_db()
    db = firestore.client()
    return get_users(db), get_history(db)


def update(pairs):
    # Put newly created pairs in the database
    # TODO
    pass

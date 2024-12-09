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


def set_config_true(db):
    conf = db.collection("config").document("matching")
    conf.update({"send": True})


def update(pairs):
    db = firestore.client()
    history_ref = db.collection("history")
    match_pairs = {
        'timestamp': firestore.SERVER_TIMESTAMP,
        "match_pairs": [
            {
                "user1_id": pair[0],
                "user1_isLike": 0,
                "user2_id": pair[1],
                "user2_isLike": 0,
                "meeting_happened": None,
            }
            for pair in pairs
        ]
    }
    set_config_true(db)
    history_ref.add(match_pairs)
    # print(pairs)

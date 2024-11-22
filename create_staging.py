import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firestore():
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db

def create_staging_database():
    db = initialize_firestore()

    users_ref = db.collection('users')

    sample_users = [
        {
            'tg_id': '123456789',
            'full_name': 'Alice Smith',
            'major': 'Computer Science',
            'degree': 'Bachelor',
            'year': '2',
            'country': 'Germany',
            'interests': ['music', 'sports'],
            'description': 'I love programming and hiking.',
            'photo': 'photo_file_id_1',
            'is_active': True,
            'last_matched': None
        },
        {
            'tg_id': '987654321',
            'full_name': 'Bob Johnson',
            'major': 'Mathematics',
            'degree': 'Masters',
            'year': '1',
            'country': 'France',
            'interests': ['books', 'travel'],
            'description': 'A math enthusiast and traveler.',
            'photo': 'photo_file_id_2',
            'is_active': True,
            'last_matched': None
        }
    ]

    for user in sample_users:
        user_id = user['tg_id']
        users_ref.document(user_id).set(user)

    print('Sample users created.')

    history_ref = db.collection('history')

    sample_history = {
        'timestamp': firestore.SERVER_TIMESTAMP,
        'match_pairs': [
            {
                'user1_id': '123456789',
                'user2_id': '987654321',
                'meeting_happened': None,
                'user1_isLike': None,
                'user2_isLike': None
            }
        ]
    }

    history_ref.add(sample_history)
    print('Sample history created.')

    config_ref = db.collection('config').document('matching')
    config_data = {
        'send': False
    }
    config_ref.set(config_data)
    print('Config document created.')

if __name__ == '__main__':
    create_staging_database()

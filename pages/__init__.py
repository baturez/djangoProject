from pymongo import MongoClient
import datetime
import bcrypt
from pymongo.errors import ConnectionFailure



MONGO_URI = 'mongodb+srv://batuhanfahri06:PezQB4OKaTHSEjFm@bartini.qyrro.mongodb.net/?retryWrites=true&w=majority&appName=bartini'
DATABASE_NAME = 'my_database'
USER_COLLECTION = 'users'
POST_COLLECTION = 'posts'
def consumers():
    return None
def save_user_to_mongo(email, username, password):
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[USER_COLLECTION]

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_data = {
            "email": email,
            "username": username,
            "password": hashed_password
        }

        result = collection.insert_one(user_data)
        if result.acknowledged:
            print(f"Kullanıcı eklendi ID: {result.inserted_id}")
            return True
        else:
            print("Kullanıcı MongoDB'ye eklenemedi.")
            return False

    except ConnectionFailure as e:
        print(f"MongoDB bağlantı hatası: {e}")
        return False
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
        return False

def save_post_to_mongo(username, content):
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[POST_COLLECTION]

        post_data = {
            "username": username,
            "content": content,
            "created_at": datetime.datetime.now()
        }

        result = collection.insert_one(post_data)
        if result.acknowledged:
            print(f"Post eklendi ID: {result.inserted_id}")
            return True
        else:
            print("Post MongoDB'ye eklenemedi.")
            return False

    except ConnectionFailure as e:
        print(f"MongoDB bağlantı hatası: {e}")
        return False
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
        return False


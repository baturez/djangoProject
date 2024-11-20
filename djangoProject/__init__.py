from pymongo import MongoClient


def save_to_mongo(email, username, password):
    # MongoDB'ye bağlanma
    client = MongoClient('mongodb://localhost:27017/')

    # Veritabanı ve koleksiyon oluşturma (eğer yoksa)
    db = client['my_database']  # Veritabanı adı
    collection = db['users']  # Koleksiyon adı

    # Kullanıcı verilerini kaydetme
    user_data = {
        "email": email,
        "username": username,
        "password": password  # Parolayı düz metin olarak saklamaktan kaçının! Şifrelemeniz gerekir.
    }

    # Verileri MongoDB'ye ekleme
    result = collection.insert_one(user_data)
    print(f"User added with id: {result.inserted_id}")

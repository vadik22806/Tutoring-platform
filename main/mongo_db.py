# echoserver/mongo_db.py
import pymongo

# Подключаемся к локальному серверу MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")

# Выбираем базу данных
db = client["bookstore"]

# Добавление книги
db.books.insert_one({"title": "Пример книги", "author": "Автор"})

# Получение всех книг
for book in db.books.find():
    print(book)
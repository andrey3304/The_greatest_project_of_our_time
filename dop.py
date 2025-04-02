from data.classes import User
from database import db_session


user = User()
user.username = "Andrey"
user.password = "qwerty"
user.email = "email@email.ru"
db_sess = db_session.create_session()
db_sess.add(user)
db_sess.commit()

from flask import Blueprint, jsonify

from database import db_session
from data.classes import User


blueprint = Blueprint('users_api', __name__, template_folder='templates')


@blueprint.route('/api/users', methods=['GET'])
def get_users():
    db_sess = db_session.create_session()
    all_users = db_sess.query(User).filter('god' == User.name).first()
    return all_users

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class AddTopicForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    about = TextAreaField('Описание[админы будут читать его для принятия решения]')
    submit = SubmitField('Отправить')
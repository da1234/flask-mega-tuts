from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,BooleanField, SubmitField,TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError,Length
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    about_me = TextAreaField('AboutMe',validators=[Length(min=0,max=140)])
    submit = SubmitField('Submit')

    def __init__(self,original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args,**kwargs)
        self.original_username = original_username

    def validate_username(self,username):
        print("validating")
        if username.data != self.original_username:
            u = User.query.filter_by(username=self.username.data).first()
            print(f"searched and found {u}")
            if u is not None:
                print(f"not None")
                return ValidationError('Please chose a different name')

class PostForm(FlaskForm):
    post = TextAreaField('Say Something', validators=[
        DataRequired(), Length(min=1,max=140)])
    submit = SubmitField("Submit")


class MessageForm(FlaskForm):
    message = TextAreaField('Message',validators=[DataRequired(),Length(min=0,max=140)])
    submit = SubmitField('Send')
    

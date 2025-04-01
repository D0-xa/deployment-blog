from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField, TelField, TextAreaField
from wtforms.validators import InputRequired, URL, Email, Length
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[InputRequired()])
    subtitle = StringField("Subtitle", validators=[InputRequired()])
    img_url = StringField("Blog Image URL", validators=[InputRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[InputRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password",
                             validators=[InputRequired(),
                                         Length(min=8, message="Password must be at least 8 characters long.")])
    name = StringField("Name", validators=[InputRequired()])
    submit = SubmitField("Sign me up!".upper())


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password",
                             validators=[InputRequired()])
    submit = SubmitField("Let me in!".upper())


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[InputRequired()])
    submit = SubmitField("Submit comment".upper())


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired()], render_kw={"placeholder": "Enter your name..."})
    email = EmailField("Email address", validators=[InputRequired(), Email()], render_kw={"placeholder": "Enter your email..."})
    tel = TelField("Phone Number", validators=[InputRequired()], render_kw={"placeholder": "Enter your phone number..."})
    message = TextAreaField("Message", validators=[InputRequired()], render_kw={"placeholder": "Enter your message here..."})
    submit = SubmitField("send".upper())

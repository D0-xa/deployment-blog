from datetime import date
from typing import List

from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5

# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '9e3e68bd4f76876f8ab73fda50b24cca21aeedaf95fd396c7bc99d86929e2535'
ckeditor = CKEditor(app)
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped["User"] = relationship(back_populates="posts")
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    blog_comments = relationship("Comment", back_populates="blog_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    posts: Mapped[List["BlogPost"]] = relationship(back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    comment_author: Mapped["User"] = relationship(back_populates="comments")
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    blog_post: Mapped["BlogPost"] = relationship(back_populates="blog_comments")
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))


with app.app_context():
    db.create_all()

def gravatar(email, size=100, default='identicon', rating='g'):
    email_hash = md5(email.lower().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}&r={rating}"


def admin_only(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return func(*args, **kwargs)

        return abort(403)
    return wrapper_func


def commenter_only(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        user_comments = db.session.execute(db.select(Comment).where(Comment.author_id == current_user.id)).scalars().all()
        if current_user.is_authenticated and kwargs.get("comment_id") in [comment.id for comment in user_comments]:
            return func(*args, **kwargs)
        return abort(403)

    return wrapper_func


@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        try:
            new_user = User(
                email=register_form.email.data, # type: ignore[call-arg]
                password=generate_password_hash(register_form.password.data, "pbkdf2", 8), # type: ignore[call-arg]
                name=register_form.name.data.title() # type: ignore[call-arg]
            )
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))
        else:
            login_user(new_user)
            return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        try:
            user = db.session.execute(db.select(User).where(User.email == login_form.email.data)).scalar_one()
        except NoResultFound:
            flash('Invalid email. Please try again or register if you have no account.')
            return redirect(url_for('login'))
        else:
            if check_password_hash(user.password, login_form.password.data):
                login_user(user)
                return redirect(url_for("get_all_posts"))
            else:
                flash('Incorrect Password. Please try again.')

    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)

    if current_user.is_authenticated:
        comment_form = CommentForm()
        if comment_form.validate_on_submit():
            new_comment = Comment(
                text=comment_form.comment_text.data,
                comment_author=current_user,
                blog_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for("show_post", post_id=post_id))
        return render_template("post.html", post=requested_post, form=comment_form, gravatar=gravatar)
    return render_template("post.html", post=requested_post, gravatar=gravatar)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/delete/comment/<int:comment_id>")
@commenter_only
def delete_comment(comment_id):
    comment_to_delete = db.get_or_404(Comment, comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()

    return redirect(url_for("show_post", post_id=comment_to_delete.post_id))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)

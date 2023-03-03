from flask import Flask, jsonify, request, abort, redirect, url_for, render_template
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import sqlalchemy
from sqlalchemy import desc
import json
import pymysql
from datetime import datetime
from sqlalchemy import DateTime

host = 'localhost'
user = 'root'
passwd = '12345'
database = 'blog_db'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + user + ':' + passwd + '@' + host + '/' + database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.app_context().push()
app.debug = True
bcryptObj = Bcrypt(app)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Users(db.Model):
    user_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    user_email = db.Column(db.String(255), unique=True, nullable=False)
    user_password = db.Column(db.String(1000), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    authenticated = db.Column(db.Boolean, default=False)

    def is_active(self):
        return True

    def get_id(self):
        return self.user_id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False


class Blog_s(db.Model):
    blog_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    blog_name = db.Column(db.String(255), nullable=False)
    blog_text = db.Column(db.Text, nullable=False)
    blog_created = db.Column(DateTime, default=datetime.now)
    blog_tag = db.Column(db.String(150), nullable=False)
    blog_publish = db.Column(db.Boolean, default=False, nullable=False)
    blog_created_by = db.Column(db.Integer, db.ForeignKey(Users.user_id), nullable=False)

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.blog_id,
            'blog_text': self.blog_text,
            "blog_name": self.blog_name,
            "blog_created": self.blog_created,
            "blog_published": self.blog_publish,
            "blog_tag": self.blog_tag
        }


db.create_all()


@login_manager.user_loader
def user_loader(user_id):
    return Users.query.get(user_id)


# index page
@app.route("/", methods=['GET'])
def index():
    blogs = Blog_s.query.filter_by(blog_publish=True).order_by(Blog_s.blog_created.desc())
    context = {"data": [blog.serialized for blog in blogs]}
    return render_template("index.html", blogs=context['data'])


# login page
@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_email = request.form.get('username')
        user_password = request.form.get('password')
        try:
            user_data = Users.query.filter_by(user_email=user_email).first()
        except sqlalchemy.exc.NoResultFound:
            abort(400, description="user not found")

        if bcryptObj.check_password_hash(user_data.user_password, user_password):
            user_data.authenticated = True
            db.session.add(user_data)
            db.session.commit()
            login_user(user_data, remember=True)
            url = f"/user/{user_data.user_id}"
            return redirect(url)
        else:
            message = {"data": "Wrong Password"}
            return render_template("login.html", result=message)
    if request.method == 'GET':
        return render_template('login.html')


# userpage
@app.route("/user/<int:user_id>", methods=['POST', 'GET'])
@login_required
def user(user_id):
    if request.method == 'GET':
        blog_data = Blog_s.query.filter_by(blog_created_by=user_id).order_by(desc(Blog_s.blog_created))
        context = {"data": [blog.serialized for blog in blog_data]}
        return render_template("home.html", blogs=context['data'])


# register page
@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_email = request.form.get('username')
        user_password = request.form.get('password')
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        hashPassword = bcryptObj.generate_password_hash(user_password)
        user = Users(user_email=user_email, user_password=hashPassword, first_name=first_name, last_name=last_name)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return render_template("error.html", error=e)

    elif request.method == 'GET':
        return render_template('register.html')


@app.route("/add_blog", methods=['POST', 'GET'])
@login_required
def add_blog():
    if request.method == 'POST':
        user = current_user
        blog_name = request.form.get('inputTitle')
        blog_text = request.form.get('inputDescription')
        blog_tag = request.form.get('inputTag')
        blog_publish = False
        if request.form.get('blog_publish') == "true":
            blog_publish = True
        blog_created_by = user.user_id
        blog = Blog_s(blog_name=blog_name, blog_text=blog_text, blog_publish=blog_publish, blog_tag=blog_tag,
                      blog_created_by=blog_created_by)
        try:
            db.session.add(blog)
            db.session.commit()
        except Exception as e:
            return render_template("error.html", error=e)
        url = f"/user/{user.user_id}"
        return redirect(url)

    elif request.method == 'GET':
        user = current_user
        data = {"userID": user.user_id}
        return render_template("AddBlog.html", result=data)


@app.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))


@app.route("/fetch_blog/<int:blog_id>", methods=['POST', 'GET'])
@login_required
def fetch_blog(blog_id):
    if request.method == 'GET':
        user = current_user
        blog = Blog_s.query.filter_by(blog_id=blog_id).first()
        context = {"data": [blog.serialized], "user": user.user_id}
        return render_template("blog.html", blogs=context)


# update blog
@app.route("/update_blog/<int:blog_id>", methods=['POST', 'GET'])
@login_required
def update_blog(blog_id):
    if request.method == 'POST':
        print("paila haribabu")
        blog = Blog_s.query.filter_by(blog_id=blog_id).first()
        blog_text = request.form.get('inputDescription')
        blog_tag = request.form.get('inputTag')
        if request.form.get('blog_publish') == "true":
            blog_publish = True
        else:
            blog_publish = False

        blog.blog_text = blog_text
        blog.blog_tag = blog_tag
        blog.blog_publish = blog_publish
        db.session.commit()
        url = f'/fetch_blog/{blog_id}'
        return redirect(url)
    elif request.method == 'GET':
        user = current_user
        blog = Blog_s.query.filter_by(blog_id=blog_id).first()
        context = {"data": [blog.serialized], "user": user.user_id}
        print(context)
        return render_template("editBlog.html", result=context)


@app.route("/delete_blog/<int:blog_id>", methods=['DELETE', 'GET'])
@login_required
def delete_blog(blog_id):
    if request.method == 'GET':
        user = current_user
        print(user.user_id)
        blog = Blog_s.query.filter_by(blog_id=blog_id).first()
        try:
            db.session.delete(blog)
            db.session.commit()
        except:
            pass
        url = f"/user/{user.user_id}"
        return redirect(url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1048, debug=True)

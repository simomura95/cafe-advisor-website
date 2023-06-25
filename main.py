import os
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from werkzeug.security import generate_password_hash, check_password_hash
from forms import *  # CreatePostForm, RegisterForm, LoginForm

# create flask app
app = Flask(__name__)
app.app_context().push()  # to avoid errors during runtime

# connect to database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe-website.db'  # db path and name. If not existing, is created with db.create_all()
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # block warnings from sqlalchemy
db = SQLAlchemy(app)

Bootstrap(app)  # bootstrap on app
ckeditor = CKEditor(app)  # CKeditor fields on app

# flask login
app.config['SECRET_KEY'] = os.environ.get('FLASK_LOGIN_KEY')  # needed for flask login
login_manager = LoginManager()
login_manager.init_app(app)

# Gravatar to generate users avatar automatically from their email
gravatar = Gravatar(app, size=30, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)


# configure database tables
class Cafe(db.Model):
    __tablename__ = "cafes"  # (optional) explicit a name for the table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)
    # RELATIONSHIP: to establish relations between tables. Cafe is 'father', so it has just one line
    # this field can't be seen explicitly in table navigation!
    reviews = relationship("Review", back_populates="cafe")
    # reviews: field of Cafe, callable for joins
    # Review: class name to join
    # back_populates='cafe': field of Review on which to join


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))
    reviews = relationship("Review", back_populates="author")


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    # CHILD TABLE, so it has a second line specifying the foreign key on parent table
    # this field can be seen in table navigation
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates="reviews")
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'))
    cafe = relationship("Cafe", back_populates="reviews")


db.create_all()  # to create entire db or missing tables


# ESSENTIAL or else login module does not work!
@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).filter_by(id=int(user_id))).scalar()


# utility decorator function to make some other functions only accessible to admins
def admin_only(fun):
    @wraps(fun)  # senza questa ho errore!
    def wrap(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return abort(403)
        else:
            return fun(*args, **kwargs)

    return wrap


# homepage
@app.route("/")
def home():
    return render_template("index.html")


# list of cafes in db, with filtering options
@app.route("/cafes", methods=["GET", "POST"])
def cafe_list():
    form = FilterForm()
    if form.validate_on_submit():
        if form.reset.data:  # if 'remove filter' was pressed, reload the page
            return redirect(url_for("cafe_list"))
        # else, dynamically build query depending on filter options given
        conditions = []
        if form.name.data != '':
            conditions.append(func.lower(Cafe.name).like(func.lower(f"%{form.name.data}%")))
        if form.location.data != '':
            conditions.append(func.lower(Cafe.location).like(func.lower(f"%{form.location.data}%")))
        if form.sockets.data:
            conditions.append(Cafe.has_sockets.is_(True))
        if form.toilet.data:
            conditions.append(Cafe.has_toilet.is_(True))
        if form.wifi.data:
            conditions.append(Cafe.has_wifi.is_(True))
        if form.calls.data:
            conditions.append(Cafe.can_take_calls.is_(True))
        cafes = db.session.execute(db.select(Cafe).where(*conditions)).scalars().all()
        # with *, conditions are unpacked and correctly evaluated. Without *, I get error
    else:  # if no filter is given, show all cafes in db
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
        # with 'scalars' I can access single elements instead of rows
    return render_template("cafes.html", all_cafes=cafes, filter_form=form)


# 'enter' into a cafe details. This actually contains just reviews from users, in a blog-style fashion
# html file shows field to insert reviews only to logged-in users
@app.route("/cafe/<int:cafe_id>", methods=["GET", "POST"])
def cafe_detail(cafe_id):  # get cafe_id from URL
    requested_cafe = db.session.execute(db.select(Cafe).filter_by(id=cafe_id)).scalar()
    review_form = ReviewForm()
    if review_form.validate_on_submit():
        new_review = Review(
            text=review_form.review.data,
            author_id=current_user.id,
            cafe_id=cafe_id,
        )
        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for('cafe_detail', cafe_id=cafe_id))
    return render_template("cafe_review.html", cafe=requested_cafe, form=review_form)


# Add a new café (only logged-in users)
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_cafe():
    new_cafe_form = NewCafeForm()
    if new_cafe_form.validate_on_submit():
        cafe_to_add = Cafe(
            name=new_cafe_form.name.data,
            map_url=new_cafe_form.map_url.data,
            img_url=new_cafe_form.img_url.data,
            location=new_cafe_form.location.data,
            has_sockets=bool(new_cafe_form.sockets.data),
            has_toilet=bool(new_cafe_form.toilet.data),
            has_wifi=bool(new_cafe_form.wifi.data),
            can_take_calls=bool(new_cafe_form.calls.data),
            seats=new_cafe_form.seats.data,
            coffee_price=f"£{'{:.2f}'.format(new_cafe_form.coffee_price.data)}"  # format price
        )
        if db.session.execute(db.select(Cafe).where(Cafe.name == cafe_to_add.name)).first():
            flash("We already have this café")
        else:
            db.session.add(cafe_to_add)
            db.session.commit()
            return redirect(url_for('cafe_list'))
    # else:  # for debug
    #     print("Form validation failed")
    #     print(form.errors)
    return render_template("add_cafe.html", form=new_cafe_form)


# Update Record (only admins)
@app.route("/update-cafe/<int:cafe_id>", methods=["GET", "POST"])
@admin_only
def update_cafe(cafe_id):
    cafe_to_edit = db.session.execute(db.select(Cafe).filter_by(id=cafe_id)).scalar()
    if not cafe_to_edit:  # without this, it crashes if an invalid id is given manually from url
        return abort(404, "Invalid café id")
    edit_form = NewCafeForm(
        name=cafe_to_edit.name,
        map_url=cafe_to_edit.map_url,
        img_url=cafe_to_edit.img_url,
        location=cafe_to_edit.location,
        sockets=cafe_to_edit.has_sockets,
        toilet=cafe_to_edit.has_toilet,
        wifi=cafe_to_edit.has_wifi,
        calls=cafe_to_edit.can_take_calls,
        seats=cafe_to_edit.seats,
        coffee_price=float(cafe_to_edit.coffee_price[1:]),
    )
    if edit_form.validate_on_submit():
        print(edit_form.data)
        cafe_to_edit.name = edit_form.name.data
        cafe_to_edit.map_url = edit_form.map_url.data
        cafe_to_edit.img_url = edit_form.img_url.data
        cafe_to_edit.location = edit_form.location.data
        cafe_to_edit.has_sockets = bool(edit_form.sockets.data)
        cafe_to_edit.has_toilet = bool(edit_form.toilet.data)
        cafe_to_edit.has_wifi = bool(edit_form.wifi.data)
        cafe_to_edit.can_take_calls = bool(edit_form.calls.data)
        cafe_to_edit.seats = edit_form.seats.data
        cafe_to_edit.coffee_price = f"£{'{:.2f}'.format(edit_form.coffee_price.data)}"
        print(cafe_to_edit)

        db.session.commit()
        return redirect(url_for('cafe_list'))
    return render_template('add_cafe.html', form=edit_form)


# Delete Record (only admins)
@app.route("/delete-cafe/<int:cafe_id>")
@admin_only
def delete_cafe(cafe_id):
    cafe_to_delete = db.session.execute(db.select(Cafe).filter_by(id=cafe_id)).scalar()
    if not cafe_to_delete:  # without this, it crashes if an invalid id is given manually from url (as in 'update_cafe')
        return abort(404, "Invalid café id")
    db.session.delete(cafe_to_delete)
    db.session.commit()
    return redirect(url_for('cafe_list'))


# register a new user, who must have a mail and username not already in use
# to show all functionality, every new user is registered as admin
# password is hashed and then saved in db, so that it is secure
@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        if db.session.execute(db.select(User).filter_by(email=register_form.email.data)).scalar():
            register_form.email.errors.append('Mail already in use')
            # flash("Mail already in use")
        elif db.session.execute(db.select(User).filter_by(username=register_form.username.data)).scalar():
            register_form.username.errors.append('Username already in use')
            # flash("Username already in use")
        else:
            new_user = User(
                email=register_form.email.data,  # ignore warning, it is correct
                password=generate_password_hash(register_form.password.data, method='pbkdf2:sha256', salt_length=8),  # encrypt password (via hashing)
                username=register_form.username.data,
                role='admin'
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('cafe_list'))
    # print(register_form.errors)
    return render_template("register.html", form=register_form)


# login
@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user_login = db.session.execute(db.select(User).filter_by(email=login_form.email.data)).scalar()
        if not user_login:
            login_form.email.errors.append('Mail not registered')
            # flash('Mail not registered')  # I decided to use form.errors instead of flashed message here
        elif check_password_hash(pwhash=user_login.password, password=login_form.password.data):
            # password stored in db is decrypted and compared to the one given by the user
            login_user(user_login)
            # flash('Logged in successfully.')  # not needed
            return redirect(url_for('cafe_list'))
        else:
            login_form.password.errors.append('Wrong Password')
            # flash('Wrong password')
    # print(login_form.errors)  # for debug
    return render_template("login.html", form=login_form)


# logout (only logged-in users, obviously)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('cafe_list'))


if __name__ == '__main__':
    app.run(debug=True)

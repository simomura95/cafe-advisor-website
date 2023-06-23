import os
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
# from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, select

# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import *  # CreatePostForm, RegisterForm, LoginForm
import random

app = Flask(__name__)
app.config[
    'SECRET_KEY'] = os.environ.get('FLASK_LOGIN_KEY')  # necessaria per usare flask login!

app.app_context().push()  # per evitare errori dopo nell'esecuzione

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


# Café TABLE Configuration
class Cafe(db.Model):
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


# db.create_all()


# homepage
@app.route("/")
def home():
    return render_template("index.html")


# list of cafes in db, with filtering options
@app.route("/cafes", methods=["GET", "POST"])
def cafe_list():
    form = FilterForm()
    if form.validate_on_submit():
        if form.reset.data:
            return redirect(url_for("cafe_list"))
        # elif form.filter.data:  # not necessary
        # print(form.data)
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
    else:
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
        # with 'scalars' I can access single elements instead of rows
    return render_template("cafes.html", all_cafes=cafes, filter_form=form)


## TODO: users login? + comment/reviews?

# Add a new café
@app.route("/add", methods=["GET", "POST"])
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
            coffee_price=f"£{'{:.2f}'.format(new_cafe_form.coffee_price.data)}"
        )
        if db.session.execute(db.select(Cafe).where(Cafe.name == cafe_to_add.name)).first():
            flash("We already have this café")
        else:
            db.session.add(cafe_to_add)
            db.session.commit()
            return redirect(url_for('cafe_list'))
    # else:
    #     print("Form validation failed")
    #     print(form.errors)
    return render_template("add_cafe.html", form=new_cafe_form)


# HTTP PUT/PATCH - Update Record
@app.route("/update-cafe/<int:cafe_id>", methods=["GET", "POST"])
def update_cafe(cafe_id):
    cafe_to_edit = db.session.execute(db.select(Cafe).filter_by(id=cafe_id)).scalar()
    if not cafe_to_edit:
        return abort(404, "Invalid café id")  # posso aggiungere il codice della risposta
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


# HTTP DELETE - Delete Record
@app.route("/delete-cafe/<int:cafe_id>")
def delete_cafe(cafe_id):
    cafe_to_delete = db.session.execute(db.select(Cafe).filter_by(id=cafe_id)).scalar()
    if not cafe_to_delete:
        return abort(404, "Invalid café id")  # posso aggiungere il codice della risposta
    db.session.delete(cafe_to_delete)
    db.session.commit()
    return redirect(url_for('cafe_list'))

if __name__ == '__main__':
    app.run(debug=True)

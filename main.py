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
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
@app.route("/")
def home():
    return render_template("index.html")

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
        # cafes = Cafe.query.filter(*conditions).all()
        cafes = db.session.execute(db.select(Cafe).where(*conditions)).scalars().all()
        # with *, conditions are unpacked and correctly evaluated. Without *, error
    else:
        #cafes = Cafe.query.scalars()
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
    for cafe in cafes:
        [cafe.has_sockets, cafe.has_toilet, cafe.has_wifi, cafe.can_take_calls] = \
            ['✔️' if elem else '❌' for elem in [cafe.has_sockets, cafe.has_toilet, cafe.has_wifi, cafe.can_take_calls]]
    return render_template("cafes.html", all_cafes=cafes, filter_form=form)

## TODO: add and remove cafes + users login? + comment/reviews?

# # HTTP GET - Read Record
# @app.route("/random")
# def random_get():
#     query_cafes = Cafe.query.all()
#     random_cafe = random.choice(query_cafes)
#     return jsonify(cafe=cafe_to_json(random_cafe))
#
#
# @app.route("/all")
# def all_get():
#     query_cafes = Cafe.query.all()
#     all_cafes = [cafe_to_json(row) for row in query_cafes]
#     return jsonify(cafes=all_cafes)  # posso trasformare in dict (1 riga di codice) e poi farci il jsonify
#
#
# @app.route("/search")
# def search_get():
#     loc = request.args.get('loc')
#     query_cafes = Cafe.query.filter_by(location=loc).all()
#     search_cafes = [cafe_to_json(row) for row in query_cafes]
#     if not search_cafes:
#         return jsonify(error={"Not Found": "No cafes at that location"})
#     return jsonify(cafes=search_cafes)
#
#
# # HTTP POST - Create Record
# @app.post("/add")
# def add_cafe():
#     cafe_to_add = Cafe(
#         name=request.form["name"],
#         map_url=request.form["map_url"],
#         img_url=request.form["img_url"],
#         location=request.form["location"],
#         seats=request.form["seats"],
#         has_toilet=bool(request.form["has_toilet"]),
#         has_wifi=bool(request.form["has_wifi"]),
#         has_sockets=bool(request.form["has_sockets"]),
#         can_take_calls=bool(request.form["can_take_calls"]),
#         coffee_price=request.form["coffee_price"]
#     )
#     db.session.add(cafe_to_add)
#     db.session.commit()
#     return jsonify(response={"success": "Successfully added the new cafe."})
#
#
# # HTTP PUT/PATCH - Update Record
# @app.patch("/update-price/<int:cafe_id>")
# def update_price(cafe_id):
#     cafe_edit = Cafe.query.get(cafe_id)
#     if not cafe_edit:
#         return jsonify(error={"Not Found": "No cafes with the given id"}), 404  # posso aggiungere il codice della risposta
#     cafe_edit.coffee_price = request.args.get('new_price')
#     db.session.commit()
#     return jsonify(response={"success": "Successfully changed the price."}), 200
#
#
# # HTTP DELETE - Delete Record
# @app.delete("/report-closed/<int:cafe_id>")
# def delete(cafe_id):
#     cafe_delete = Cafe.query.get(cafe_id)
#     if not cafe_delete:
#         return jsonify(error={"Not Found": "No cafes with the given id"}), 404
#     api_key = request.args.get('api-key')
#     if api_key == "TopSecretAPIKey":
#         db.session.delete(cafe_delete)
#         db.session.commit()
#         return jsonify(response={"success": "Successfully deleted from database."}), 200
#     else:
#         return jsonify(error="Not allowed: invalid API key"), 403


if __name__ == '__main__':
    app.run(debug=True)

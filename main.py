from flask import Flask, request
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
import base64
from datetime import datetime, timedelta
import time

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

message = "message"

class AuthorizationModel(db.Model):
    access_token = db.Column(db.String(100), primary_key=True)
    expires_at = db.Column(db.Integer, nullable=False)

    def get_expires_at(self):
        return self.expires_at


class CarParkingModel(db.Model):
    parking_spot = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(6), nullable=True)
    vehicle_mark = db.Column(db.String(100), nullable=True)
    parking_available = db.Column(db.Boolean, nullable=False)

    def get_spot(self):
        return self.parking_spot

    def get_available(self):
        return self.parking_available

    def get_number(self):
        return self.vehicle_number

    def get_mark(self):
        return self.vehicle_mark

    def set_mark(self, mark):
        self.vehicle_mark = mark

    def set_number(self,number):
        self.vehicle_number = number

    def set_available(self, status):
        self.parking_available = status

#Authorization activities
@app.route("/get_token/<string:vehicle_number>/<string:vehicle_mark>")
def get_token(vehicle_number, vehicle_mark):
    token = base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode('utf8').replace('\n', '')
    expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
    authorization = AuthorizationModel(access_token="Basic " + token, expires_at=expires_at)
    db.session.merge(authorization)
    db.session.commit()
    return {"access_token": token, "expires_at": expires_at}


def is_authorized(headers):
    if 'Authorization' not in headers:
        return {message: "You are not authorized"}, False
    basic_token = headers['Authorization']
    access_token = AuthorizationModel.query.filter_by(access_token=basic_token).first()
    if access_token is None:
        return {message: "You are not authorized"}, False
    if access_token.get_expires_at() < int(time.mktime(datetime.now().timetuple())):
        return {message: "You are not authorized, token expired"}, False
    return {}, True


def auth(function):
    def decorator(*args,**kwargs):
        error, ok = is_authorized(request.headers)
        if not ok:
            return error
        return function(*args,**kwargs)
    decorator.__name__ = function.__name__
    return decorator

#End-points for parking lot activities

@app.route("/free_spots")
@auth
def free_spots():
    result = CarParkingModel.query.filter_by(parking_available=True).all()
    free = len(result)
    return {"free": free}


@app.route("/next_free_spot")
@auth
def next_free_spot():
    result = CarParkingModel.query.filter_by(parking_available=True).first()
    if result is None:
        return {message: "There are no free spots in a parking lot."}
    return {"closest spot": result.get_spot()}


@app.route("/get_parking_spot/<string:vehicle_number>")
@auth
def get_parking_spot(vehicle_number):
    search_number = CarParkingModel.query.filter_by(vehicle_number=vehicle_number).first()
    if search_number is None:
        return {message: "There is no car with this vehicle number in a parking lot."}
    return {vehicle_number: search_number.get_spot()}


@app.route("/get_all")
@auth
def get_all():
    empty_dict = {}
    results = CarParkingModel.query.filter_by(parking_available=False).all()
    if len(results) == 0:
        return {message: "There are no cars parked in this parking lot."}
    for result in results:
        empty_dict[result.get_spot()] = result.get_number()
    return empty_dict


@app.route("/parking/<int:spot_number>", methods=["PUT"])
@auth
def parking(spot_number):
    spot = CarParkingModel.query.filter_by(parking_spot=spot_number).first()
    if not spot.get_available():
        return {message: "This spot is not available!"}
    body = request.get_json()
    spot.set_mark(body["vehicle_mark"])
    spot.set_number(body["vehicle_number"])
    spot.set_available(False)
    db.session.merge(spot)
    db.session.commit()
    return {"parking spot": spot_number}


@app.route("/leave/<int:spot_number>", methods=["PATCH"])
@auth
def leave(spot_number):
    spot = CarParkingModel.query.filter_by(parking_spot=spot_number).first()
    if spot.get_available() is True:
        return {message: "There is no car parked in this spot."}
    spot.set_available(True)
    spot.set_number(None)
    spot.set_mark(None)
    db.session.merge(spot)
    db.session.commit()
    return {"message": f"spot {spot_number} is available"}


@app.route("/change_to/<int:new_spot>", methods=["PUT"])
@auth
def change_spot(new_spot):
    body = request.get_json()
    vehicle_number = body['vehicle_number']
    spot = get_parking_spot(vehicle_number)
    if vehicle_number not in spot:
        return {message: f"Car {vehicle_number} not parked."}
    spot_nr = spot[vehicle_number]
    with app.test_request_context(
        headers={"Authorization": request.headers["Authorization"]},
        json=body
    ):
        reparking = parking(new_spot)
    if "parking spot" not in reparking:
        return reparking
    with app.test_request_context(headers={"Authorization": request.headers["Authorization"]}):
        leave(spot_nr)
    return {"message": f"{vehicle_number} parked to {new_spot}"}

limit = 10
if __name__ == "__main__":
    db.drop_all()
    db.create_all()
    for i in range(limit):
        db.session.add(CarParkingModel(parking_available=True))
        db.session.commit()
    app.run(debug=True)

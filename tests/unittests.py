from unittest import TestCase, main, mock
from main import free_spots, next_free_spot, get_parking_spot, \
    get_all, parking, leave, change_spot, message, get_token,  is_authorized, CarParkingModel, AuthorizationModel
from flask import Flask
import base64
from datetime import datetime, timedelta
import time

testapp = Flask(__name__)


class Authorization(TestCase):

    def test_get_token(self):
        vehicle_mark = "Honda"
        vehicle_number = "THR335"
        expected = {"access_token": base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode('utf8').replace('\n', '')}
        result = get_token(vehicle_number=vehicle_number, vehicle_mark=vehicle_mark)
        self.assertEqual(expected['access_token'], result['access_token'])

    @mock.patch('main.AuthorizationModel')
    def test_is_authorized_success(self, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = "THR3351"
        basic_token = "Basic "+base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode('utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(access_token=basic_token, expires_at=expires_at)
        expected = {}, True
        result = is_authorized({"Authorization": basic_token})
        self.assertEqual(expected, result)

    @mock.patch('main.AuthorizationModel')
    def test_is_authorized_none_fail(self, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = "THR3351"
        basic_token = "Basic "+base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode('utf8').replace('\n', '')
        expected = {message: "You are not authorized"}, False
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = None
        result = is_authorized({"Authorization": basic_token})
        self.assertEqual(expected, result)

    @mock.patch('main.AuthorizationModel')
    def test_is_authorized_time_fail(self, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = "THR3352"
        basic_token = "Basic "+base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode('utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() - timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(access_token=basic_token, expires_at=expires_at)
        expected = {message: "You are not authorized, token expired"}, False
        result = is_authorized({"Authorization": basic_token})
        self.assertEqual(expected, result)


class FreeSpots(TestCase):

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_no_free_spots(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = "THR335"
        free = 0
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {"free": free}
        car_parking_model.query.filter_by(parking_available=True).all.return_value = []
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = free_spots()
        self.assertEqual(expected, result)

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_free_spots_in_parking_lot(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = "THR3351"
        free = 7
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {"free": free}
        car_parking_model.query.filter_by(parking_available=True).all.return_value = \
            [CarParkingModel() for i in range(free)]
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = free_spots()
        self.assertEqual(expected, result)


class NextFreeSpot(TestCase):

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_next_free_spot(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = "THR3351"
        closest_spot = 8
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {"closest spot": closest_spot}
        car_parking_model.query.filter_by(parking_available=True).first.return_value = \
            CarParkingModel(parking_spot=closest_spot)
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = next_free_spot()
        self.assertEqual(expected, result)

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_no_next_free_spot(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = "THR3351"
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {message: "There are no free spots in a parking lot."}
        car_parking_model.query.filter_by(parking_available=True).first.return_value = None
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = next_free_spot()
        self.assertEqual(expected, result)


class GetParkingSpot(TestCase):

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_get_parking_spot_fail(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = 'THR334'
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {message: "There is no car with this vehicle number in a parking lot."}
        car_parking_model.query.filter_by(vehicle_number=vehicle_number).first.return_value = None
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = get_parking_spot(vehicle_number)
        self.assertEqual(expected, result)

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_get_parking_spot_success(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = 'THR334'
        parking_spot = 5
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {vehicle_number: parking_spot}
        car_parking_model.query.filter_by(vehicle_number=vehicle_number).first.return_value = \
            CarParkingModel(parking_spot=parking_spot, vehicle_number=vehicle_number)
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = get_parking_spot(vehicle_number)
        self.assertEqual(expected, result)


class GetAll(TestCase):

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_get_all_no_cars(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = 'THR334'
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {message: "There are no cars parked in this parking lot."}
        car_parking_model.query.filter_by(parking_available=False).all.return_value = []
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = get_all()
        self.assertEqual(expected, result)

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_get_all_cars_and_spots(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = 'THR334'
        parking_spot = 5
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {parking_spot: vehicle_number, parking_spot+1: vehicle_number+"1"}
        car_parking_model.query.filter_by(parking_available=False).all.return_value = [
            CarParkingModel(parking_spot=parking_spot, vehicle_number=vehicle_number),
            CarParkingModel(parking_spot=parking_spot+1, vehicle_number=vehicle_number+"1")
        ]
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = get_all()
        self.assertEqual(expected, result)


class Parking(TestCase):

    @mock.patch('main.CarParkingModel')
    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.db')
    def test_parking_success(self, car_parking_model,authorization_model, db):
        vehicle_mark = "Honda"
        vehicle_number = 'THR334'
        spot_number = 3
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {"parking spot": spot_number}
        car_parking_model.query.filter_by(parking_spot=spot_number).first.return_value = CarParkingModel(
            parking_spot=spot_number, parking_available=True)
        with testapp.test_request_context(json={"vehicle_number": "THR445", "vehicle_mark": "Honda"}, headers={"Authorization": basic_token}):
            result = parking(spot_number)
        self.assertEqual(expected, result)

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_parking_fail(self, car_parking_model,authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = 'THR334'
        spot_number = 2
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {message: "This spot is not available!"}
        car_parking_model.query.filter_by(parking_spot=spot_number).first.return_value = CarParkingModel(parking_spot=spot_number, parking_available=False)
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = parking(spot_number)
        self.assertEqual(expected, result)


class Leave(TestCase):

    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_leave_fail(self, car_parking_model, authorization_model):
        vehicle_mark = "Honda"
        vehicle_number = 'THR334'
        spot_number = 3
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {message: "There is no car parked in this spot."}
        car_parking_model.query.filter_by(parking_spot=spot_number, parking_available=False).first.return_value = \
            CarParkingModel(parking_spot=spot_number, parking_available=True)
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = leave(spot_number)
        self.assertEqual(expected, result)

    @mock.patch('main.db')
    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.CarParkingModel')
    def test_leave_success(self, car_parking_model, authorization_model, db):
        vehicle_mark = "Honda"
        vehicle_number = 'THR334'
        spot_number = 3
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {"message": f"spot {spot_number} is available"}
        car_parking_model.query.filter_by(parking_spot=spot_number).first.return_value = \
            CarParkingModel(parking_spot=spot_number)
        with testapp.test_request_context(headers={"Authorization": basic_token}):
            result = leave(spot_number)
        self.assertEqual(expected, result)


class ChangeSpot(TestCase):

    @mock.patch('main.parking')
    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.get_parking_spot')
    def test_change_spot_fail(self, get_parking_spot, authorization_model, parking):
        expected = {message: "This spot is not available!"}
        spot_number = 3
        vehicle_number = "123"
        vehicle_mark = "honda"
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        get_parking_spot.return_value = {vehicle_number: spot_number}
        parking.return_value = {message: "This spot is not available!"}
        with testapp.test_request_context(json={"vehicle_number": vehicle_number, "vehicle_mark": vehicle_mark}, headers={"Authorization": basic_token}):
            result = change_spot(spot_number)
        self.assertEqual(expected, result)

    @mock.patch('main.db')
    @mock.patch('main.AuthorizationModel')
    @mock.patch('main.leave')
    @mock.patch('main.parking')
    @mock.patch('main.get_parking_spot')
    def test_change_spot_success(self, get_parking_spot, parking, leave, authorization_model, db):
        spot_number = 3
        new_spot = 5
        vehicle_number = "123"
        vehicle_mark = "honda"
        basic_token = "Basic " + base64.encodebytes(('%s:%s' % (vehicle_number, vehicle_mark)).encode('utf8')).decode(
            'utf8').replace('\n', '')
        expires_at = int(time.mktime((datetime.now() + timedelta(minutes=15)).timetuple()))
        authorization_model.query.filter_by(access_token=basic_token).first.return_value = AuthorizationModel(
            access_token=basic_token, expires_at=expires_at)
        expected = {"message": f"{vehicle_number} parked to {new_spot}"}
        get_parking_spot.return_value = {vehicle_number: spot_number}
        leave.return_value = {"message": f"spot {spot_number} is available"}
        parking.return_value = {"parking spot": spot_number}
        with testapp.test_request_context(json={"vehicle_number": vehicle_number, "vehicle_mark": vehicle_mark}, headers={"Authorization": basic_token}):
            result = change_spot(new_spot)
        self.assertEqual(expected, result)


if __name__ == '__main__':
    main()

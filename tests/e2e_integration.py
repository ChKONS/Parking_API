import requests
from unittest import TestCase, main
from main import message, db, get_token, CarParkingModel, limit

BASE = "http://127.0.0.1:5000"

#Helping function for cleaning data
def clean_data():
    for i in range(1,limit+1):
        db.session.merge(CarParkingModel(
            vehicle_number=None,
            vehicle_mark=None,
            parking_available=True,
            parking_spot=i,
        ))
        db.session.commit()

#Helping function for generating the data for parking
def gen_data_parking(limit):
    for i in range(1,limit+1):
        db.session.merge(CarParkingModel(
            vehicle_number="test_"+str(i),
            vehicle_mark="test-mark",
            parking_available=False,
            parking_spot=i,
        ))
        db.session.commit()

#Helping function for getting token
def gen_token(vehicle_number,vehicle_mark):
    return get_token(vehicle_number,vehicle_mark)["access_token"]


class Reparking(TestCase):
    
    def test_reparking_success(self):
        clean_data()
        gen_data_parking(1)
        token = gen_token("test_1","test-mark")
        expected = {"message": f"test_1 parked to {2}"}
        response = requests.put(url=BASE + "/change_to/2",
                                json={"vehicle_number": "test_1", "vehicle_mark": "test-mark"},
                                headers={"content-type": "application/json","authorization": f"Basic {token}"})
        response =response.json()
        self.assertEqual(expected, response)
        # Integration test part
        actual_db = CarParkingModel.query.filter_by(parking_spot=2).first()
        self.assertEqual(actual_db.get_number(), 'test_1')
        self.assertEqual(actual_db.get_mark(), 'test-mark')
        self.assertEqual(actual_db.get_available(), False)
        self.assertEqual(actual_db.get_spot(), 2)

        prev_spot_db = CarParkingModel.query.filter_by(parking_spot=1).first()
        self.assertEqual(prev_spot_db.get_number(), None)
        self.assertEqual(prev_spot_db.get_mark(), None)
        self.assertEqual(prev_spot_db.get_available(), True)
        self.assertEqual(prev_spot_db.get_spot(), 1)
        clean_data()

    def test_reparking_fail(self):
        clean_data()
        gen_data_parking(2)
        expected = {message: "This spot is not available!"}
        token = gen_token("test_1", "test-mark")
        response = requests.put(url=BASE + "/change_to/2",
                                json={"vehicle_number": "test_1", "vehicle_mark": "test-mark"},
                                headers={"content-type": "application/json", "authorization": f"Basic {token}"})
        response =response.json()
        self.assertEqual(expected, response)
        clean_data()


class Leaving(TestCase):

    def test_leaving_success(self):
        clean_data()
        gen_data_parking(1)
        expected = {"message": f"spot {1} is available"}
        token = gen_token("test_1", "test-mark")
        response = requests.patch(
            url=BASE + "/leave/1",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)
        # Integration test part
        actual_db = CarParkingModel.query.filter_by(parking_spot=1).first()
        self.assertEqual(actual_db.get_number(), None)
        self.assertEqual(actual_db.get_mark(), None)
        self.assertEqual(actual_db.get_available(), True)
        self.assertEqual(actual_db.get_spot(), 1)
        clean_data()


    def test_leaving_fail(self):
        clean_data()
        expected = {message: "There is no car parked in this spot."}
        token = gen_token("test_1", "test-mark")
        response = requests.patch(
            url=BASE + "/leave/1",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)


class Parking(TestCase):

    def test_parking_success(self):
        clean_data()
        token = gen_token("test_1", "test-mark")
        expected = {"parking spot": 1}

        response = requests.put(
            url=BASE + "/parking/1",
            json={"vehicle_number": "test_1", "vehicle_mark": "test-mark"},
            headers={"content-type": "application/json", "authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)
        # Integration test part
        actual_db = CarParkingModel.query.filter_by(parking_spot=1).first()
        self.assertEqual(actual_db.get_number(),"test_1")
        self.assertEqual(actual_db.get_mark(),"test-mark")
        self.assertEqual(actual_db.get_available(),False)
        self.assertEqual(actual_db.get_spot(),1)
        clean_data()

    def test_parking_fail(self):
        token = gen_token("test_1", "test-mark")
        gen_data_parking(1)
        expected = {message: "This spot is not available!"}
        response = requests.put(
            url=BASE + "/parking/1",
            json={"vehicle_number": "test", "vehicle_mark": "honda"},
            headers={"content-type": "application/json", "authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)
        clean_data()

class GetAll(TestCase):

    def test_get_all_cars_success(self):
        gen_data_parking(2)
        expected = {'1': "test_1", '2': "test_2"}
        token = gen_token("test_1", "test-mark")
        response = requests.get(
            url=BASE + "/get_all",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected,response)
        clean_data()

    def test_get_all_cars_none(self):
        clean_data()
        expected = {message: "There are no cars parked in this parking lot."}
        token = gen_token("test_1", "test-mark")
        response = requests.get(
            url=BASE + "/get_all",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)


class GetParkingSpot(TestCase):

    def test_get_parking_spot(self):
        gen_data_parking(1)
        expected = {"test_1": 1}
        token = gen_token("test_1", "test-mark")
        response = requests.get(
            url=BASE + "/get_parking_spot/test_1",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)
        clean_data()

    def test_get_parking_spot_fail(self):
        expected = {message: "There is no car with this vehicle number in a parking lot."}
        token = gen_token("test_1", "test-mark")
        response = requests.get(
            url=BASE + "/get_parking_spot/test_1",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)


class NextFreeSpot(TestCase):

    def test_next_free_parking_spot(self):
        expected = {"closest spot": 1}
        token = gen_token("test_1", "test-mark")
        response = requests.get(
            url=BASE + "/next_free_spot",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected,response)

    def test_next_free_spot_fail(self):
        gen_data_parking(limit)
        expected = {message: "There are no free spots in a parking lot."}
        token = gen_token("test_1", "test-mark")
        response = requests.get(
            url=BASE + "/next_free_spot",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)
        clean_data()

class FreeSpots(TestCase):

    def test_free_spots_in_parking_lot(self):
        free = 6
        expected = {"free": free}
        gen_data_parking(limit-free)
        token = gen_token("test_1","test-mark")
        response = requests.get(
            url=BASE + "/free_spots",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)
        clean_data()

    def test_no_free_spots(self):
        free = 0
        expected = {"free": free}
        gen_data_parking(limit-free)
        token = gen_token("test_1","test-mark")
        response = requests.get(
            url=BASE + "/free_spots",
            headers={"authorization": f"Basic {token}"}
        ).json()
        self.assertEqual(expected, response)
        clean_data()


if __name__ == '__main__':
    main()

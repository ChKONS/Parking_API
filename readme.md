## Project name: Car parking API (Python - Flask)

### Project description: 
This car parking API is made as technical assignment. 
The goal was to create API that deals with car parking. 
It has endpoints for different actions to do in parking lot.
To call each endpoint you need to be authorized.
Main technologies used in this project are: Python, Flask and SQLAlchemy.
Also, there are unit, end-to-end and integration tests included.

### Dependencies: 
    SQLAlchemy
    flask
    unittest
    requests
    flask_restful
    flask_sqlalchemy
    base64
    time
    datetime

### How to Install and Run the Project/How to Use the Project:

NB! All commands should be run in Git Bash.

1. For Running this API you first need to install the needed dependencies.
2. To start API from the command line run following command in project directory:
```sh
python main.py
```
3. Before sending request to API endpoint we need to get authorization token first:
```sh
$ curl --silent -X GET localhost:5000/get_token/{vehicle_number}/{vehicle_mark}
```
4. Examples how to call API endpoints:
```sh
# Getting all free spots in parking lot
$ curl --silent -X GET -H "Authorization: Basic {access_token}" localhost:5000/free_spots
# Getting next free spot in parking lot
$ curl --silent -X GET -H "Authorization: Basic {access_token}" localhost:5000/next_free_spot
# Getting parking spot number by vehicle number
$ curl --silent -X GET -H "Authorization: Basic {access_token}" localhost:5000/get_parking_spot/<string:vehicle_number>
#Getting all the the used spots with vehicle numbers
$ curl --silent -X GET -H "Authorization: Basic {access_token}" localhost:5000/get_all
#To park car
$ curl --silent -X PUT \
  -H "Authorization: Basic {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"vehicle_number": <vehicle_number>, "vehicle_mark": <vehicle_mark>}' \
  localhost:5000/parking/<int:spot_number>
#To leave from spot
$ curl --silent -X PATCH -H "Authorization: Basic {access_token}" localhost:5000/leave/<int:spot_number>
#To change parking spot
$ curl --silent -X PUT \
  -H "Authorization: Basic {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"vehicle_number": <vehicle_number>, "vehicle_mark": <vehicle_mark>}' \
  localhost:5000/change_to/<int:new_spot>
```

### Author

Christelle Utt

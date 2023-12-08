###############################################################
# CET1112 - Devbot.py Student Assessment Script
# Professor: Jeff Caldwell
# Year: 2023-09
###############################################################

import requests
import json
import time

def get_access_token():
    choice = input("Do you wish to use the hard-coded Webex token? (y/n) ")

    if choice == "N" or choice == "n":
        access_token = input("What is your access token? ")
        access_token = "Bearer " + access_token
    else:
        access_token = "Bearer ZThkNWY0MGEtNjk0MC00NmZiLWFhMjgtODkyMjMyODZhYzc5NDMzYjBjM2EtY2Iz_PC75_47fe537e-27d1-4e32-b2dc-2c26e4aa4fa0"

    return access_token

def get_rooms(access_token):
    url = "https://webexapis.com/v1/rooms"
    headers = {"Authorization": access_token}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        return response.json()["items"]
    except requests.exceptions.RequestException as e:
        print("Error fetching Webex Teams rooms:", e)
        return []

def select_room(rooms):
    while True:
        room_name_to_search = input("Which room should be monitored for /location messages? ")
        room_id_to_get_messages = None

        for room in rooms:
            if room["title"].find(room_name_to_search) != -1:
                print("Found rooms with the word " + room_name_to_search)
                print(room["title"])
                room_id_to_get_messages = room["id"]
                room_title_to_get_messages = room["title"]
                print("Found room: " + room_title_to_get_messages)
                break

        if room_id_to_get_messages is None:
            print("Sorry, I didn't find any room with " + room_name_to_search + " in it.")
            print("Please try again...")
        else:
            return room_id_to_get_messages

def get_location_coordinates(location, mapquest_api_key):
    url = "https://www.mapquestapi.com/geocoding/v1/address"
    params = {
        "location": location,
        "key": mapquest_api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["info"]["statuscode"] == 0:
            location_results = data["results"][0]["providedLocation"]["location"]
            location_lat = data["results"][0]["locations"][0]["displayLatLng"]["lat"]
            location_lng = data["results"][0]["locations"][0]["displayLatLng"]["lng"]
            return location_results, location_lat, location_lng
        else:
            print("Error fetching location coordinates from MapQuest API.")
    except requests.exceptions.RequestException as e:
        print("Error fetching location coordinates:", e)

    return None, None, None

def get_sunrise_sunset(location_lat, location_lng, date="today"):
    url = "https://api.sunrise-sunset.org/json"
    params = {
        "lat": location_lat,
        "lng": location_lng,
        "date": date
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "results" in data:
            sunrise_time = data["results"]["sunrise"]
            sunset_time = data["results"]["sunset"]
            return sunrise_time, sunset_time
        else:
            print("Error fetching sunrise and sunset times.")
    except requests.exceptions.RequestException as e:
        print("Error fetching sunrise and sunset times:", e)

    return None, None

def main():
    mapquest_api_key = "v542l5rJoGZu2I9XDUd4adzrMQKtSfHB"
    access_token = get_access_token()
    rooms = get_rooms(access_token)

    if not rooms:
        return

    room_id_to_get_messages = select_room(rooms)

    while True:
        time.sleep(1)

        get_parameters = {
            "roomId": room_id_to_get_messages,
            "max": 1
        }

        try:
            response = requests.get("https://webexapis.com/v1/messages", params=get_parameters, headers={"Authorization": access_token})
            response.raise_for_status()
            data = response.json()

            if "items" in data and len(data["items"]) > 0:
                message = data["items"][0]["text"]
                print("Received message: " + message)

                if message.startswith("/"):
                    location = message[1:]
                    location_results, location_lat, location_lng = get_location_coordinates(location, mapquest_api_key)

                    if location_lat is not None and location_lng is not None:
                        sunrise_time, sunset_time = get_sunrise_sunset(location_lat, location_lng)

                        if sunrise_time is not None:
                            response_message = f"In {location_results}, the sunrise is at {sunrise_time} and the sunset is at {sunset_time}."
                            print("Sending to Webex Teams: " + response_message)

                            http_headers = {
                                "Authorization": access_token,
                                "Content-Type": "application/json"
                            }

                            post_data = {
                                "roomId": room_id_to_get_messages,
                                "text": response_message
                            }

                            try:
                                response = requests.post("https://webexapis.com/v1/messages", data=json.dumps(post_data), headers=http_headers)
                                response.raise_for_status()
                            except requests.exceptions.RequestException as e:
                                print("Error posting message to Webex Teams:", e)
        except requests.exceptions.RequestException as e:
            print("Error fetching Webex Teams messages:", e)

if __name__ == "__main__":
    main()

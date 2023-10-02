import requests
import json
import os
import random
import string
import boto3
from requests.structures import CaseInsensitiveDict

limit = 2

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_PUBLIC_BUCKET_NAME = ""
aws_upload = True


def send_post_request(url, dynamic_value):
    headers = {
        "Content-Type": "multipart/form-data; boundary=---------------------------257077820923972032752219100462"
    }

    form_data = f"""
-----------------------------257077820923972032752219100462
Content-Disposition: form-data; name="id"


-----------------------------257077820923972032752219100462
Content-Disposition: form-data; name="slug"

{dynamic_value}
-----------------------------257077820923972032752219100462--
"""

    try:
        response = requests.post(url, headers=headers, data=form_data)
        response.raise_for_status()
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request Error for {dynamic_value}: {e}")
        return None
    except ValueError as e:
        print(f"JSON Parsing Error for {dynamic_value}: {e}")
        return None


def get_meeting_room_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request Error : {e}")
        return None
    except ValueError as e:
        print(f"JSON Parsing Error : {e}")
        return None


def get_service_room_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request Error : {e}")
        return None
    except ValueError as e:
        print(f"JSON Parsing Error : {e}")
        return None


def upload_to_aws(image, image_type):
    try:
        key = "".join(random.choice(string.ascii_lowercase) for i in range(20))
        key = key + "." + image_type
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        res = s3.put_object(
            Body=image,
            Bucket=AWS_PUBLIC_BUCKET_NAME,
            Key=key,
        )
        if res:
            return key
        return ""
    except Exception as e:
        print(f"Error uploading to AWS: {e}")
        return ""


def read_image(url):
    data = requests.get(url)
    image_data = data.content
    typeH = ""
    try:
        image_data.decode("utf-8")
        image_data = ""
    except:
        typeH = data.headers["Content-Type"].replace("image/", "")
        if typeH.find("octet-stream"):
            if "jpeg" in url:
                typeH = "jpeg"
            if "jpg" in url:
                typeH = "jpg"
            if "png" in url:
                typeH = "png"
            return image_data, typeH
        if typeH in ("jpeg", "jpg", "png"):
            return image_data, typeH
    return "", ""


base_url = "https://www.leasinghub.com"


def loadLeasinghub():
    api_url = f"{base_url}/office/coworking?task=servicedoffices.fetch&format=json&with_images=1&limit={limit}&limitstart=0&filter_order=default&filter_order_Dir=DESC&usage=&alias=&keyword=&with_sponsors=1"
    all_listings = f"{base_url}/cowork?task=centerbuilding.item&format=json"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        items = data.get("data", {}).get("items", [])

        all_info = []
        print("Data extraction started...........")
        for n, item in enumerate(items, start=1):
            dynamic_value = item.get("locale_slug", "")
            response_data = send_post_request(all_listings, dynamic_value)

            listing_id = item.get("id", "")
            meeting_room_url = f"{base_url}/cowork?task=centerbuilding.rooms&format=json&center_id={listing_id}&with_images=1&limit=300&limitstart=0&filter_order=default&filter_order_Dir=desc"

            meeting_room_response_data = get_meeting_room_request(meeting_room_url)
            meeting_room_items = meeting_room_response_data.get("data", {}).get(
                "items", []
            )

            service_room_url = f"{base_url}/cowork?task=centerbuilding.suites&format=json&center_id={listing_id}&with_images=1&limit=500&limitstart=0&filter_order=default&filter_order_Dir=desc"

            service_room_response_data = get_service_room_request(service_room_url)
            service_room_items = service_room_response_data.get("data", {}).get(
                "items", []
            )

            if response_data:
                # FOR AWS
                if aws_upload:
                    listing_images = response_data.get("data", {}).get("images", "")
                    listing_lq_urls = []
                    if isinstance(listing_images, list):
                        if listing_images:
                            for img in listing_images:
                                try:
                                    data, typeI = read_image(img.get("lq_url", ""))
                                    if data != "":
                                        up = upload_to_aws(data, typeI)
                                        listing_lq_urls.append(up)
                                except Exception as err:
                                    print("error=====", err)
                else:
                    listing_images = response_data.get("data", {}).get("images", "")
                    listing_lq_urls = [img.get("lq_url", "") for img in listing_images]
                listing_info = {
                    "building_name": item.get("building_name", "")
                    + " "
                    + item.get("building_name_cht", ""),
                    "detail": [
                        {
                            "description": response_data.get("data", {}).get(
                                "description", ""
                            ),
                            "operator_desc_locale": response_data.get("data", {}).get(
                                "operator_desc_locale", ""
                            ),
                            "name_locale": item.get("name_locale", ""),
                            "street_name": item.get("street_name", ""),
                            "area_name": item.get("area_name", ""),
                            "utilities_text": response_data.get("data", {}).get(
                                "utilities_text", ""
                            ),
                            "images": listing_lq_urls,
                        }
                    ],
                }
                meeting_room_info = []
                service_room_info = []
                co_working_space_info = []
                building_info = []
                print(f"============= FETCHING LISTING {n} =============")

                co_working_space_info.append(
                    {
                        "area": response_data.get("data", {}).get("area", ""),
                        "capacity": response_data.get("data", {}).get("capacity", ""),
                        "branch_counts": response_data.get("data", {}).get(
                            "branch_counts", ""
                        ),
                        "name": response_data.get("data", {}).get("name", ""),
                        "intl_suite_rate1": response_data.get("data", {}).get(
                            "intl_suite_rate1", ""
                        ),
                        "intl_suite_rate2": response_data.get("data", {}).get(
                            "intl_suite_rate2", ""
                        ),
                        "wnd_suite_rate1": response_data.get("data", {}).get(
                            "wnd_suite_rate1", ""
                        ),
                        "wnd_suite_rate2": response_data.get("data", {}).get(
                            "wnd_suite_rate2", ""
                        ),
                        "float_rate_full": response_data.get("data", {}).get(
                            "float_rate_full", ""
                        ),
                        "fixed_rate_full": response_data.get("data", {}).get(
                            "fixed_rate_full", ""
                        ),
                    }
                )

                print(f"============= FETCHING CO WORKING SPACE INFO =============")

                building_info_get = response_data.get("data", {}).get("building", {})
                if aws_upload:
                    floor_plan_images = response_data.get("data", {}).get("floorplans", [])
                    floor_plan_lq_urls = []
                    if isinstance(floor_plan_images, list):
                        if floor_plan_images:
                            for img in floor_plan_images:
                                try:
                                    data, typeI = read_image(img.get("lq_url", ""))
                                    if data != "":
                                        up = upload_to_aws(data, typeI)
                                        floor_plan_lq_urls.append(up)
                                except Exception as err:
                                    print("error=====", err)
                else:
                    floor_plan_images = response_data.get("data", {}).get("floorplans", [])
                    floor_plan_lq_urls = [
                        img.get("lq_url", "") for img in floor_plan_images
                    ]
                if aws_upload:
                    building_images = building_info_get.get("images", [])
                    building_lq_urls = []
                    if isinstance(building_images, list):
                        if building_images:
                            for img in building_images:
                                try:
                                    data, typeI = read_image(img.get("lq_url", ""))
                                    if data != "":
                                        up = upload_to_aws(data, typeI)
                                        building_lq_urls.append(up)
                                except Exception as err:
                                    print("error=====", err)
                else:
                    building_images = building_info_get.get("images", [])
                    building_lq_urls = [
                        img.get("lq_url", "") for img in building_images
                    ]
                building_info.append(
                    {
                        "building_type_text": building_info_get.get("building_type_text", ""),
                        "age": building_info_get.get("age", ""),
                        "grade": building_info_get.get("grade", ""),
                        "last_updated": building_info_get.get("last_updated", ""),
                        "building_ownership": building_info_get.get("building_ownership", ""),
                        "has_carparking": building_info_get.get("has_carparking", ""),
                        "carparking": building_info_get.get("carparking", ""),
                        "year": building_info_get.get("year", ""),
                        "highest_floor": building_info_get.get("highest_floor", ""),
                        "comment_auto": building_info_get.get("comment_auto", ""),
                        "floor_system_text": building_info_get.get("floor_system_text", ""),
                        "lifts": building_info_get.get("lifts", ""),
                        "ac_systems": building_info_get.get("ac_systems", ""),
                        "ac_type_text": building_info_get.get("ac_type_text", ""),
                        "ceil_false": building_info_get.get("ceil_false", ""),
                        "mtrs_nearby": building_info_get.get("mtrs_nearby", ""),
                        "floor_plan": floor_plan_lq_urls,
                        "images": building_lq_urls,
                       
                    }
                )

                print(f"============= FETCHING BUILDING INFO =============")
                for i, meeting_room in enumerate(meeting_room_items, start=1):
                    if aws_upload:
                        meeting_room_images = meeting_room.get("images", [])
                        meeting_room_lq_urls = []
                        if isinstance(meeting_room_images, list):
                            if meeting_room_images:
                                for img in meeting_room_images:
                                    try:
                                        data, typeI = read_image(img.get("lq_url", ""))
                                        if data != "":
                                            up = upload_to_aws(data, typeI)
                                            meeting_room_lq_urls.append(up)
                                    except Exception as err:
                                        print("error=====", err)
                    else:
                        meeting_room_images = meeting_room.get("images", [])
                        meeting_room_lq_urls = [
                            img.get("lq_url", "") for img in meeting_room_images
                        ]
                    meeting_room_info.append(
                        {
                            "type_text": meeting_room.get("type_text", ""),
                            "seat_count": meeting_room.get("seat_count", ""),
                            "area": meeting_room.get("area", ""),
                            "viewing_text": meeting_room.get("viewing_text", ""),
                            "hourly_rate": meeting_room.get("hourly_rate", ""),
                            "full_day_rate": meeting_room.get("full_day_rate", ""),
                            "remark": meeting_room.get("remark", ""),
                            "images": meeting_room_lq_urls,
                        }
                    )

                    print(
                        f"============= FETCHING MEETING ROOM LISTINGS {i} ============="
                    )
                for i, service_room in enumerate(service_room_items, start=1):
                    if aws_upload:
                        service_room_images = service_room.get("images", [])
                        service_room_lq_urls = []
                        if isinstance(service_room_images, list):
                            if service_room_images:
                                for img in service_room_images:
                                    try:
                                        data, typeI = read_image(img.get("lq_url", ""))
                                        if data != "":
                                            up = upload_to_aws(data, typeI)
                                            service_room_lq_urls.append(up)
                                    except Exception as err:
                                        print("error=====", err)
                    else:
                        service_room_images = service_room.get("images", [])
                        service_room_lq_urls = [
                            img.get("lq_url", "") for img in service_room_images
                        ]
                    service_room_info.append(
                        {
                            "type_text": service_room.get("type_text", ""),
                            "desks": service_room.get("desks", ""),
                            "area_range": service_room.get("area_range", ""),
                            "viewing_text": service_room.get("viewing_text", ""),
                            "monthly_rental_1": service_room.get("rent1", ""),
                            "monthly_rental_2": service_room.get("rent2", ""),
                            "images": service_room_lq_urls,
                        }
                    )

                    print(
                        f"============= FETCHING SERVICE ROOM LISTINGS {i} ============="
                    )

                listing_info["meeting_rooms"] = meeting_room_info
                listing_info["service_rooms"] = service_room_info
                listing_info["co_working_space_info"] = co_working_space_info
                listing_info["building_info"] = building_info

                all_info.append(listing_info)

        with open(
            "leasinghub_co_working_data.json", "w", encoding="utf-8"
        ) as json_file:
            json.dump(all_info, json_file, indent=4, ensure_ascii=False)

        print("Data extracted and saved successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
    except ValueError as e:
        print(f"JSON Parsing Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

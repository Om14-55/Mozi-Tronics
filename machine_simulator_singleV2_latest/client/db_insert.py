
# def write_to_port(host, port, port_queue, queue_lock, stop_event):
#     while not(stop_event.is_set() and len(port_queue) == 0):
#         try:
#             client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             client.connect((host, port))
#             print("Connected to socket!")

#             with client:
#                 while not stop_event.is_set():
#                     final_data = None
#                     with queue_lock:
#                         if port_queue:
#                             data = port_queue.pop()
#                             final_data = json.dumps(data.to_dict()) + "\n"
#                     if final_data is not None:
#                         client.sendall(final_data.encode('utf-8'))
#                     else:
#                         time.sleep(0.1)

#         except (socket.error, socket.timeout) as e:
#             if not stop_event.is_set():
#                 print(f"Socket Error: {e}. Retrying...")
#                 time.sleep(5)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# import time, json, requests

# def write_to_db(api_queue, queue_lock, stop_event):
#     API_URL = "http://127.0.0.1:8000/api/v1/database_operation/"

#     while not(stop_event.is_set() and len(api_queue) == 0):
#         data = None
#         try:
#             final_data = None
#             with queue_lock:
#                 if api_queue:
#                     data = api_queue.pop()
#                     final_data = json.dumps(data.to_dict()) + "\n"

#             if final_data is not None:
#                 response = requests.post(API_URL, json=final_data, timeout=5)

#             if response.status_code == 200 or response.status_code == 201:
#                 match response.status_code:
#                     case 200: 
#                         print(f"API Success: Sent {final_data}")
#                     case 201:
#                         print(f"API Success: Created {final_data}")
#                     case _:
#                         print("API: Other status code")
#             else:
#                 print(f"API Error: Received status {response.status_code}")

#         except requests.exceptions.RequestException as e:
#             print(f"Network/API error: {e}")
#             time.sleep(2)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import time, requests

# API_BASE_URL = 'http://127.0.0.1:8000'

def write_to_db(api_queue, queue_lock, stop_event, api_base_url):
    API_URL = f"http://{api_base_url}/api/v1/data_insert_update_delete/"

    while not (stop_event.is_set() and len(api_queue) == 0):
        data = None
        try:
            with queue_lock:
                if api_queue:
                    data = api_queue.pop()

            if data is not None:
                print(data)
                response = requests.get(API_URL, params=data, timeout=5)

                if response.status_code in [200, 201]:
                    print(f"API Success ({response.status_code}): Sent {data}")
                else:
                    print(f"API Error {response.status_code}: {response.text}")
                    # pass
            else:
                time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            print(f"Network/API error: {e}")
            time.sleep(2)

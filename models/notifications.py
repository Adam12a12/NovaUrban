from dotenv import load_dotenv
import os
from pyfcm import FCMNotification
import datetime

class Notifications:

    def __init__(self):
        load_dotenv()
        self.server_key = os.getenv('SERVER_KEY')
        self.project_id = os.getenv('PROJECT_ID')
        self.fcm = FCMNotification(service_account_file=os.getenv('FCM_SERVICE_FILE'), project_id=self.project_id)

    def send_notification(camera_index):
        now = datetime.now()
        today = datetime.today()
        time = now.strftime('%H:%M:%S')
        date = today.strftime('%d-%m-%Y')
        data = { 
            'time': time,
            'date': date,
            'camera_index':  camera_index
            } 
        title = 'Danger Alert'
        body = 'Danger description'
        # TODO: data fcm.notify returns payload type error
        result = self.fcm.notify(fcm_token=DEVICE_TOKEN,notification_title=title,notification_body=body, data_payload=data)
        print (result)

    def get_tokens():
        #TODO; get tokens from firebase firestore
        pass

# Will refactor all notifications methods here


@app.route('/send_notification')
def send_notification():
    now = datetime.now()
    today = datetime.today()
    time = now.strftime('%H:%M;%S')
    date = today.strftime('%d-%m-%Y')
    data = { 
        'time': time,
        'date': date
        } 
    title = 'Danger Alert'
    body = 'Danger description'
    result = fcm.notify(fcm_token=DEVICE_TOKEN,notification_title=title,notification_body=body, data_payload=data)
    print (result)


@app.route('/register_token', methods=['POST'])
def register_token():
    data = request.get_json()
    token = data.get('token')
    if token:
        DEVICE_TOKEN = token
        return jsonify({'status': 'success', 'message': 'Token received'}), 200 
    else: 
        return jsonify({'status': 'error', 'message': 'No token provided'}), 400

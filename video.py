# Will refactor all video processing methods here
from flask import request, Response
import cv2

is_recording = False

@app.route('/video_feed',methods=['GET'])
def video_feed():
    return Response(start_processing(),mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_processing')
def start_processing():
    cam = cv2.VideoCapture(0)

    frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if is_recording:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('output.mp4', fourcc, 20.0, (frame_width, frame_height))
    
    while True:
        ret, frame = cam.read()
        what, buffer = cv2.imencode('.jpg', frame)
        # cv2.imshow('Camera', frame)
        frame = buffer.tobytes()
        buffer.tobytes() 
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        if is_recording:
            out.write(frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
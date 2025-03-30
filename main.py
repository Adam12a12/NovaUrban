import sys
# from scripts import nova_urban_server, yolov5s_server

server.start()
if sys.argv[1] == 'yolo':
    yolov5s_server.start()
else:
    nova_urban_server.start()
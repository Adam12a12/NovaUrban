import sys
import threading
from apps import server



if len(sys.argv) > 1 and sys.argv[1] == 'yolo':
    threading.Thread(target=server.start, daemon=True).start()
    from apps import yolov5s_server
    threading.Thread(target=yolov5s_server.start, daemon=True).start()
elif len(sys.argv) > 1 and sys.argv[1] == 'nova':
    threading.Thread(target=server.start, daemon=True).start()
    from apps import nova_urban_server
    threading.Thread(target=nova_urban_server.start, daemon=True).start()
else:
    server.start()
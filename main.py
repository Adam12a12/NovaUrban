import sys
import threading
from scripts import server


threading.Thread(target=server.start, daemon=True).start()
if len(sys.argv) > 1 and sys.argv[1] == 'yolo':
    from scripts import yolov5s_server
    threading.Thread(target=yolov5s_server.start, daemon=True).start()
else:
    from scripts import nova_urban_server
    threading.Thread(target=nova_urban_server.start, daemon=True).start()
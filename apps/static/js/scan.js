async function run_cam(){
  fetch('/process_video'); //TODO: add daemon start and stop funcs to view
}

async function video_feed(){
  fetch('/video_feed');
}
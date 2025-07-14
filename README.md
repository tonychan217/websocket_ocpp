# websocket_ocpp
==============================
- Source Reference:
  * ParametricCamp: https://github.com/ParametricCamp/TutorialFiles
  
- Set environment:
  * $> source myenv/bin/activate

- Websocket server:
  * $> git clone https://github.com/tonychan217/websocket_ocpp.git
  * $> cd websocket_ocpp
  * $> python server_ocpp.py

- Startup service:
  * $> sudo nano /etc/systemd/system/server_ocpp.service
  * $> sudo systemctl daemon-reload

    
 [Unit]
Description=WebSocket OCPP Server
After=network.target

[Service]
Type=simple
# run as your user
User=tony
Group=tony
# ensure we start in your project folder
WorkingDirectory=/home/tony/websocket_ocpp
# give the service your venv’s python & log everything
# -l: run as a login shell so ~/.bashrc / PATH tweaks are honored
ExecStart=/bin/bash -lc 'source /home/tony/myenv/bin/activate && exec python s>
Restart=on-failure
# if your server forks or daemonizes itself, you may need Type=forking
# but most simple apps work with Type=simple

[Install]
WantedBy=multi-user.target


- Browser: 
  * http//[your_raspberrypi_IP]:2409

- Video:
  * https://www.youtube.com/watch?v=SfQd1FdcTlI

- Other References:
  * http://www.piface.org.uk/guides/Install_PiFace_Software/
  * https://piface.github.io/pifacedigitalio/

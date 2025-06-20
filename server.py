import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import datetime
import json
import sys

# Fake PiFace data to simulate input/output states
class FakePiFaceDigital:
    def __init__(self):
        self.input_port = FakePort()
        self.output_port = FakePort()

class FakePort:
    """Simulates an 8-bit input/output port."""
    def __init__(self):
        self.value = 0b00000000  # All pins start as low (0)

    def toggle_pin(self, pin):
        """Toggle the state of a specific pin."""
        self.value ^= (1 << pin)  # XOR flips the specific pin

# Initialize a fake PiFace for simulation purposes
pifacedigital = FakePiFaceDigital()

class IndexHandler(tornado.web.RequestHandler):
    async def get(self):
        self.render("index.html")  # Serve the "index.html" page

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    clients = []  # Track all connected clients
    last_data = None  # Store the last state sent to clients

    def open(self):
        self.connected = True
        print("New connection")
        self.clients.append(self)
        self.timeout_loop()

    def check_origin(self, origin):
        """Allow connections from any origin."""
        return True

    def on_message(self, message):
        """Handle messages from the client."""
        try:
            # Simulate toggling a pin based on the received message
            pin = int(message)
            pifacedigital.output_port.toggle_pin(pin)
            self.timeout_loop()
        except ValueError:
            print("Invalid message received:", message)

    def on_close(self):
        self.connected = False
        print("Connection closed")
        self.clients.remove(self)

    def timeout_loop(self):
        """Simulate periodically sending input/output states to clients."""
        # Simulate input/output states
        r_input = '{0:08b}'.format(pifacedigital.input_port.value)
        r_output = '{0:08b}'.format(pifacedigital.output_port.value)

        # Prepare data to send to clients
        data = {"in": [], "out": []}
        for i in range(8):
            data['in'].append(r_input[7 - i])
            data['out'].append(r_output[7 - i])

        # Only send updates if the data has changed
        if data != self.last_data:
            for client in self.clients:
                client.write_message(json.dumps(data))
        self.last_data = data

        # Continue looping if the client is still connected
        if self.connected:
            tornado.ioloop.IOLoop.instance().add_timeout(
                datetime.timedelta(seconds=0.5), self.timeout_loop
            )

# Tornado application setup
application = tornado.web.Application([
    (r'/', IndexHandler),        # HTTP handler for the main page
    (r'/piface', WebSocketHandler)  # WebSocket handler
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)  # Start the server on port 8888
    print("WebSocket Server started at localhost:8888")
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

import socket, logging, threading
import json
import queue
import pathlib
import os.path


# Comment out the line below to not print the INFO messages
logging.basicConfig(level=logging.INFO)


class HttpRequest():

    def __init__(self, requeststr):
        self.rstr = requeststr
        self.rjson = {}
        self.parse_string()


    def parse_string(self):
        req = self.rstr.split("\r\n")
        print(req)
        requestLine = req[0].split()
        req.pop(0)
        reqLine = {}
        reqLine['method'] = requestLine[0]
        reqLine['URI'] = requestLine[1]
        reqLine['version'] = requestLine[2]
        self.rjson['request-line'] = reqLine

        if reqLine["method"] == "POST":
            body = req[-1]
            self.rjson['body'] = body
            # self.rjson['body-length'] = "size of body in bytes"
            print("JSON:", self.rjson['body'])

        headers = {}
        length = 0
        for line in req:
            start = ""
            for element in line:
                if element == ':' and start != "":
                    if (start == "Content-Length"):
                        num = line[len(start)+2:len(line)]
                        length = int(num)

                    end = line[len(start)+2:len(line)]
                    headers[start] = end
                    break
                start += element
        
        headers["Content-Length"] = length
        self.rjson['headers'] = headers
        print("+++++++++++++++++\rHEADERS:", self.rjson['headers'],"\r+++++++++++++++++\r")


    def display_request(self):
        print("\n\nJSON: \n",self.rjson)

    def process_request(self):
        method = self.rjson["request-line"]["method"]
        print("method:", method)
        URI = "WWW" + self.rjson["request-line"]["URI"]
        print("URI:", URI)

        # TODO: ADD ONTO THIS : 
            # HTTP/1.1 404 Not Found
            # Date: Sun, 18 Oct 2012 10:36:20 GMT
            # Server: Apache/2.2.14 (Win32)
            # Content-Length: 230
            # Content-Type: text/html; charset=iso-8859-1
            # Connection: Closed

            # && LINK : https://www.tutorialspoint.com/http/http_message_examples.htm



        response = b"HTTP/1.1 404 File not found\r\nServer: cihttpd\r\n\r\n<html><body><h1>404 File not found</h1><p>\n\t\t-The Garbage Tier Server</p></body></html>"

        if method == "POST":
            print( "\r--------------\rLENGTH:", self.rjson, "\r--------------\r" )

        try:
            with open(URI, "r") as f:
                # print(f.read()) 
                r = "HTTP/1.1 200 OK\r\nServer: cihttpd\r\n\r\n" + f.read()
                response = bytes(r, 'utf-8')
        except IOError:
            print("FILE NOT FOUND")
            
        return response





class ClientThread(threading.Thread):
    def __init__(self, address, socket, turn, queue, clientNumber):
        threading.Thread.__init__(self)
        self.csock = socket
        self.turn = turn
        self.queue = queue
        self.client = clientNumber
        logging.info('New connection added.')


    def run(self):
        if self.client == -1:
            request = self.csock.recv(1024)
            req = request.decode('utf-8')
            self.csock.send(b"HTTP/1.1 503 SERVER BUSY\r\nServer: cihttpd\r\n\r\n<html><body><h1>503 SERVR BUSY, TRY AGAIN</h1><p> \r\t\t\t- The Garbage Tier Server.</p></body></html>")
        else:
            with self.turn:
                # exchange messages
                request = self.csock.recv(1024)
                req = request.decode('utf-8')

                while self.queue.whos_turn() != self.client:
                    # client is waiting for server to not be busy
                    self.turn.wait() # wait

                print("\n\n---\nClient:[",self.client,"]")
                print("Client Queue:",self.queue.get_queue())

                httpreq = HttpRequest(req)
                # httpreq.display_request()

                # TODO: Process Request GET
                # TODO: Process Request POST
                self.csock.send(httpreq.process_request())
                
                logging.info('Disconnect client.')
                self.turn.notify()

            # disconnect client
            self.queue.exit_queue()
        self.csock.close()


def server():
    logging.info('Starting cihttpd...')

    # start serving (listening for clients)
    port = 9001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost',port))

    q = queue.QueueMachine()
    clientNumber = 0

    turn = threading.Condition() # two phases turn.wait()  & turn.notify()
    
    logging.info('Server is listening on port ' + str(port))

    while True:
        sock.listen(1)
        # client has connected
        sc,sockname = sock.accept()
        # logging.info('Accepted connection.')
        clientNumber = q.enter_queue()
        # print('Client:',clientNumber,' entering the server.')
        t = ClientThread(sockname, sc, turn, q, clientNumber)
        t.start()


server()
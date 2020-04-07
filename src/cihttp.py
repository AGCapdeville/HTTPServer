import socket, logging, threading
import json

# Comment out the line below to not print the INFO messages
logging.basicConfig(level=logging.INFO)


class HttpRequest():
    def __init__(self, requeststr):
        self.rstr = requeststr
        self.rjson = {}
        self.parse_string()

    def parse_string(self):
        req = self.rstr.split("\r\n")

        requestLine = req[0].split()
        req.pop(0)
        reqLine = {}
        reqLine['method'] = requestLine[0]
        reqLine['URI'] = requestLine[1]
        reqLine['version'] = requestLine[2]
        self.rjson['request-line'] = reqLine

        headers = []
        for line in req:
            head = {}
            start = ""
            for element in line:
                start += element
                
                if element == ':' and start != "":
                    end = line[len(start):len(line)]
                    head[start] = end
                    headers.append(head)
                    break
                
        self.rjson['headers'] = headers


    def display_request(self):
        print("\n\nJSON: \n",self.rjson)

    def process_request(self):
        if self.rjson['request-line']['method'] == 'GET':
            # process the GET
            return(b"HTTP/1.1 GET AKN \r\nServer: cihttpd\r\n\r\n<html><body><h1>Acknowledged! File exists</h1><p>Still Garbage Tier Server.</p></body></html>")
        else:
            return(b"HTTP/1.1 500 Not a real fake server (yet).\r\nServer: cihttpd\r\n\r\n<html><body><h1>500 UWU Internal Server Error</h1><p>Garbage Tier Server.</p></body></html>")
        




class ClientThread(threading.Thread):
    def __init__(self, address, socket):
        threading.Thread.__init__(self)
        self.csock = socket
        logging.info('New connection added.')



    def run(self):
        # exchange messages
        request = self.csock.recv(1024)
        req = request.decode('utf-8')

        httpreq = HttpRequest(req)
        httpreq.display_request()
        
        # TODO: Process Request GET
        # TODO: Process Request POST

        # process & send a response
        self.csock.send(httpreq.process_request())

        # disconnect client
        self.csock.close()
        logging.info('Disconnect client.')


def server():
    logging.info('Starting cihttpd...')

    # start serving (listening for clients)
    port = 9001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost',port))
    
    while True:
        sock.listen(1)

        # client has connected
        logging.info('Server is listening on port ' + str(port))
        sc,sockname = sock.accept()
        logging.info('Accepted connection.')
        t = ClientThread(sockname, sc)
        t.start()


server()
import socket

class URL:

    scheme : str
    host : str
    path : str

    def __init__(self, url : str):
        self.scheme, url = url.split("://", 1)
        assert self.scheme == "http"

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

    def request(self):
        s = socket.socket(
            family = socket.AF_INET,
            type = socket.SOCK_STREAM,
            proto = socket.IPPROTO_TCP
        )
        s.connect((self.host, 80))
        
        # Make a request
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        request += "\r\n"

        s.send(request.encode("utf8")) # Send the request

        response = s.makefile("r", encoding="utf8", newline="\r\n") # Receive response and decode via UTF8(SHORTCUT)

        # Breaking response
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line in "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
    

    
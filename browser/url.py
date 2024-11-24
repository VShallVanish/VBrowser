import socket
import ssl

class URL:

    # URL Attributes
    scheme : str
    host : str
    path : str
    port : int

    # URL Constructor
    def __init__(self, url : str):
        try:
            self.scheme, url = url.split("://", 1)
            assert self.scheme in ["http", "https", "file"]

            if "/" not in url:
                url = url + "/"
            self.host, url = url.split("/", 1)
            
            if self.scheme == "http":
                self.port = 80
                self.path = "/" + url
            elif self.scheme == "https":
                self.port = 443
                self.path = "/" + url
            elif self.scheme == "file":
                self.port = 8000
                self.path = "./" + url
                
            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)
                
        except Exception as e:
            print("Invalid URL, falling back to default URL")
            print("User URL:", url)
            print("Error:", e)
            self.scheme = "file"
            self.host = ""
            self.path = "./index.html"
            self.port = 8000

    # Request Method
    def request(self):
        s = socket.socket(
            family = socket.AF_INET,
            type = socket.SOCK_STREAM,
            proto = socket.IPPROTO_TCP
        )
        
        print("Connecting to:", self.host, "on port:", self.port)
        s.connect((self.host, self.port)) # Connect to the server
        
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        
        # Make a request
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        request += "Connection: close\r\n"
        request += "User-Agent: VBrowser\r\n"
        request += "\r\n"

        s.send(request.encode("utf8")) # Send the request

        # Breaking response
        response = s.makefile("r", encoding="utf8", newline="\r\n") # Receive response and decode via UTF8(SHORTCUT)
        
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line in "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
            
        # Make sure data is not being sent in an encoded format    
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read()
        s.close()
        
        return content
  
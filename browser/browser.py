import socket
import ssl
import tkinter


WIDTH, HEIGHT = 800, 600

HSTEP, VSTEP = 13, 18


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
                
        except:
            print("Invalid URL, falling back to default URL")
            print("User URL:", url)
            self.__init__("file:///index.html")

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
        response : str = s.makefile("r", encoding="utf8", newline="\r\n") # Receive response and decode via UTF8(SHORTCUT)
        
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
    
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title("VBrowser")
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        
        # Pack and enable resizing on the canvas
        self.canvas.pack(fill = tkinter.BOTH, expand = True)
        
        # self.window.bind("<Configure>", self.resize) #TODO: Fix this
        
        self.scroll = 0
        self.window.bind("<Down>", self.scrollDown)
        self.window.bind("<Up>", self.scrollUp)
        self.window.bind("<Button-4>", self.scrollUp)
        self.window.bind("<Button-5>", self.scrollDown)
        self.SCROLLSTEP = 100
        self.pageText = ""
        
    def resize(self, e):
        WIDTH, HEIGHT = e.width, e.height
        self.display_list = layout(self.pageText)
        self.draw()
        
    def load(self, url):
        if url.scheme == "file": # Handle file schema
            with open(url.host + url.path, "r") as f:
                body = f.read()
        else:    
            body = url.request()
        
        self.pageText = lex(body)
        
        self.display_list = layout(self.pageText)
        self.draw()
                
    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
            
    def scrollDown(self, e):
        self.scroll += self.SCROLLSTEP
        self.draw()
        
    def scrollUp(self, e):
        if self.scroll > 0:
            self.scroll -= self.SCROLLSTEP
        self.draw()

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        
        if cursor_x >= WIDTH - HSTEP:
            cursor_x = HSTEP
            cursor_y += VSTEP
        
    return display_list
    
def lex(body):
    text = ""
    in_tag = False
    in_entity = False
    entity = ""
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif c == "&":
            in_entity = True
            entity = ""
        elif c == ";":
            in_entity = False
            if entity == "lt":
                text += "<"
            elif entity == "gt":
                text += ">"
            else:
                text += "&" + entity + ";"
            entity = ""
            
        elif in_entity:
            entity += c
        elif not in_tag and not in_entity:
            text += c
            
    return text
        
        
if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
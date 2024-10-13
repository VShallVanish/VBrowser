import socket
import ssl
import tkinter
import tkinter.font


global WIDTH, HEIGHT, HSTEP, VSTEP

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
        
        # Make the scroll bar on the right side of the screen and fit it to the window
        # self.scrollbar = tkinter.Scrollbar(self.window)
        # self.scrollbar.pack(side = tkinter.RIGHT, fill = tkinter.Y)
        
        # Set the title of the window
        self.window.title("VBrowser")
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        print("Canvas created")
        # print(tkinter.font.families())
        
        # Pack and enable resizing on the canvas
        self.canvas.pack(fill = tkinter.BOTH, expand = True)
        
        self.window.bind("<Configure>", self.resize)
        
        self.scroll = 0
        self.window.bind("<Down>", lambda e: self.scrollDown(e))
        self.window.bind("<Up>", lambda e: self.scrollUp(e))
        self.window.bind("<Button-4>", lambda e: self.scrollUp(e))
        self.window.bind("<Button-5>", lambda e: self.scrollDown(e))

        self.display_list = []
        self.SCROLLSTEP = 100
        self.pageText = ""
        self.width, self.height = WIDTH, HEIGHT
        
    # Windows has resized, update the display list
    def resize(self, event):
        if (self.width, self.height) != (event.width, event.height):
            self.width, self.height = event.width, event.height
            self.display_list = Layout(self.pageText).display_list
            self.draw()
        
    def load(self, url):
        if url.scheme == "file": # Handle file schema
            with open(url.host + url.path, "r") as f:
                body = f.read()
        else:    
            body = url.request()
        
        self.pageText = lex(body)
        
        self.display_list = Layout(self.pageText).display_list
        self.draw()
                
    def draw(self):
        self.canvas.delete("all")
        HEIGHT = self.height
        WIDTH = self.width
        for x, y, c, f in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + f.metrics("linespace") < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=f, anchor="nw")
            
    def scrollDown(self, e):
        self.scroll += self.SCROLLSTEP
        self.draw()
        
    def scrollUp(self, e):
        if self.scroll > 0:
            self.scroll -= self.SCROLLSTEP
        self.draw()

class Text:
    def __init__(self, text):
        self.text = text
        
class Tag:
    def __init__(self, tag):
        self.tag = tag

class Layout:
    def __init__(self, tokens):
        self.line = []
        self.display_list = []
        self.tokens = tokens
        
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12
        
        for tok in tokens:
            self.token(tok)
            
        self.flush()
    
    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
                 
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4  
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP
        
    
    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
        
    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        
        baseline = self.cursor_y + max_ascent * 1.25
        
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + max_descent * 1.25
        self.cursor_x = HSTEP
        self.line = []
        
FONTS = {}
    
def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]
          
def lex(body):
    out = []
    buffer = ""
    in_tag = False
    in_entity = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer:
                out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        elif c == "&":
            in_entity = True
            if buffer:
                out.append(Text(buffer))
            buffer = ""
        elif c == ";":
            in_entity = False
            if buffer == "lt":
                buffer += "<"
            elif buffer == "gt":
                buffer += ">"
            else:
                buffer += "&" + buffer + ";"
            buffer = ""
        else:
            buffer += c
    if buffer:
        if not in_tag and not in_entity:
            out.append(Text(buffer))
    return out
        
        
if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
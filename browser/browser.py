
import tkinter
import tkinter.font


global WIDTH, HEIGHT, HSTEP, VSTEP

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18

from url import URL
from html_parser import HTMLParser, Text, Element
  
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
        self.nodes = ""
        self.width, self.height = WIDTH, HEIGHT
        
    # Windows has resized, update the display list
    def resize(self, event):
        if (self.width, self.height) != (event.width, event.height):
            self.width, self.height = event.width, event.height
            self.document = DocumentLayout(self.nodes)
            self.display_list = []
            paint_tree(self.document, self.display_list)
            self.draw()
        
    def load(self, url):
        if url.scheme == "file": # Handle file schema
            with open(url.host + url.path, "r") as f:
                body = f.read()
        else:    
            body = url.request()
        
        self.nodes = HTMLParser(body).parse()
        
        self.document = DocumentLayout(self.nodes)
        self.display_list = []
        paint_tree(self.document, self.display_list)
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

class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None

        
    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        
        self.width = WIDTH - 2*HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height
        
    
    def paint(self):
        return []

class BlockLayout:
    BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"]
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.display_list = []
        
        # self.cursor_x = HSTEP
        # self.cursor_y = VSTEP
        # self.weight = "normal"
        # self.style = "roman"
        # self.size = 12
        
        # self.recurse(self.tokens)
        # self.flush()
        
    def layout_intermediate(self):
        previous = None
        for child in self.node.children:
            next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next
            
    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any([isinstance(child, Element) and \
                child.tag in self.BLOCK_ELEMENTS for child in self.node.children]):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"
        
    def layout(self):
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
            
        self.x = self.parent.x
        self.width = self.parent.width
        mode = self.layout.mode()
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 12
            
            self.line = []
            self.recurse(self.node)
            self.flush()
            
        for child in self.children:
            child.layout()
            
        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y
        
    
    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        
        if self.cursor_x + w > self.width:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
        
    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + max_ascent * 1.25
        
        for rel_x, word, font in self.line:
            x = self.x + rel_x
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + max_descent * 1.25
        self.cursor_x = 0
        self.line = []
        
    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()
            
    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "/p":
            self.flush()
            self.cursor_y += VSTEP
            
    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)
            
    def paint(self):
        return self.display_list
               
    
def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)
            

def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())
    
    for child in layout_object.children:
        paint_tree(child, display_list)


FONTS = {}
    
def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]
        
        
if __name__ == "__main__":
    import sys
    
    # body = URL(sys.argv[1]).request()
    # nodes = HTMLParser(body).parse()
    # print_tree(nodes)
    
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
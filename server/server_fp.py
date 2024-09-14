#!/usr/bin/env python3
import binascii
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
from http.server import SimpleHTTPRequestHandler
from io import BytesIO
import json
import base64
import mimetypes
from PIL import Image

def save_pixels(img:Image, filename:str):
    # Open the file where the pixels will be save
    fic = open(filename, "w")
    pix = img.load()
    # Parse the PIL object pixel by pixel
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            fic.write(str(pix[i, j]))
        fic.write('\n')
    fic.close()

def base64_to_pixels(base64_string: str, filename: str):
    try:
        img = Image.open(BytesIO(base64.b64decode(base64_string)))
    except binascii.Error as e:
        print("Error decoding base64: ", e)
        return None
    save_pixels(img, filename)

def fingerprint_from_noised(noised: str, r: int, g: int, b: int, a: int):
    #Delete html tag from noised base64 image (data:image/png;base64)
    noised = noised.split(',')[1]
    try:
        noised_canvas = Image.open(BytesIO(base64.b64decode(noised)))
    except binascii.Error as e:
        print("Error decoding base64: ", e)
        return None
    pix = noised_canvas.load()
    for i in range(noised_canvas.size[0]):
        for j in range(noised_canvas.size[1]):
            pr, pg, pb, pa = pix[i,j]
            pix[i,j] = (pr - r, pg - g, pb - b, pa - a)
    
    noised_canvas.save("unnoised.png")
    buffered = BytesIO()
    noised_canvas.save(buffered, format="png")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str

#Python webserver
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':        
            self.path = '/index.html'
            mime_type, _ = mimetypes.guess_type(self.path)
            with open('.' + self.path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.end_headers()
            self.wfile.write(bytes(content))
        else:
            self.send_response(404, "Not found")
            self.end_headers()
            self.wfile.write(b"<h1>Error 404: Not Found</h1>")

    def do_POST(self):
        if self.path == '/uploads':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = json.loads(post_data)
            noised = post_data['image']
            if "noise" in post_data:
                noise = post_data['noise'][0].split(',')
                r = int(noise[0])
                g = int(noise[1])
                b = int(noise[2])
                a = int(noise[3])
                print("With noise: ", noised)
                fingerprint = fingerprint_from_noised(noised, r, g, b, a)
                print("With deleted noise: ", fingerprint)
            else:
                print("Without noise: ", noised)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

httpd = HTTPServer(('0.0.0.0', 3000), SimpleHTTPRequestHandler)
#no ssl
httpd.serve_forever()


import socket
import datetime

class Request:
    def __init__(self, method, uri, version, text, headers):
        self.method = method
        self.uri = uri
        self.version = version
        self.text = text
        self.headers = headers

class Response:
    def __init__(self, version, code, reason, headers, text):
        self.version = version
        self.code = code
        self.reason = reason
        self.headers = headers
        self.text = text

# Middleware definitions
def logging_middleware(next_middleware):
    def middleware(request):
        print(f"Request: {request.method} {request.uri}")
        response = next_middleware(request)
        print(f"Response: {request.uri} {response.code} {response.reason}")
        return response
    return middleware

def static_files_middleware(next_middleware):
    def middleware(request):
        if '.' in request.uri:
            try:
                file_path = 'static' + request.uri
                with open(file_path, 'rb') as file:
                    content = file.read()
                    content_type = 'text/css' if file_path.endswith('.css') else 'text/javascript'
                    return Response("HTTP/1.1", 200, "OK", {"Content-Type": content_type}, content.decode())
            except FileNotFoundError:
                return Response("HTTP/1.1", 404, "Not Found", {"Content-Type": "text/html"}, "<h1>File Not Found</h1>")
        return next_middleware(request)
    return middleware

# Middleware chain
def apply_middleware(request, middlewares):
    if not middlewares:
        return router(request)
    first_middleware = middlewares[0]
    rest_middlewares = middlewares[1:]
    next_middleware = lambda req: apply_middleware(req, rest_middlewares)
    return first_middleware(next_middleware)(request)


def parse_http_request(request_data):
    lines = request_data.decode().split('\r\n')
    request_line = lines[0].split(' ')
    headers = {}
    for line in lines[1:]:
        if line:
            key, value = line.split(': ')
            headers[key] = value
    return Request(method=request_line[0], uri=request_line[1], version=request_line[2], text=None, headers=headers)

def encode_http_response(response):
    response_line = f"{response.version} {response.code} {response.reason}\r\n"
    headers = ''.join([f"{key}: {value}\r\n" for key, value in response.headers.items()])
    return (response_line + headers + "\r\n" + response.text).encode()

def read_template(file_name):
    with open(f'templates/{file_name}', 'r') as file:
        return file.read()

# Router and endpoints
def router(request):
    if request.uri == '/':
        return Response("HTTP/1.1", 200, "OK", {"Content-Type": "text/html"}, read_template('index.html'))
    elif request.uri == '/about':
        return Response("HTTP/1.1", 200, "OK", {"Content-Type": "text/html"}, read_template('about.html'))
    elif request.uri == '/experience':
        return Response("HTTP/1.1", 200, "OK", {"Content-Type": "text/html"}, read_template('experience.html'))
    elif request.uri == '/projects':
        return Response("HTTP/1.1", 200, "OK", {"Content-Type": "text/html"}, read_template('projects.html'))
    elif request.uri == '/info':
        headers = {"Location": "/about"}
        return Response("HTTP/1.1", 301, "Moved Permanently", headers, "")
    else:
        return Response("HTTP/1.1", 404, "Not Found", {"Content-Type": "text/html"}, "<h1>404 Not Found</h1>")

def common_headers_middleware(next_middleware):
    def middleware(request):
        response = next_middleware(request)
        # Common headers
        response.headers['Server'] = 'My cool HTTP server'
        response.headers['Date'] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.headers['Connection'] = 'close'
        response.headers['Cache-Control'] = 'no-cache'

        # Conditional headers
        if response.code != 301:
            response.headers['Content-Type'] = response.headers.get('Content-Type', 'text/html')
            response.headers['Content-Length'] = str(len(response.text))

        return response
    return middleware


def run_server():
    middlewares = [logging_middleware, static_files_middleware, common_headers_middleware]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 8000))
        s.listen()
        print("Server is listening on port 8000")

        while True:
            connection, addr = s.accept()
            with connection:
                data = connection.recv(8192)
                if not data:
                    connection.close()
                    continue

                request = parse_http_request(data)
                response = apply_middleware(request, middlewares)
                response_data = encode_http_response(response)
                
                connection.send(response_data)
                connection.close()

if __name__ == "__main__":
    run_server()

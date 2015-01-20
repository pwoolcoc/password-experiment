#!/usr/bin/env python3
import os
import re
import cgi
import sqlite3
from base64 import b64decode, b64encode

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from wsgiref.util import setup_testing_defaults, application_uri
from wsgiref.simple_server import make_server

PORT = 8000
KEY = b'VIA9YtdA6OXq2ORcPbLBz4RaP4y7LrW7icO8IRn+/xE='
conn = sqlite3.connect(":memory:")
DB = conn.cursor()

def make_db():
    DB.execute("CREATE TABLE users (username string, publickey string)")
    DB.execute("INSERT INTO users (username, publickey) VALUES (?, ?)",
                ('paul', b64decode(KEY)))

def postbody(environ):
    post_env = environ.copy()
    post_env["QUERY_STRING"] = ""
    return cgi.FieldStorage(
            fp=post_env["wsgi.input"],
            environ=post_env,
            keep_blank_values=True)

def redirect(location, start_response, code=302):
    if code == 302:
        status = "302 FOUND"
    else:
        status = "301 MOVED PERMANENTLY"

    headers = [("Location", location)]
    start_response(status, headers)
    return [b""]


def login(environ, start_response):
    post = postbody(environ)

    username = post['username'].value
    signed_username = b64decode(post['signed_username'].value)

    DB.execute("SELECT publickey FROM users WHERE username = ?", (username,))

    publickey = DB.fetchone()

    if publickey:
        try:
            key = VerifyKey(publickey[0])
            might_be_username = key.verify(signed_username).decode("utf-8")
        except BadSignatureError:
            return redirect("/failure.html", start_response)

    # should be able to remove this, VerifyKey will fail with an exception if
    # the password is bad
    if username == might_be_username:
        return redirect("/success.html", start_response)
    else:
        return redirect("/failure.html", start_response)

def register(environ, start_response):
    post = postbody(environ)

    username = post['username'].value
    publickey = b64decode(post['publickey'].value)
    signed_username = b64decode(post['signed_username'].value)

    key = VerifyKey(publickey)

    might_be_username = key.verify(signed_username).decode("utf-8")

    is_username = username == might_be_username

    if is_username:
        location = "/index.html"
        DB.execute("INSERT INTO users (username, publickey) VALUES (?, ?)",
                (username, publickey))
    else:
        location = "/failure.html"

    return redirect(location, start_response)

def notfound(start_response):
    status = "404 NOT FOUND"
    headers = [("Content-type", "text/plain; charset=utf-8")]

    start_response(status, headers)

    return ["404 Not found".encode("utf-8")]

def servefile(environ, start_response):
    filename = environ.get("PATH_INFO")
    if filename.endswith(".html"):
        filetype = "text/html"
    elif filename.endswith(".css"):
        filetype = "text/css"
    elif filename.endswith(".js"):
        filetype = "application/javascript"
    else:
        filetype = "text/plain"
    status = "200 OK"
    headers = [("Content-Type", "{0}; charset=utf-8".format(filetype))]

    start_response(status, headers)

    with open(uri_to_path(filename)) as f:
        return [f.read().encode("utf-8")]

def uri_to_path(uri):
    return uri[1:]

def index(environ, start_response):
    environ["PATH_INFO"] = "/index.html"
    with open(os.path.join(os.getcwd(), environ["PATH_INFO"][1:])) as f:
        content = f.read()

    status = "200 OK"
    headers = [("Content-Type", "text/html; charset=utf-8")]

    start_response(status, headers)

    DB.execute("SELECT * FROM users")

    collected = []
    # collected = ["{0}" for username, pk in results for results in DB.fetchmany()
    # if results]
    while True:
        results = DB.fetchmany()
        if not results:
            break

        for username, pk_ in results:
            pk = b64encode(pk_)
            collected.append("<tr><td>{0}</td><td>{1}</td></tr>".format(username, pk))

    final = re.sub(re.compile(r"%%USERS%%"), "\n".join(collected), content)
    return [final.encode("utf-8")]

def app(environ, start_response):
    setup_testing_defaults(environ)
    uri = environ.get("PATH_INFO")
    print("Requesting {0}".format(uri))

    routes = {
        r"^/$": index,
        r"^/index.html$": index,
        r"^/login$": login,
        r"^/register$": register,
    }

    found = False
    for r in routes:
        patt = re.compile(r)
        if patt.match(uri):
            found = True
            handler = routes[r]
            return handler(environ, start_response)

    if not found:
        if os.path.exists(uri_to_path(uri)):
            return servefile(environ, start_response)
        return notfound(start_response)


if __name__ == u'__main__':
    make_db()
    httpd = make_server('', 8000, app)
    print("Serving on port {port}".format(port=PORT))
    httpd.serve_forever()

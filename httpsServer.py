#!/usr/bin/env python

#Link to github: https://github.com/rhmoult/SecurityTools/blob/master/Platform_Independent/Python/httpsWithUpload/src/httpsWithUpload.py
"""Simple HTTP Server With Upload and SSL.
This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

Create a certificate using the hostname or IP address as the common name with
the following command: openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
Enter that path under /path/to/cert
"""

__version__ = "0.2"
__all__ = ["SimpleHTTPRequestHandler"]
__author__ = "Halcy0nic"
__home_page__ = "http://halcyonic.net/"
__ssl_addition__ = 'rhmoult'

import os
import posixpath
import BaseHTTPServer
import urllib
import cgi
import shutil
import mimetypes
import re
import sys  # Modification by rmoulton
import ssl  # Modification by rmoulton
from subprocess import call

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET/HEAD/POST commands.
    This serves files from the current directory and any of its
    subdirectories. The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.
    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.
    """

    server_version = "SimpleHTTPWithUpload/" + __version__

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        if info != 'DELETING':
            print r, info, "by: ", self.client_address
            f = StringIO()
            f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
            f.write("<html>\n<title>Upload Result Page</title>\n")
            f.write("<body background=\"wallpaper.jpg\", style=\'background-size:cover\'>\n\n")
            f.write("<h2 style=\"color:white\">Upload Result Page</h2>\n")
            f.write("<hr>\n")
            if r:
                f.write("<strong style=\"color:white\">Success: </strong>")
            else:
                f.write("<strong style=\"color:white\">Failed: </strong>")
            f.write("<p style=\"color:white\">")
            f.write(info)
            f.write("</p>")
            f.write("<br><strong><a style=\"color:white\" href=\"%s\">Click here to go back</a></strong>" % self.headers['referer'])
            f.write("<hr><small style=\"color:white\">Powered By: Halcy0nic & Nick Engmann, check for the new version ")
            f.write("<strong><a style=\"color:white\" href=\"https://github.com/Halcy0nic/SUBZero\">")
            f.write("here</a></strong>.</small></body>\n</html>\n")
            length = f.tell()
            f.seek(0)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            if f:
                self.copyfile(f, self.wfile)
                f.close()

    def do_DELETE(self, filename):
        """Serve a DELETE request."""
        delete_cmd = 'sudo rm -f ' + filename
        call(delete_cmd, shell=True)
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title style=\"color:white\">Upload Result Page</title>\n")
        f.write("<body background=\"wallpaper.jpg\", style=\'background-size:cover\'>\n\n")
        f.write("<h2 style=\"color:white\">Delete Result Page</h2>\n")
        f.write("<hr>\n")
        f.write("<strong style=\"color:white\">Successfully deleted the File: </strong>")
        f.write("<p style=\"color:white\">")
        f.write(filename)
        f.write("</p>")
        f.write("<br><strong><a style=\"color:white\" href=\"%s\">Click here to go back</a></strong>" % self.headers['referer'])
        f.write("<hr><small style=\"color:white\">Powered By: Halcy0nic & Nick Engmann, check for the new version ")
        f.write("<strong><a style=\"color:white\" href=\"https://github.com/Halcy0nic/SUBZero\">")
        f.write("here</a></strong>.</small></body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def deal_post_data(self):
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if boundary not in line:
            return False, "Content NOT begin with boundary"
        line = self.rfile.readline()
        remainbytes -= len(line)
        delete = re.findall(r'Content-Disposition.*name="delete:(.*)"', line)
        if delete:
            self.do_DELETE(delete[0])
            return False, "DELETING"
        fn = re.findall(r'Content-Disposition.*name="file"; filename="([^\/]*)"', line)
        if not fn:
            return False, "Can't find out file name..."
        path = self.translate_path(self.path)
        fn = os.path.join(path, fn[0])
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return False, "Can't create file to write, do you have permission to write?"

        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return True, "File '{}' upload success!".format(fn)
            else:
                out.write(preline)
                preline = line
        return False, "Unexpect Ends of data."

    def send_head(self):
        """Common code for GET and HEAD commands.
        This sends the response code and MIME headers.
        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
        """
        path = self.translate_path(self.path)
        # f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).
        Return value is either a file object, or None (indicating an
        error). In either case, the headers are sent, making the
        interface the same as for send_head().
        """
        try:
            directory_list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        directory_list.sort(key=lambda a: a.lower())
        f = StringIO()
        #displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>TeslaCam Secure File Upload</title>\n")
        f.write("<body background=\"wallpaper.jpg\", style=\'background-size:cover\'>\n<h2 style=\"color:white\">TeslaCam Secure File Upload</h2>\n")
        f.write("<hr>\n")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write("<input name=\"file\" type=\"file\" style=\"color:white\"/>")
        f.write("<input type=\"submit\" value=\"upload\"/></form>\n")
        f.write("<hr>\n<ul>\n")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        for name in directory_list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            if displayname != "httpsServer.py" and displayname != "wallpaper.jpg" and displayname != "server.pem": #Do not list httpsServer.py, wallpaper, or self signed cert
                f.write('<li><a href="%s" style=\"color:#808080\">%s</a>\n' % (urllib.quote(linkname), cgi.escape(displayname)))
                f.write("<input name=\"delete:%s\" type=\"submit\" value=\"delete\"/>" % cgi.escape(displayname))
        f.write("</form>\n")
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.
        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored. (XXX They should
        probably be diagnosed.)
        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.
        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).
        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.
        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.
        Argument is a PATH (a filename).
        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.
        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.
        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream',  # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
    })


def run(HandlerClass=SimpleHTTPRequestHandler, ServerClass=BaseHTTPServer.HTTPServer, protocol="HTTP/1.0"):

    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 443

    server_address = ('', port)

    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./server.pem', server_side=True)
    httpd.serve_forever()


if __name__ == '__main__':
    run()

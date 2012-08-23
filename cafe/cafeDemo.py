import cherrypy
import os
import simplejson
import sys
from multiprocessing import Process, Value, Queue

from auth import AuthController, require, member_of, name_is
from coffee import CoffeeMachine

cm = CoffeeMachine()

class RestrictedArea:
    
    # all methods in this controller (and subcontrollers) is
    # open only to members of the admin group
    
    _cp_config = {
        'auth.require': [name_is('staff')]
    }
    
    @cherrypy.expose
    def index(self):
        return """This is the admin only area."""

def check_credentials(username, password):
    if username == 'staff' and password == 'hacker':
        return None
    else:
        return u"Incorrect username or password."

MEDIA_DIR = os.path.join(os.path.abspath("."), u"media")


class Coffee:
    @require()
    @cherrypy.expose
    def index(self):
        return open(os.path.join(MEDIA_DIR, u'index.html'))
        
    @require()
    @cherrypy.expose
    def submit(self, quantity):
        print("\n*** pouring: %s ***\n" % quantity)
        cm.pour(int(quantity))
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(result="Pouring %s" % quantity))

    @require()
    @cherrypy.expose
    def till(self, log):
        print("\n *** %s *** " % log)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(result="saved"))

    @require()
    @cherrypy.expose
    def showlog(self):

        return open(u"/cafe/log.txt")

class Cafe:

    _cp_config = {
        'tools.sessions.on': True,
        'tools.auth.on': True
    }
    
    auth = AuthController()
    restricted = RestrictedArea()
    
    coffee = Coffee()
    
    @cherrypy.expose
    def index(self):
        return "\
<html><head><title>Open Shed Caf&eacute; Pi</title></head><body>\
<h1>Welcome to Open Shed</h1>\
<p>How may I serve you?</p>\
<ul>\
<li><a href='http://192.168.1.135'>Music</a></li>\
<li><a href='/coffee'>Coffee</a></li>\
<li><a href='/coffee/showlog'>log</a></li>\
</ul>\
</body></html>"
    
config = {'/media':
                {'tools.staticdir.on': True,
                 'tools.staticdir.dir': MEDIA_DIR,
                }
        }

cherrypy.server.socket_host = '0.0.0.0'
cherrypy.quickstart(Cafe(), '/', config=config)


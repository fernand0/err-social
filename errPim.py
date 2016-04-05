# This is a skeleton for Err plugins, use this to get started quickly.

from errbot import BotPlugin, botcmd
import ConfigParser
import subprocess
import os
import time
import urllib2
import re
import sys
import json
from bs4 import BeautifulSoup
from cStringIO import StringIO
from twitter import *
import facebook


class ErrPim(BotPlugin):
    """An Err plugin skeleton"""
    min_err_version = '1.6.0' # Optional, but recommended
    max_err_version = '4.0.4' # Optional, but recommended

    def ptw(self, msg, args):
        config = ConfigParser.ConfigParser()
        config.read([os.path.expanduser('~/.rssTwitter')])

        CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
        CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
        TOKEN_KEY = config.get('fernand0', "TOKEN_KEY")
        TOKEN_SECRET = config.get('fernand0', "TOKEN_SECRET")

        authentication  = OAuth(TOKEN_KEY, 
                                   TOKEN_SECRET, 
                                   CONSUMER_KEY, 
                                   CONSUMER_SECRET)
        t = Twitter(auth=authentication)
        reply = t.statuses.update(status = args)
        return reply["created_at"]

    def pfb(self, msg, args):
         config = ConfigParser.ConfigParser()
         config.read([os.path.expanduser('~/.rssFacebook')])

         oauth_access_token= config.get("Facebook", "oauth_access_token")

         graph = facebook.GraphAPI(oauth_access_token)
         return graph.put_object("me", "feed", message = args)
   
    # Passing split_args_with=None will cause arguments to be split on any kind
    # of whitespace, just like Python's split() does
    #@botcmd(split_args_with=None)
    @botcmd
    def buscar(self, msg, args):

         arg='/usr/bin/sudo /usr/bin/mairix %s'%args
         p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
         yield "Indexando ..." 
         data = p.communicate()
         yield data[0]

    @botcmd
    def tran(self, msg, args):
         url = 'http://www.zaragoza.es/api/recurso/urbanismo-infraestructuras/tranvia?rf=html&results_only=false&srsname=utm30n'
         cadTemplate = 'Faltan: [%d, %d] minutos (Destino %s)'
         
         if args:
            parada = args.upper()
         else:
            parada = "CAMPUS RIO EBRO"
         
         request = urllib2.Request(url)
         request.add_header("Accept",  "application/json")
         
         resProc = json.load(StringIO(urllib2.urlopen(request).read()))
         tit = 0
         if resProc["totalCount"] > 0:
            for i in range(int(resProc["totalCount"])):
                if (resProc["result"][i]["title"].find(parada) >= 0):
                   if (tit == 0):
			   yield "Parada: " + resProc["result"][i]["title"] + " (" + parada + ")"
			   tit = 1
                   timeDest = {}
                   if "destinos" in resProc["result"][i]:
                       for j in range(len(resProc["result"][i]["destinos"])):
                          if (resProc["result"][i]["destinos"][j]["destino"]) in timeDest:
                             timeDest[resProc["result"][i]["destinos"][j]["destino"]].append(resProc["result"][i]["destinos"][j]["minutos"])
                          else:
                             timeDest[resProc["result"][i]["destinos"][j]["destino"]] = []
                             timeDest[resProc["result"][i]["destinos"][j]["destino"]].append(resProc["result"][i]["destinos"][j]["minutos"])
                       for j in timeDest.keys():
                          time1 = timeDest[j][0]
                          if (len(timeDest[j]) > 1):
		                  time2 = timeDest[j][1]
		                  cad = cadTemplate % (time1, time2, j)
                          else:
		                  cad = cadTemplate % (time1, time1, j)
                          yield cad
                   else:
                      yield "No hay trenes"
         else:
            yield "Sin respuesta"


    @botcmd
    def dir(self, msg, args):
         url='http://diis.unizar.es/?q=directorio'
         
         req = urllib2.Request(url) 
         directorio = urllib2.urlopen(req)
         
         soup = BeautifulSoup(directorio)
         
         name=args
         found=0
         yield "Buscando... "+name
         for record in soup.find_all('tr'):
             if  re.match(".*"+name+".*", record.get_text(),re.IGNORECASE):
                  txt=''
                  for dato in record.find_all('td'):
                      txt=txt +' ' + dato.get_text()
                  yield txt
                  found = found + 1
         if (found==0):
            yield name+" not found."

    @botcmd
    def tw(self, msg, args):
         yield self.ptw(msg, args)

    @botcmd
    def fb(self, msg, args):	
         yield self.pfb(msg, args)

    @botcmd
    def ptf(self, msg, args):
         yield "Twitter..."
         yield self.ptw(msg, args)
         yield "Facebook..."
         yield self.pfb(msg, args)



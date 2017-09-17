# This is a skeleton for Err plugins, use this to get started quickly.

from errbot import BotPlugin, botcmd
import configparser
import subprocess
import os
import time
#import urllib2
import urllib.request
import requests
import re
import sys
import json
from bs4 import BeautifulSoup
#from cStringIO import StringIO
import io #import StringIO
from twitter import *
import facebook
from linkedin import linkedin
import dateparser

def end(msg=""):
    return("END"+msg)

class ErrPim(BotPlugin):
    """An Err plugin skeleton"""
    min_err_version = '1.6.0' # Optional, but recommended
    max_err_version = '4.3.4' # Optional, but recommended

    def get_configuration_template(self):
        """ configuration entries """
        config = {
            'pathMail': '',
            'listBlogs': '',
        }
        return config

    def _check_config(self, option):

        # if no config, return nothing
        if self.config is None:
            return None
        else:
            # now, let's validate the key
            if option in self.config:
                return self.config[option]
            else:
                return None
    @botcmd
    def addBlog(self, msg, args):
        self.config['listBlogs'].append(args)
        self.configure(self.config)
        yield(self.config)

    def is_date(self, string):
        if dateparser.parse(string):
            return True
        else:
            return False

    def selectLastLink(self, msg, args):
        url = self._check_config('listBlogs')
        r = requests.get(url)
        soup = BeautifulSoup(r.text)
        links = soup.find_all('a')
        listLinks = []
        for link in links:
            theUrl = link.get('href')
            theText = link.text
            if not self.is_date(theText):
                # some templates in Wordpress include the link with the date.
                if theUrl:
                    if (theUrl.find(url) >= 0 and (theUrl != url)):
                        if theUrl.count('/') > url.count('/') + 1:
                            # This is to avoid /about /rss and others...
                            listLinks.append((theUrl,theText))
                    if theUrl and ((theUrl[0] == '/') and (theUrl != '/')):
                        if theUrl.count('/') > 1:
                            listLinks.append((url+theUrl,theText))
        return(listLinks[0])

    def ptw(self, msg, args):
        config = configparser.ConfigParser()
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
        return "OK" #reply["created_at"]

    def pfb(self, msg, args):
        config = configparser.ConfigParser()
        config.read([os.path.expanduser('~/.rssFacebook')])

        oauth_access_token= config.get("Facebook", "oauth_access_token")

        graph = facebook.GraphAPI(oauth_access_token, version='2.7')

        graph.put_object("me", "feed", message = args)

        return "Ok" 

    def pln(self, msg, args):
        config = configparser.ConfigParser()
        config.read([os.path.expanduser('~/.rssLinkedin')])

        CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY")
        CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET")
        USER_TOKEN = config.get("Linkedin", "USER_TOKEN")
        USER_SECRET = config.get("Linkedin", "USER_SECRET")
        RETURN_URL = config.get("Linkedin", "RETURN_URL"),

        authentication = linkedin.LinkedInDeveloperAuthentication(
                    CONSUMER_KEY,
                    CONSUMER_SECRET,
                    USER_TOKEN,
                    USER_SECRET,
                    RETURN_URL,
                    linkedin.PERMISSIONS.enums.values())

        application = linkedin.LinkedInApplication(authentication)

        application.submit_share(comment=args)
        return "Ok" 


    def search(self, msg, args):
        path = self._check_config('pathMail')
        arg='/usr/bin/sudo -H -u %s /usr/bin/mairix "%s"'%(path, args)
        p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
        data = p.communicate()
        return data[0]

    @botcmd
    def ll(self, msg, args):
        yield "Looking for the link"
        link = self.selectLastLink(msg, args)
        yield(link)
        yield "Twitter..."
        self.ptw(msg, link[1]+' '+link[0])
        yield "Facebook..."
        self.pfb(msg, link[1]+' '+link[0])

    @botcmd
    def sm(self, msg, args):
        yield "Indexando ..." 
        yield self.search(msg, args)
        yield end()

    @botcmd(split_args_with=None)
    def sf(self, msg, args):
        yield "Searching %s"%args[0] 
        yield self.search(msg, args[0])
        if len(args) > 1:
           yield " in %s"%args[1] 

        path = self._check_config('pathMail')
        yield path
	# We are using mairix, which leaves a link to the messages in the
	# Search folder. Now we just look for the folders where the actual
	# messages are located.
        arg='/usr/bin/sudo -H -u %s /bin/ls -l /home/%s/Maildir/.Search/cur' % (path, path)
        p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
        data = p.communicate()
        
        folders = []
        
        
        for i in data[0].decode("utf-8").split('\n')[1:]:
            j = i[i.find('/.')+2:]
            folder = j[:j.find('/')]
            if folder and 'mairix' not in folder and not folder in folders: 
                if (len(args) == 1) or (len(args)>1 and folder.find(args[1])>=0):
                    folders.append(folder)

        yield folders
        yield end()


    @botcmd
    def tran(self, msg, args):
        url = 'http://www.zaragoza.es/api/recurso/urbanismo-infraestructuras/tranvia?rf=html&results_only=false&srsname=utm30n'
        cadTemplate = 'Faltan: [%d, %d] minutos (Destino %s)'
        
        if args:
           parada = args.upper()
        else:
           parada = "CAMPUS RIO EBRO"
        
        cad = 'Faltan: %s minutos (Destino %s)'
        request = urllib.request.Request(url)
        headers = {"Accept":  "application/json"}
        response = requests.get(url, headers = headers)
        resProc = response.json() 
        if resProc["totalCount"] > 0:
           tit = 0
           for i in range(int(resProc["totalCount"])):
               if (resProc["result"][i]["title"].find(parada) >= 0):
                  if (tit == 0):
                      yield "Parada: " + resProc["result"][i]["title"] + " (" + parada + ")"
                      tit = 1
                  dest = {}
                  for j in range(len(resProc["result"][i]["destinos"])):
                      myDest = resProc["result"][i]["destinos"][j]["destino"] 
                      if myDest in dest:
                          dest[myDest].append(resProc["result"][i]["destinos"][j]["minutos"])
                      else:
                          dest[myDest] = [resProc["result"][i]["destinos"][j]["minutos"]]
                  for j in dest.keys():
                      yield cad % (dest[j], j)
        else:
           yield "Sin respuesta"
        yield end()


    @botcmd
    def dir(self, msg, args):
        url='http://diis/?q=directorio'
        
        req = urllib.request.Request(url) 
        directorio = urllib.request.urlopen(req)
        
        soup = BeautifulSoup(directorio)
        
        name=args
        found=0
        self.send(msg.frm,
                  'Buscando... "{0}" '.format(name),
                  in_reply_to=msg,
                  groupchat_nick_reply=True)
        for record in soup.find_all('tr'):
            if  re.match(".*"+name+".*", record.get_text(),re.IGNORECASE):
                 txt=''
                 for dato in record.find_all('td'):
                     txt=txt +' ' + dato.get_text()
                 yield txt
                 found = found + 1
        if (found==0):
            self.send(msg.frm,
                      '"{0}" not found.'.format(name),
                      in_reply_to=msg,
                      groupchat_nick_reply=True)
        self.send(msg.frm,
                  '{0}'.format(end()),
                  in_reply_to=msg,
                  groupchat_nick_reply=True)

    @botcmd
    def tw(self, msg, args):
        yield self.ptw(msg, args)
        yield end()

    @botcmd
    def fb(self, msg, args):    
        yield self.pfb(msg, args)
        yield end()

    @botcmd
    def ln(self, msg, args):    
        yield self.pln(msg, args)
        yield end()

    @botcmd
    def ptf(self, msg, args):
        yield "Twitter..."
        yield self.ptw(msg, args)
        yield "Facebook..."
        yield self.pfb(msg, args)
        yield end()

    @botcmd
    def ptfl(self, msg, args):
        yield "Twitter..."
        yield self.ptw(msg, args)
        yield "Facebook..."
        yield self.pfb(msg, args)
        yield "LinkedIn..."
        yield self.pln(msg, args)
        yield end()


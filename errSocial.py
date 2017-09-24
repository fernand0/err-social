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
import pickle
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

        posHttp = args.find('http')
        if posHttp >=0:
            message = args[0:posHttp-1]
            link = args[posHttp:] 
            graph.put_object("me", "feed", message = message, link = link)
        else: 
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

    @botcmd
    def ll(self, msg, args):
        # The idea is to recover the list of links and to check whether the
        # link has been posted before or not. At the end we delete one link and
        # add the new one.
        path = os.path.expanduser('~')
        with open(path + '/.urls.pickle', 'rb') as f:
            theList = pickle.load(f)
        yield "Looking for the link"
        link = self.selectLastLink(msg, args)
        yield(link)
        if (link[0] in theList):
            yield "This should not happen. This link has been posted before"
        else:
            yield "Twitter..."
            self.ptw(msg, link[1]+' '+link[0])
            yield "Facebook..."
            self.pfb(msg, link[1]+' '+link[0])
            theList.pop()
            theList.append(link[0])
            with open(path+'/.urls.pickle', 'wb') as f:
                theList = pickle.dump(theList,f)
            yield theList

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


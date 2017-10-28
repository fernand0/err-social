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
import moduleSocial

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
                if not self.is_date(theText[:int(len(theText)/2)]):
                    # Twice
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
        res = moduleSocial.publishTwitter(args, '', '', 'fernand0')
        if type(res) is str:
            return("Something went wrong")
        else:
            return("Published! Text: ", res['text'], " Url: https://twitter.com/fernand0Test/status/%s"%res['id_str'])

    def pfb(self, msg, args):
        posHttp = args.find('http')
        if posHttp >=0:
            message = args[0:posHttp-1]
            link = args[posHttp:] 
            moduleSocial.publishFacebook(message, link, "", "", "me")
            #graph.put_object("me", "feed", message = message, link = link)
        else: 
            message = args
            moduleSocial.publishFacebook(message, "", "", "", "me")
            #graph.put_object("me", "feed", message = args)

        return "Ok" 

    def pln(self, msg, args):
        moduleSocial.publishLinkedin(args, '', '', '')
        return "Ok" 

    @botcmd
    def pl(self, msg, args):
        # The idea is to recover the list of links and to check whether the
        # link has been posted before or not. At the end we delete one link and
        # add the new one.
        path = os.path.expanduser('~')
        with open(path + '/.urls.pickle', 'rb') as f:
            theList = pickle.load(f)
        yield "Looking for the link"
        link = self.selectLastLink(msg, args)
        yield(link)
        if (link[0][link[0].find(':')+2:] in theList):
            yield "This should not happen. This link has been posted before"
        else:
            yield "Twitter..."
            self.ptw(msg, link[1]+' '+link[0])
            yield "Facebook..."
            self.pfb(msg, link[1]+' '+link[0])
            theList.pop()
            theList.append(link[0][link[0].find(':')+2:])
            # We need to avoid http or https
            with open(path+'/.urls.pickle', 'wb') as f:
                theList = pickle.dump(theList,f)
            yield theList


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
        if (link[0][link[0].find(':')+2:] in theList):
            yield "This should not happen. This link has been posted before"
        else:
            yield "I'd post it"

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


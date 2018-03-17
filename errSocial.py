# This is a the ErrSocial code. It is intended to be able to publish in some
# social networks (currently Twitter, Facebook, LinkedIn) usign the bot.
#
# It uses:
# https://github.com/fernand0/scripts/blob/master/moduleSocial.py
# This moduel has its own configuration files.
# 
# It can also check the links in a list of configured blogs and to publish the
# links

from errbot import BotPlugin, botcmd
import configparser
import subprocess
import os
import io
import time
import urllib.request
import requests
import re
import sys
import pickle
from bs4 import BeautifulSoup
from twitter import *
import facebook
from fbchat import Client
from fbchat.models import *
#https://github.com/carpedm20/fbchat
from linkedin import linkedin
import dateparser
import moduleSocial
# https://github.com/fernand0/scripts/blob/master/moduleSocial.py
import keyring
import keyrings #keyrings.alt
keyring.set_keyring(keyrings.alt.file.PlaintextKeyring())
# We will store credentials on the keyring

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
            'twUser': '',
            'fbUser': '',
            'twSearches': '',
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
        yield end()

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
        twUser = self._check_config('twUser')
        res = moduleSocial.publishTwitter(twUser, args, '', '', '', '', '')
        if type(res) is str:
            return("Something went wrong %s %s %s" % (res, twUser, args))
        else:
            return("Published! Text: %s Url: https://twitter.com/%s/status/%s"% (res['text'], twUser, res['id_str']))

    def pstw(self, msg, args):
        twUser = self._check_config('twUser')
        twExcl = [twUser]
        if len(args) > 1:
            search, excl = args[0], args[1]
            twExcl.append(excl)
        elif len(args) == 1 :
            search = args
        else:
            search = self._check_config('twSearches').split(' ')
            search, excl = search[0], search[1]
            twExcl.append(excl)
        res = moduleSocial.searchTwitter(search, twUser)
        self.log.debug("Res Twitter %s" % res)
        yield("There are %d tweets for search %s" % (len(res), search))
        tuitTxt = "Search:\nhttps://twitter.com/search?q=%s&src=typd\n"%search
        # This avoids showing big images from tweets
        for tuit in res: 
            if tuit['user']['screen_name'] not in twExcl: 
                # All the tweets at once
                tuitTxt = tuitTxt + 'https://twitter.com/'+tuit['user']['screen_name']+'/status/'+tuit['id_str']+'\n'
        yield tuitTxt.replace('_','\_')
        

    def pfb(self, msg, args):
        fbUser = self._check_config('fbUser')
        posHttp = args.find('http')
        if posHttp >=0:
            message = args[0:posHttp-1]
            link = args[posHttp:] 
            res = moduleSocial.publishFacebook(message, link, "", "", "me")
            #graph.put_object("me", "feed", message = message, link = link)
        else: 
            message = args
            res = moduleSocial.publishFacebook("me", message, "", "", "", "", "")
            #graph.put_object("me", "feed", message = args)

        return("Published! Text: %s Page: %s Url: https://facebook.com/%s/posts/%s"% (message, res[0], fbUser, res[1]['id'][res[1]['id'].find('_')+1:]))
        # Names hardcoded

    def pln(self, msg, args):
        return("Published! Url: %s" % moduleSocial.publishLinkedin('', args, '', '', '', '', '')['updateUrl'])

    @botcmd
    def rmfb(self, msg, args):
        email = args
        password = keyring.get_password('fb', email)

        client = Client(email, password)
        threads = client.fetchThreadList()
        
        i = 0 # Last message is the first one

        self.log.debug("Threads: %s", threads)
        import pprint
        pp = pprint.PrettyPrinter(indent=4)

        if len(threads) > 0:
            message = client.fetchThreadMessages(thread_id=threads[i].uid, limit=10)
            self.log.debug("Message: %s" % message[0])
            message = message[0].text
            self.log.debug("Form Message: %s" % pp.pprint(message[0].text))
            self.log.debug("Form Message: %s" % pp.pprint(message[1].text))
            self.log.debug("Form Message: %s" % pp.pprint(message[2].text)) 
        else: 
            message = "No messages"
            self.log.debug("Message: %s" % "empty list")
        
        #yield "Last message is '%s' " % message[2].text
        #yield "Last message is '%s' " % message[2].sticker
        #yield "Last message is '%s' " % client.fetchUserInfo(message[2].author)
        #yield "Last message is '%s' " % message[1].text
        #yield "Last message is '%s' " % message[1].sticker
        #yield "Last message is '%s' " % client.fetchUserInfo(message[1].author)
        yield "Last message is '%s' " % message
        #yield "Last message is '%s' " % message[0].sticker
        #author = client.fetchUserInfo(message[0].author)
        #self.log.debug("Form Message: %s" % pp.pprint(author['first_name']+' '+author['last_name']+str(author['affinity'])))
        #yield "Last author is '%s' " % author['first_name']+' '+author['last_name']+str(author['affinity'])

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
            res = self.ptw(msg, link[1]+' '+link[0])
            yield(res)
            yield "Facebook..."
            self.pfb(msg, link[1]+' '+link[0])
            theList = theList[1:]
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
        yield end()

    @botcmd(split_args_with=None)
    def stw(self, msg, args):
        for res in self.pstw(msg, args):
            yield(res)
        yield end()

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


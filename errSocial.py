# This is a the ErrSocial code. It is intended to be able to publish in some
# social networks (currently Twitter, Facebook, LinkedIn) usign the bot.
#
# It uses:
# https://github.com/fernand0/socialModules/blob/master/moduleSocial.py
# This moduel has its own configuration files.
# 
# It can also check the links in a list of configured blogs and to publish the
# links

import dateparser
import io
import urllib.request
import os
import requests
import re
import pickle
import subprocess
import time
import logging
from bs4 import BeautifulSoup
import sys


from errbot import BotPlugin, botcmd
from errbot.templating import tenv

# Needs to set $PYTHONPATH to the dir where this modules are located

#from twitter import *
#import facebook
#from fbchat import Client
#from fbchat.models import *
#https://github.com/carpedm20/fbchat
# Next modules from:
# https://github.com/fernand0/socialModules
# import socialModules.moduleSocial
from socialModules.configMod import *
import socialModules.moduleFacebook
import socialModules.moduleLinkedin
import socialModules.moduleMastodon
import socialModules.moduleTwitter
import socialModules.modulePocket
# We will store credentials on the keyring

def end(msg=""):
    return("END"+msg)

class ErrPim(BotPlugin):
    """A PIM (Personal Information Manager) Err plugin """
    min_err_version = '1.6.0' # Optional, but recommended
    max_err_version = '4.3.4' # Optional, but recommended

    def get_configuration_template(self):
        """ configuration entries """
        config = {
            'listBlogs': '',
            'lnUser': '',
            'twUser': '',
            'fbUser': '',
            'maUser': '',
            'poUser': '',
            'twSearches': '',
            'blogCache': '',
            'log': ''
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
    def logW(self, msg, args):
        """ Search in the log the last Finished commands and show them
        """
        n = 40 
        if args.isdigit(): 
            n = int(args) 
            
        if self.bot_config.BOT_LOG_FILE: 
            res = ''
            with open(self.config['log']) as f: 
                for line in f.readlines()[-n:]:
                    if (line.find('Waiting') >= 0) or (line.find('Finished') >= 0) :
                        pos = line.find('     ')
                        line = line[:pos] + line[pos+5-1:]
                        maxLen=len('11:03 [moduleSocial] fernand0-errbot -> Twitter: Waiting ... 40.89 ')
                        res = res + line[11:][:maxLen] + '\n'
                        # Five spaces
                return res
                
            return 'No log is configured, please define BOT_LOG_FILE in config.py'


    @botcmd
    def logS(self, msg, args):
        """ Show the log file defined in the bot configuration
        """
        n = 40 
        if args.isdigit(): 
            n = int(args) 
            
        if self.bot_config.BOT_LOG_FILE: 
            with open(self.config['log']) as f: 
                return '```\n' + ''.join(f.readlines()[-n:]) + '\n```' 
                #return self.config['log']
                
            return 'No log is configured, please define BOT_LOG_FILE in config.py'

    @botcmd
    def addBlog(self, msg, args):
        """ Add a URL to the 'listBlogs' config parameter
        """
        self.config['listBlogs'].append(args)
        self.configure(self.config)
        yield(self.config)
        yield end()

    def is_date(self, string):
        if dateparser.parse(string):
            return True
        else:
            return False

    def pma(self, msg, args):
        user = self._check_config('maUser')
        ma = socialModules.moduleMastodon.moduleMastodon()
        ma.setClient(user)
        ma.publishPost(args,'','')

    def ppo(self, msg, args):
        poUser = self._check_config('poUser')
        po = socialModules.modulePocket.modulePocket()
        po.setClient(poUser)
        res = po.publishPost('', args,'')

    def ptw(self, msg, args):
        twUser = self._check_config('twUser')
        tw = socialModules.moduleTwitter.moduleTwitter()
        tw.setClient(twUser)
        res = tw.publishPost(args,'','')
        self.log.info("Res: %s" % str(res))
        if isinstance(res, str):
            return("Published! Text: {}".format(res))
        else:
            return("Something went wrong %s %s %s" % (res, twUser, args))

    def pstw(self, msg, args):

        import socialModules.moduleTwitter

        tw = socialModules.moduleTwitter.moduleTwitter()

        twUser = self._check_config('twUser')
        tw.setClient(twUser)

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
        res = tw.search(search)
        res = res['statuses']
        res.reverse()
        self.log.debug("Res Twitter %s" % res)
        tuitTxt = []
        tuitTxt.append("There are %d tweets for search %s" % (len(res), search))
        tuitTxt.append("Search:\nhttps://twitter.com/search?q=%s&src=typd\n"%search)
        # This avoids showing big images from tweets
        for tuit in res: 
            if tuit['user']['screen_name'] not in twExcl: 
                # All the tweets at once
                tuitTxt.append('- @{0} {2} https://twitter.com/{1}/status/{3}'.format(tuit['user']['name'], tuit['user']['id'],tuit['text'], tuit['id']))
        return(tuitTxt)#.replace('_','\_')
        
    # def pfb(self, msg, args):
    #     page = self._check_config('fbUser')
    #     posHttp = args.find('http')
    #     
    #     fc = getApi('facebook', page)
    #     # fc = socialModules.moduleFacebook.moduleFacebook()
    #     # fc.setClient(page)

    #     if posHttp >=0:
    #         message = args[0:posHttp-1]
    #         link = args[posHttp:] 
    #         res = fc.publishPost(message, link, "")
    #     else: 
    #         message = args
    #         res = fc.publishPost(message, "", "")

    #     return("Published! Text: %s Page: %s Url: %s" %(message, page, res))

    def pln(self, msg, args):
        lnUser = self._check_config('lnUser')
        self.log.info("Publishing in LinkedIn")
        posHttp = args.find('http')
        client = socialModules.moduleLinkedin.moduleLinkedin()
        client.setClient(lnUser)
        self.log.info("Publishing in LinkedIn")
        
        if posHttp >=0:
            message = args[0:posHttp-1]
            link = args[posHttp:] 
            res = client.publishPost(message,link,'')
        else:
            message = args
            res = client.publishPost(message, None, "")
        self.log.info("Res: %s" % res)
        for re in res:
            yield(res)
        if isinstance(res, str): 
            return("Published! Url: %s" % res)
            # Res: {'updateKey': 'UPDATE-8822-6522789677471186944', 'updateUrl': 'www.linkedin.com/updates?topic=6522789677471186944'}
            # https://www.linkedin.com/feed/update/urn:li:activity:6522789677471186944/
        else: 
            if 'updateUrl' in res: 
                return("Published! Url: %s" % res['updateUrl']) 
            elif 'message' in res: 
                return("Published! Url: %s" % res['message'])

    @botcmd(split_args_with=None)
    def stw(self, msg, args):
        """ Search for a string in Twitter
        """
        if args:
            replies = self.pstw(msg, args)
            self.log.info("Replies %s"%str(replies))
            for res in replies:
                yield(res)
        else: 
            yield("No args")
        yield end()

    @botcmd 
    def ma(self, msg, args):
        """ Publish entry in Mastodon 
        """
        yield self.pma(msg, args)
        yield end()

    @botcmd
    def tw(self, msg, args):
        """ Publish entry in Twitter
        """
        yield self.ptw(msg, args)
        yield end()

    @botcmd
    def po(self, msg, args):
        """ Publish entry in Twitter
        """
        yield self.ppo(msg, args)
        yield end()

    # @botcmd
    # def fb(self, msg, args):    
    #     """ Publish entry in Facebook
    #     """
    #     yield self.pfb(msg, args)
    #     yield end()

    @botcmd
    def ln(self, msg, args):    
        """ Publish entry in LinkedIn
        """
        self.log.info("1 Publishing in LinkedIn")
        yield self.pln(msg, args)
        self.log.info("2 Publishing in LinkedIn")
        yield end()

    @botcmd
    def ptfm(self, msg, args):
        """ Publish entry in Twitter, Facebook, Mastodon
        """
        yield "Twitter..."
        yield self.ptw(msg, args)
        # yield "Facebook..."
        # yield self.pfb(msg, args)
        yield "Mastodon..."
        yield self.pma(msg, args)
        yield end()

    @botcmd
    def ptfl(self, msg, args):
        """ Publish entry in Twitter, Facebook, LinkedIn
        """
        yield "Twitter..."
        yield self.ptw(msg, args)
        yield "Facebook..."
        yield self.pfb(msg, args)
        yield "LinkedIn..."
        yield self.pln(msg, args)
        yield end()


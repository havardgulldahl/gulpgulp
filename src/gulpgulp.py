#!/usr/bin/env python
#-*- encoding: utf8 -*-
# havard@gulldahl.no (C) 2012
# GPLv3 License

FORMAT_CSV=1
FORMAT_TSV=2
FORMAT_JSON=3
FORMAT_XLS=4
FORMAT_DEFAULT = FORMAT_CSV

import urllib
import re
from HTMLParser import HTMLParser
import json
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import datetime
import sqlite3

class GulpLoginError(Exception):
    pass

req = None

class GulpParser(HTMLParser):
    reFloat = re.compile(r'^\d\d?,\d$')
    reTime = re.compile(r'^\d\d:\d\d:\d\d$')
    reDuration = re.compile(r'^\d\d\d\d:\d\d$')
    def __init__(self, channel, reportType, date):
        HTMLParser.__init__(self)
        self.meta = {'channel':channel,
                     'reportType':reportType,
                     'date':date}
        self.rows = []
        self.__currentrow = []
        self.__data = None
        self.__tag = None

    def handle_starttag(self, tag, attrs):
        print "Encountered a start tag: ==%s==" % tag
        if tag == 'tr' and len(self.__currentrow) > 0:
            # previous row had no end tag, force it
            self.handle_endtag('tr')
        self.__tag = tag
    def handle_endtag(self, tag):
        print "Encountered  an end tag: ==%s==" % tag
        if tag == 'tr':
            self.rows.append(self.__currentrow[:])
            self.__currentrow = []
        elif tag == 'td':
            self.__currentrow.append(self.parse_data(self.__data))
        self.__tag = None
        self.__data = None
    def handle_data(self, data):
        print "Encountered   some data: ==%s==" % data
        if self.__data is None:
            self.__data = data
        else:
            self.__data += data
    def parse_data(self, data):
        try:
            _data = data.strip()
        except AttributeError:
            return ''
        print "Parsing  some data: ==%s==" % _data
        if not len(_data): 
            return _data
        if self.reFloat.match(_data):
            return float(_data.replace(',', '.'))
        elif self.reTime.match(_data):
            _t = [ int(s, 10) for s in _data.split(':') ]
            _d = self.meta['date']
            if _t[0] > 23: # next day
                _d = _d + datetime.timedelta(1)
                _t[0] = _t[0] - 23
            return datetime.datetime.combine(_d, datetime.time(*_t))
        elif self.reDuration.match(_data):
            _mins, _secs = ( int(s, 10) for s in _data.split(':') )
            return datetime.timedelta(minutes=_mins, seconds=_secs)
        else:
            try:
                return int(_data)
            except ValueError:
                return _data
    

class gulp(object):
    loginurl = 'http://tv-research.gallup.no/Login.asp' 
    
    def __init__(self):
        self.loggedIn = False
        self.cookie = None

    def login(self, username, password):
        _data = ( ('submit', 'Send'), ('Login', 1), ('UserName', username), ('Password', password) )
        _req = urllib.urlopen(self.loginurl, _data)
        req = _req
        if _req.code <> 200:
            raise GulpLoginError('Username and password not accepted')
        else:
            self.loggedIn = True

    def readReport(self, channel, reportType, date):
        _scope = 'barne' # 'barne' || 'Overnight'
        _url =  'http://tv-research.gallup.no/sider/%s/table/%s/%.2s/%s%sNasjonalt%s%.2s%.2s%s.htm' % \
                 (channel,
                  date.year,
                  date.month,
                  channel,
                  _scope, 
                  reportType,
                  date.day,
                  date.month,
                  date.year)
        _url = '/Users/n18040/Documents/Utvikling/gulpgulp/examplereport.html'
        print _url
        return urllib.urlopen(_url)

    def parseReport(self, channel, reportType, date):
        _data = self.fixData(self.readReport(channel, reportType, date).read())
        _parser = GulpParser(channel, reportType, date)
        _parser.feed(_data)
        return _parser

    def fixData(self, data):
        return re.sub(r'<![^>]+>', '', data, re.M)

    def export(self, parser, format=None):
        _out = StringIO()
        _format = format or FORMAT_DEFAULT
        if _format == FORMAT_CSV:
            for r in parser.rows:
                _out.write(';'.join(r))
                _out.write('\r\n')
        elif _format == FORMAT_TSV:
            for r in parser.rows:
                _out.write('\t'.join(r))
                _out.write('\r\n')
        elif _format == FORMAT_JSON:
            _out.write(json.dumps(parser.rows))

        return (parser.meta, _out)


        

if __name__ == '__main__':
    import sys
    G = gulp()
    r = G.parseReport('NRK3', 'andel', datetime.date(2011, 9, 11))
    from pprint import pprint as pp
    pp(r.rows)

        


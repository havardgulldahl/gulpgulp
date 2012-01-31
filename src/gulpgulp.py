#!/usr/bin/env python
#-*- encoding: utf8 -*-
# havard@gulldahl.no (C) 2012
# GPLv3 License

cmt = """
     function login(uname, pass)
     {
        // http://doc.qt.nokia.com/4.7/qdeclarativeglobalobject.html#xmlhttprequest
          //var url = "http://tv-research.gallup.no/Login.asp";
          var url = "http://tv-research.gallup.no/Login.asp";
          var u = encodeURIComponent(uname);
          var p = encodeURIComponent(pass);
          var data = "submit=Send&Login=1&UserName="+u+"&Password="+p;
          console.log(data);
          var req = new XMLHttpRequest();
          req.open("POST", url);
          req.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
          req.send(data);
          req.onreadystatechange = function() {
            if (req.readyState == XMLHttpRequest.DONE) {
                console.log("POST ok");
                console.log("Status: "+req.status);
                console.log(req.getAllResponseHeaders());
                console.log("cookie: "+req.getResponseHeader("Set-Cookie"))
                if (req.status == 200) {
                    console.log("Logged in!");
                    header.loggedIn = true;
               }
            }
            else { console.log("no dice:"+req.readyState) }
          }
     }

     function openReport(chnl, reporttype, day, month, year)
     {
        var scope = "barne"; // "barne" || "Overnight"
        //var url = "http://tv-research.gallup.no/sider/NRK3/table/2011/06/NRK3OvernightNasjonaltandel29062011.htm"
        var url = "http://tv-research.gallup.no/sider/"+chnl+"/table/"+year+"/"+month+"/"+chnl+scope+"Nasjonalt"+
            reporttype + day + month + year + ".htm";
        console.log(url);
        webView.url = url;
        """

import urllib
import re
from HTMLParser import HTMLParser

class GulpLoginError(Exception):
    pass

req = None

class GulpParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
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
            try:
                self.__currentrow.append(self.__data.strip())
            except AttributeError:
                # self.data is None == empty tag
                self.__currentrow.append('')
        self.__tag = None
        self.__data = None
    def handle_data(self, data):
        print "Encountered   some data: ==%s==" % data
        if self.__data is None:
            self.__data = data
        else:
            self.__data += data
    

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

    def readReport(self, channel, reportType, day, month, year):
        _scope = 'barne' # 'barne' || 'Overnight'
        _url =  'http://tv-research.gallup.no/sider/%s/table/%s/%.2s/%s%sNasjonalt%s%.2s%.2s%s.htm' % \
                 (channel,
                  year,
                  month,
                  channel,
                  _scope, 
                  reportType,
                  day,
                  month,
                  year)
        _url = '/Users/n18040/Documents/Utvikling/gulpgulp/examplereport.html'
        print _url
        return urllib.urlopen(_url)

    def parseReport(self, channel, reportType, day, month, year):
        _data = self.fixData(self.readReport(channel, reportType, day, month, year).read())
        _parser = GulpParser()
        _parser.feed(_data)
        return _parser

    def fixData(self, data):
        return re.sub(r'<![^>]+>', '', data, re.M)

        

if __name__ == '__main__':
    import sys
    G = gulp()
    r = G.parseReport('NRK3', 'andel', 29, 11, 2011)
    print r
    from pprint import pprint as pp
    pp(r.rows)

        


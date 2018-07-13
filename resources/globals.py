import re
import os
import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import uuid
import string, random
import urllib, urllib2, requests
import HTMLParser
import time
import cookielib
import base64
from StringIO import StringIO
from datetime import datetime, timedelta
import calendar

# KODI ADDON GLOBALS
ADDON_HANDLE = int(sys.argv[1])
ADDON_PATH_PROFILE = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
LOCAL_STRING = xbmcaddon.Addon().getLocalizedString
ROOTDIR = xbmcaddon.Addon().getAddonInfo('path')
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"
ROOT_URL = 'http://stream.nbcsports.com/data/mobile/'

#Settings file location
settings = xbmcaddon.Addon()

#Main settings
#QUALITY = str(settings.getSetting(id="quality"))
CDN = int(settings.getSetting(id="cdn"))
USERNAME = str(settings.getSetting(id="username"))
PASSWORD = str(settings.getSetting(id="password"))
PROVIDER = str(settings.getSetting(id="provider"))
#CLEAR = str(settings.getSetting(id="clear_data"))
FREE_ONLY = str(settings.getSetting(id="free_only"))
#PLAY_MAIN = str(settings.getSetting(id="play_main"))
PLAY_BEST = str(settings.getSetting(id="play_best"))

filter_ids = [
            "show-all",
            "nbc-nfl",
            "nbc-premier-league",
            "nbc-nascar",
            "nbc-nhl",
            "nbc-golf",
            "nbc-pga",
            "nbc-nd",
            "nbc-college-football",
            "nbc-f1",
            "nbc-nba",
            "nbc-mlb",
            "nbc-rugby",
            "nbc-horses",
            "nbc-tennis",
            "nbc-indy",
            "nbc-moto",
            "nbc-olympic-sports",
            "nbc-csn-bay-area",
            "nbc-csn-california",
            "nbc-csn-chicago",
            "nbc-csn-mid-atlantic",
            "nbc-csn-new-england",
            "nbc-csn-philadelphia",
            "nbc-sny"
            ]

#Create a filter list
filter_list = []
for fid in filter_ids:
    if str(settings.getSetting(id=fid)) == "true":
        filter_list.append(fid)

#User Agents
UA_NBCSN = 'NBCSports-iOS/12153 CFNetwork/894 Darwin/17.4.0'

#Event Colors
FREE = 'FF43CD80'
LIVE = 'FF00B7EB'
UPCOMING = 'FFFFB266'
FREE_UPCOMING = 'FFCC66FF'


VERIFY = False
# Add-on specific Adobepass variables
SERVICE_VARS = {
    'public_key': 'nTWqX10Zj8H0q34OHAmCvbRABjpBk06w',
    'private_key': 'Q0CAFe5TSCeEU86t',
    'registration_url': 'http://nbcsports.com/activate',
    'requestor_id': 'nbcsports',
    'resource_id': urllib.quote("<rss version='2.0'><channel><title>nbcsports</title></channel></rss>")
}


def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date


def set_stream_quality(url):
    stream_url = {}
    stream_title = []

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "deflate",
        "Accept-Language": "en-us",
        "User-Agent": UA_NBCSN
    }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    master = r.text

    xbmc.log(str(master))

    cookies = ''
    for cookie in r.cookies:
        if cookies != '':
            cookies = cookies + "; "
        cookies = cookies + cookie.name + "=" + cookie.value

    xbmc.log(cookies)

    line = re.compile("(.+?)\n").findall(master)
    for temp_url in line:
        if '#EXT' not in temp_url:
            temp_url = temp_url.rstrip()
            start = 0
            if 'http' not in temp_url:
                if 'master' in url:
                    start = url.find('master')
                elif 'manifest' in url:
                    start = url.find('manifest')

            if url.find('?') != -1:
                replace_url_chunk = url[start:url.find('?')]
            else:
                replace_url_chunk = url[start:]

            temp_url = url.replace(replace_url_chunk,temp_url)
            temp_url = temp_url.rstrip() + "|User-Agent=" + UA_NBCSN
            temp_url = temp_url + "&Cookie=" + cookies

            if desc not in stream_title:
                stream_title.append(desc)
                stream_url.update({desc:temp_url})
        else:
            desc = ''
            start = temp_url.find('BANDWIDTH=')
            if start > 0:
                start = start + len('BANDWIDTH=')
                end = temp_url.find(',',start)
                if end != -1: desc = temp_url[start:end]
                else: desc = temp_url[start:]
                try:
                    int(desc)
                    desc = str(int(desc)/1000) + ' kbps'
                except:
                    pass

    if len(stream_title) > 0:
        stream_title.sort(key=natural_sort_key, reverse=True)
        if str(PLAY_BEST) == 'true':
            ret = 0
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.select('Choose Stream Quality', stream_title)

        if ret >= 0:
            url = stream_url.get(stream_title[ret])
        else:
            sys.exit()
    else:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog()
        dialog.ok('Streams Not Found', msg)

    return url


def natural_sort_key(s):
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def save_cookies(cookiejar):
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file,ignore_discard=True)
    except:
        pass
    for c in cookiejar:
        args = dict(vars(c).items())
        args['rest'] = args['_rest']
        del args['_rest']
        c = cookielib.Cookie(**args)
        cj.set_cookie(c)
    cj.save(cookie_file, ignore_discard=True)


def load_cookies():
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass

    return cj


def add_link(name, url, title, iconimage, fanart, info=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)

    liz.setProperty('fanart_image',fanart)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info is not None:
        liz.setInfo( type="Video", infoLabels=info)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    return ok


def add_free_link(name, link_url, iconimage, fanart=None, info=None, stream_info=None):
    ok = True
    u = sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode=6&icon_image="+urllib.quote_plus(iconimage)
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if info is not None:
        liz.setInfo( type="Video", infoLabels=info)
    if stream_info is not None:
        stream_values = ''
        for key, value in stream_info.iteritems():
            stream_values += '&' + urllib.quote_plus(key) + '=' + urllib.quote_plus(value)
        u += stream_values
    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,url=u,listitem=liz)
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    return ok


def add_premium_link(name, link_url, iconimage, fanart=None, info=None, stream_info=None):
    ok = True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode=5&icon_image="+urllib.quote_plus(iconimage)
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    if stream_info is not None:
        stream_values = ''
        for key, value in stream_info.iteritems():
            stream_values += '&' + urllib.quote_plus(key) + '=' + urllib.quote_plus(value)
        u += stream_values
    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,url=u,listitem=liz)
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    return ok


def add_dir(name, url, mode, iconimage, fanart=None, isFolder=True, info=None):
    ok = True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&icon_image="+urllib.quote_plus(str(iconimage))
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)

    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,url=u,listitem=liz,isFolder=isFolder)
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    return ok


def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]

    return param


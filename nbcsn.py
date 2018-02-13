from resources.globals import *
#from resources.adobepass import ADOBE
from adobepass.adobe import ADOBE


def categories():
    headers = {
        'User-Agent': UA_NBCSN
    }

    r = requests.get(ROOT_URL+'apps/NBCSports/configuration-ios.json', headers=headers, verify=VERIFY)
    json_source = r.json()

    olympic_icon = os.path.join(ROOTDIR, "olympics_icon.png")
    olympic_fanart = 'http://www.nbcolympics.com/sites/default/files/field_no_results_image/06April2016/bg-img-pye-951x536.jpg'
    add_dir('Olympics', ROOT_URL+'apps/NBCSports/configuration-ios.json', 3, olympic_icon, olympic_fanart)

    for item in json_source['brands'][0]['sub-nav']:
        display_name = item['display-name']
        url = item['feed-url']
        url = url.replace('/ios','/firetv')

        add_dir(display_name,url,4,ICON,FANART)


def olympics(url):
    headers = {
        'User-Agent': UA_NBCSN
    }

    r = requests.get(ROOT_URL+'apps/NBCSports/configuration-ios.json', headers=headers, verify=VERIFY)
    json_source = r.json()

    olympic_icon = os.path.join(ROOTDIR,"olympics_icon.png")
    olympic_fanart = 'http://www.nbcolympics.com/sites/default/files/field_no_results_image/06April2016/bg-img-pye-951x536.jpg'

    for item in json_source['sections'][0]['sub-nav']:
        display_name = item['display-name']
        url = item['feed-url']
        url = url.replace('/ios','/firetv')

        add_dir(display_name, url, 4, olympic_icon, olympic_fanart)


def scrape_videos(url):
    headers = {
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'User-Agent': UA_NBCSN,
        'Accept-Language': 'en-us',
    }

    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    if 'featured' in url:
        json_source = json_source['showCase']

    if 'live-upcoming' not in url:
        json_source = sorted(json_source, key=lambda k: k['start'], reverse=True)
    else:
        json_source = sorted(json_source, key=lambda k: k['start'], reverse=False)

    for item in json_source:
        if 'show-all' in filter_list or item['sport'] in filter_list:
            build_video_link(item)


def build_video_link(item):
    url = ''

    if 'ottStreamUrl' in item:
        url = item['ottStreamUrl']
    elif 'iosStreamUrl' in item:
        url = item['iosStreamUrl']
    elif 'videoSources' in item:
        if 'ottStreamUrl' in item['videoSources'][0]:
            url = item['videoSources'][0]['ottStreamUrl']
        elif 'iosStreamUrl' in item['videoSources'][0]:
            url = item['videoSources'][0]['iosStreamUrl']

    menu_name = item['title']
    title = menu_name
    desc = item['info']
    free = int(item['free'])
    tv_title = title
    if 'channel' in item:
        tv_title = item['channel']

    requestor_id = ''
    if 'requestorId' in item:
        requestor_id = item['requestorId']

    # Highlight active streams
    start_time = item['start']

    aired = start_time[0:4]+'-'+start_time[4:6]+'-'+start_time[6:8]
    genre = item['sportName']

    length = 0
    if 'length' in item:
        length = int(item['length'])

    info = {
        'plot':desc,
        'tvshowtitle':tv_title,
        'title':title,
        'originaltitle':title,
        'duration':length,
        'aired':aired,
        'genre':genre
    }

    imgurl = "http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/"+item['image']+"_m50.jpg"
    menu_name = filter(lambda x: x in string.printable, menu_name)

    start_date = stringToDate(start_time, "%Y%m%d-%H%M")
    start_date = datetime.strftime(utc_to_local(start_date),xbmc.getRegion('dateshort')+' '+xbmc.getRegion('time').replace('%H%H','%H').replace(':%S',''))
    info['plot'] = 'Starting at: '+start_date+'\n\n' + info['plot']

    if url != '':
        if free:
            menu_name = '[COLOR='+FREE+']'+menu_name + '[/COLOR]'
            add_free_link(menu_name,url,imgurl,FANART,info)
        elif FREE_ONLY == 'false':
            menu_name = '[COLOR='+LIVE+']'+menu_name + '[/COLOR]'
            add_premium_link(menu_name,url,imgurl,requestor_id,FANART,info)
    else:
        #elif my_time < event_start:
        if free:
            menu_name = '[COLOR='+FREE_UPCOMING+']'+menu_name + '[/COLOR]'
            add_dir(menu_name + ' ' + start_date, '/disabled', 0, imgurl, FANART, False, info)
        elif FREE_ONLY == 'false':
            menu_name = '[COLOR='+UPCOMING+']'+menu_name + '[/COLOR]'
            add_dir(menu_name + ' ' + start_date,'/disabled', 0, imgurl, FANART, False, info)


def sign_stream(stream_url, stream_name, stream_icon, requestor_id):
    #SERVICE_VARS['requestor_id'] = requestor_id
    adobe = ADOBE(SERVICE_VARS)
    if adobe.checkAuthN():
        if adobe.authorize():
            resource_id = get_resource_id()
            media_token = adobe.mediaToken()
            stream_url = tv_sign(media_token, resource_id, stream_url)
            stream_url = set_stream_quality(stream_url)
            listitem = xbmcgui.ListItem(path=stream_url)
            xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem)
        else:
            sys.exit()
    else:
        msg = 'Your device is not currently authorized to view the selected content.\n Would you like to authorize this device now?'
        dialog = xbmcgui.Dialog()
        answer = dialog.yesno("Authorize",msg)
        if answer:
            adobe.registerDevice()
            sign_stream(stream_url, stream_name, stream_icon, requestor_id)
        else:
            sys.exit()


def tv_sign(media_token, resource_id, stream_url):
    url = 'http://sp.auth.adobe.com/tvs/v1/sign'
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en;q=1",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": UA_NBCSN
    }

    payload = urllib.urlencode({'cdn': 'akamai',
                             'mediaToken': media_token,
                             'resource': base64.b64encode(resource_id),
                             'url': stream_url
                             })

    r = requests.post(url, headers=headers, cookies=load_cookies(), data=payload, verify=VERIFY)
    save_cookies(r.cookies)

    return r.text


def logout():
    adobe = ADOBE(SERVICE_VARS)
    adobe.deauthorizeDevice()


params=get_params()
url = None
name = None
mode = None
icon_image = None
requestor_id = None

if 'url' in params: url = urllib.unquote_plus(params["url"])
if 'name' in params: name = urllib.unquote_plus(params["name"])
if 'mode' in params: mode = int(params["mode"])
if 'icon_image' in params: icon_image = urllib.unquote_plus(params["icon_image"])
if 'requestor_id' in params: requestor_id = urllib.unquote_plus(params['requestor_id'])

if mode is None or url is None or len(url) < 1:
    categories()

elif mode == 3:
    olympics(url)

elif mode == 4:
        scrape_videos(url)

elif mode == 5:
        sign_stream(url, name, icon_image, requestor_id)

elif mode == 6:
    #Set quality level based on user settings
    stream_url = set_stream_quality(url)
    listitem = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem)

elif mode == 999:
    logout()

# Don't cache live and upcoming list
if mode==1:
    xbmcplugin.endOfDirectory(ADDON_HANDLE, cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

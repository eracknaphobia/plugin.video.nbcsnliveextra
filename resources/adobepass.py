from resources.globals import *


class ADOBE():    
    requestor_id=''
    public_key = ''
    private_key = ''
    api_root_url = 'http://api.auth.adobe.com'

    def __init__(self, requestor_id, public_key, private_key):        
        self.requestor_id = requestor_id
        self.public_key = public_key
        self.private_key = private_key


    def createAuthorization(self, request_method, request_uri):
        nonce = str(uuid.uuid4())
        epochtime = str(int(time.time() * 1000))        
        authorization = request_method + " requestor_id="+self.requestor_id+", nonce="+nonce+", signature_method=HMAC-SHA1, request_time="+epochtime+", request_uri="+request_uri
        signature = hmac.new(self.private_key , authorization, hashlib.sha1)
        signature = base64.b64encode(signature.digest())
        authorization += ", public_key="+self.public_key+", signature="+signature

        return authorization


    def registerDevice(self):         
        reggie_url = '/reggie/v1/'+self.requestor_id+'/regcode'
        authorization = self.createAuthorization('POST',reggie_url)       
        url = self.api_root_url+reggie_url
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "gzip, deflate"),
                    ("User-Agent", UA_PC),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]
        
        body = "registrationURL=http://sp.auth.adobe.com/adobe-services&ttl=1800&deviceId="+DEVICE_ID+"&format=json"        
        
        json_source = self.requestJSON(url, headers, body)
       
        #prompt user to got to http://activate.nbcsports.com/?device=Win10 and activate the code in the messagebox
        msg = '1. Go to [B][COLOR yellow]activate.nbcsports.com[/COLOR][/B][CR]'
        #msg += '2. Select [B][COLOR yellow]Windows 10[/COLOR][/B] as your device[CR]'
        msg += '2. Enter [B][COLOR yellow]'+json_source['code']+'[/COLOR][/B] as your activation code'
        #msg += "\n" + json_source['code']
        
        dialog = xbmcgui.Dialog() 
        #a = dialog.yesno(heading='Activate Device', line1=msg, nolabel='Cancel', yeslabel='Continue')
        ok = dialog.ok('Activate Device', msg)
        #if a:
        #self.authorizeDevice()        
        #return json_source

        

    def authorizeDevice(self, resource_id):
        auth_url = '/api/v1/authorize'
        authorization = self.createAuthorization('GET',auth_url)
        url = self.api_root_url+auth_url
        url += '?deviceId='+DEVICE_ID
        url += '&requestor='+self.requestor_id
        url += '&resource='+urllib.quote(resource_id)
        url += '&format=json'
        #req = urllib2.Request(url)

        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", UA_PC),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        json_source = self.requestJSON(url, headers)
       

    def deauthorizeDevice(self):        
        auth_url = '/api/v1/logout'
        authorization = self.createAuthorization('DELETE',auth_url)
        url = self.api_root_url+auth_url
        url += '?deviceId='+DEVICE_ID
        url += '&requestor='+self.requestor_id
        url += '&format=json'
        #req = urllib2.Request(url)

        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", UA_PC),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        try: json_source = self.requestJSON(url, headers, None, 'DELETE')
        except: pass
     

    def mediaToken(self, resource_id):
        url = 'http://api.auth.adobe.com/api/v1/tokens/media'
        url += '?deviceId='+DEVICE_ID
        url += '&requestor='+self.requestor_id        
        url += '&resource='+urllib.quote(resource_id)
        url += '&format=json'
        authorization = self.createAuthorization('GET','/api/v1/tokens/media')
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", UA_PC),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        json_source = self.requestJSON(url, headers)

        return json_source['serializedToken']


    def tvSign(self, media_token, resource_id, stream_url):
        url = 'http://sp.auth.adobe.com//tvs/v1/sign'        
        headers = [ ("Accept", "*/*"),
                    ("Accept-Encoding", "deflate"),
                    ("Accept-Language", "en;q=1"),
                    ("Content-Type", "application/x-www-form-urlencoded"),  
                    ("User-Agent", UA_PC)
                    ]        

        body = urllib.urlencode({'cdn' : 'akamai',
                                 #'mediaToken' : base64.b64encode(media_token),
                                 'mediaToken' : media_token,
                                 'resource' : base64.b64encode(resource_id),
                                 'url' : stream_url
                                })

        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))        
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = headers 
        response = opener.open(url, body)
        stream_url = response.read()
        response.close()
        SAVE_COOKIE(cj)
                
        return stream_url


    def requestJSON(self, url, headers, body=None, method=None):        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        try: cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        except: pass
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = headers     
          
        try:           
            request = urllib2.Request(url, body)
            if method == 'DELETE': request.get_method = lambda: method            
            response = opener.open(request)
            json_source = json.load(response) 
            response.close()
            SAVE_COOKIE(cj)
        except HTTPError as e:            
            if e.code == 403:
                msg = 'Your device is not authorized to view the selected stream.\n Would you like to authorize this device now?'
                dialog = xbmcgui.Dialog() 
                answer = dialog.yesno('Account Not Authorized', msg)                 
                if answer: self.registerDevice()
            sys.exit(0)

        return json_source
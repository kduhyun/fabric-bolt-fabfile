#-*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
import socket
import json
import datetime
from monitoring import *
__doc__ = """How to ensure that a given (HTTP) service stays up and running."""

f = open("./key.json", 'r')
key=json.loads(f.readline())
print(key['emailpw'])
print(key['emailaddress'])
print(key['fcmkey'])
print(key['receiveraddress'])
print(key['receiverfcm'])
f.close()

host="http://localhost:8080/util/serverlist"
hostname=socket.gethostname()
lastErrorTs=0
DURATION_MS=60000

class GmailSender(Action):
    def __init__(self, MSG=None, TO=None):
        Action.__init__(self)
        
        self.msg = MIMEText(MSG) 
        self.msg['Subject'] = "[ERR] "+hostname+" server error."
        self.msg['From'] = key['emailaddress']
        self.msg['To'] = TO
        self.password=key['emailpw']
        
        GmailSender.lastErrorTs=0
        
    def run(self, monitor, service, rule, runner):
        diff=rule.lastRun - FCMSender.lastErrorTs
        GmailSender.lastErrorTs = rule.lastRun        
        
        if(diff < DURATION_MS*2):
            return True
        
        s = smtplib.SMTP_SSL('smtp.gmail.com',465)
        s.login(self.msg['From'], self.password)
        s.sendmail(self.msg['From'], self.msg['To'], self.msg.as_string())
        s.quit()
        
        print("sent gmail.")
        
        return True

class FCMSender(Action):
    def __init__(self, MSG=None, TO=None):
        Action.__init__(self)
        
        url = "http://fcm.googleapis.com/fcm/send"

        if url.startswith("http://"):
            url = url[7:]
        server, uri = url.split("/",  1)

        if not uri.startswith("/"):
            uri = "/" + uri

        if server.find(":") >= 0:
            server, port = server.split(":", 1)
        else:
            port = 80

        self.server = server
        self.port = port
        self.uri = uri
        self.body = json.dumps({"data":{"msg":MSG,"mode":""},"to":TO})
        self.fcmkey=key['fcmkey']
        self.headers = {"Content-type": "application/json",
            "Authorization":"key="+self.fcmkey}
        self.method = "POST"
        self.timeout = 10
        FCMSender.lastErrorTs=0

    def run(self, monitor, service, rule, runner):
    
        diff=rule.lastRun - FCMSender.lastErrorTs
        FCMSender.lastErrorTs = rule.lastRun
        
        if(diff < DURATION_MS*2):
            return True
            
        conn = httplib.HTTPConnection(self.server, self.port, timeout=self.timeout)
        res = None
        try:
            conn.request(self.method, self.uri, self.body, self.headers or {})
            resp = conn.getresponse()
            res = resp.read()
        except Exception as e:
            return True
            
        print("sent FCM.")
        return True
        
Monitor(
    Service(
        name=__file__[0].split(".")[0],
        monitor=(
            HTTP(
                # We monitor the 'http://localhost:8000' URL, which is where
                # we expect the 'myservice' to be bound
                GET=host,
                freq=Time.ms(DURATION_MS/5),
                fail=[
                    Incident(
                        # If we have 5 errors during 5 seconds...
                        errors=2,
                        during=Time.ms(DURATION_MS),
                        actions=[
                            # We kill the 'myservice-start.py' script if it exists
                            # and (re)start it, so that the 'http://localhost:8000' will
                            # become available
                            # NOTE: Restart will make the process a child of the monitoring, so
                            # you might prefer to use something like upstart
                            Print("error!"),
                            GmailSender(MSG="[ERR] "+datetime.datetime.now().strftime("%H:%M:%S.%f")+","+hostname+" Timeout.", TO=key['receiveraddress']),
                            FCMSender(MSG="[ERR] "+datetime.datetime.now().strftime("%H:%M:%S.%f")+","+hostname+" Timeout.", TO=key['receiverfcm'])
                        ]
                    )
                ]
            )
        )
    )
).run()

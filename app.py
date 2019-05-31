from flask import Flask, render_template
import urllib.request
from datetime import datetime
import pandas as pd
from flask_mail import Mail, Message
import matplotlib.pyplot as plt
import requests
import json
import threading
from pathlib import Path
home = str(Path.home())
app=Flask(__name__, static_url_path='/static')
#setting up the configuration for smtp server for email
app.config.update(
	DEBUG=True,
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = 'senderemail785@gmail.com',
	MAIL_PASSWORD = 'SenderEmail785',
    MAIL_SUBJECT_PREFIX='test'
	)
mail = Mail(app)

@app.route('/')
def index():

    #the service will run in every five minutes to check if the data is correct or not, else send the notification for threshold breach
    threading.Timer(300.0, index).start()
    
    # create a df from the data imported from the url
    url='ftp://ftp.swpc.noaa.gov/pub/lists/particle/'+datetime.today().strftime('%Y%m%d')+'_Gp_part_5m.txt'
    df=pd.read_csv(url, skiprows=26,  sep="\s+", engine='python', names=['YR', 'MO', 'DA',  'HHMM', 'Modified Julian Day', 'Seconds of the Day', 'P > 1', 'P > 5', 'P >10', 'P >30', 'P >50', 'P>100', 'E>0.8', 'E>2.0', 'E>4.0'])
    
    #plot a graph for >10MeV levels according to the time(HHMM)
    df.plot(y=['P >10','P >30', 'P >50','P>100'],x='HHMM', kind="line")
    plt.draw()
    plt.savefig(home+'/img.png', dpi=100)

    #code for checking if level>1 or >10 or >100 or <1 and send email accordingly with apicall
    count1=0
    for i in ['P >10', 'P >30', 'P >50', 'P>100']:
        for j in range(len(df)):
            if float(df[i][j])>=1:
                sendEmail('Warning Email')
            elif float(df[i][j])>=10:
                sendEmail('Alert Email')
                callApi(float(df[i][j]), i)
            elif float(df[i][j])>=100:
                sendEmail('Critical Email')
                callApi(float(df[i][j]), i)
            else:
                if float(df[i][j])<1 and count1<90:
                    count1+=5
                elif float(df[i][j])<1 and count1==90:
                    callApi(float(df[i][j]), i)
                    sendEmail("info Email")
                    count1=0
                elif float(df[i][j])>=1:
                    count1=0

    return 'Hello Team Planet!!'

def sendEmail(body):
    # code for sending email with generated plot for >10MeV levels from the time, the sender and receipient email id can be changed
    msg = Message(body, sender="senderemail785@gmail.com", recipients=["surabhimaheshwari.cs@gmail.com"])
    msg.body = body
    with app.open_resource(home+"/img.png") as fp:
        msg.attach(home+"/img.png", "image/png", fp.read())
    with app.app_context():
        mail.send(msg)
    return 'Mail sent!'

def callApi(value, level):
    # code for calling the api, HTTP Request is post, content-type- 'application/json', url is configurable 'https://httpbin.org/post' is used for testing purposes in this code
    data={"alert_text": "Space weather "+str(level)+" : > 10 Mev proton flux currently at "+str(value),
           "level":str(level),
           "link":"https://www.swpc.noaa.gov/products/goes-proton-flux" }
    headers = {'Content-type': 'application/json'}
    r=requests.post('https://httpbin.org/post', json=json.dumps(data), headers=headers )

    #print the response
    print(r.status_code)
    print(r.json())

if __name__=='__main__':
    app.run()

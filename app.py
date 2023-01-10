from flask import Flask, jsonify, render_template, request
import requests
import xmltodict
import json
import xml.etree.ElementTree as ET
import jwt
import datetime
import uuid

app = Flask(__name__)

TABLEAU_HOST = "https://tableau-console-dev-dashboards.points.com/api/3.15"
SITE_ID = "0991ad9a-8a66-42a6-806a-97e631d65288"



def get_auth_token():
    try:
        data = """
        <tsRequest>
            <credentials personalAccessTokenName="APITEST"
                personalAccessTokenSecret="yajJU3P+S4KJuxAHPFvPCA==:8bqGnd8QEsCDYUcmRcItXJALQ861WmT1" >
                <site contentUrl="" />
            </credentials>
        </tsRequest>"""
        r = requests.post(f"{TABLEAU_HOST}/auth/signin", data=data)
        if (r.status_code == 200): 
            xml_response = ET.fromstring(r.text)
            token = list(xml_response[0].attrib.values())[0]
            return token
        else: 
            return "error" + r.status_code.__str__()
    except Exception as ex: 
        return ex   

@app.route('/', methods=['GET','POST'])
def get_workbooks(): 
    token = get_auth_token()
    try: 
        request = requests.get(f"{TABLEAU_HOST}/sites/{SITE_ID}/workbooks", headers={'Authorization': 'Bearer {}'.format(token)})
        if (request.status_code == 200): 
            views_parse = xmltodict.parse(request.text)
            views_json_format = json.dumps(views_parse)
         
            json_decoded = json.loads(views_json_format)
            workbooks = filter_dict(json_decoded, 'tsResponse.workbooks.workbook')
        
            return render_template('index.html', workbooks_data=workbooks, token=token)
    except Exception as ex: 
        return ex
  


@app.route('/views', methods=['GET','POST'])
def get_views(): 
    try: 
        workbook_name = request.args.get('content_url')
        workbook_id = request.args.get('id')
        token = request.args.get('token')
        r = requests.get(f"{TABLEAU_HOST}/sites/{SITE_ID}/workbooks/{workbook_id}", headers={'Authorization': 'Bearer {}'.format(token)})
        if(r.status_code == 200): 
            views_parse = xmltodict.parse(r.text)
            views_json_format = json.dumps(views_parse)

            json_decoded = json.loads(views_json_format)
            views = filter_dict(json_decoded, 'tsResponse.workbook.views.view')

            
            return render_template('views.html', views_data=views, content_url=workbook_name, token=token)
         
        else: 
            return "error" + r.status_code.__str__()
       
    except Exception as ex: 
        return ex

@app.route('/iframe', methods=['GET','POST'])
def get_iframe():  
        view_url_name = request.args.get('view_url_name')
        content_url = request.args.get('content_url')
        token = jwt.encode(
            {
                "iss": '91373ede-38f2-42a8-8327-bd9a2f34d297',
		        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
		        "jti": str(uuid.uuid4()),
		        "aud": "tableau",
		        "sub": 'tableau-dev@points.com',
		        "scp": ["tableau:views:embed"]
            }, 
            	'Inm6vn38AE0rVUXRiWt9xXVIqA7XbgNlJLNZ4EinQos=',
		        algorithm = "HS256",
		        headers = {
		        'kid': '42d5fa43-dc85-45e5-beb8-a1145c72ba95',
		        'iss': '91373ede-38f2-42a8-8327-bd9a2f34d297'
            }
        )
        return render_template('iframe.html', token=token, view_url_name=view_url_name, content_url=content_url)

def filter_dict(data: dict, extract):
    try:
        if isinstance(extract, list):
            while extract:
                if result := filter_dict(data, extract.pop(0)):
                    return result
        shadow_data = data.copy()
        for key in extract.split('.'):
            if str(key).isnumeric():
                key = int(key)
            shadow_data = shadow_data[key]
        return shadow_data
    except (IndexError, KeyError, AttributeError, TypeError):
        return None


if __name__ == '__main__': 
    app.run(debug=True, port=4000)
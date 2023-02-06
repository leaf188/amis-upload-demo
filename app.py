from flask import Flask,render_template,jsonify,request,make_response,Response
import datetime
import os
import uuid
import json

app = Flask(__name__)

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/upload',methods=['POST'])
def upload():
    file = request.files['file']
    now_time = datetime.datetime.now()
    today_str = datetime.datetime.strftime(now_time,'%Y%m%d')
   
    if os.path.exists(os.path.join(app.root_path,"upload",today_str))==False:
        os.makedirs(os.path.join(app.root_path,"upload",today_str))
    
    try:
        with open(os.path.join(app.root_path,"upload",today_str,file.filename),'wb') as f:
            f.write(file.stream.read())
    except IOError:
        return make_response('erro',500)
    
    return jsonify({
        "status": 0,
        "msg": "",
        "data": {
            "value": file.filename
        }
    })

@app.route('/startchunk',methods=['POST'])
def startchunk():
    data = json.loads(request.get_data(as_text=True))
    fileName = data['filename']
    now_time = datetime.datetime.now()
    today_str = datetime.datetime.strftime(now_time,'%Y%m%d')
   
    if os.path.exists(os.path.join(app.root_path,"upload",today_str))==False:
        os.makedirs(os.path.join(app.root_path,"upload",today_str))

    return jsonify({
        "status": 0,
        "msg": "",
        "data": {
            "key": today_str+"/"+fileName,
            "uploadId": str(uuid.uuid1()).replace('-','')
        }
    })

@app.route('/chunk',methods=['POST'])
def chunk():
    key = request.form.get('key')
    file = request.files['file']

    eTag = str(uuid.uuid1()).replace('-','')
    save_path = os.path.join(app.root_path,"upload",key.split('/')[0])
    file_path = os.path.join(save_path,eTag)
    
    try:
        with open(file_path,'ab') as f:
            f.seek(0)
            f.write(file.stream.read())
    except OSError:
        return make_response('errors',500)

    return jsonify({
        "status": 0,
        "msg": "",
        "data": {
            "eTag": eTag
        }
    })
    
@app.route('/finishchunk',methods=['POST'])
def finishchunk():
    data = json.loads(request.get_data(as_text=True))
    filename = data['filename']
    key = data['key']
    partList = data['partList']

    filePath = os.path.join(app.root_path,"upload",key.split('/')[0],filename)

    try:
        with open(filePath,'wb') as f:
            for part in partList:
                #partNumber = part['partNumber']
                eTag = part['eTag']
                eTagFile = open(os.path.join(app.root_path,"upload",key.split('/')[0],eTag),'rb')
                f.write(eTagFile.read())
                eTagFile.close()
                os.remove(os.path.join(app.root_path,"upload",key.split('/')[0],eTag))
    except IOError:
        return make_response('errors',500) 

    return jsonify({
        "status": 0,
        "msg": "",
        "data": {
            "value": request.url_root + "download/" + key
        }
    })

@app.route('/delete',methods=['POST'])
def delete_file():
    fileName = request.args.get('file')
    now_time = datetime.datetime.now()
    today_str = datetime.datetime.strftime(now_time,'%Y%m%d')
    filePath = os.path.join(app.root_path,"upload",today_str,fileName)
    if os.path.isfile(filePath):
        os.remove(filePath)
        return jsonify({"status":0,"msg":"The file has been deleted successfully. "})
    return jsonify({"status":422,"errors":" Failure!"})

@app.route('/download/<createdDate>/<fileName>')
def download(createdDate,fileName):
    filePath = os.path.join(app.root_path,"upload",createdDate,fileName)
    try:
        with open(filePath,'rb') as f:
            stream = f.read()
        response = Response(stream,content_type='application/octet-stream')
        response.headers['Content-dispostion']='attachment;filename=%s' %fileName
        return response 
    except IOError:
        make_response('errors',500) 

if __name__ == "__main__":
    app.run()

from flask import Flask, render_template, request, abort, jsonify, Response, url_for
from requests import get
from bson.objectid import ObjectId
from bson import SON
from .config import Config
import boto3, re, time, os, pymongo
import os, re
from flask import send_from_directory
from dlx import DB
from dlx.marc import AuthSet, BibSet, QueryDocument, Condition
#import datetime
import json
from datetime import datetime
from datetime import timedelta


'''
simple test URLs
/20200707/xml?skip=10&limit=35
/20200707/json?skip=10&limit=35
/unbis?skip=10&limit=35
/20200707/S?skip=10&limit=35
/2020-07-07/S?skip=10&limit=35


'''
# Initialize your application.
app = Flask(__name__)
if __name__ == "__main__":
    pass

DB.connect(Config.connect_string)
collection = Config.DB.bibs

# Define any classes you want to use here, or you could put
# them in other files and import.

return_data=""

# Start building your routes.

@app.route('/')
def index():
    return(render_template('index.html', data=return_data))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/date')
def date():
    '''
    returns the current date - for test purposes
    '''
    data={}
    current_time = datetime.datetime.now() 
    data['year']=current_time.year
    data['month']=current_time.month
    data['day']=current_time.day
    return(render_template('date.html', data=return_data))

@app.route('/<date>/xml')
def xml(date):
    '''
outputs records in MARCXML format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
/YYYYMMDD/xml?skip=n&limit=m
skip=n URL parameter is used to skip n records. Default is 0.
limit=m URL parameter is used to limit number of records returned. Default is 50.
if the date is in wrong format the function returns today's records
it uses DLX bibset.to_xml serialization function to output MARCXML
'''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        #date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")     
    query = QueryDocument(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )
    print(query.to_json())
    start_time=datetime.now()
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1}, skip=skp, limit=limt)
    print(f"duration for 998z was {datetime.now()-start_time}")
    start_time_xml=datetime.now()
    xml=bibset.to_xml()
    
    #removing double space from the xml; creates pbs with the job number on ODS export
    xml=xml.replace("  "," ")
    print(f"duration for xml serialization was {datetime.now()-start_time_xml}")
    return Response(xml, mimetype='text/xml')
    

@app.route('/<date>/xml999')
def xml999(date):
    '''
outputs records in MARCXML format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
/YYYYMMDD/xml?skip=n&limit=m
skip=n URL parameter is used to skip n records. Default is 0.
limit=m URL parameter is used to limit number of records returned. Default is 50.
if the date is in wrong format the function returns today's records
it uses DLX bibset.to_xml serialization function to output MARCXML
'''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")     
    query = QueryDocument(
        Condition(
            tag='999',
            subfields={'b': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )
    print(query.to_json())
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1}, skip=skp, limit=limt)
    xml=bibset.to_xml()
    #removing double space from the xml; creates pbs with the job number on ODS export
    xml=xml.replace("  "," ")
    return Response(xml, mimetype='text/xml')


@app.route('/<date>/xmlupdated')
def xmlupdated(date):
    '''
outputs records in MARCXML format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
/YYYYMMDD/xml?skip=n&limit=m
skip=n URL parameter is used to skip n records. Default is 0.
limit=m URL parameter is used to limit number of records returned. Default is 50.
if the date is in wrong format the function returns today's records
it uses DLX bibset.to_xml serialization function to output MARCXML
'''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
        date_from=date
    else:   
        date_year=str_date[0:4]
        date_month=str_date[4:6]
        date_day=str_date[6:8]
    date_from=datetime.fromisoformat(date_year+"-"+date_month+"-"+date_day)
    #date_to=date_from+timedelta(days = 2)
    print(f"date_from is {date_from}")
    #print(f"date_to is {date_to}")
    dict_query= {"$and":[{"updated": {"$gte": date_from, "$lt": date_from+timedelta(days = 1)}},{"029.subfields.value":"JN"}]}  
    #dict_query= {"updated": {"$gte": date_from, "$lt": date_from+timedelta(days = 1)}}
    #print(query.to_json())
    #print(f"son query is {son_query}")
    print(f"dict query is {dict_query}")
    start_time=datetime.now()
    bibset = BibSet.from_query(dict_query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1}, skip=skp, limit=limt)
    xml=bibset.to_xml()
    #removing double space from the xml; creates pbs with the job number on ODS export
    xml=xml.replace("  "," ")
    print(f"duration for updated was {datetime.now()-start_time}")
    return Response(xml, mimetype='text/xml')

@app.route('/<date>/json')
def jsonf(date):
    '''
    outputs records in native central DB schema json format for the date which is provided as a dynamic route inputed in YYYYMMDD or YYYY-MM-DD
    e.g. /YYYY-MM-DD/json
    e.g. /YYYYMMDD/json?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    if the date is in wrong format the function returns today's records
    it uses DLX's bibset.to_json serialization function to output json
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    query = QueryDocument(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )

    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1,'998':1}, skip=skp, limit=limt)

    jsonl=[]
    for bib in bibset.records:
        jsonl.append(bib.to_json())
    return jsonify(jsonl)

@app.route('/ds/<path:path>')
def show_txt(path):
    query = QueryDocument(
        Condition(
            tag='191',
            #subfields={'a': re.compile('^'+path+'$')}
            subfields={'a': path}
        )
    )
    #print(f" the imp query is  -- {query.to_json()}")
    #export_fields={'089':1,'091':1,'191': 1,'239':1,'245':1,'249':1,'260':1,'269':1,'300':1,'500':1,'515':1,'520':1,'596':1,'598':1,'610':1,'611':1,'630:1,''650':1,'651':1,'710':1,'981':1,'989':1,'991':1,'992':1,'993':1,'996':1}
    bibset = BibSet.from_query(query)
    out_list=[('089','b'),('091','a'),('191','a'),('191','b'),('191','c'),('191','9'),('239','a'),('245','a'),('245','b'),('249','a'),('245','a'),('260','a'),('260','b'),('260','a'),('260','c'),('269','a'),('300','a'),('500','a'),('515','a'),('520','a'),('596','a'),('598','a'),('610','a'),('611','a'),('630','a'),('650','a'),('651','a'),('710','a'),('981','a'),('989','a'),('989','b'),('989','c'),('991','a'),('991','b'),('991','d'),('992','a'),('993','a'),('996','a')]
    #print(f"duration for query was {datetime.now()-start_time_query}")
    jsonl=[]
    
    for bib in bibset.records:
        out_dict={}
        #start_time_bib=datetime.now()
        for entry in out_list:
            #start_time_field=datetime.now()
            out_dict[entry[0]+'__'+entry[1]]=bib.get_values(entry[0],entry[1])
            #print(f"for the field {entry[0]+'__'+entry[1]}")
            #print(f"duration for getting values was {datetime.now()-start_time_field}")
        jsonl.append(out_dict)
        print(f"for the bib {bib.get_values('191','a')}")
        #print(f"duration for getting bib values was {datetime.now()-start_time_bib}")
    #print(f"total duration was {datetime.now()-start_time_all}")
    return jsonify(jsonl)


@app.route('/xml/<path:path>')
def show_xml(path):
    query = QueryDocument(
        Condition(
            tag='191',
            #subfields={'a': re.compile('^'+path+'$')}
            subfields={'a': path}
        )
    )
    #print(f" the imp query is  -- {query.to_json()}")
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1})
    xml=bibset.to_xml()
    #removing double space from the xml; creates pbs with the job number on ODS export
    xml=xml.replace("  "," ")
    return Response(xml, mimetype='text/xml')


@app.route('/<date>/symbols')
def symbols(date):
    '''
    outputs records in txt format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
    e.g. /YYYYMMDD/symbols /YYYY-MM-DD/symbols?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    if the date is in wrong format the function returns today's records
    it uses DLX bibset.to_txt serialization function to output MARCXML
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    
        
    query = QueryDocument(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )

    bibset = BibSet.from_query(query, projection={'029':1,'191': 1}, skip=skp, limit=limt)

    str_out=''
    for bib in bibset.records:
        str_out+=bib.to_str()
    return Response(str_out, mimetype='text/plain')



@app.route('/unbis')
def unbis():

    '''
    outputs UNBIS thesaurus subject heading records in MARCXML format /unbis?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    it uses DLX bibset.to_xml serialization function to output fields 035 and 150 in MARCXML
    '''

    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")    
    query = QueryDocument(
        Condition(
            tag='035',
            subfields={'a': re.compile('^T')}

            )

    )
    print(query.to_json())
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    unbis=authset.to_xml()
    return Response(unbis, mimetype='text/xml')



@app.route('/<date>/unbis')
def date_unbis(date):
    '''
    outputs records in native central DB schema json format for the date which is provided as a dynamic route inputed in YYYYMMDD or YYYY-MM-DD
    e.g. /YYYY-MM-DD/json
    e.g. /YYYYMMDD/json?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    if the date is in wrong format the function returns today's records
    it uses DLX's bibset.to_json serialization function to output json
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    #print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    #if len(str_date)!= 8:
        #date = datetime.datetime.now()
        #str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    query = QueryDocument(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
            ),
        Condition(
            tag='035',
            subfields={'a': re.compile('^T')}
            )
        )
        
    #print(query.to_json())
    '''
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    unbis=authset.to_xml()
    return Response(unbis, mimetype='text/xml')
    '''
    dict1={}
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    for auth in authset:
        val_035a=auth.get_values('035','a')
        #print(f"035 values are: {val_035a}")
        val_035a=''.join([str for str in val_035a if str[0]=='T'])
        #dict1[auth.get_value('035','a')]=auth.get_value('150','a')
        dict1[val_035a]=auth.get_value('150','a')
        #dict1['FR']=auth.get_value('993','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)

@app.route('/tcode/<tcode>')
def unbis_tcode(tcode):
    '''
    looks up UNBIS thesaurus T codes and returns matching subject heading records 
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    it uses DLX bibset.to_xml serialization function to output fields 035 and 150 in MARCXML
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    #print(f"skip is {skp} and limit is {limt}")    
    query = QueryDocument(
        Condition(
            tag='035',
            subfields={'a': re.compile(str(tcode).upper())}
            )
    )
    print(query.to_json())
    dict1={}
    authset = AuthSet.from_query(query, projection={'035':1,'150':1,'993':1,'994':1,'995':1, '996':1, '997':1}, skip=skp, limit=limt)
    for auth in authset:
        val_035a=auth.get_values('035','a')
        #print(f"035 values are: {val_035a}")
        val_035a=''.join([str for str in val_035a if str[0]=='T'])
        #dict1[auth.get_value('035','a')]=auth.get_value('150','a')
        dict1[val_035a]={'EN':auth.get_value('150','a'),'FR':auth.get_value('993','a'),'ES':auth.get_value('994','a'),'AR':auth.get_value('995','a'), 'ZH':auth.get_value('996','a'),'RU':auth.get_value('997','a')}
        #dict1['FR']=auth.get_value('993','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)


@app.route('/label/<label>')
def unbis_label(label):
    '''
    looks up UNBIS thesaurus labels and returns matching T codes 
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    it uses DLX authset to output fields 035 and 150
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")    
    query = QueryDocument(
        Condition(
            tag='150',
            subfields={'a': re.compile(str(label).upper())}
            )
    )
    print(query.to_json())
    dict1={}
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    '''
    for auth in authset:
        dict1[auth.get_value('150','a')]=auth.get_value('035','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)
    '''

    for auth in authset:
        val_035a=auth.get_values('035','a')
        #print(f"035 values are: {val_035a}")
        val_035a=''.join([str for str in val_035a if str[0]=='T'])
        #dict1[auth.get_value('035','a')]=auth.get_value('150','a')
        dict1[auth.get_value('150','a')]=val_035a
        #dict1['FR']=auth.get_value('993','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)

@app.route('/<date>/S')
def jsons(date):
    '''
    outputs Security Council bib records in plain simple json format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
    e.g. /YYYY-MM-DD/xml?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    if the date is in wrong format the function returns today's records
    it is used to publish S/ records for iSCAD+ in a plain json
    22 July added fields 049:a and 260:a
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")    
    #start_time_all=datetime.now()
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    #start_time_query=datetime.now()   
    query = QueryDocument(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
        ),
        Condition(
            tag='191',
            subfields={'b': re.compile('^S\/')}
        ) 
    )
    export_fields={'089':1,'091':1,'191': 1,'239':1,'245':1,'249':1,'260':1,'269':1,'300':1,'500':1,'515':1,'520':1,'596':1,'598':1,'610':1,'611':1,'630:1,''650':1,'651':1,'710':1,'981':1,'989':1,'991':1,'992':1,'993':1,'996':1}
    bibset = BibSet.from_query(query, projection=export_fields, skip=skp, limit=limt)
    out_list=[('089','b'),('091','a'),('191','a'),('191','b'),('191','c'),('191','9'),('239','a'),('245','a'),('245','b'),('249','a'),('245','a'),('260','a'),('260','b'),('260','a'),('260','c'),('269','a'),('300','a'),('500','a'),('515','a'),('520','a'),('596','a'),('598','a'),('610','a'),('611','a'),('630','a'),('650','a'),('651','a'),('710','a'),('981','a'),('989','a'),('989','b'),('989','c'),('991','a'),('991','b'),('991','d'),('992','a'),('993','a'),('996','a')]
    #print(f"duration for query was {datetime.now()-start_time_query}")
    jsonl=[]
    
    for bib in bibset.records:
        out_dict={}
        #start_time_bib=datetime.now()
        for entry in out_list:
            #start_time_field=datetime.now()
            out_dict[entry[0]+'__'+entry[1]]=bib.get_values(entry[0],entry[1])
            #print(f"for the field {entry[0]+'__'+entry[1]}")
            #print(f"duration for getting values was {datetime.now()-start_time_field}")
        jsonl.append(out_dict)
        #print(f"for the bib {bib.get_values('191','a')}")
        #print(f"duration for getting bib values was {datetime.now()-start_time_bib}")
    #print(f"total duration was {datetime.now()-start_time_all}")
    return jsonify(jsonl)


@app.route('/votes/<topic>')
def votes(topic):
    '''
    looks up UNBIS thesaurus labels and returns matching T codes ..
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    it uses DLX authset to output fields 035 and 150
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    try:   
        yr_from=request.args.get('year_from')
    except:
        yr_from="1980"
    try:
        yr_to=request.args.get('year_to')
    except:
        yr_to='2020'
    try:
        cntry=request.args.get('Country')
    except:
        cntry='CANADA'
    try:
        vt=request.args.get('Vote')
    except:
        vt='A'

    print(f"skip is {skp} and limit is {limt}")
    print(f"year_from is {yr_from} and year_to is {yr_to}") 
    print(f"Country is {cntry}")
    print(f"Vote is {vt}")

    query = QueryDocument(
        Condition(
            tag='191',
            subfields={'d': re.compile(str(topic))}
            ),
        Condition(
            tag='191',
            subfields={'a': re.compile('^A')}
            )

    )
    print(query.to_json())
    dict_auth_ids={}
    authset = AuthSet.from_query(query, projection={'001':1,'191':1}, skip=skp, limit=limt)
    for auth in authset:
        dict_auth_ids[auth.get_value('191','a')]=auth.get_value('001')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    #return jsonify(dict_auth_ids)
    dict_bibs={}
    str_bibs=''
    votecountry=''
    for key,value in dict_auth_ids.items():
        #sample_id=int(dict_auth_ids['A/74/251'])
        print(f"the id of {key} is {value}")
        query_bib = QueryDocument(
            Condition(
                tag='991',
                subfields={'d':int(value)}
                ),
            Condition(
                tag='989',
                subfields={'a': re.compile(str('Voting Data'))}
                )
        )
        
        print(query_bib.to_json())
        bibset = BibSet.from_query(query_bib, projection={'001':1,'791':1, '967':1}, skip=skp, limit=limt)
        for bib in bibset:
            for field in bib.get_fields('967'):
                votecountry= field.get_value("d")+field.get_value("e")
                #print(f'Country+Vote: {votecountry}')
                if str(votecountry) == str(vt)+str(cntry): # for the entries matching input query parameters using AND logic
                    dict_bibs[bib.get_value('791','a')]=bib.get_value('001')
                    str_bibs=str_bibs+' OR 791:['+bib.get_value('791','a')+']'
    print(str_bibs)   
    return jsonify(dict_bibs)
'''
Executes Sierra API patron object query.
Requests the following patron properties only: names,patronType,varFields (barcode is fieldType "b" in varFields)
Requests "limit" number of records each time, iterating to retrieve all records. I do it in increments of 1000 records. This is adjustable. API permits a maximum of 2000 records per request.
Writes results to rawUsers.txt file so that follow-up analysis is done locally. Not reliant on repeat queries of server.
Use createUsers-regex.py file to analyze/write users.txt.
'''

import requests
import json,re
import unidecode
from base64 import b64encode

def getPatronData(offset,limit):

    apiURL = 'https://ifolio.justice.gc.ca/iii/sierra-api/v6/'
    apiKey = 'YOUR_API_KEY'
    apiSecret = 'YOUR_API_SECRET'

    apiEncodedKey = b64encode(str.encode(apiKey + ':' + apiSecret))
    tokenResponse = requests.post(apiURL + 'token', headers={'Authorization': 'Basic ' + str(apiEncodedKey, 'utf-8'),'content-type':'application/x-www-form-urlencoded'})
    newToken = tokenResponse.json()['access_token']


    response = requests.get(apiURL + 'patrons', params={'offset': offset, 'limit': limit,'deleted':'false','fields':['names','patronType','varFields']}, headers={'authorization':'Bearer '+newToken,'content-type':'application/x-www-form-urlencoded'})
    response.encoding = "utf-8"
    patronData = response.json()
    patrons= json.dumps(patronData, ensure_ascii=False)
    patrons = patrons.replace('{"id"','\n{"id"')
    
    writeFile(patrons,offset,limit)
    
def writeFile(patronData,offset,limit):
    findTotal = re.search(r"total.*?(\d+),", patronData, re.I)
    total = int(findTotal.group(1))

    with open('rawUsers.txt','a',encoding='utf-8') as rawUsers:
        if total == limit:
            offset = offset + limit
            rawUsers.write(patronData)
            getPatronData(offset,limit)
            
        else:
            rawUsers.write(patronData)

getPatronData(0,1000)#I request 1000 records at a time, starting with the first record (offset). You can adjust both of these.

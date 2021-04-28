'''
Evaluates rawUsers.txt file returned from API call. 
Captures only records with barcodes where patronType is NOT 3. 
Cleans up captured names to remove parentheticals and extraneous quotation marks. 
Checks if name has accents; if so, duplicates that user entry with and without accents.
Writes to output file users.txt in form "FName LName:pwd\n"
'''

import re,unicodedata


with open('rawUsers.txt','r',encoding='utf-8') as rawUsers:

    
    for line in rawUsers:
        matchObj = re.search(r'"names"\:\s\["(.*?)"\].."patronType"\:.[^3].*?"fieldTag":."b",."content":."(\d+)"},', line, re.I)
        
        if matchObj:
            barcode = matchObj.group(2)
            name = matchObj.group(1)
            name = name.strip()
            

            #restructure LastName,FirstName to FirstName LastName
            if ',' in name:
                name = name.split(', ')[1]+" "+name.split(', ')[0]
                name = re.sub(r'\(.*?\)', '', name)#delete parentheticals
                name = re.sub(r'"','',name)#delete weird extra quotations in names
                accents = re.search(r'[^\x00-\x7F]',name,re.I)#find non-Ascii characters
                
                #double entry for username:barcode if name has accents
                if accents:
                    normName = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
                    patAuth = name+':'+barcode+'\n'+normName+':'+barcode
                else:
                    patAuth=name+':'+barcode

                with open('users.txt','a',encoding='utf-8') as users:
                    users.write(patAuth+'\n')

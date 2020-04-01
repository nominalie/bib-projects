'''
Pet project for a colleague who volunteered at a German Language School. They have a small in-house library of German books.
Years before, someone had created a simple mySQL db to record book titles with a basic check-out system.
They wanted a modern web OPAC & checkout solution for the students. It had to be easy to administer by a non-tech b/c no resources.
How to transform messy homegrown bibs with only title & author info, plus some pub dates, 
entered in EN and/or DE by hand with many mistakes and character encoding issues to boot?
-----------------------------------------------------------------
The incredibly amazing Deutschenationalbibliothek to the rescue 
https://portal.dnb.de/metadataShop.htm
-----------------------------------------------------------------
Lots of manual overight, of course. Resulting spreadsheet data was cleaned up and bib data uploaded to LibraryThing. 
In LibraryThing, no technical skills are required to modify items if desired.
The German Language School now pays a modest fee for their clean, easy to use, TinyCat web catalogue.
They add new publications, and link book covers etc. via their LibraryThing account, 
primarily relying on bibliographic data available online (ISBN lookup)
'''

import re,csv, urllib.request,traceback
from urllib.parse import urlencode, quote_plus

class DNB:
	
	def __init__(self):
		
		self.bookList = "failed isbns.csv" #local filepath of input file
		self.token = "27d9c1b1657729bcb5a3fb7f9fbe4327" #access token that the DNB provided
		self.queryURL = "https://services.dnb.de/sru/dnb?version=1.1&"#stem of DNB query URL
		self.isbn=""
		self.dnb_year=""
		self.dnb_author=""
		self.dnb_subject=""
		self.out_rows=[]
		self.review=""	

	def readFile(self):
		
		out_rows = self.out_rows

		with open(self.bookList, newline='') as csvfile:#reading input file row by row
			readCSV = csv.reader(csvfile)
		
			for row in readCSV:
				title = (row[0])
				author = (row[1])
				year = (row[2])
				#ISBN = (row[3]) don't use this input - fill from DNB or leave blank
				pubInfo = (row[4])
				tags = (row[5])
				rating = (row[6])
				review = (row[7])
				dateRead = (row[8])
				pageCount = (row[9])
				callNum = (row[10])
				
				print("processing title "+title)#logging line
					
				if title == "'TITLE'":
					out_rows.append([title,"DNB title",author,"DNB author",year,"DNB year","'ISBN'",pubInfo,tags,rating,review,dateRead,pageCount,callNum,'Query URL'])#Write header row to output file
					
				#build query URL using input title and author data as payloads
				else:
					payloads = {'operation':'searchRetrieve','query':'"'+title+'" and "'+author+'"', 'accessToken':self.token}
					payloadsEnc = urlencode(payloads, quote_via=quote_plus)
					query = self.queryURL+payloadsEnc
					try:
						with urllib.request.urlopen(query) as response:
							res = response.read()
							res = res.decode('utf-8')
							res = res.replace('\n','')
							
							#start evaluating DNB response
							
							matchObj = re.search(r"<numberOfRecords>(\d+)</numberOfRecords>", res, re.I)
							recordCount = matchObj.group(1)
							
							if recordCount:
							
								if int(recordCount) < 1:
									print("No records found")
									out_rows.append([title,recordCount,author,"",year,"","",pubInfo,tags,rating,"No German National Library records retrieved.",dateRead,pageCount,callNum,query])
									
								else:
									print("Returned result for "+title+". Record count: "+recordCount+". Parsing records now.")
									self.findRecord(res,year)
									out_rows.append([title,self.dnb_title,author,self.dnb_author,year,self.dnb_year,self.isbn,pubInfo,tags+','+self.dnb_subject,rating,self.review,dateRead,pageCount,callNum,query])
									
							else:
								print("No match for record count regex")
								out_rows.append([title,query,author,"",year,"",ISBN,pubInfo,tags,rating,"No match for record count regex",dateRead,pageCount,callNum,query])

					#error handling
					except:
						errorMsg = traceback.format_exc()
						print("Error: "+errorMsg)
						out_rows.append([title,"Error: "+errorMsg,author,"",year,"","",pubInfo,tags,rating,review,dateRead,pageCount,callNum,query])

						
				print("Moving to next title now.")
			
			self.outrows = out_rows
			print("That's all. We're done evaluating rows.")
			
			self.writeFile()
			
	def findRecord(self,xml,year):
		
		#Evaluates DNB query result to select best possible record match to parse.
		
		recordPattern = r'<recordData>(.*?)</recordData>'
		records = re.compile(recordPattern,re.I)

		for record in records.finditer(xml):
			pattern_1 = r'<recordData>.*?'+year+'.*?<dc:language>ger</dc:language>.*?"tel:ISBN">\d[-|\d]+.*?<dc:format>[^CD]</dc:format>.*?</recordData>'
			re_check1 = re.compile(pattern_1,re.I)
			fullMatch = re_check1.search(record.group(0))
			
			pattern_2 = r'<recordData>.*?<dc:language>ger</dc:language>.*?"tel:ISBN">\d[-|\d]+.*?<dc:format>[^CD]</dc:format>.*?</recordData>'
			re_check2 = re.compile(pattern_2,re.I)
			isbnRec = re_check2.search(record.group(0))
			
			if fullMatch:
				print("Found record with matching year and an ISBN. Parsing now.")
				self.review=("Match found in the German National Library.")
				self.parseRecord(fullMatch.group(0))
				break
				
			elif isbnRec:
				print("Found valid record with an ISBN. Parsing now.")
				self.review=("Found record with ISBN. Different publication year.")
				self.parseRecord(isbnRec.group(0))
				break
				
			else:
				print("Retrieving record: Bibliographic match uncertain.")
				self.review="Retrieved a record: Bibliographic match uncertain."
				self.parseRecord(record.group(0))
					
	def parseRecord(self,xml):
		
		#Use regular expressions to parse record elements	
		
		recordPattern=r'<dc:(.*?)>(.*?)</dc'
		parseRecord = re.compile(recordPattern,re.I)
		re_ISBN = re.compile(r'([\d|-]+X*)',re.I)
		author = ""
		self.isbn = ""
		self.dnb_subject = ""
		self.dnb_year = ""
		self.dnb_title = ""
		self.dnb_author = ""
		
		print("Running parse record function now.")
		for element in parseRecord.finditer(xml):
			if 'title' in element.group(1):
				self.dnb_title = element.group(2)
			if 'creator' in element.group(1):
				author = author+'; '+element.group(2)#appending multiple author fields together
			if 'ISBN' in element.group(1):
				raw_isbn = element.group(2)
				match = re_ISBN.search(raw_isbn)
				if match and not self.isbn:
					self.isbn = match.group(1)
			if 'subject' in element.group(1):
				self.dnb_subject = element.group(2)				
			if 'date' in element.group(1):
				self.dnb_year = element.group(2)
		
		self.dnb_author = author[2:]#strip extraneous semi-colon from author
		
		return self.dnb_title,self.dnb_author,self.isbn,self.dnb_subject,self.dnb_year
	
	def writeFile(self):
		out_rows = self.out_rows
		escape_row = []
		print('Trying to write all rows to file now.')

		with open('failed isbn lookup.csv', 'w', newline='',encoding='utf_8_sig') as output:#data found will write to this file
			writer = csv.writer(output)
						
			for row in out_rows:
				try:
					writer.writerow(row)
				except:
					escape_row.extend((row[0],'',row[2]))
					print("Error writing this record to file: ",row[0])
					writer.writerow(escape_row)
					escape_row = []
goDNB = DNB()
goDNB.readFile()


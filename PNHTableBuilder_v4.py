import sys, os, csv, sys, pdb
import dateutil.parser as parser
from datetime import datetime

script, erlogFiles, matchToFile = sys.argv

############ NPI MATCH SECTION #############
NPIDict = dict()

for root, dirs, files in os.walk(erlogFiles):
	for name in files:
		if name.endswith('.csv'):
			with open(os.path.join(root, name)) as erlog:
				reader = csv.reader(erlog, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
				header2 = next(reader)[1:]
				for row in reader:
					NPIDict[row[0]] =  row[1:]

npiOutputList = []
with open(matchToFile) as matchFile:
	reader = csv.reader(matchFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
	header1 = next(reader)
	inputHeader = header1 + header2

	#matchedNPI = set()
	rows = 0
	#matches = 0
	for row in reader:
		docID = row[0]
		if docID[-4:] != '.txt': #ensure proper matching regardless if direct i2e output with '. txt'
			docID = docID[:-4] + 'txt'
			row[0] = docID #reassign docID to have correctly formatted file extension 
		if docID in NPIDict and NPIDict[docID][1] != '': #if name in dict and NPI# populated
			#matchedNPI.add(NPIDict[docID][0]) #register of matched names
			#matches +=1
			matchvals = row[:] + NPIDict[docID][:]
			npiOutputList.append(matchvals)

		rows +=1

########### TABLE BUILD SECTION ##########
del NPIDict #clear memory, var was only used above

outputFile = matchToFile[:-4] + '_TABLE.csv'

#load Alexion RAM Territory Reference
with open('Alexion_Territory_Reference.csv', 'r') as document:
	territoryRef = dict()
	for line in document:
		line = line.strip().split(',')
		if not line:  # empty line?
			continue
		territoryRef[line[0]] = [line[4], line[5], line[-1]]

patients = dict()

vals=[]

#list of diagnoses for later categorization into PNH or aHUS
pnhdx = ['PNH Dx','Renal Dys w Hemolysis','Pan/Cytopenia+','FC+ PNH Dx','Cerebral Arterial Thrombosis',
'MDS','Portal Vein Thrombosis','Aplastic Anemia','Budd-Chiari','Coombs',
'Superior Sagittal Sinus Thrombosis','FC Ordered','FC-','Renal Thrombosis','Hemoglobinuria']
ahushdx = ['TMA','MFM','MHT','HUS','aHUS','ADAMTS13 >5%']

#list of specialties we want to keep for each indication
indict = {'PNH': ['207ZH0000X','Hematology','207RH0000X','Hematology','207RH0003X',
'Hematology & Oncology','207RC0200X','Critical Care Medicine','207P00000X',
'Emergency Medicine','207R00000X','Internal Medicine','207RG0100X','Gastroenterology',
'208M00000X','Hospitalist','207RN0300X','Nephrology','2084N0400X','Neurology'],

'aHUS': ['207ZH0000X','Hematology','207RH0000X','Hematology','207RH0003X',
'Hematology & Oncology','2080P0207X','Pediatric Hematology-Oncology',
'207RN0300X','Nephrology','2080P0210X','Pediatric Nephrology','','363LX0001X',
'Obstetrics & Gynecology','207ZB0001X',
'Blood Banking & Transfusion Medicine','207RR0500X','Rheumatology','2080P0216X',
'Pediatric Rheumatology']}

tax = {'207ZH0000X':'Hematology','207RH0000X':'Hematology',
'207RH0003X':'Hematology & Oncology','207RC0200X':'Critical Care Medicine','207P00000X':'Emergency Medicine',
'207R00000X':'Internal Medicine','207RG0100X':'Gastroenterology','208M00000X':'Hospitalist',
'207RN0300X':'Nephrology','2084N0400X':'Neurology','207ZH0000X':'Hematology','207RH0000X':'Hematology',
'207RH0003X':'Hematology & Oncology','2080P0207X':'Pediatric Hematology-Oncology','207RN0300X':'Nephrology',
'2080P0210X':'Pediatric Nephrology','363LX0001X':'Obstetrics & Gynecology','207VM0101X':'Maternal & Fetal Medicine ',
'207ZB0001X':'Blood Banking & Transfusion Medicine','207RR0500X':'Rheumatology','2080P0216X':'Pediatric Rheumatology'}

def indicator(dx1): #categorize the diagnosis
	if dx1 in pnhdx:
		return 'PNH'
	elif dx1 in ahushdx:
		return 'aHUS'

writerows = []
#checker to print only rows for relevant specialties
def write_if_spec(ind, special): 
	if dx != 'MFM' and special in indict[ind]:
		writerows.append(vals)
	elif dx == 'MFM' and special == '207VM0101X': #if MFM dx only print for MFM specialist
		writerows.append(vals)


header = ['DocumentID','Indication (not Dx)','Diagnosis Type / Alert','Data Delivery Week',
'PatientID','NPI Number','Provider Name','DOS', 'Clinic Name', 'Address','City','State','Zip','Specialty',
'Diagnosis Group','Previous DX','Area','Region','RAM']

#if i2e's docs and source columns are present in header, toggle on and store index for later removal in each row
if '#Docs' in inputHeader: 
	i2eOutCols = True
	i2eColindex = inputHeader.index('#Docs')

with open(outputFile, 'w') as outTable:

	writer = csv.writer(outTable, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
	writer.writerow(header)

	#collect all rows into list for chronological sorting, and arrange in final columns
	rawlist = []
	for i in npiOutputList: 
		i[2] = parser.parse(i[2]) #parse the date for later sorting of elements
		if i2eOutCols: #if i2e #Docs/Source cols present, delete them from row
			del i[i2eColindex]
			del i[i2eColindex-1]
		#pdb.set_trace()
		zipcode = i[11]
		try: #create the row output structure, including the alexion rep name by looking up the alexion territory zip code
			rawlist.append([i[0],'','','',i[1],i[5],i[4],i[2],i[7],i[8],i[9],i[10],zipcode,i[6],i[3],'']+territoryRef[zipcode])
		except KeyError: #if zip code does not match during alexion rep zip code lookup, just forget about this row and move on
			print("KeyError! Attempting zipcode lookup on this value: " + zipcode)
			continue
	#pdb.set_trace()

	rawlist.sort(key=lambda x: x[7]) #sort the rows in ascending chronological order
	
	for i in rawlist: #now that entries are sorted, return the dates to standard string output format 'mm/dd/yyyy'
		i[7] = i[7].strftime('%m/%d/%Y')
	
	for vals in rawlist: 
		docID = vals[0]
		patID = vals[4]
		date = vals[7]
		provName = vals[6]
		specialty = vals[13]
		dx = vals[14]
		visit = (provName, dx, docID, date)
		vals[1] = indicator(dx) #Disease profile chooser assigned to each row regardless of condition

		if patID in patients:
			visits = patients[patID][0] #list of previous visit tuples
			prevDx = patients[patID][1] #ordered cumulative list of previously encountered Dx

			if dx not in prevDx: #to avoid duplicates in ordered list
				vals[2] = 'New Diagnosis'
				vals[15] = ', '.join(prevDx)
				prevDx.insert(0,dx)  #add this dx to patient's dx history at index 0 regardless of print or not
				write_if_spec(vals[1], specialty)

			elif visit[:-2] not in [visits[i][:-2] for i in range(0,len(visits))]: #listify previous visits and compare to this one
				vals[2] = 'Existing Dx by other MD'
				vals[15] = ', '.join(prevDx)
				write_if_spec(vals[1], specialty)	
			
			visits.insert(0,visit)	
			
		else: 
			patients[patID] = [[visit], [dx]] #[visits, prevDx]
			vals[2] = 'New Diagnosis'
			write_if_spec(vals[1], specialty)
	#pdb.set_trace()
	writerows.reverse() #print the table in descending (reverse) chronological order newest at top (list was previously sorted above)
	for x in writerows:
		#pdb.set_trace()
		try:
			x[-6] = tax[x[-6]] #convert NPI to long name before printing
		except KeyError:
			print("ERROR SPECIALTY TAX KEPT IN PLACE \n"+x)
			continue
		writer.writerow(x)
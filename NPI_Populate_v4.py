import os, csv, pdb
from sys import argv

script, inputDirectory, outputDirectory, npiDataFile = argv

#INSTRUCTIONS: execute script from NPI directory that contains the following files:
#REQUIRED FILES: 
#FOLDERSTATEREF.TXT references what state a particular text file belongs to via its parent folder's metadata
#FOLDERREF.CSV complete list of every raw text file and its corresponding folder
#ADJACENT_STATES.TXT a reference list of every US State and its corresponding adjacent states
#PREFERREDSPECIALTIES.TXT a list of the preferred NPI specialties in cases of duplicate doctors in a given state
fullDict = dict()#collect all NPI doctor names from data dissemination file

def docInfo(name, fileName): #return string of dr. info based on file location if there are multiple drs with same name
	if len(fullDict[name]) > 1: #more than 1 individual for a doc name?
		try: #if file not in folder ref means not in index assign XX state
			theFolder = folderRef[fileName] 
			theState = folderStateRef[theFolder]
		except KeyError:
			theState = 'XX' 

		allDrStates = [item.split(',')[6] for item in fullDict[name]] #list just the states of all the matching doctor names

		if theState in allDrStates: #if there's a direct match between metadata state and dr state
			desiredStateIndexes = [i for i, j in enumerate(allDrStates) if j == theState] #list the indexes of npi dr's located in the state
			if len(desiredStateIndexes) == 1:
				return fullDict[name][desiredStateIndexes[0]]
			else:
				for i in desiredStateIndexes: #check the specialties of dr's in if multiple docs in desired state
					if fullDict[name][i].split(',')[1] in PreferredSpecialties:
						return fullDict[name][i]
				return fullDict[name][desiredStateIndexes[0]]

		elif len([i for i in adjStates[theState] if i in allDrStates]) > 0: #if any potential dr.s are in any adjacent states
			selectedAdjState = [i for i in adjStates[theState] if i in allDrStates][0]
			desiredStateIndexes = [i for i, j in enumerate(allDrStates) if j == selectedAdjState] #list the indexes dr's in potential adj state
			if len(desiredStateIndexes) == 1:
				return fullDict[name][desiredStateIndexes[0]]
			else:
				for i in desiredStateIndexes: #check the specialties if multiple docs in state
					if fullDict[name][i].split(',')[1] in PreferredSpecialties:
						return fullDict[name][i]
				return fullDict[name][desiredStateIndexes[0]]
		
		else: #if no adjacent state hits, just give up and return the first index
			return min(fullDict[name])
	else: #if only 1 person with this name, return the value
		return min(fullDict[name])

with open('folderStateRef.txt', 'r') as document:
	folderStateRef = dict()
	for line in document:
		line = line.strip().split(',')
		if not line:  # empty line?
			continue
		folderStateRef[line[0]] = line[1]

with open('PreferredSpecialties.txt', 'r') as document:
	PreferredSpecialties = []
	for line in document:
		PreferredSpecialties.append(line.strip())

with open('folderRef.csv', 'r') as document:
	folderRef = dict()
	for line in document:
		line = line.strip().split(',')
		#pdb.set_trace()
		if not line:  # empty line?
			continue
		folderRef[line[1]] = line[0]

with open('Adjacent_States.txt', 'r') as document:
	adjStates = dict()
	for line in document:
		line = line.strip().split()
		if not line:  # empty line?
			continue
		adjStates[line[0]] = line[1:]
	adjStates['XX']=[''] #to error handle files with no folderRef
	adjStates['#N/A']=[''] #to error handle folders outside USA

with open(npiDataFile, 'r') as npiCSVFile: #collect all NPI doctor names from npi compact file
	reader = csv.reader(npiCSVFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
	next(reader)
	for row in reader:
		name = row[1] + ' ' + row[3]
		#info = row[0] + ',' + row[4] + ',' + row[5] + ',' + row[6]+ ',' + row[7] + ',' + row[8]+ ',' + row[9][:5]+ ',' + row[10]
		info = row[0] + ',' + ','.join(row[4:]) #dr info is npi and rest of info in the row of npi compact file
		key = name
		if key != ' ':
			if key in fullDict:
				fullDict[key].add(info)
			else:	
				fullDict[key] = {info}
	for key in fullDict:
		fullDict[key] = list(fullDict[key]) #turn each element into ordered list for later use in docInfo method

print('Populated dictionary with ' + str(len(fullDict)) + ' names')

#for filename in os.listdir(inputDirectory):
for root, dirs, files in os.walk(inputDirectory):
	for filename in files:
		if(filename[-3:] == "csv"):
			#fullPath = os.path.join(inputDirectory, filename)
			fullPath = os.path.join(root, filename)
			#outputFilePath = os.path.join(outputDirectory, os.path.basename(filename) + "_populated" + ".csv")
			outputFilePath = os.path.join(outputDirectory, os.path.relpath(fullPath).split('/')[1], filename + "_populated" + ".csv")
			#pdb.set_trace()
			print('Populating file ' + outputFilePath)

			with open(fullPath, 'r') as csvInputFile:
				reader = csv.reader(csvInputFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
				next(reader)
				os.makedirs(os.path.dirname(outputFilePath), exist_ok=True)
				with open(outputFilePath, 'w') as csvOutputFile:
					writer = csv.writer(csvOutputFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
					writer.writerow(['File Name', 'Provider Name', 'NPI Number', 'Specialty', 'Facility Name', 'Address', 'City', 'State', 'Zip', 'Tel'])
					for row in reader:
						name = row[1].upper() + ' ' + row[3].upper() 
						fileName = row[0]

						if name in fullDict:	
							drInfo = docInfo(name, fileName)
							vals = drInfo.split(",")
							writer.writerow([fileName, name.title(), vals[0], vals[1],vals[2], vals[3]+ ' ' + vals[4], vals[5],vals[6],vals[7],vals[8]])
						else:
							writer.writerow([fileName, name.title(), '','','','','','','',''])


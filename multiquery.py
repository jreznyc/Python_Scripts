import os, csv, sys, pdb
import dateutil.parser as parser
import pandas as pd
import numpy as np
from datetime import datetime

script, sourceFile  = sys.argv
omniFile = "/Users/jp/Dropbox/Work/RHD_201903_OMNI.csv"
erlogFiles = "/Users/jp/Dropbox/Work/NPI Data RP/Populated CSVs"
exclpatids=['68205698725117190','682056987251171963','25911492072461460','259114920724614659','14627474991652080','12421324022250140','373917115923155128','124213240222501410','21621121271911608','37391711592315510','21621121271911600','80168187119251195','80168187119251190','10207542372172260']
start = datetime.now()

#Load Csvs into dataframes
query = pd.read_csv(sourceFile, dtype={'PatientID': object,'ProviderID': object})
if 'DocumentID' in query.columns: #fix docid suffix for NPI match later
	query.DocumentID = query.DocumentID.str.replace('. txt','.txt') 
omni = pd.read_csv(omniFile, dtype={'PatientID': object,'ProviderID': object})

#count patients by query term and create new summary DF
ReWRDoutput=query.groupby('Query').PatientID.nunique().to_frame()
ReWRDoutput['Records']=query.groupby('Query')['#Docs'].sum() #by summing #Docs at row[-1]
ReWRDoutput['Providers'] = query.groupby('Query').ProviderID.nunique().values

#COUNT OMNI:
ReWRDoutput['Omni Records'] = 0
ReWRDoutput['Omni Providers'] = 0
for x in query.Query.unique(): #for unique disease values in i2e results
	patids = [x for x in query.loc[query['Query']==x].PatientID if x not in exclpatids] #get list of patient IDs
	#select '#Docs' from omni where patientID in list of each disease's patient IDs
	ReWRDoutput["Omni Records"][x] = omni.loc[omni['PatientID'].isin(patids)]["#Docs"].sum()
	ReWRDoutput["Omni Providers"][x] = omni.loc[omni['PatientID'].isin(patids)]["ProviderID"].nunique()

ReWRDoutput=ReWRDoutput.rename(index=str, columns={"PatientID": "Patients"})
print('ReWRD')
ReWRDoutput.sort_values('Patients',ascending=False).to_csv(sys.stdout)
print("*Omni represents longitudinal records for a patient that may not mention the disease or medication directly.")

if 'DocumentID' in query.columns: #returns an npi matched dataframe from the query results
	list_ = []
	for root, dirs, files in os.walk(erlogFiles):
		for name in files:
			if name.endswith('.csv'):
				df = pd.read_csv(os.path.join(root, name), dtype=object, index_col=None, header=0)#.dropna(subset=['NPI Number'])
				list_.append(df)
	npiframe = pd.concat(list_, axis = 0, ignore_index = True).dropna(subset=['NPI Number'])
	
	matchedNPI = pd.merge(query, npiframe, left_on = 'DocumentID', right_on = 'File Name')#.dropna(subset=['NPI Number'])
	matchedNPI.drop(['File Name', 'Source', '#Docs','ProviderID','Tel'], axis=1, inplace=True)
	sumvals = [matchedNPI['PatientID'].nunique(), matchedNPI['DocumentID'].nunique(), matchedNPI['Provider Name'].nunique()]
	
	#count patients by query term and create new summary DF
	CLADoutput = matchedNPI.groupby('Query').PatientID.nunique().to_frame()
	CLADoutput['Records'] = matchedNPI.groupby('Query').DocumentID.nunique().values #using DocumentIDs
	CLADoutput['Providers'] = matchedNPI.groupby('Query')['Provider Name'].nunique().values
	CLADoutput=CLADoutput.rename(index=str, columns={"PatientID": "Patients"})
	CLADoutput=CLADoutput.sort_values('Patients',ascending=False)
	CLADoutput=CLADoutput.append(pd.Series(sumvals, index=['Patients','Records','Providers'],name='Net Results'))

	
	print('\nCLAD')
	CLADoutput.to_csv(sys.stdout)
	outputfile = sourceFile+'_NPI_Matched.csv'
	matchedNPI.to_csv(outputfile)

end = datetime.now()
print(end-start)
#pdb.set_trace()

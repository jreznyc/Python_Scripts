import os, re, sys, pdb, shutil
from datetime import datetime
import xml.etree.ElementTree as ET
from snapy import MinHash, LSH #used for the dupe detection


#Loads document data either XML or TXT. Should use pre-HIPS documents.
def load_document_data(folder):
    my_documents = []
    labels = []
    allpaths = dict()

    for root, dirs, files in os.walk(folder):
        for fname in files:
            if fname.endswith('.xml'):
                fullPath = os.path.join(root, fname)
                tree = ET.parse(fullPath)
                xmlroot = tree.getroot()
                #pdb.set_trace()
                try:
                    bodyString = xmlroot[0].find('Body').text
                except:
                    bodyString = xmlroot[1].find('Body').text
                my_documents.append(bodyString)
                labels.append(fname)
                allpaths[fname]=fullPath

            elif fname.endswith('.txt'):
                fullPath = os.path.join(root, fname)
                with open(fullPath) as file:
                    docText = file.read()
                    my_documents.append(docText)
                    labels.append(fname)
                    allpaths[fname]=fullPath

    
    print('Loaded %d documents' % (len(my_documents)))
    return my_documents, labels, allpaths


def remove_headers_and_footers(text):
    print(f"Removing header for file: {labels[index]}")
    header_size = 0
    #pdb.set_trace()
    for line in text.split("\n"):
        foundMatch = re.match("Patient ID\.\..*|\w+ Name:.*|Dictation ID:|Patient:.*|\w+ Date:.*|\w+ Number:.*|Medical Record Number.*|\w+ Entity:.*|Speaker:.*|Speaker ID:.*|CC List:.*|PCP:.*|Referring Physician:.*|DATE OF BIRTH:.*|Work Type:.*|\*\*NAME$|D\.O\.", line)
        if(foundMatch):
            header_size += 1
        elif line.strip() == "": # blank line
            header_size += 1
            continue
        else:
            break

    if(header_size > 0):
        text = text.split("\n",header_size)[header_size];

    footer_size = 0

    for line in reversed(text.split("\n")):
        foundMatch = re.match("Status:.*|\[ Status:.*|\*\*NAME$", line)
        if(foundMatch):
            footer_size += 1
        elif line.strip() == "": # blank line
            footer_size += 1
            continue
        else:
            break

    if(footer_size > 0):
        text = (text.rsplit("\n",footer_size)[0]);

    return text

def remove_family_history_heading_section(text):
    text = re.sub("FAMILY(\w*) HISTORY:.*\n\n", "", text)
    return text

def get_lsh_model(documents, seed_int):
    seed = seed_int
    # Create MinHash object.
    minhash = MinHash(my_documents, n_gram=9, permutations=100, hash_bits=64, seed=seed)
    # Create LSH model.
    lsh = LSH(minhash, labels, no_of_bands=50)
    return lsh

def query_lsh_dupes(lsh_model, label):
    return lsh_model.query(label, min_jaccard=0.5)


def get_list_of_dupes(lsh, labels):
    all_dupes = []
    files_with_dupes = []

    for label in labels:
        if label in all_dupes: #don't double count dupe pairings
            continue
        
        this_files_dupes = query_lsh_dupes(lsh,label)
        
        if len(this_files_dupes)>0:
            files_with_dupes.append(label)
            all_dupes+=this_files_dupes
            print('%s : %s' % (label , this_files_dupes))

    all_dupes =  set(all_dupes)
    print("Total Dupes Found:  %i" % (len(all_dupes)))
    return all_dupes



if __name__ == "__main__":
    script, document_folder  = sys.argv

    my_documents, labels, allpaths = load_document_data(document_folder)

    for index,doc in enumerate(my_documents):
        text = doc
        text = remove_headers_and_footers(text)
        text = remove_family_history_heading_section(text)
        my_documents[index]=text

    start = datetime.now()

    lsh = get_lsh_model(my_documents, 3)

    all_dupes = get_list_of_dupes(lsh,labels)
    #pdb.set_trace()
    all_dupes

    end = datetime.now()

    for x in all_dupes: #backup and delete each file (x) where found
        backup = './BACKUP/'+ os.path.relpath(x)
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        shutil.copyfile(allpaths[x], backup)
        os.remove(allpaths[x])

    print(end-start)
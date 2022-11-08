import agenda
import json
import numpy as np
import spacy
import regex
nlp = spacy.load("en_core_web_lg")

question = 'Hi can u print my 12000 document entitled doc.docx please?'
input = nlp(question)

answer = ''

#inserer modèle et intent récupère model.pred


intent = 'printing_request'

data_file = open('intents.json').read()
intents = json.loads(data_file)

for x in intents['intents']:
    if (x['tag'] == intent):
        answer_list = x['responses']
        answer = answer_list[np.random.randint(len(answer_list))]
        if (x['tag'] == 'printing_request'):
            name_list = regex.findall('[^ ]+\.[^ ]+',question)
            num_list = []
            for token in input:
                if token.pos_ == 'NUM':
                    num_list.append(token.text)
            if (len(name_list) == 1):
                doc_name = name_list[0]
            if (len(num_list) == 1):
                doc_pages = num_list[0]
            
print(answer)
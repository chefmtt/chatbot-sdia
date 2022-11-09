import json

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import spacy
from spacy.tokens import DocBin
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from joblib import dump
import sklearn

nlp = spacy.load("en_core_web_lg")


# Helper functions

def lemmatize_text(text, preprocessed=True):
    return process_text(text, "lemmatize", preprocessed)


def tokenize_text(text, preprocessed=True):
    return process_text(text, "tokenize", preprocessed)


def process_text(text, mode: str, preprocessed=True):
    if not preprocessed:
        text = nlp(text)
    if mode == "tokenize":
        processed_text = [token.text for token in
                          text]  # token and embed must have the same processing + SpaCy provides embeddings for punctuation
    elif mode == "embed":
        processed_text = [token.vector for token in text]  # token and embed must have the same processing
    elif mode == "lemmatize":
        processed_text = [token.lemma_ for token in text
                          if not token.is_punct and not token.is_space and not token.like_url and not token.like_email]
    else:
        raise ValueError("Mode not supported")
    return processed_text


def save_preprocessed(raw_text, save_path):
    doc_bin = DocBin(attrs=["LEMMA", "ENT_IOB", "ENT_TYPE"], store_user_data=True)
    for doc in nlp.pipe(raw_text):
        doc_bin.add(doc)
    # save DocBin to a file on disc
    doc_bin.to_disk(save_path)


if __name__ == '__main__':

    # Load and preprocess data using SpaCy

    data_file = open('intents.json').read()
    intents = json.loads(data_file)

    data = []
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            data.append([pattern, intent['tag']])
    df_json = pd.DataFrame(data, columns=['text', 'intent'])
    df_csv = pd.read_csv("sentences/full.csv")
    df = pd.concat([df_json, df_csv], axis=0)

    file_name_spacy = 'preprocessed_dataset_chatbot.spacy'
    save_preprocessed(raw_text=df["text"], save_path=file_name_spacy)

    # Load DocBin at later time or on different system from disc or bytes object
    doc_bin = DocBin().from_disk(file_name_spacy)
    df["doc"] = list(doc_bin.get_docs(nlp.vocab))

    X_train = df["doc"].reset_index(drop=True)
    y_train = df["intent"].reset_index(drop=True)

    X_train_embedded = df["doc"].apply(process_text, args=("embed", True,))
    X_train_embedded_avg = X_train_embedded.apply(np.mean, axis=0).apply(pd.Series)

    clf = RandomForestClassifier()

    clf.fit(X_train_embedded_avg, y=y_train)

    dump(clf, filename="clf_chatbot")

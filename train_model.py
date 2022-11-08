import json

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import spacy
from spacy.tokens import DocBin
from keras.models import Sequential
from keras.layers import LSTM
from keras.layers import Dense, Input, Masking
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
from joblib import dump

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
    df = pd.DataFrame(data, columns=['text', 'intent'])

    file_name_spacy = 'preprocessed_dataset_chatbot.spacy'
    save_preprocessed(raw_text=df["text"], save_path=file_name_spacy)

    # Load DocBin at later time or on different system from disc or bytes object
    doc_bin = DocBin().from_disk(file_name_spacy)
    df["doc"] = list(doc_bin.get_docs(nlp.vocab))

    train, test = train_test_split(df, test_size=0.2)

    X_train = train["doc"].reset_index(drop=True)
    y_train = train["intent"].reset_index(drop=True)

    X_test = test["doc"].reset_index(drop=True)
    y_test = test["intent"].reset_index(drop=True)

    X_train_embedded = train["doc"].apply(process_text, args=("embed", True,))
    X_train_embedded_avg = X_train_embedded.apply(np.mean, axis=0).apply(pd.Series)

    X_test_embedded = test["doc"].apply(process_text, args=("embed", True,))
    X_test_embedded_avg = X_test_embedded.apply(np.mean, axis=0).apply(pd.Series)

    import tensorflow as tf

    max_words = 30  # Max number of words in a sentence

    raw_inputs = X_train_embedded
    padded_inputs = tf.keras.preprocessing.sequence.pad_sequences(
        X_train_embedded,
        maxlen=max_words,
        padding="pre",
        truncating="pre",
        dtype="float32",
    )

    le = LabelEncoder()
    y_encoded = le.fit_transform(y_train)
    number_classes = len(y_train.unique())

    model = Sequential()
    # model.add(Embedding(vocab_size,300,input_length=max_words))
    model.add(Masking(mask_value=0, input_shape=(None, 300)))
    model.add(LSTM(units=128,
                   return_sequences=False,
                   input_shape=(None, 300)
                   ))
    model.add(Dense(number_classes, activation='softmax'))

    print(model.summary())
    model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    history = model.fit(tf.convert_to_tensor(padded_inputs), y_encoded, epochs=10)

    test = process_text("tell me your name", mode="embed", preprocessed=False)
    predict = model.predict(np.asarray([test]))
    predicted_class = np.argmax(predict)
    predicted_class = le.inverse_transform([predicted_class])
    print(predicted_class)

    model.save("chatbot_clf")
    dump(le, filename="classes_encoder")

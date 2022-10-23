import json
import cloudpickle as pickle
import pandas as pd
from sklearn import tree, svm, naive_bayes
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from pprint import pprint
from time import time
import spacy
from spacy.tokens import DocBin
nlp = spacy.load("en_core_web_lg")
data_file = open('intents.json').read()
intents = json.loads(data_file)


data = []
for intent in intents['intents']:
    for pattern in intent['patterns']:
        data.append([pattern, intent['tag']])

df = pd.DataFrame(data, columns=['text','intent'])

def lemmatize_text(text, preprocessed=True):
    if not preprocessed:
        text = nlp(text)
    lemmatized_texts = [token.lemma_ for token in text
                               if not token.is_punct and not token.is_space and not token.like_url and not token.like_email]
    return lemmatized_texts

#Load DocBin at later time or on different system from disc or bytes object
file_name_spacy = 'preprocessed_documents.spacy'
doc_bin = DocBin().from_disk(file_name_spacy)
docs = list(doc_bin.get_docs(nlp.vocab))

def embed_words(text, preprocessed=False):
    if not preprocessed:
        text = nlp(text)
    return [token.vector for token in text]

df["doc"] = docs
X_train = df["doc"]
y_train = df["intent"]

vectorizer = TfidfVectorizer(ngram_range=(1, 1), lowercase=False, tokenizer=lemmatize_text, max_features=3000)
X_train_tfidf = vectorizer.fit_transform(X_train)

X_train_embedded = df["doc"].apply(embed_words, args=(True,))

X_train_embedded_avg = X_train_embedded.apply(sum)
# classifiers to use

from collections import defaultdict

gs_dict = defaultdict(dict)

dectree = tree.DecisionTreeClassifier()
svm_clf = svm.SVC()
multi_nb = naive_bayes.MultinomialNB()

gs_dict['dectree']['pipeline'] = Pipeline([
    ('dectree', dectree)])

gs_dict['multi_nb']['pipeline'] = Pipeline([
    ('multi_nb', multi_nb)])

gs_dict['dectree']['params'] = {
    "dectree__max_depth": [4, 10],
}

gs_dict['multi_nb']['params'] = {
    "multi_nb__alpha": [0.00001, 0.0001, 0.001, 0.1, 1, 10, 100,1000],
}
gs_dict['svm_clf']['pipeline'] = Pipeline([
    ('svm_clf', svm)])

gs_dict['svm_clf']['params'] = {
    "svm_clf__kernel": ["linear", "rbf"],
}

def perform_grid_search(pipeline, parameters):
    gs_clf = GridSearchCV(pipeline, parameters, n_jobs=2, verbose=1, cv=5, scoring="accuracy")

    print("\nPerforming grid search...")
    print("pipeline:", [name for name, _ in pipeline.steps])
    print("parameters:")
    pprint(parameters)

    t0 = time()

    gs_clf.fit(X_train_embedded_avg, y_train)

    print("done in %0.3fs" % (time() - t0))
    print()

    print("Best score: %0.3f" % gs_clf.best_score_)
    print("Best parameters set:")
    best_parameters = gs_clf.best_estimator_.get_params()
    for param_name in sorted(parameters.keys()):
        print("\t%s: %r" % (param_name, best_parameters[param_name]))
    return gs_clf

def best_estimator_per_clf(gs_dict: defaultdict):
    for clf in dict(gs_dict):
        gs_dict[clf]['gs'] = perform_grid_search(
            gs_dict[clf]['pipeline'],
            gs_dict[clf]['params']
        )
    return gs_dict


final = best_estimator_per_clf(gs_dict)

df_result = pd.DataFrame(gs_dict['multi_nb']['gs'].cv_results_)

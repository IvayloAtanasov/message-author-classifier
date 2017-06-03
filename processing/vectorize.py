#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Fit and transform messages data using a tf-idf vectorizer
"""
import sys
import pickle
import pprint
import numpy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.tree import DecisionTreeClassifier
from sklearn import cross_validation
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import string
import json


# ref: http://stackoverflow.com/a/10883893
# usage: MyPrettyPrinter().pprint(channels)
class MyPrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, unicode):
            return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


def main():
    clf, vectorizer = vectorize_and_get_classifier()

    # test message
    message = "като цяло"
    stemmed_message = stem_message(message.decode('unicode-escape'))
    feature = vectorizer.transform([stemmed_message])
    author_index = clf.predict(feature)[0]

    # TODO: taken from json-topkl.py
    with open('../output/users.json', 'r') as users_json:
        users = json.load(users_json)

    print('"' + message + '"' + ' най-вероятно е съобщение на ' + str(users[author_index]['real_name']) + ' (' + str(author_index) + ')')


def stem_message(message):
    """ TODO: reuse from json-to-pkl.py? """
    stemmer = SnowballStemmer("russian")
    # remove punctuation
    # ref 1: https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    # ref 2: https://stackoverflow.com/questions/23175809/typeerror-translate-takes-one-argument-2-given-python
    message = message.translate({ord(c): None for c in string.punctuation})
    # stem each word from message and compose again
    stemmed_words = [stemmer.stem(word) for word in message.split()]
    return string.join(stemmed_words)


def vectorize_and_get_classifier(trainset_limit=0):
    authors = pickle.load(open('authors.pkl', 'r'))
    messages = pickle.load(open('messages.pkl', 'r'))

    # print messages
    # MyPrettyPrinter().pprint(messages)

    # split into testing and training sets
    features_train, features_test, labels_train, labels_test = cross_validation.train_test_split(messages, authors, test_size=0.1, random_state=42)

    bulgarian_stopwords = stopwords.words('bulgarian')
    # build tf-idf vectorizer
    #   ignore bulgarian stopwords
    #   ignore words with document frequency > 0.5
    # TODO: almost no words that are frequent through our dataset. max_df=0.01 barely has effect :) is it a problem?
    vectorizer = TfidfVectorizer(stop_words=bulgarian_stopwords, max_df=0.5)
    # build tf-idf matrix
    # ref: https://en.wikipedia.org/wiki/Tf%E2%80%93idf
    features_train = vectorizer.fit_transform(features_train)
    features_test = vectorizer.transform(features_test).toarray()

    # limit data volume, useful for development
    if trainset_limit is not 0:
        features_train = features_train[:trainset_limit].toarray()
        labels_train = labels_train[:trainset_limit]

    # print tf-idf matrix length
    print('tf-idf matrix length: ' + str(len(vectorizer.get_feature_names())))

    # use DT classifier
    clf = DecisionTreeClassifier()
    clf.fit(features_train, labels_train)
    # print classifier accuracy
    print('dt accuracy: ' + str(clf.score(features_test, labels_test)))
    # find most important word index in list
    most_important_feature_index = numpy.argmax(clf.feature_importances_)
    # print most important feature and it's importance coefficient
    feature = vectorizer.get_feature_names()[most_important_feature_index]
    feature_importance = clf.feature_importances_[most_important_feature_index]
    print('most important feature: ' + feature.encode('utf-8') + ' with importance index of ' + str(feature_importance))

    return clf, vectorizer


if __name__ == '__main__':
    sys.exit(main())

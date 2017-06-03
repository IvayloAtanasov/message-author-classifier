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
import json

from processing.stem import stem_message


def main():
    # TODO: cache classifier and vectorizer into pkl files.
    # ref: http://scikit-learn.org/stable/modules/model_persistence.html
    clf, vectorizer = vectorize_and_get_classifier()

    # TODO: taken from json-to-pkl.py
    with open('../slack-data/users.json', 'r') as users_json:
        users = json.load(users_json)

    print('Listening for messages...')

    # listen for messages in stdin
    for message in sys.stdin:
        # remove newline symbols, if any
        message = message.strip('\r\n')
        stemmed_message = stem_message(message)
        feature = vectorizer.transform([stemmed_message])
        author_index = clf.predict(feature)[0]

        print('"' + str(message) + '"' + ' най-вероятно е съобщение на ' + str(users[author_index]['real_name']) + ' (' + str(author_index) + ')')
        # slack-data response to stdout
        sys.stdout.write(str(users[author_index]['real_name']) + '\n')

def vectorize_and_get_classifier(trainset_limit=0):
    authors = pickle.load(open('authors.pkl', 'rb'))
    messages = pickle.load(open('messages.pkl', 'rb'))

    # print messages
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(messages)

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
    # learn vocabulary on training set, and return training matrix
    features_train = vectorizer.fit_transform(features_train)
    # return testing matrix with the vocabulary learned from the training set
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
    print('most important feature: ' + feature + ' with importance index of ' + str(feature_importance))

    return clf, vectorizer


if __name__ == '__main__':
    sys.exit(main())

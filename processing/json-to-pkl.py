#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Transforms Slack API json data into pkl file with single messages list for each user
"""
import sys
import io
import json
import pickle
import pprint
from nltk.stem.snowball import SnowballStemmer
import string


# ref: http://stackoverflow.com/a/10883893
# usage: MyPrettyPrinter().pprint(channels)
class MyPrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, unicode):
            return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


def main():
    # load files
    with open('../output/users.json', 'r') as users_json:
        users = json.load(users_json)

    with open('../output/channels.json', 'r') as channels_json:
        channels = json.load(channels_json)

    # testing user_index_by_id
    #print(user_index_by_id('U039UP4E6', users)) # 31
    #print(user_index_by_id('UE39AP456', users)) # False
    #print(user_index_by_id('U02JCLRNM', users)) # 14
    #print(user_index_by_id('U035G43MH', users)) # 3

    user_messages = flatten_messages(channels)
    # stem words before outputting to pkl
    user_messages = stem_messages(user_messages)

    messages_output = []
    authors_output = []
    for user_id, messages in user_messages.iteritems():
        for message in messages:
            authors_output.append(user_index_by_id(user_id, users))
            messages_output.append(message)

    pickle.dump(messages_output, open('messages.pkl', 'w'))
    pickle.dump(authors_output, open('authors.pkl', 'w'))


def user_index_by_id(slack_id, users):
    """ Returns index of user in users list, based on it's Slack id """

    found_users = [user for user in users if user['id'] == slack_id]
    if len(found_users) == 0:
        # not found
        return False
    elif len(found_users) == 1:
        return users.index(found_users[0])
    else:
        # found more than one, this should never happen
        return False


def flatten_messages(channels):
    """
        transforms:
        [{
            channel: String, // channelId
            history: [{
                user: String, // userId
                messages: [String]
            }]
        }]
        into dict (sorted by user):
        {
            userId: messages
        }
    """
    messages = {}
    for channel in channels:
        for history in channel['history']:
            user_id = history['user']
            if user_id in messages:
                # merge
                messages[user_id] += history['messages']
            else:
                # create for that user
                messages[user_id] = history['messages']

    return messages


def stem_messages(user_messages):
    user_stemmed_messages = {}
    # TODO: used a russian stemmer, english words remain unprocessed
    stemmer = SnowballStemmer("russian")
    for user_id, messages in user_messages.iteritems():
        # keep only strings with content as messages
        messages = [message for message in messages if isinstance(message, basestring) and len(message) > 1]
        for index, message in enumerate(messages):
            # remove punctuation
            # ref 1: https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
            # ref 2: https://stackoverflow.com/questions/23175809/typeerror-translate-takes-one-argument-2-given-python
            message = message.translate({ord(c): None for c in string.punctuation})
            # stem each word from message and compose again
            stemmed_words = [stemmer.stem(word) for word in message.split()]
            messages[index] = string.join(stemmed_words)

        user_stemmed_messages[user_id] = messages
        print('User', user_id, 'has', len(messages))

    # TODO: debug
    #MyPrettyPrinter().pprint(user_stemmed_messages)
    return user_stemmed_messages


if __name__ == '__main__':
    sys.exit(main())

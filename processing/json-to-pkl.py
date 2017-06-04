"""
    Transforms Slack API json data into pkl file with single messages list for each user
"""
import sys
import json
import pickle
import pprint

from stem import stem_message

MIN_MESSAGES_REQUIRED = 500

def main():
    # load files
    with open('../slack-data/users.json', 'r', encoding='utf-8') as users_json:
        users = json.load(users_json)

    with open('../slack-data/channels.json', 'r', encoding='utf-8') as channels_json:
        channels = json.load(channels_json)

    # testing user_index_by_id
    #print(user_index_by_id('U039UP4E6', users)) # 31
    #print(user_index_by_id('UE39AP456', users)) # False
    #print(user_index_by_id('U02JCLRNM', users)) # 14
    #print(user_index_by_id('U035G43MH', users)) # 3

    users_messages = flatten_messages(channels)
    # balance dataset by discarding users without enough messages
    # and discarding data for users with too many
    # ref: https://www.quora.com/In-classification-how-do-you-handle-an-unbalanced-training-set
    users_messages = balance_messages(users_messages)
    # stem words before outputting to pkl
    users_messages = stem_messages(users_messages)

    messages_output = []
    authors_output = []
    for user_id, messages in users_messages.items():
        for message in messages:
            authors_output.append(user_index_by_id(user_id, users))
            messages_output.append(message)

    pickle.dump(messages_output, open('messages.pkl', 'wb'))
    pickle.dump(authors_output, open('authors.pkl', 'wb'))


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


def balance_messages(users_messages):
    users_before_balancing = len(users_messages.keys())
    for user_id in list(users_messages.keys()):
        if len(users_messages[user_id]) < MIN_MESSAGES_REQUIRED:
            del users_messages[user_id]

    users_after_banalcing = len(users_messages.keys())
    print('balance_messages discarded ', users_before_balancing - users_after_banalcing, ' users')

    return users_messages


def stem_messages(users_messages):
    users_stemmed_messages = {}
    for user_id, messages in users_messages.items():
        # keep only strings with content as messages
        messages = [message for message in messages if message_is_valid(message)]
        for index, message in enumerate(messages):
            stemmed_message = stem_message(message)
            stemmed_message = clear_low_information_words(stemmed_message)
            if len(stemmed_message) > 1:
                messages[index] = stemmed_message

        users_stemmed_messages[user_id] = messages
        print('User', user_id, 'has', len(messages), 'messages')

    # TODO: debug
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(user_stemmed_messages)
    return users_stemmed_messages


def message_is_valid(message):
    return isinstance(message, str) and len(message) > 1


def clear_low_information_words(message):
    output = []
    for word in message.split():
        # remove links, as they contain no real conversation info and cannot be stemmed
        if not word.startswith('http'):
            output.append(word)

    return str.join(' ', output)

if __name__ == '__main__':
    sys.exit(main())

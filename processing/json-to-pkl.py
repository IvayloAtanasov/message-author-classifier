"""
    Transforms Slack API json data into pkl file with single messages list for each user
"""
import sys
import json
import pickle

from processing.stem import stem_message


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

    user_messages = flatten_messages(channels)
    # stem words before outputting to pkl
    user_messages = stem_messages(user_messages)

    messages_output = []
    authors_output = []
    for user_id, messages in user_messages.items():
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


def stem_messages(user_messages):
    user_stemmed_messages = {}
    for user_id, messages in user_messages.items():
        # keep only strings with content as messages
        messages = [message for message in messages if isinstance(message, str) and len(message) > 1]
        for index, message in enumerate(messages):
            messages[index] = stem_message(message)

        user_stemmed_messages[user_id] = messages
        print('User', user_id, 'has', len(messages), 'messages')

    # TODO: debug
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(user_stemmed_messages)
    return user_stemmed_messages


if __name__ == '__main__':
    sys.exit(main())

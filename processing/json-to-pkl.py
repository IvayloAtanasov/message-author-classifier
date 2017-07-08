"""
    Transforms Slack API json data into pkl file with single messages list for each user
"""
import sys
import json
import pickle
import random
import pprint

from stem import stem_message

# TODO: could be made dynamic based on dataset average and median
MIN_SAMPLES_PER_CLASS = 1500
TARGET_SAMPLES_PER_CLASS = 2500


def main():
    # load files
    # TODO: json loading is different every time, use object_pairs_hook?
    #  https://docs.python.org/3/library/json.html#json.load
    with open('../slack-data/users.json', 'r', encoding='utf-8') as users_json:
        users = json.load(users_json)

    with open('../slack-data/channels.json', 'r', encoding='utf-8') as channels_json:
        channels = json.load(channels_json)

    with open('../slack-data/privateChannels.json', 'r', encoding='utf-8') as private_channels_json:
        private_channels = json.load(private_channels_json)

    # merge channels with private channels
    channels = channels + private_channels

    # merge from "per-channel" to "per-user" messages collection
    users_messages = flatten_messages(channels)
    # remove users with not enough messages as over-sampling their messages can lead to overfitting
    users_messages = discard_insufficient_data_users(users_messages, users)
    # stem words in messages
    users_messages = stem_messages(users_messages)
    # make all remained users have equal number of messages
    users_messages = balance_messages(users_messages)

    messages_output = []
    authors_output = []
    for user_id, messages in users_messages.items():
        for message in messages:
            authors_output.append(user_index_by_id(user_id, users))
            messages_output.append(message)

    pickle.dump(messages_output, open('messages.pkl', 'wb'))
    pickle.dump(authors_output, open('authors.pkl', 'wb'))

    print('Saved a total of ' + str(len(messages_output)) + ' processed messages')


def user_index_by_id(slack_id, users):
    """
        Returns index of user in users list, based on it's Slack id
        :param slack_id:
        :param users:
        :return: Index in users or False
    """

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
        :param channels:
        :return: messages
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


def discard_insufficient_data_users(users_messages, users):
    """
        Remove custom slack bot messages (as they are represented in a single class)
        Remove users without enough messages for processing
        :param users_messages:
        :param users:
        :return: users_messages
    """
    users_before_count = len(users_messages.keys())
    for user_id in list(users_messages.keys()):
        # remove user with id of undefined (custom Slack bots)
        if user_id == 'undefined':
            del users_messages[user_id]
            continue
        # remove users with less messages than defined threshold
        if len(users_messages[user_id]) < MIN_SAMPLES_PER_CLASS:
            del users_messages[user_id]

    users_after_count = len(users_messages.keys())
    print('Discarded ', users_before_count - users_after_count, ' users, ', users_after_count, ' remained.')
    # debugging in detail
    users_after = [users[user_index_by_id(user_id, users)]["real_name"] for user_id in users_messages.keys()]
    print(users_after)

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
    """
        Remove links from messages
        :param message:
        :return: message
    """
    output = []
    for word in message.split():
        # remove links, as they contain no real conversation info and cannot be stemmed
        if not word.startswith('http'):
            output.append(word)

    return str.join(' ', output)


def balance_messages(users_messages):
    """
        Balance dataset by:
        1. over-sampling data for users with less than the target messages count
        2. under-sampling (discarding) data for users with too many
        ref: https://www.quora.com/In-classification-how-do-you-handle-an-unbalanced-training-set
        :param users_messages:
        :return: users_messages
    """
    random.seed(420)
    for user_id in list(users_messages.keys()):
        # sorted guarantees random function will remove the same messages on run
        messages = sorted(users_messages[user_id])
        messages_count = len(messages)
        if messages_count > TARGET_SAMPLES_PER_CLASS:
            # under-sampling
            discard_count = messages_count - TARGET_SAMPLES_PER_CLASS
            selected_for_removal = random.sample(messages, discard_count)
            # select one by one, not filter, so we leave duplicating values intact if any
            selection = []
            for message in messages:
                if message in selected_for_removal:
                    selected_for_removal.remove(message)
                    continue
                selection.append(message)
            users_messages[user_id] = selection
        elif messages_count < TARGET_SAMPLES_PER_CLASS:
            # over-sampling
            duplicate_count = TARGET_SAMPLES_PER_CLASS - messages_count
            selected_for_adding = random.sample(messages, duplicate_count)
            users_messages[user_id] = users_messages[user_id] + selected_for_adding
        else:
            # just the right samples volume, do nothing
            pass

    return users_messages


if __name__ == '__main__':
    sys.exit(main())

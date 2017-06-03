from nltk.stem.snowball import SnowballStemmer
import string


def stem_message(message):
    # TODO: used a russian stemmer, english words remain unprocessed
    stemmer = SnowballStemmer("russian")
    # remove punctuation
    # ref 1: https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    # ref 2: https://stackoverflow.com/questions/23175809/typeerror-translate-takes-one-argument-2-given-python
    message = message.translate({ord(c): None for c in string.punctuation})
    # stem each word from message and compose again
    stemmed_words = [stemmer.stem(word) for word in message.split()]
    return str.join(' ', stemmed_words)

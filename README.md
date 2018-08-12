# Message author classifier

## Dependencies

- NodeJS 6.3.0+
- Python 3.4.3+

## Setup

### Install SciPy + NumPy by following [these instructions](https://www.scipy.org/install.html).

### Install scikit-learn by following [these instructions](http://scikit-learn.org/stable/install.html).

### Install nltk by following [these instructions](http://www.nltk.org/install.html)

0. You now need to download nltk data from nltk package manager.

    Open a python console and run:
    ```
    >>> import nltk
    >>> nltk.download()
    ```

    This will open up a UI from. Locate `install 'all-corpora'` option and download the corpora.

0. Now add bulgarian stopwords into nltk data.

    Locate nltk download directory (C:\Users\me\AppData\Roaming\nltk_data)

    go into `corpora\stopwords`

    from project copy `people-classifier\processing\stopwords-bg.txt` and paste into stopwords folder as `bulgarian`

### Run `npm install` to download all NodeJS libraries needed.

## Start

Make your own `secrets.json` file using `secrets.template.json`

Run `npm run reload-data` to fetch your chat history from Slack API

Run `python ./processing/json-to-pkl.py` to transform your data into features/labels format, suitable for further processing

Run `npm start`

*You can also run `python ./processing/vectorize.py` standalone to test the classifier manually from stdin*

# This file contains additional functions necessary for the analysis.

import pandas as pd
import numpy as np
import re
import spacy
import nltk
from nltk.stem import WordNetLemmatizer, SnowballStemmer, PorterStemmer
from nltk.corpus import stopwords

from statsmodels.tsa.stattools import grangercausalitytests, adfuller

### Data preprocessing

def strip(word):
    """
    Remove non-alphanumeric characters from a word.

    Parameters:
    - word (str): The word to be stripped of non-alphanumeric characters.

    Returns:
    str: The modified word with non-alphanumeric characters removed.
    """
    mod_string = re.sub(r'\W+', '', word)
    return mod_string


def abbr_or_lower(word):
    """
    Determine whether to keep a word in original case or convert it to lowercase based on its pattern.

    Parameters:
    - word (str): The word to be evaluated.

    Returns:
    str: The word in original case if it contains two or more consecutive capital letters, otherwise in lowercase.
    """
    if re.match('([A-Z]+[a-z]*){2,}', word):
        return word
    else:
        return word.lower()


def tokenize(text, modulation):
    """
    Tokenize and preprocess text using stemming, lemmatization, and lowercasing.

    Parameters:
    - text (str): The text to be tokenized and preprocessed.
    - modulation (int): The level of modulation for preprocessing.
                        0: No preprocessing
                        1: Apply stemming
                        2: Apply lemmatization

    Returns:
    str: The preprocessed text.

    Note:
    - Stop words and non-alphanumeric tokens are removed during preprocessing.
    - Stemming is applied using the Porter Stemmer.
    - Lemmatization is performed using spaCy's English language model.
    """

    nltk.download('stopwords')
    sp = spacy.load('en_core_web_sm')

    # Getting a library of stopwords and defining a lemmatizer
    porter = SnowballStemmer("english")
    lmtzr = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))


    if modulation < 2:
        tokens = re.split(r'\W+', text)
        stems = []
        # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
        for token in tokens:
            lowers = abbr_or_lower(token)
            if lowers not in stop_words:
                if re.search('[a-zA-Z]', lowers):
                    if modulation == 0:
                        stems.append(lowers)
                    if modulation == 1:
                        stems.append(porter.stem(lowers))
    else:
        sp_text = sp(text)
        stems = []
        lemmatized_text = []
        for word in sp_text:
            lemmatized_text.append(word.lemma_)
        stems = [abbr_or_lower(strip(w)) for w in lemmatized_text if
                 (abbr_or_lower(strip(w))) and (abbr_or_lower(strip(w)) not in stop_words)]
    return " ".join(stems)


### Time-line of the Coverage

def group_data(df, period='D'):
    """
    Groups the given DataFrame by the specified time period and calculates counts of total records
    and mentions of Ukraine, as well as share of documents that mention Ukraine.

    Parameters:
    - df (DataFrame): The DataFrame containing the data to be grouped.
    - period (str): The time period for grouping. Default is 'D' for daily.

    Returns:
    DataFrame: A DataFrame containing counts of total records, mentions of Ukraine, and the share of
    mentions for each time period.

    Example:
    >>> grouped_data = group_data(df, period='M')
    """

    # Group by date and calculate total count of records
    counts_by_date = df.groupby(df['Date'].dt.to_period(period)).size().reset_index(name='Total Count')

    # Filter data where "Ukraine" == 1 and group by date to calculate count of records mentioning Ukraine
    mentions_by_date = df[df['Ukraine'] == 1].groupby(df['Date'].dt.to_period(period)).size().reset_index(
        name='Mentions Count')

    # Merge the two dataframes on date
    result = pd.merge(counts_by_date, mentions_by_date, on='Date', how='left').fillna(0)

    # Calculate the share
    result['Mentions Share'] = result['Mentions Count'] / result['Total Count']

    return result


### Granger Causality Test

def granger_causality_matrix(data, variables, maxlag, test='ssr_chi2test', verbose=False):
    """
    Check Granger Causality of all possible combinations of the Time series.

    The rows represent the response variables, and the columns represent the predictors.
    The values in the table are the P-Values. P-Values less than the significance level (0.05) imply
    rejection of the Null Hypothesis, suggesting that the coefficients of the corresponding past values are
    non-zero, indicating that the X variable causes Y.

    Parameters:
    - data (DataFrame): A pandas DataFrame containing the time series variables.
    - variables (list): A list containing the names of the time series variables.
    - maxlag (int): The maximum lag to consider for Granger Causality testing.
    - test (str): The statistical test to use. Default is 'ssr_chi2test'.
    - verbose (bool): Whether to print verbose output. Default is False.

    Returns:
    DataFrame: A DataFrame containing the P-Values for Granger Causality tests between the variables.
    """
    df = pd.DataFrame(np.zeros((len(variables), len(variables))), columns=variables, index=variables)
    for c in df.columns:
        for r in df.index:
            test_result = grangercausalitytests(data[[r, c]], maxlag=maxlag, verbose=False)
            p_values = [round(test_result[i+1][0][test][1], 4) for i in range(maxlag)]
            if verbose: print(f'Y = {r}, X = {c}, P Values = {p_values}')
            min_p_value = np.min(p_values)
            df.loc[r, c] = min_p_value
    df.columns = [var + '_x' for var in variables]
    df.index = [var + '_y' for var in variables]
    return df


def check_stationarity(data):
    """
    Perform the Augmented Dickey-Fuller test to check for stationarity in a time series.

    Parameters:
    - data (array-like): The time series data to be tested.

    Returns:
    - bool: True if the time series is stationary, False otherwise.
    """
    result = adfuller(data)
    p_value = result[1]
    if p_value < 0.05:
        return True  # Reject the null hypothesis (stationary)
    else:
        return False  # Fail to reject the null hypothesis (non-stationary)

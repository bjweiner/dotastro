
# Try to classify matplotlib functions and associated keywords
# in order to recommend matplotlib keywords you might like to use

# Analyze an input python file (training set) to find the matplotlib calls
# assume they have the format  plt.funcname( .., keyword= ..., )
# and find the keywords associated with functions
# Use this to make a training set (like a Ngram?)
# then take a second file (test data), analyze it similarly, and
# make recommendations for keywords based on the functions used

# Calling syntax:
# python keyword_recommend.py training_set.py file_to_analyze.py

# or python keyword_recommend.py
# and it will prompt for the filenames

# Benjamin Weiner, Sept 26, 2018
# bjw@mmto.org
# A dot Astronomy X hack

# BSD 3 clause license applies.

import os
import sys
import re

import numpy as np
# from scikit-learn import ...

# get text from a file or series of files
# do we want to return one string or a list?
def get_text_from_file(fname):
    f = open(fname,'r')
    # text = f.read()
    textlines = f.readlines()
    return textlines

# Analyze file to find what prefix used for matplotlib.
def get_prefix(text):
    # Here we could match a line that looks like the import
    # and find the abbreviation.  Just assume plt for now
    # regex = 'from .*matplotlib.* import .*'
    prefix = 'plt'
    return prefix

# Parse a line for eg plt.funcname( ..., keyword1=..., keyword2= ...)
# Maybe the returned structure should be a dict with function name
# and value keywords, but, just make it a list
def parse_line_for_call(prefix, line):
    # line is like plt.test(x,y,markersize=20, fontsize=20)
    # find strings with eg 'plt.'
    search1 = prefix + '\.(.*)'
    result = re.search(search1, line, re.I)
    if not (result is None):
        # result.group() is the whole line
        # call is something like 'test(x,y,markersize=20, fontsize=20)'
        call = result.group(1)
        # Find stuff before parenthesis
        search2 = '[^\(]*'
        result2 = re.search(search2, call, re.I)
        if not (result2 is None):
            # funcname is 'test'
            funcname = result2.group()
            # print('funcname = ',funcname)
            outlist = [funcname]
            # find stuff in parentheses but not the leading paren - doesn't do what I want
            # search3 = '[^\(].*'
            # find stuff in parentheses 
            search3 = '\(.*\)'
            result3 = re.search(search3, call, re.I)
            # now result3.group() is '(x,y,markersize=20, fontsize=20)'
            # now let's split the string on commas
            keywords = []
            if not (result3 is None):
                args = result3.group().split(',')
                # look for stuff that precedes an '='
                # require that keywords contain only a-z0-9_ ?
                for a in args:
                    # this was to look for stuff after a comma
                    # search4 = '\,[a-z0-9_]*[^=]'
                    result4 = re.search('.*=', a, re.I)
                    if not (result4 is None):
                        # remove spaces and =
                        kw = re.sub('[\ \=]', '', result4.group())
                        keywords.append(kw)
            if len(keywords) >= 1:
                # print('keywords ',keywords)
                outlist.append(keywords)
        else:
            outlist = None
    else:
        outlist = None
    return outlist
            
                

# Find each string that matches the prefix to return the function calls
def find_calls(prefix,text):
    calls = []
    # this assumes each call is on a single line, which is crude
    for line in text:
        res = parse_line_for_call(prefix, line)
        if not(res is None):
            # print(res)
            calls.append(res)
    return calls

# Parse a file for the funcname keyword pairs
def get_calls_from_file(fname):
    text = get_text_from_file(fname)
    prefix = get_prefix(text)
    calls_list = find_calls(prefix, text)
    # print(calls_list)
    return calls_list

# make sorted list of unique function names found in the list
def make_unique_funcnames(calls_list):
    funcs = []
    for pair in calls_list:
        funcs.append(pair[0])
    tmp1 = set(funcs)
    funcs_sort = list(sorted(tmp1))
    return funcs_sort

# make sorted list of unique keywords found in the list 
def make_unique_keywords(calls_list):
    keys = []
    for pair in calls_list:
        # Append elements of a list one by one
        # This is very un-python, need to make cleaner
        if len(pair) > 1:
            if len(pair[1]) >=1:
                for k in pair[1]:
                    keys.append(k)
    tmp1 = set(keys)
    keys_sort = list(sorted(tmp1))
    return keys_sort

# Make a 2-d array of times keywords occur along with a function
# then normalize it to fractional frequency of keyword per that function call
def compute_key_probs(funcs, keyws, calls_list):
    func_num = np.zeros(len(funcs))
    key_num = np.zeros(len(keyws))
    func_key_num = np.zeros([len(funcs), len(keyws)])
    for pair in calls_list:
        f = pair[0]
        i = funcs.index(f)
        func_num[i] += 1
        if len(pair) > 1:
            if len(pair[1]) >= 1:
                for k in pair[1]:
                    j = keyws.index(k)
                    key_num[j] += 1
                    func_key_num[i,j] += 1
    fsum = sum(func_num)
    ksum = sum(key_num)
    fksum = sum(func_key_num)
    # print('Occurrences: ', fsum, ksum, fksum)
    # broadcast func_num on the first coord of func_key_num
    # this should divide the number of keyword occurences with a
    # function, by the number of times that function was called
    # return func_key_num
    norm_freq = func_key_num / func_num[:, None]
    return norm_freq

# Find the most probable keywords for a function
# Return a list of tuples (frequency, keyw name) sorted from most to least frequent
def most_probable_kws(funcs, keyws, norm_freq, funcname):
    i = funcs.index(funcname)
    kw_freqs = norm_freq[i,:]
    kw_freq_name = zip(kw_freqs, keyws)
    sort_f_k_tuples = sorted(kw_freq_name, key=lambda x: x[0], reverse=True)
    # print( sort_f_k_tuples )
    # Unzip the tuples
    sort_freq = [a for a,b in sort_f_k_tuples]
    sort_keyw = [b for a,b in sort_f_k_tuples]
    # print(sort_freq)
    # print(sort_keyw)
    # Eliminate entries with zero frequency. There must be an easier
    # way to do this.
    freqarr = np.array(sort_freq)
    out_freq = []
    out_keyw = []
    for i in range(len(sort_freq)):
        if freqarr[i] > 0.0:
            out_freq.append( sort_freq[i] )
            out_keyw.append( sort_keyw[i] )
    # ii = np.where(sort_freq > 0.0)
    # freqarr = np.array(sort_freq)
    # ii = (freqarr > 0.0)
    # if len(ii) >=1:
    #     out_freq = freqarr[ii]
    #     out_keyw = []
    #     for j in range(len(sort_keyw)):
    #         if ii[j]==True:
    #            out_keyw.append(sort_keyw[j])
    if len(out_freq) >=1 :
        return out_freq, out_keyw
    else:
        return None, None
    
    
# Make the normalized freq array from the training file
def make_training_freq(fname):
    calls_list = get_calls_from_file(fname)
    funcs = make_unique_funcnames(calls_list)
    keyws = make_unique_keywords(calls_list)
    print('Functions: ',funcs)
    print('Keywords: ',keyws)
    f_k_freq = compute_key_probs(funcs, keyws, calls_list)
    print('Normalized kw frequency: ',f_k_freq)
    return funcs, keyws, f_k_freq

# analyze a file by finding what functions were called
# and reporting the keywords you used and that the training set used
def analyze_file(fname, funcs, keyws, f_k_freq):
    calls_list = get_calls_from_file(fname)
    funcs_new = make_unique_funcnames(calls_list)
    keyws_new = make_unique_keywords(calls_list)
    f_k_freq_new = compute_key_probs(funcs_new, keyws_new, calls_list)
    for f_test in funcs_new:
        your_freq, your_keys = most_probable_kws(funcs_new, keyws_new, f_k_freq_new, f_test)
        train_freq, train_keys = most_probable_kws(funcs, keyws, f_k_freq, f_test)
        print('You used function ',f_test,' with keywords and frequency: ')
        # print(your_freq, your_keys)
        # print(train_freq, train_keys)
        if not your_freq is None:
            for i in range(len(your_freq)):
                print("{0:s}  {1:5.3f}".format(your_keys[i], your_freq[i]))
        else:
            print("None!")
        print('We recommend these keywords with frequency: ')
        if not train_freq is None:
            for i in range(len(train_freq)):
                print("{0:s}  {1:5.3f}".format(train_keys[i], train_freq[i]))
        else:
            print("None!")
           
    return 

def main():
    if len(sys.argv) >= 3:
        train_name = sys.argv[1]
        fname = sys.argv[2]
    elif len(sys.argv) == 2:
        train_name = sys.argv[1]
        fname = input('Enter file name to analyze: ')
    else:
        train_name = input('Enter training file name: ')
        fname = input('Enter file name to analyze: ')
    funcs, keyws, f_k_freq = make_training_freq(train_name)
    while not (fname==''):
        out = analyze_file(fname, funcs, keyws, f_k_freq)
        fname = input('Enter file name to analyze [quit]: ')
        
    print('Done!')
    return

        
# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
  main()

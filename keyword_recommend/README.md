

A hack to read your code and recommend matplotlib keywords.
It takes a training set of python code, such as an ensemble of 
the matplotlib examples, analyzes the functions and keywords,
then takes your file to be analyzed, and suggests keywords
based on the training set.

So far it just does a dumb frequency analysis: it tells you
the keywords most often used with the functions you're using.


"""
# ClassyPie

Python toolkit for easily classifying (grouping) data values.

## Introduction

Data classification algorithms are commonly used to group together data
values in order to simplify and highlight different aspects of the data
distribution.

ClassyPie implements and gives users easy access to many of the most
commonly used data classification algorithms. 
Can be used on any sequence of values, including objects by
specifying a key-function to obtain the value.

The library was originally built as a convenient high-level wrapper around
Carston Farmer's "class_intervals.py" script for QGIS, but has since been
improved and expanded with several new algorithms and new convenience functions.

## Platforms

Python 2 and 3. 


## Dependencies

Pure Python, no dependencies. 


## Installation

ClassyPie is installed with pip from the commandline:

    pip install plassypie

It also works to just place the "classypie" package folder in an importable location like 
"PythonXX/Lib/site-packages".


## Documentation

This tutorial only covers some basic examples. For the full list of functions and supported crs formats,
check out the reference API Documentation. 

- [Home Page](http://github.com/karimbahgat/ClassyPie)
- [API Documentation](https://karimbahgat.github.io/ClassyPie/)


## Examples

We start by importing the library, and we recommend abbreviating it to 'cp':

    >>> import classypie as cp


### The Classifier

#### Classifying values

##### + proportional

#### Retrieving class values


### Low-level operations

#### Calculating break points

##### histogram (alias for equal)
##### equal
##### quantile
##### pretty
##### stdev
##### natural
##### headtail
##### log (base-10, uses offset to handle 0s but not negative numbers)

#### Splitting/grouping values

##### + Custom
##### + Categorical
##### + Membership

#### Finding the class of a value


## License

This code is free to share, use, reuse, and modify according to the MIT
license, see license.txt

## Credits

- Karim Bahgat
- Carston Farmer

"""


__version__ = "0.1.0"


from .main import *



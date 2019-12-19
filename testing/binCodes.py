# This file is just for development purposes
# It demonstrates how binary commands are composed for various purposes
# flake8: noqa

# A bunch of binary commands:

# Make an evaluation call to Rserv, giving a simple string with a number:
#    CMD_EVAL     MSG_SIZE       2nd part of header   DT_STRING+len   data
c1 = '\3\0\0\0' + '\x08\0\0\0' + '\0\0\0\0\0\0\0\0' + '\4\4\0\0'    + '1\0\0\0'
# -> evaluates to: numpy.array([1.0])


# Make a CMD_setSEXP call to Rserve, providing a variable name and a simple expression (array):
#     CMD_setSEXP   MSG_SIZE        2nd part of header   DT_STRING+len   str-data
c2 = '\x20\0\0\0' + '\x18\0\0\0' + '\0\0\0\0\0\0\0\0' + '\4\4\0\0'    + 'abc\0' + \
     '\0a\x0c\x00\x00\x20\x08\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00'  # <-  array expression

# define a function in R
# myfunc <- function(y1, y2) { tst <- y1 + y2; tst }

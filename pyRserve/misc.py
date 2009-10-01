

class FunctionMapper(object):
    'This class is used in Lexer, Parser, and Serializer to map IDs to functions'
    def __init__(self, adict):
        self.adict=adict
        
    def __call__(self, *args):
        def wrap(func):
            for a in args:
                self.adict[a]=func
            return func
        return wrap


pyRserve manual
===============

Setting up a connection to Rserve
---------------------------------

First of all startup Rserve if it is not yet running::

  $ R CMD Rserve

If you started it on your local machine (i.e. ``localhost``) without any extra options Rserve should be listening on port 6311 (its default).

From the python interpreter import the pyRserve package and by omitting any arguments to the ``rconnect()`` function setup the connection to your locallly running Rserve::

  $ python
  >>> import pyRserve
  >>> conn = pyRserve.rconnect()

To connect to a different location host and port can be specified explicitely::

  pyRserve.rconnect(host='localhost', port=6311)

The resulting connection handle can tell you where it is connected to::

  >>> conn
  <Handle to Rserve on localhost:6311>

The connection will be closed automatically when conn is deleted, or by explicitely calling the ``close()``-method::

  >>> conn.close()
  >>> conn
  <Closed handle to Rserve on localhost:6311>

Running operations on a closed pyRserve connector results in an exception. However a connection can be reopened by calling the ``connect()`` method. It reuses the previously given values (or defaults) for ``host`` and ``port``::

  >>> conn.connect()
  <Handle to Rserve on localhost:6311>

To check the status of the connection use::

  >>> conn.isClosed
  False



String evaluation in R
-------------------------------

Having established a connection to Rserve you can run the first commands on it. A valid R command can be executed by making a call directly on the connector, providing a string as argument::

  >>> conn('3 + 5')
  8.0

In this example the string ``"3 + 5"`` will be sent to the remote side and evaluated by R. The result is then delivered back into a native Python object, a floating point number in this case. As an R expert you are probably aware of the fact that R uses vectors for all numbers internally by default. But why did we received a single floating point number? The reason is that pyRserve looks at vectors coming from Rserve and converts vectors with only one single item into an atomic value. This behaviour is for convenience reasons only, and might change in the future.

Of course also more complex data types can be sent from R to Python, e.g. lists or real vectors. Here are some examples::

  >>> conn("list(1, 'otto')")
  [1, 'otto']
  >>> conn('c(1, 5, 7)')
  array([ 1.,  2.])

As demonstrated R lists are converted into plain Python lists whereas R vectors are converted into numpy arrays on the Python side 

It is also possible to create functions inside the R interpreter through the connector, or even to execute entire scripts. Basically you can do everything which is possible inside a normal R console::

  # create a function and execute it:
  >>> conn('doubleit <- function(x) { x*2 }')
  >>> conn('doubleit(2)')
  4.0
  # store a script as a string ...
  >>> my_r_script = '''
  squareit <- function(x)
    { x**2 }
  squareit(4)
  '''
  # and execute the mini-script in R:
  >>> conn(my_r_script)
  16.0




The R namespace
-------------------------

The Rserve connector ``conn`` used above provides an attribute called "``r``" which gives you direct access to the namespace of the R connection. Each Rserve connection has its private namespace which is lost after the connection is closed (if you don't save it). 

Through the ``r``-attribute you can set and access variables, and also call functions defined in the R-namespace. The advantage of using the R namespace is that you can assign data in R from real Python objects, instead of from strings only. The following two statements are equivalent::

  >>> conn('aVar <- "abc"')
  >>> conn.aVar = "abc"



Setting and accessing variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In its current implementation pyRserve allows to set and access the following base types:

* boolean
* integers (32-bit only)
* floating point numbers (64 bit only), i.e. doubles
* strings

Furthermore the following containers are supported:

* lists
* numpy arrays
* TaggedList

Lists can be nested arbitrarily, containing other lists, numbers or arrays.

The following example shows how to assign a python list with mixed data types to an R variable called ``aList``, and then to retrieve it again:

  >>> conn.r.aList = [1, 'abcde', numpy.array([1, 2, 3], dtype=int)]
  >>> conn.r.aList
  [1, 'abcde', array([1, 2, 3])]

Numpy-arrays can also contain dimension information which translates them into R matrices when assigned to the R namespace::

  >>> arr = numpy.array(range(12))
  >>> arr.shape = (3, 4)
  >>> conn.r.aMatrix = arr
  
  NOTE: THIS IMPLEMENTATION IS STILL BUGGY, WILL BE FIXED ASAP!!

A special type of container is a so called "TaggedList". Such an object is created in R and its items accessed as shown here::

  > t <- list(husband="otto", wife="erna", "5th avenue")
  > t[1]
  $husband
  [1] "otto"

  > t['husband']
  $husband
  [1] "otto"

So items in the list can be either access via their index position or through their "tag". Please note that the third argument ("5th avenue") is not tagged, so it can only be accessed via its index number, i.e. ``t[3]``.

There is no direct match to any standard Python construct for a TaggedList. Python dictionaries do not preserve their elements' order, and also don't allow for missing keys. The solution was to provide a special class in Python which is called ``TaggedList``. When accessing the list ``t`` from the example above you'll obtain an instance of a TaggedList in Python::

  >>> t = conn('t <- list(husband="otto", wife="erna", "5th avenue")')
  >>> t
  TaggedList(husband='otto', wife='erna', '5th avenue')

This TaggedList instance can be accessed in the same way as its R pendant, except for the fact the indexing is starting at zero in the usual pythonic way::

  >>> t[0]
  'otto'
  >>> t['husband']
  'otto'
  >>> t[2]
  '5th avenue'

To retrieve its data suitable for instantiating another TaggeList on the Python side get its data as a list of tuples. This also demonstrates how a TaggeList is created::

  >>> from pyRserve import TaggedList
  >>> t.astuples
  [('husband', 'otto'), ('wife', 'erna'), (None, '5th avenue')]
  >>> new_tagged_list = TaggedList(t.astuples)


Calling functions
^^^^^^^^^^^^^^^^^

Before the examples below are usable we need to define a couple of very simple functions within the R namespace: ``func0()`` accepts no parameters and returns a fixed string, ``func1()`` exactly one parameter and ``funcKKW()`` takes keyword arguments with defaults set::

  conn('func0 <- function() { "hello world" }')
  conn('func1 <- function(v) { v*2 }')
  conn('funcKW <- function(a1=1.0, a2=4.0) { list(a1, a2) }')

Now calling R functions is as trivial as calling plain python functions::

  >>> conn.r.func0()
  "hello world"
  >>> conn.r.func1(5)
  10
  >>> conn.r.funcKW(a2=6.0)
  [1.0, 6.0]

Of course you can also call functions built-in to R::

  >>> conn.r.length([1,2,3])
  3


Getting help with functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Also here no surprise - just do it the Python way through the ``__doc__`` attribute::

  >>> print conn.r.sapply.__doc__
  lapply                 package:base                 R Documentation
   
  Apply a Function over a List or Vector
   
  Description:
   
  'lapply' returns a list of the same length as 'X', each element of
  which is the result of applying 'FUN' to the corresponding element
  of 'X'.
  [...]

Of course this only works for functions which provide documentation. For all others ``__doc__`` just returns ``None``.



Applying an R function as argument to another function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A typical application in R is to apply a vector to a function, especially via ``sapply`` and its brothers. Fortunately this is as easy as you would expect::

  >>> conn('double <-- function(x) { x*2 }')
  >>> conn.r.sapply(array([1, 2, 3]), conn.r.double)
  array([ 2.,  4.,  6.])

Here a Python array and a function defined in R are provided as arguments to the R function ``sapply``.


Of course the following trying to provide a Python function makes no sense::

  >>> def double(v): return v*2
  ...
  >>> conn.r.sapply(array([1, 2, 3]), double)

This will result in a serialization error because the connector tries to copy a Python function into R. 


Applying a variable already defined in R to a function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To understand why this is an interesting feature one has to understand how Python and pyRserve works. The following code is pretty inefficient::

  >>> conn.r.arr = numpy.array([1, 2, 3])
  >>> conn.r.sapply(conn.r.arr, conn.r.double)

To see why it is inefficient it is reproduced here more explicitely, but doing exactly the same thing::

  >>> conn.r.arr = numpy.array([1, 2, 3])
  >>> arr = conn.r.arr
  >>> conn.r.sapply(arr, conn.r.double)

Now it is clear that the value of ``conn.r.arr`` is first set inside R, then retrieved back to python (in the second line) and then again sent back to the ``sapply`` function. This is pretty inefficient, it would be much better just to set the array in R and then to refer to ``conn.r.arr`` instead of sending it back and forth. Here the "reference" namespace called ``ref`` comes into play::

   >>> conn.ref.arr
   <RVarProxy to variable "arr">

Through `conn.ref` it is possible to only reference a variable (or a function) in the R namespace without actually bringing it over to Python. Such a reference can then be given as an argument to every function called from ``conn.r``.
However it is still possible to retrieve the actual content of a variable proxy through its ``value()`` method::

  >>> conn.ref.arr.value()
  array([1., 2., 3.])

So using ``conn.ref`` instead of ``conn.r`` primarily returns a reference to the remote variable in the R namespace, instead of its value. Actually we have done that before with the function ``conn.r.double``. This doesn't return the R function to Python - something which would be pretty useless. Instead only a proxy to the R function is returned::

  >>> conn.r.double
  <RFuncProxy to function "double">

Actually functions are always returned as proxy references, both in the ``conn.r`` and the ``conn.ref`` namespace, so ``conn.r.<function>`` is the same as ``conn.ref.<function>``.

Now to make ``sapply`` above really access ``arr`` from the R namespace let's modify the call slightly:

  >>> conn.r.sapply(conn.ref.arr, conn.r.double)

Using reference to R variables is indeed absolutely necessary for variable content which is not transferable into Python, like special types of R classes, complex data frames etc. 



Handling complex results from R functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some functions in R (especially those doing statistical calculations) return quite complex result objects. The T-test is such an example. In R you would see something like this (please ignore the dummy values to it)::

    > t.test(c(1,2,3,1),c(1,6,7,8))
    
            Welch Two Sample t-test
    
    data:  c(1, 2, 3, 1) and c(1, 6, 7, 8)
    t = -2.3054, df = 3.564, p-value = 0.09053
    alternative hypothesis: true difference in means is not equal to 0
    95 percent confidence interval:
     -8.4926941  0.9926941
    sample estimates:
    mean of x mean of y
         1.75      5.50

This is what you would get to see directly in your R shell. 

Now if the test function is called from pyRserve the result has to somehow be translated into Python objects. Here is what you would expect (note that the result has been manually reformatted to be easier to read in this example)::

    >>> res = conn('t.test(c(1,2,3,1),c(1,6,7,8))')
    >>> res
    <TaggedList(statistic=TaggedArray([-2.30541984]), 
     parameter=TaggedArray([ 3.56389482], tags=['df']), 
     p.value=0.090532640733331213, 
     conf.int=AttrArray([-8.49269413,  0.99269413], attr={'conf.level': array([ 0.95])}), 
     estimate=TaggedArray([ 1.75,  5.5 ], tags=['mean of x', 'mean of y']), 
     null.value=TaggedArray([ 0.], tags=['difference in means']), 
     alternative='two.sided', 
     method='Welch Two Sample t-test', 
     data.name='c(1, 2, 3, 1) and c(1, 6, 7, 8)')>
    >>>

The result is again an instance of a `TaggedList`. As explained above a TaggedList is a Python list that can additionally be accessed via key-words (like in a Python dictionary). However the order is maintained, and keys don't have to be unique (in which case it would only return the first item of the list assigned to that key).

So to access the confidence interval and its confidence level from the t-test you would type in Python::

    >>> res['conf.int'].attr['conf.level']
    array([ 0.95])

In the `res` result data structure above there are also objects of a container called `AttrArray`.
An `AttrArray` is a normal Numpy-Array with an additional attribute `attr`, a dictionary that holds further information provided by R for this data item. In this case is is the confidence level (0.95) for the given confidence interval.

A `TaggedArray` basically behaves like a `TaggedList`, except that the underlying container is a Numpy array instead of a Python list. So to access the second item of the `TaggedList` called `estimate` the following two commands are equivalent::

    >>> res['estimate'][1]
    5.5
    >>> res['estimate']['mean of y']
    5.5


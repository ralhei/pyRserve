pyRserve manual
===============

This manual is written in sort of a `walk-through`-style. All examples can be tried out on the Python
command line as you read through it. 

Setting up a connection to Rserve
------------------------------------

First of all startup Rserve if it is not yet running::

  $ R CMD Rserve

If you started it on your local machine (i.e. ``localhost``) without any extra options Rserve should be listening on
port 6311 (its default). R puts itself into daemon mode, meaning that your shell comes back, and you have no way to
shutdown R via ``ctrl-C`` (you need to call ``kill`` with it's process id). However ``Rserve`` can be started in 
debug mode during development. In this mode it'll print messages to stdout helping you to see whether your 
connection works etc. To do so `Rserve` needs to be started like::

  $ R CMD Rserve.dbg

Now we can try to connect to it.
From the python interpreter import the pyRserve package and by omitting any arguments to the ``connect()`` function
setup the connection to your locally running ``Rserve``::

  $ python
  >>> import pyRserve
  >>> conn = pyRserve.connect()

To connect to a different location host and port can be specified explicitly::

  pyRserve.connect(host='localhost', port=6311)

The resulting connection handle can tell you where it is connected to::

  >>> conn
  <Handle to Rserve on localhost:6311>

The connection will be closed automatically when conn is deleted, or by explicitly calling the ``close()``-method::

  >>> conn.close()
  >>> conn
  <Closed handle to Rserve on localhost:6311>

Running operations on a closed pyRserve connector results in an exception. However a connection can be reopened by
calling the ``connect()`` method. It reuses the previously given values (or defaults) for ``host`` and ``port``::

  >>> conn.connect()
  <Handle to Rserve on localhost:6311>

To check the status of the connection use::

  >>> conn.isClosed
  False

.. NOTE::
   When a remote connection to Rserve should be opened, and pyRserve cannot connect to it, most likely Rserve
   only listens to it's own internal network connection. To force Rserve accepting connections from other machines
   create a file called `/etc/Rserv.conf` and add at least the following line:

          ``remote enable``

   Then restart Rserve.

The R namespace
-------------------------

The Rserve connector ``conn`` created above provides an attribute called "``r``" which gives direct access to the
namespace of the R connection. Each Rserve connection has its private namespace which is lost after the connection
is closed (if you don't save it).

Through the ``r``-attribute you can set and access variables, and also call functions defined in the R-namespace.
The following sections explain how to use the namespace in various ways.

String evaluation in R
-------------------------------

Having established a connection to Rserve you can run the first commands on it. A valid R command can be executed 
by making a call to the R name space, providing a string as argument which contains valid R syntax::

  >>> conn.r('3 + 5')
  8.0

In this example the string ``"3 + 5"`` will be sent to the remote side and evaluated by the R interpreter. The result is then
delivered back into a native Python object, a floating point number in this case. As an R expert you are
probably aware of the fact that R uses vectors for all numbers internally by default. But why did we receive
a single floating point number? The reason is that pyRserve looks at arrays coming from Rserve and converts
arrays with only one single item into an atomic value. This behaviour is for convenience reasons only.
To override this behaviour (i.e. to always receive arrays with only one element) open the connection to
Rserve with an additional argument ``atomicArray`` set to ``True``, i.e.

    ``conn = pyRserve.connect(atomicArray=True)``

Then the called above would return a `numpy` array:

  >>> conn.r('3 + 5')
  array([ 8.])

``conn.atomicArray`` will tell you how the connection handles results. This attribute contains the value of the
``atomicArray`` kw-argument given to connect. It can also be changed directly for a running connection.

  >>> conn.atomicArray
  True
  >>> conn.atomicArray = False  # change value

More expression evaluation
------------------------------

Of course also more complex data types can be sent from R to Python, e.g. lists or real arrays. Here are some examples::

  >>> conn.r("list(1, 'otto')")
  [1, 'otto']
  >>> conn.r('c(1, 5, 7)')
  array([ 1.,  2.])

As demonstrated R lists are converted into plain Python lists whereas R vectors are converted into numpy
arrays on the Python side.

To set a variable inside the R namespace do::

  >>> conn.r('aVar <- "abc"')

and to request its value just do::

  >>> conn.r('aVar')
  'abc'

It is also possible to create functions inside the R interpreter through the connector's namespace, or even to
execute entire scripts. Basically you can do everything which is possible inside a normal R console::

  # create a function and execute it:
  >>> conn.r('doubleit <- function(x) { x*2 }')
  >>> conn.r('doubleit(2)')
  4.0

  # store a mini script definition in a Python string ...
  >>> my_r_script = '''
  squareit <- function(x)
    { x**2 }
  squareit(4)
  '''
  # .... and execute it in R:
  >>> conn.r(my_r_script)
  16.0



Setting and accessing variables in a more Pythonic way
---------------------------------------------------------

The previous section showed how to set a variable inside R by evaluation a statement in string format::

  >>> conn.r('aVar <- "abc"')

This is not very elegant and has limited ways to provide values already stored in Python variables. A much nicer
way to do this is by setting the variable name in R as an attribute to the namespace. The following statement
does the same thing as the one above, just "more Pythonic"::

  >>> conn.r.aVar = "abc"

So of course it is then possible to compute values or copy them from Python variables into R::

  >>> conn.r.aVar = some_python_number * 1000.505

To retrieve a variable from R just use it as expected::

  >>> print 'A value from R:', conn.r.aVar

In its current implementation pyRserve allows to set and access the following base types:

* None (NULL)
* boolean
* integers (32-bit only)
* floating point numbers (64 bit only), i.e. doubles
* complex numbers
* strings

Furthermore the following containers are supported:

* lists
* numpy arrays
* TaggedList
* AttrArray
* TaggedArray

Lists can be nested arbitrarily, containing other lists, numbers, or arrays. ``TaggedList``, ``AttrArray``, and 
``TaggedArray`` are 
special containers to handle very R-specific result types. They will be explained further down in the manual.

The following example shows how to assign a python list with mixed data types to an R variable called ``aList``,
and then to retrieve it again::

  >>> conn.r.aList = [1, 'abcde', numpy.array([1, 2, 3], dtype=int)]
  >>> conn.r.aList
  [1, 'abcde', array([1, 2, 3])]

Numpy arrays can also contain dimension information which are translated into R matrices when assigned to the R namespace::

  >>> arr = numpy.array(range(12))
  >>> arr.shape = (3, 4)
  >>> conn.r.aMatrix = arr
  >>> conn.r('dim(aMatrix)')  # give me the dimension of aMatrix on the R-side
  array([3, 4])

The result of the shape information is - in contrast to what one gets from numpy arrays - an array itself.
There is nothing special about this, this is just the way R internally deals with that information.


Handling Fortran and C style ordering of arrays
-------------------------------------------------

In R arrays are handled the Fortran way, meaning that the first index iterates over columns, while in C-style arrays
(like the default in `numpy`) the first index iterates over the cells of the array.

  >>> arr = numpy.array([[1, 2, 3], [4, 5, 6]])
  >>> arr
  array([[1, 2, 3],
         [4, 5, 6]])
  >>> arr[0]
  [1, 2, 3]

Not so in R::

  > arr = c(1,2,3,4,5,6)
  > dim(arr) = c(2,3)
  > arr
       [,1] [,2] [,3]
  [1,]    1    3    5
  [2,]    2    4    6
  > arr[1]
  [1] 1

To retrieve R arrays in Fortran-style order, there are two possibilities:

  * provide the option ``arrayOrder='F'`` to the ``pyRserve.connect()`` call
  * change ``conn.arrayOrder`` from 'C' to 'F'

Examples:

  >>> conn.r('arr = c(1,2,3,4,5,6)')
  >>> conn.r('dim(arr) = c(2,3)')
  # In C-style:
  >>> conn.arrayType
  'C'
  >>> ronn.r.arr
  array([[1, 2, 3],
         [4, 5, 6]])
  # In Fortran-style:
  >>> conn.arrayType = 'F'
  >>> ronn.r.arr
  array([[1, 3],
         [2, 5],
         [3, 6]])


Calling functions in R
------------------------

Functions defined in R can be called as if they were a Python methods, declared in the namespace of R.

Before the examples below are usable we need to define a couple of very simple functions within the R namespace:
``func0()`` accepts no parameters and returns a fixed string, ``func1()`` takes exactly one parameter and
``funcKKW()`` takes keyword arguments with default values::

  conn.r('func0 <- function() { "hello world" }')
  conn.r('func1 <- function(v) { v*2 }')
  conn.r('funcKW <- function(a1=1.0, a2=4.0) { list(a1, a2) }')

Now calling R functions is as trivial as calling plain Python functions::

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
------------------------------

If R is properly installed including its help messages those can be retrieved directly.
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
---------------------------------------------------------

A typical application in R is to apply a vector to a function, especially via ``sapply`` and its brothers (or sisters, 
depending how how one sees them).

Fortunately this is as easy as you would expect::

  >>> conn.r('double <-- function(x) { x*2 }')
  >>> conn.r.sapply(array([1, 2, 3]), conn.r.double)
  array([ 2.,  4.,  6.])

Here a Python array and a function defined in R are provided as arguments to the R function ``sapply``.

Of course the following attempt to provide a Python function as an argument into R makes no sense::

  >>> def double(v): return v*2
  ...
  >>> conn.r.sapply(array([1, 2, 3]), double)
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
  NameError: name 'double' is not defined

This will result in a NameError error because the connector tries to reference the function 'double' inside the
R namespace. It should be obvious that it is not possible to transfer function implementations from Python to R.


Applying a variable already defined in R to a function
-----------------------------------------------------------

To understand why this is an interesting feature one has to understand how Python and pyRserve works. The following
code is pretty inefficient::

  >>> conn.r.arr = numpy.array([1, 2, 3])
  >>> conn.r.sapply(conn.r.arr, conn.r.double)

To see why it is inefficient it is reproduced here more explicitly, but doing exactly the same thing::

  >>> conn.r.arr = numpy.array([1, 2, 3])
  >>> arr = conn.r.arr
  >>> conn.r.sapply(arr, conn.r.double)

Now it is clear that the value of ``conn.r.arr`` is first set inside R, then retrieved back to Python
(in the second line) and then again sent back to the ``sapply`` function. This is pretty inefficient,
it would be much better just to set the array in R and then to refer to ``conn.r.arr`` instead of sending
it back and forth. Here the "reference" namespace called ``ref`` comes into play::

   >>> conn.ref.arr
   <RVarProxy to variable "arr">

Through ``conn.ref`` it is possible to only reference a variable (or a function) in the R namespace without actually
bringing it over to Python. Such a reference can then be passed as an argument to every function called
from ``conn.r``. So the proper way to make the call above is::

  >>> conn.r.arr = numpy.array([1, 2, 3])
  >>> conn.r.sapply(conn.ref.arr, conn.r.double)

However it is still possible to retrieve the actual content of a variable proxy through its ``value()`` method::

  >>> conn.ref.arr.value()
  array([1., 2., 3.])

So using ``conn.ref`` instead of ``conn.r`` primarily returns a reference to the remote variable in the R namespace,
instead of its value. Actually we have done that before with the function ``conn.r.double``. This doesn't return
the R function to Python - something which would be pretty useless. Instead only a proxy to the R function is returned::

  >>> conn.r.double
  <RFuncProxy to function "double">

Actually functions are always returned as proxy references, both in the ``conn.r`` and the ``conn.ref`` namespace,
so ``conn.r.<function>`` is the same as ``conn.ref.<function>``.

Using reference to R variables is indeed absolutely necessary for variable content which is not transferable into
Python, like special types of R classes, complex data frames etc.


Handling complex result objects from R functions
---------------------------------------------------

Some functions in R (especially those doing statistical calculations) return quite complex result objects. 

The T-test is such an example. In the R shell you would see something like this (please ignore the silly values 
applied to the t test)::

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

Now, how would this convoluted result be transferred into Python objects? For this to be possible
pyRserve has defined three special classes that allow for a mapping from R to Python objects. These classes
are explained the the following sections. Afterwards - with that knowledge - we have a final look at the result
of the t-test again.


TaggedLists
~~~~~~~~~~~~~~~~

The first special type of container is called "TaggedList". It reflects a list-type object in R where 
items can be accessed in two ways as shown here (this is now pure R code)::

  > t <- list(husband="otto", wife="erna", "5th avenue")
  > t[1]
  $husband
  [1] "otto"

  > t['husband']
  $husband
  [1] "otto"

So items in the list can be either accessed via their index position, or through their "tag". Please note that the
third list item ("5th avenue") is not tagged, so it can only be accessed via its index number, i.e. ``t[3]``
(indexing in R starts at 1 and not at zero as in Python!).

There is no direct match to any standard Python construct for a ``TaggedList``. Python dictionaries do not preserve
their elements' order and also don't allow for missing keys (which is why an OrderDict also doesn't help).
NamedTuples on the other side would do the job but don't allow items to be appended or deleted since they are 
immutable.

The solution was to provide a special class in Python which is called ``TaggedList``. When accessing the
list ``t`` from the example above you'll obtain an instance of a TaggedList in Python::

  >>> t = conn.r('list(husband="otto", wife="erna", "5th avenue")')
  >>> t
  TaggedList(husband='otto', wife='erna', '5th avenue')

This ``TaggedList`` instance can be accessed in the same way as its R pendant, except for the fact the indexing is
starting at zero in the usual Pythonic way::

  >>> t[0]
  'otto'
  >>> t['husband']
  'otto'
  >>> t[2]
  '5th avenue'

To retrieve its data suitable for instantiating another ``TaggedList`` on the Python side get its data as a list of
tuples. This also demonstrates how a ``TaggedList`` can be created directly in Python::

  >>> from pyRserve import TaggedList
  >>> t.astuples
  [('husband', 'otto'), ('wife', 'erna'), (None, '5th avenue')]
  >>> new_tagged_list = TaggedList(t.astuples)

.. NOTE::
   ``TaggedList`` does not provide the full list API that one would expect, some methods are just to entirely
   implemented yet. However it is useful enough to retrieve all information obtained out of a R result object.


AttrArrays
~~~~~~~~~~~~~~~~~

An ``AttrArray`` is simply an normal numpy array, with an additional dictionary attribute called ``attr``. 
This dicionary is used to store meta data associated to an array retrieved from R. 

Let's create such an ``AttrArray`` in R, and transfer it into to the Python side::

   >>> conn.r("t <- c(-8.49, 0.99)")
   >>> conn.r("attributes(t) <- list(conf.level=0.95)")
   >>> conn.r.t
   AttrArray([-8.49, 0.99], attr={'conf.level': array([ 0.95])})

To create such an array from Python in R is also possible via::

   >>> from pyRserve import AttrArray
   >>> conn.r.t = AttrArray.new([-8.49, 0.99], {'conf.level': numpy.array([ 0.95])})

Instead of a list argument the ``new`` function also accepts a numpy array as well::

   >>> conn.r.t = AttrArray.new(numpy.array([-8.49, 0.99]), {'conf.level': numpy.array([ 0.95])})


TaggedArrays
~~~~~~~~~~~~~~~~

The third special data type provided by pyRserve is the so called ``TaggedArray``. It provides basically the same
features as ``TaggedList`` above, however the underlying data type is a numpy-Array instead of a Python list. 
In fact, a TaggedArray is a direct subclass of ``numpy.ndarray``, enhanced with some new features 
like accessing array cells by name as in ``TaggedList``.

For the moment ``TaggedArrays`` only make real sense if they are 1-dimensional, so please do not change 
its shape. The results would not really be predictable.

To create a ``TaggedArray`` on the R side and transfer it to Python type:

  >>> res = conn.r('c(a=1.,b=2.,3.)')
  >>> res
  TaggedArray([ 1.,  2.,  3.], key=['a', 'b', ''])
  >>> res[1]
  2.0
  >>> res['b']
  2.0

The third element in the array did not obtain a name on the R side, so it is represented by an empty string in
the ``TaggedArray`` object.

Although ``TaggedArray``s are normal numpy arrays they loose their tags when further processed in Python, but still
present themselves (via ``__repr__``) as ``TaggedArray``. This is a current flaw in their implementation.

To create a ``TaggedArray`` directly in Python there is a constructor function ``new()`` which takes a normal
1-d numpy array as the first argument and a list of tags as the second. Both arguments must match in their size::

  >>> from pyRserve import TaggedArray
  >>> arr = TaggedArray.new(numpy.array([1, 2, 3]), ['a', 'b', ''])
  >>> arr
  TaggedArray([1, 2, 3], key=['a', 'b', ''])


Back to the t-test example
--------------------------------

After ``TaggedList`` and ``TaggedArray`` have been introduced we can now go back to the t-test mentioned
before. Let's make the same call to the test function, this time just from the Python side, and then
look at the result. Again there are two ways to call it, one via string evaluation by the R interpreter,
one by directly providing native Python parameters.
So::

   >>> res = conn.r('t.test(c(1,2,3,1),c(1,6,7,8))')

and::

   >>> res = conn.r.test(numpy.array([1,2,3,1]), numpy.array([1,6,7,8]))

does actually the same thing.

Looking at the result we get::
   >>> res
   <TaggedList(statistic=TaggedArray([-2.30541984]),
    parameter=TaggedArray([ 3.56389482], tags=['df']),
    p.value=0.090532640733331213,
    conf.int=TaggedArray([-8.49269413,  0.99269413], attr={'conf.level': array([ 0.95])}),
    estimate=TaggedArray([ 1.75,  5.5 ], tags=['mean of x', 'mean of y']),
    null.value=TaggedArray([ 0.], tags=['difference in means']),
    alternative='two.sided',
    method='Welch Two Sample t-test',
    data.name='c(1, 2, 3, 1) and c(1, 6, 7, 8)')>

The result is an instance of a ``TaggedList``, containing different types of list items.

So to access e.g. the confidence interval one would type in Python::

   >>> res['conf.int']
   AttrArray([-8.49269413,  0.99269413], attr={'conf.level': array([ 0.95])})

This returns an AttrArray where the confidence level is stored in an attribute called ``conf.level``
in the ``attr``-dictionary::

   >>> res['conf.int'].attr['conf.level']
   array([ 0.95])

In the ``res``-result data structure above there are also objects of a container called TaggedArray::

   >>> res['estimate']
   TaggedArray([ 1.75,  5.5 ], tags=['mean of x', 'mean of y'])
   >>> res['estimate'][1]
   5.5
   >>> res['estimate']['mean of y']
   5.5


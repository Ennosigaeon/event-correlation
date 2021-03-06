import logging
import sys

import numpy as np

from algorithms import Matcher, RESULT_MU, RESULT_SIGMA, RESULT_KDE, RESULT_IDX
from core.distribution import KdeDistribution


class MunkresMatcher(Matcher):
    def __init__(self):
        super().__init__(__name__)

    def _compute(self, trigger, response):
        [TTrigger, TResponse] = np.meshgrid(trigger, response)
        delta = TResponse - TTrigger
        # square to make pair-wise distances asymmetric
        delta[delta > 0] **= 2

        m = Munkres()
        idx = m.compute(delta)
        idx[:, [0, 1]] = idx[:, [1, 0]]

        delta[delta > 0] = np.sqrt(delta[delta > 0])
        cost = delta[idx[:, 1], idx[:, 0]]
        self._logger.debug("Found matchings with total cost {:.2f}".format(cost.sum()))

        if (self._logger.isEnabledFor(logging.TRACE)):
            for i in range(min(len(trigger), len(response))):
                self._logger.trace("Matched ({}, {}) -> {:.4f} - {:.4f} = {:.4f}"
                                   .format(idx[i][0], idx[i][1], response[idx[i][1]], trigger[idx[i][0]],
                                          delta[idx[i][1], idx[i][0]]))
            if (len(trigger) != len(response)):
                self._logger.trace("Remaining events were not assigned")

        cost = self._trimVector(cost)
        return {RESULT_MU: cost.mean(), RESULT_SIGMA: cost.std(), RESULT_KDE: KdeDistribution(cost), RESULT_IDX: idx}


"""
Introduction
============

The Munkres module provides an implementation of the Munkres algorithm (also called the Hungarian algorithm or the
Kuhn-Munkres algorithm), useful for solving the Assignment Problem.

Assignment Problem
==================

Let *C* be an *n*\ x\ *n* matrix representing the costs of each of *n* workers to perform any of *n* jobs. The
assignment problem is to assign jobs to workers in a way that minimizes the total cost. Since each worker can perform
only one job and each job can be assigned to only one worker the assignments represent an independent set of the matrix
*C*.

One way to generate the optimal set is to create all permutations of the indexes necessary to traverse the matrix so
that no row and column are used more than once. For instance, given this matrix (expressed in Python)::

    matrix = [[5, 9, 1],
              [10, 3, 2],
              [8, 7, 4]]

You could use this code to generate the traversal indexes::

    def permute(a, results):
        if len(a) == 1:
            results.insert(len(results), a)

        else:
            for i in range(0, len(a)):
                element = a[i]
                a_copy = [a[j] for j in range(0, len(a)) if j != i]
                subResults = []
                permute(a_copy, subResults)
                for subResult in subResults:
                    result = [element] + subResult
                    results.insert(len(results), result)

    results = []
    permute(range(len(matrix)), results) # [0, 1, 2] for a 3x3 matrix

After the call to permute(), the results matrix would look like this::

    [[0, 1, 2],
     [0, 2, 1],
     [1, 0, 2],
     [1, 2, 0],
     [2, 0, 1],
     [2, 1, 0]]

You could then use that index matrix to loop over the original cost matrix and calculate the smallest cost of the
combinations::

    n = len(matrix)
    minval = sys.maxsize
    for row in range(n):
        cost = 0
        for col in range(n):
            cost += matrix[row][col]
        minval = min(cost, minval)

    print(minval)

While this approach works fine for small matrices, it does not scale. It executes in O(*n*!) time: Calculating the
permutations for an *n*\ x\ *n* matrix requires *n*! operations. For a 12x12 matrix, that's 479,001,600 traversals. Even
if you could manage to perform each traversal in just one millisecond, it would still take more than 133 hours to
perform the entire traversal. A 20x20 matrix would take 2,432,902,008,176,640,000 operations. At an optimistic
millisecond per operation, that's more than 77 million years.

The Munkres algorithm runs in O(*n*\ ^3) time, rather than O(*n*!). This package provides an implementation of that
algorithm.

This version is based on http://csclab.murraystate.edu/bob.pilgrim/445/munkres.html.

This version was written for Python by Brian Clapper from the (Ada) algorithm at the above web site. (The
``Algorithm::Munkres`` Perl version, in CPAN, was clearly adapted from the same web site.)

Usage
=====

Construct a Munkres object::

    from munkres import Munkres

    m = Munkres()

Then use it to compute the lowest cost assignment from a cost matrix. Here's a sample program::

    from munkres import Munkres, print_matrix

    matrix = [[5, 9, 1],
              [10, 3, 2],
              [8, 7, 4]]
    m = Munkres()
    indexes = m.compute(matrix)
    print_matrix(matrix, msg='Lowest cost through this matrix:')
    total = 0
    for row, column in indexes:
        value = matrix[row][column]
        total += value
        print('(%d, %d) -> %d' % (row, column, value))
    print('total cost: %d' % total)

Running that program produces::

    Lowest cost through this matrix:
    [5, 9, 1]
    [10, 3, 2]
    [8, 7, 4]
    (0, 0) -> 5
    (1, 1) -> 3
    (2, 2) -> 4
    total cost=12

The instantiated Munkres object can be used multiple times on different matrices.

Non-square Cost Matrices
========================

The Munkres algorithm assumes that the cost matrix is square. However, it's possible to use a rectangular matrix if you
first pad it with 0 values to make it square. This module automatically pads rectangular cost matrices to make them
square.

Notes:

- The module operates on a *copy* of the caller's matrix, so any padding will not be seen by the caller.
- The cost matrix must be rectangular or square. An irregular matrix will *not* work.

Calculating Profit, Rather than Cost
====================================

The cost matrix is just that: A cost matrix. The Munkres algorithm finds the combination of elements (one from each row
and column) that results in the smallest cost. It's also possible to use the algorithm to maximize profit. To do that,
however, you have to convert your profit matrix to a cost matrix. The simplest way to do that is to subtract all
elements from a large value. For example::

    from munkres import Munkres, print_matrix

    matrix = [[5, 9, 1],
              [10, 3, 2],
              [8, 7, 4]]
    cost_matrix = []
    for row in matrix:
        cost_row = []
        for col in row:
            cost_row += [sys.maxsize - col]
        cost_matrix += [cost_row]

    m = Munkres()
    indexes = m.compute(cost_matrix)
    print_matrix(matrix, msg='Highest profit through this matrix:')
    total = 0
    for row, column in indexes:
        value = matrix[row][column]
        total += value
        print('(%d, %d) -> %d' % (row, column, value))

    print('total profit=%d' % total)

Running that program produces::

    Highest profit through this matrix:
    [5, 9, 1]
    [10, 3, 2]
    [8, 7, 4]
    (0, 1) -> 9
    (1, 0) -> 10
    (2, 2) -> 4
    total profit=23

The ``munkres`` module provides a convenience method for creating a cost matrix from a profit matrix. Since it doesn't
know whether the matrix contains floating point numbers, decimals, or integers, you have to provide the conversion
function; but the convenience method takes care of the actual creation of the cost matrix::

    import munkres

    cost_matrix = munkres.make_cost_matrix(matrix,
                                           lambda cost: sys.maxsize - cost)

So, the above profit-calculation program can be recast as::

    from munkres import Munkres, print_matrix, make_cost_matrix

    matrix = [[5, 9, 1],
              [10, 3, 2],
              [8, 7, 4]]
    cost_matrix = make_cost_matrix(matrix, lambda cost: sys.maxsize - cost)
    m = Munkres()
    indexes = m.compute(cost_matrix)
    print_matrix(matrix, msg='Lowest cost through this matrix:')
    total = 0
    for row, column in indexes:
        value = matrix[row][column]
        total += value
        print('(%d, %d) -> %d' % (row, column, value))
    print('total profit=%d' % total)

References
==========

1. http://csclab.murraystate.edu/bob.pilgrim/445/munkres.html

2. Harold W. Kuhn. The Hungarian Method for the assignment problem.
   *Naval Research Logistics Quarterly*, 2:83-97, 1955.

3. Harold W. Kuhn. Variants of the Hungarian method for assignment
   problems. *Naval Research Logistics Quarterly*, 3: 253-258, 1956.

4. Munkres, J. Algorithms for the Assignment and Transportation Problems.
   *Journal of the Society of Industrial and Applied Mathematics*,
   5(1):32-38, March, 1957.

5. http://en.wikipedia.org/wiki/Hungarian_algorithm

Modifications
=============

This program was modified by Marc Zoeller to make the code Python 3.x compatible, fix some bugs and incorporate
significant speedups by using Numpy for computations. Changes were partially based on open pull requests available under
https://github.com/bmc/munkres/pulls

Copyright and License
=====================

This software is released under a BSD license, adapted from <http://opensource.org/licenses/bsd-license.php>

Copyright (c) 2008 Brian M. Clapper
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following
  disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
  disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name "clapper.org" nor the names of its contributors may be used to endorse or promote products derived
  from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

__docformat__ = 'restructuredtext'
__all__ = ['Munkres', 'make_cost_matrix']

# Info about the module
__version__ = "2.0.0"
__author__ = "Brian Clapper, bmc@clapper.org"
__url__ = "http://software.clapper.org/munkres/"
__copyright__ = "(c) 2008 Brian M. Clapper"
__license__ = "BSD-style license"


class Munkres:
    """
    Compute the Munkres solution to the classical assignment problem.
    See the module documentation for usage.
    """

    def __init__(self):
        """Create a new instance"""
        self.C = None
        self.row_covered = np.zeros(0, dtype=bool)
        self.col_covered = np.zeros(0, dtype=bool)
        self.n = 0
        self.Z0_r = 0
        self.Z0_c = 0
        self.marked = None
        self.path = None
        self.original_length = 0
        self.original_width = 0

    def make_cost_matrix(profit_matrix, inversion_function):
        """
        **DEPRECATED**

        Please use the module function ``make_cost_matrix()``.
        """
        return make_cost_matrix(profit_matrix, inversion_function)

    make_cost_matrix = staticmethod(make_cost_matrix)

    @staticmethod
    def pad_matrix(matrix):
        """
        Pad a possibly non-square matrix to make it square.

        :Parameters:
            matrix : Numpy array to pad

            pad_value : int
                value to use to pad the matrix

        :rtype: Numpy array
        :return: a new, possibly padded, matrix
        """
        num_rows, num_cols = matrix.shape
        n = max(num_rows, num_cols)

        new_matrix = np.zeros((n, n))
        for i, row in enumerate(matrix):
            # for a 1D numpy array, row.size is ~10% faster than row.shape[0]
            new_matrix[i, :row.size] = row

        return new_matrix

    def compute(self, cost_matrix):
        """
        Compute the indexes for the lowest-cost pairings between rows and columns in the database. Returns a list of
        (row, column) tuples that can be used to traverse the matrix.

        :Parameters:
            cost_matrix : list of lists or Numpy array
                The cost matrix. If this cost matrix is not square, it will be padded with zeros, via a call to
                ``pad_matrix()``. (This method does *not* modify the caller's matrix. It operates on a copy of the
                matrix.)

                **WARNING**: This code handles square and rectangular matrices. It does *not* handle irregular matrices.

        :rtype: list
        :return: A list of ``(row, column)`` tuples that describe the lowest cost path through the matrix
        """
        cost_matrix = np.array(cost_matrix)

        # munkres does not handle negative values
        cost_matrix[cost_matrix < 0] = sys.maxsize

        self.C = self.pad_matrix(cost_matrix)
        self.n = self.C.shape[0]
        self.original_length, self.original_width = cost_matrix.shape

        self.row_covered = np.zeros(self.n, dtype=bool)
        self.col_covered = np.zeros(self.n, dtype=bool)
        self.Z0_r = 0
        self.Z0_c = 0

        self.path = np.zeros((self.n * 2, self.n * 2))
        self.marked = np.zeros((self.n, self.n))

        step = 1
        steps = {
            1: self.__step1,
            2: self.__step2,
            3: self.__step3,
            4: self.__step4,
            5: self.__step5,
            6: self.__step6
        }

        while step < 7:
            func = steps[step]
            step = func()

        ones = np.where(self.marked[:self.original_length, :self.original_width] == 1)
        return np.array(ones).T

    def __step1(self):
        """
        For each row of the matrix, find the smallest element and subtract it from every element in its row. Go to Step
        2.
        """
        for row in self.C:
            row -= np.min(row)

        return 2

    def __step2(self):
        """
        Find a zero (Z) in the resulting matrix. If there is no starred zero in its row or column, star Z. Repeat for
        each element in the matrix. Go to Step 3.
        """
        zeros = zip(*np.where(self.C == 0))
        for (i, j) in zeros:
            if (not self.row_covered[i]) and (not self.col_covered[j]):
                self.marked[i][j] = 1
                self.row_covered[i] = True
                self.col_covered[j] = True

        self.__clear_covers()
        return 3

    def __step3(self):
        """
        Cover each column containing a starred zero. If K columns are covered, the starred zeros describe a complete set
        of unique assignments. In this case, Go to DONE, otherwise, Go to Step 4.
        """
        rows, cols = np.where(self.marked == 1)
        for j in cols:
            self.col_covered[j] = True
        count = np.sum(self.col_covered)

        if count >= self.n:
            return 7
        else:
            return 4

    def __step4(self):
        """
        Find a non-covered zero and prime it. If there is no starred zero in the row containing this primed zero, Go to
        Step 5. Otherwise, cover this row and uncover the column containing the starred zero. Continue in this manner
        until there are no uncovered zeros left. Save the smallest uncovered value and Go to Step 6.
        """
        while True:
            (row, col) = self.__find_a_zero()
            if row < 0:
                return 6

            self.marked[row][col] = 2
            star_col = self.__find_star_in_row(row)
            if star_col >= 0:
                col = star_col
                self.row_covered[row] = True
                self.col_covered[col] = False
            else:
                self.Z0_r = row
                self.Z0_c = col
                return 5

    def __step5(self):
        """
        Construct a series of alternating primed and starred zeros as follows. Let Z0 represent the uncovered primed
        zero found in Step 4. Let Z1 denote the starred zero in the column of Z0 (if any). Let Z2 denote the primed zero
        in the row of Z1 (there will always be one). Continue until the series terminates at a primed zero that has no
        starred zero in its column. Unstar each starred zero of the series, star each primed zero of the series, erase
        all primes and uncover every line in the matrix. Return to Step 3.
        """
        count = 0
        path = self.path
        path[count][0] = self.Z0_r
        path[count][1] = self.Z0_c

        while True:
            row = self.__find_star_in_col(path[count][1])
            if row < 0:
                self.__convert_path(path, count)
                self.__clear_covers()
                self.__erase_primes()
                return 3

            count += 1
            path[count][0] = row
            path[count][1] = path[count - 1][1]

            col = self.__find_prime_in_row(path[count][0])
            count += 1
            path[count][0] = path[count - 1][0]
            path[count][1] = col

    def __step6(self):
        """
        Add the value found in Step 4 to every element of each covered row, and subtract it from every element of each
        uncovered column. Return to Step 4 without altering any stars, primes, or covered lines.
        """
        minval = self.__find_smallest()
        self.C[self.row_covered, :] += minval
        self.C[:, np.logical_not(self.col_covered)] -= minval
        return 4

    def __find_smallest(self):
        """Find the smallest uncovered value in the matrix."""
        uncovered_rows = np.logical_not(self.row_covered)
        uncovered_cols = np.logical_not(self.col_covered)
        uncovered_matrix = self.C[uncovered_rows, :][:, uncovered_cols]
        if uncovered_matrix.size > 0:
            return np.min(uncovered_matrix)
        return sys.maxsize

    def __find_a_zero(self):
        """Find the first uncovered element with value 0"""
        uncovered_rows = np.logical_not(self.row_covered)
        uncovered_cols = np.logical_not(self.col_covered)
        uncovered_matrix = self.C[uncovered_rows][:, uncovered_cols]
        zeros = list(zip(*np.where(uncovered_matrix == 0)))

        if len(zeros) > 0:
            _r, _c = zeros[0]
            row = np.where(uncovered_rows)[0][_r]
            col = np.where(uncovered_cols)[0][_c]
            return (row, col)
        return (-1, -1)

    def __find_star_in_row(self, row):
        """
        Find the first starred element in the specified row. Returns the column index, or -1 if no starred element was
        found.
        """
        ones = np.where(self.marked[row] == 1)[0]
        if ones.size > 0:
            return ones[0]
        return -1

    def __find_star_in_col(self, col):
        """
        Find the first starred element in the specified row. Returns the row index, or -1 if no starred element was
        found.
        """
        ones = np.where(self.marked[:, int(col)] == 1)[0]
        if ones.size > 0:
            return ones[0]
        return -1

    def __find_prime_in_row(self, row):
        """
        Find the first prime element in the specified row. Returns the column index, or -1 if no starred element was
        found.
        """
        twos = np.where(self.marked[int(row)] == 2)[0]
        if twos.size > 0:
            return twos[0]
        return -1

    def __convert_path(self, path, count):
        for i in range(count + 1):
            x = int(path[i][0])
            y = int(path[i][1])

            if self.marked[x][y] == 1:
                self.marked[x][y] = 0
            else:
                self.marked[x][y] = 1

    def __clear_covers(self):
        """Clear all covered matrix cells"""
        self.row_covered.fill(False)
        self.col_covered.fill(False)

    def __erase_primes(self):
        """Erase all prime markings"""
        self.marked[self.marked == 2] = 0


def make_cost_matrix(profit_matrix, inversion_function):
    """
    Create a cost matrix from a profit matrix by calling 'inversion_function' to invert each value. The inversion
    function must take one numeric argument (of any type) and return another numeric argument which is presumed to be
    the cost inverse of the original profit.

    This is a static method. Call it like this:

    .. python::

        cost_matrix = Munkres.make_cost_matrix(matrix, inversion_func)

    For example:

    .. python::

        cost_matrix = Munkres.make_cost_matrix(matrix, lambda x : sys.maxsize - x)

    :Parameters:
        profit_matrix : list of lists
            The matrix to convert from a profit to a cost matrix

        inversion_function : function
            The function to use to invert each entry in the profit matrix

    :rtype: list of lists
    :return: The converted matrix
    """
    return inversion_function(profit_matrix)

##
## Test math functions
##
import os
import sys
import time
import unittest

import numpy as np

import scipy
import scipy.misc 
from scipy.special import gammaln

import misopy
import misopy.pyx
import misopy.pyx.math_utils as math_utils
import misopy.pyx.matrix_utils as matrix_utils
import misopy.pyx.sampling_utils as sampling_utils
import misopy.pyx.miso_proposals as miso_proposals
import misopy.internal_tests.py_scores as py_scores


class TestMath(unittest.TestCase):
    """
    Test mathematics functions.
    """
    def setUp(self):
        pass

    
    def test_mat_trans(self):
        """
        Test matrix transpose.
        """
        print "Testing matrix transpose"
        A = np.array([[1,2],
                      [3,4],
                      [5,6]], dtype=float)
        A_trans_pyx = np.empty((A.shape[1], A.shape[0]), dtype=float)
        A_trans_pyx = matrix_utils.mat_trans(A, A.shape[0], A.shape[1], A_trans_pyx)
        A_trans_numpy = A.T
        assert (np.array_equal(A_trans_pyx, A_trans_numpy)), \
          "Matrix transpose failed (1)."
          
        B = np.array([[1,2,3,4,5],
                      [10,20,30,40,50]], dtype=float)
        B_trans_pyx = np.empty((B.shape[1], B.shape[0]), dtype=float)
        B_trans_pyx = matrix_utils.mat_trans(B, B.shape[0], B.shape[1],
                                             B_trans_pyx)
        B_trans_numpy = B.T
        assert (np.array_equal(B_trans_pyx, B_trans_numpy)), \
          "Matrix transpose failed (2)."


    def test_mat_plus_mat(self):
        print "Testing matrix addition"
        A = np.array([[1, 2, 3],
                      [4, 5, 6]], dtype=float)
        B = np.array([[10, 100, 1000],
                      [1, 1, 1]], dtype=float)
        numpy_C = np.array(np.matrix(A) + np.matrix(B))
        pyx_C = np.empty((A.shape[0], A.shape[1]), dtype=float)
        pyx_C = matrix_utils.mat_plus_mat(A, A.shape[0], A.shape[1],
                                          B, B.shape[0], B.shape[1],
                                          pyx_C)
        assert (np.array_equal(numpy_C, pyx_C)), \
          "Matrix addition failed."

          
    def test_mat_times_mat(self):
        print "Testing matrix multiplication"
        A = np.array([[1, 2, 3],
                      [4, 5, 6]], dtype=float)
        B = np.array([[10, 20],
                      [40, 50],
                      [0, 1]], dtype=float)
        C = np.empty((A.shape[0], B.shape[1]), dtype=float)
        numpy_A_times_B = np.matrix(A) * np.matrix(B)
        pyx_A_times_B = \
          matrix_utils.mat_times_mat(A,
                                     A.shape[0],
                                     A.shape[1],
                                     B.shape[1],
                                     B,
                                     C)
        pyx_A_times_B = np.asarray(pyx_A_times_B)
        assert (np.array_equal(pyx_A_times_B, numpy_A_times_B)), \
          "Matrix multiplication failed."
        # Multiply a matrix by a column vector
        A = np.matrix(np.array([[1,2,3],
                                [4,5,6],
                                [7,8,9]]), dtype=float)
        c = np.matrix(np.array([1,2,3], dtype=float)).T
        pyx_A_times_c = np.empty((A.shape[0], 1), dtype=float)
        numpy_A_times_c = A * c
        pyx_A_times_c = \
          matrix_utils.mat_times_mat(A, A.shape[0], A.shape[1],
                                     1, c,
                                     pyx_A_times_c)
        pyx_A_times_c = np.asarray(pyx_A_times_c)
        assert (np.array_equal(pyx_A_times_c, numpy_A_times_c)), \
          "Matrix multiplication by vector column failed."


    def test_mat_times_col_vect(self):
        print "Testing matrix multiplication times column vector"
        # Multiply a matrix by a column vector
        A = np.matrix(np.array([[1,2,3],
                                [4,5,6],
                                [7,8,9]]), dtype=float)
        # Interpreted as a column vector by Cython code
        c = np.array([1,2,3], dtype=float)
        pyx_A_times_c = np.empty(A.shape[0], dtype=float)
        numpy_A_times_c = A * np.matrix(c).T
        # Convert to flat 1d array
        numpy_A_times_c = np.squeeze(np.asarray(numpy_A_times_c))
        pyx_A_times_c = \
          matrix_utils.mat_times_col_vect(A, A.shape[0], A.shape[1],
                                          c,
                                          len(c),
                                          pyx_A_times_c)
        pyx_A_times_c = np.asarray(pyx_A_times_c)
        print "numpy result: "
        print numpy_A_times_c
        print "pyx result: "
        print pyx_A_times_c
        assert (np.array_equal(pyx_A_times_c, numpy_A_times_c)), \
          "Matrix multiplication by 1d vector column failed."


    def test_sample_multivar_normal(self):
        print "Testing sampling from multivariate normal"
        mu = np.array([2.05, 0.55], dtype=float)
        sigma = np.matrix(np.array([[0.05, 0],
                                    [0, 0.05]], dtype=float))
        # Get Cholesky decomposition L of Sigma covar matrix
        L = np.linalg.cholesky(sigma)
        k = mu.shape[0]
        all_numpy_samples = []
        all_pyx_samples = []
        # Compile a list of all the samples
        num_iter = 1000
        for n in range(num_iter):
            npy_samples = np.random.multivariate_normal(mu, sigma)
            all_numpy_samples.append(npy_samples)
            pyx_samples = sampling_utils.sample_multivar_normal(mu, L, k)
            pyx_samples = list(np.asarray(pyx_samples))
            all_pyx_samples.append(pyx_samples)
        # The means should equal the mean we started with
        all_numpy_samples = np.array(all_numpy_samples)
        all_pyx_samples = np.array(all_pyx_samples)
        print "Numpy mean across %d iterations" %(num_iter)
        numpy_mean = np.mean(all_numpy_samples, axis=0)
        print numpy_mean
        print "Cython mean across %d iterations" %(num_iter)
        pyx_mean = np.mean(all_pyx_samples, axis=0)
        print pyx_mean
        # The two methods should yield very similar means
        error_range = 0.025
        assert (py_scores.approx_eq(numpy_mean[0],
                                    pyx_mean[0],
                                    error=error_range) and \
                py_scores.approx_eq(numpy_mean[1],
                                    pyx_mean[1],
                                    error=error_range)), \
                "Numpy and Cython average values of sampled normals are different."


    def test_logit(self):
        print "Testing logit transform"
        x = np.array([0.5, 0.6, 0.01, 0.001, 0.9999, 0, 0.99],
                     dtype=float)
        numpy_logit = py_scores.logit(x)
        pyx_logit = np.asarray(math_utils.logit(x, x.shape[0]))
        print "Numpy logit: "
        print numpy_logit
        print "Pyx logit: "
        print pyx_logit
        assert (np.array_equal(numpy_logit, pyx_logit)), \
          "Logit failed."

          
    def test_logit_inv(self):
        print "Testing inverse logit transform"
        x = np.array([-100, 100, 0.5, 0.6, -0.58, 0.8, 1, 0],
                     dtype=float)
        numpy_logit_inv = py_scores.logit_inv(x)
        pyx_logit_inv = np.asarray(math_utils.logit_inv(x, x.shape[0]))
        print "Numpy logit inv: "
        print numpy_logit_inv
        print "Pyx logit inv: "
        print pyx_logit_inv
        assert (np.array_equal(numpy_logit_inv, pyx_logit_inv)), \
          "Logit inverse failed."


    def test_propose_norm_drift_psi_alpha(self):
        print "Test norm drift proposal"
        # Different alpha vectors to have as initial alpha
        alpha_vectors = [np.array([1], dtype=float),
                         np.array([0.5], dtype=float),
                         np.array([0.8, 0.99], dtype=float),
                         np.array([1, 0.5, 0.5], dtype=float),
                         np.array([0.5, 0.6, 0.8], dtype=float)]
        sigma = 0.05
        for curr_alpha_vector in alpha_vectors:
            # Alpha vector has k-1 dimensions, where k is
            # the number of isoforms
            num_isoforms = curr_alpha_vector.shape[0] + 1
            covar_mat = py_scores.get_diag_covar_mat(num_isoforms-1, sigma)
            # Get Cholesky decomposition of covar matrix
            L = np.linalg.cholesky(covar_mat)
            # Sample new psi and alpha vectors
            print "Sampling new psi and alpha vectors..."
            print "Input alpha vector: "
            print curr_alpha_vector
            print "Input covar matrix: "
            print covar_mat
            print "Input Cholesky: "
            print L
            num_iters = 10000
            numpy_psi_vals = []
            pyx_psi_vals = []
            for n in range(num_iters):
                # Calculate with Python
                numpy_new_psi, numpy_new_alpha = \
                  py_scores.propose_norm_drift_psi_alpha(curr_alpha_vector,
                                                         covar_mat)
                # Calculate with Cython
                pyx_new_psi, pyx_new_alpha = \
                  miso_proposals.propose_norm_drift_psi_alpha(curr_alpha_vector,
                                                              covar_mat,
                                                              L)
                pyx_new_psi = np.asarray(pyx_new_psi)
                pyx_new_alpha = np.asarray(pyx_new_alpha)
                numpy_psi_vals.append(numpy_new_psi)
                pyx_psi_vals.append(pyx_new_psi)
            # Compare the mean sampled values across all iterations
            numpy_psi_vals = np.mean(np.array(numpy_psi_vals), axis=0)
            pyx_psi_vals = np.mean(np.array(pyx_psi_vals), axis=0)
            print "Mean values from %d iterations" %(num_iters)
            print "numpy_psi_vals: ", numpy_psi_vals
            print "pyx_psi_vals: ", pyx_psi_vals
            # Check that values are close
            error_val = 0.025
            assert (py_scores.approx_eq_arrays(numpy_psi_vals,
                                               pyx_psi_vals,
                                               error=error_val)), \
                "Cython and Numpy sampled Psi values disagree."
            
        

def main():
    unittest.main()


if __name__ == "__main__":
    main()
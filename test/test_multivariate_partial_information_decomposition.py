"""Provide unit tests for high-level Multivariate PID estimation."""
import pytest
import numpy as np
from idtxl.multivariate_partial_information_decomposition import (
                                        MultivariatePartialInformationDecomposition)
from idtxl.data import Data


def test_pid_user_input():
    """Test if user input is handled correctly."""
    # Test missing estimator name
    pid = MultivariatePartialInformationDecomposition()
    settings = {'verbose': False}    
    with pytest.raises(RuntimeError):
        pid.analyse_single_target(settings=settings, data=Data(), target=0,
                                  sources=[1, 2])

    # Test wrong estimator name
    settings = {'pid_estimator': 'TestPID', 'verbose': False}
    with pytest.raises(RuntimeError):
        pid.analyse_single_target(settings=settings, data=Data(), target=0,
                                  sources=[1, 2])

    # Test default lags for network_analysis
    settings = {'pid_estimator': 'SxPID', 'verbose': False}
    data = Data(np.random.randint(0, 10, size=(5, 100)), dim_order='ps',
                normalise=False)
    results = pid.analyse_network(settings=settings, data=data,
                                  targets=[0, 1, 2],
                                  sources=[[1, 3], [2, 4], [0, 1]])
    assert np.all(results.settings['lags_pid'] == [1, 1]), (
        'Lags were not set to default.')

    # Test sources lists have different length
    with pytest.raises(RuntimeError):
        pid.analyse_network(settings=settings, data=data,
                                  targets=[0, 1, 2],
                                  sources=[[1, 3], [2, 4], [0, 1, 3]])

    # Tests for Bivariate case
    n = 20
    alph = 2
    x = np.random.randint(0, alph, n)
    y = np.random.randint(0, alph, n)
    z = np.logical_xor(x, y).astype(int)
    data = Data(np.vstack((x, y, z)), 'ps', normalise=False)

    # Test two-tailed significance test
    settings = {'pid_estimator': 'SxPID', 'tail': 'two', 'lags_pid': [0, 0],
                'verbose': False}
    pid = MultivariatePartialInformationDecomposition()

    with pytest.raises(RuntimeError):  # Test incorrect number of sources
        pid.analyse_single_target(settings=settings, data=data, target=2,
                                  sources=[1, 2, 3])
    settings['lags_pid'] = [0, 0, 0]
    with pytest.raises(RuntimeError):  # Test incorrect number of lags # [1, 3]
        pid.analyse_single_target(settings=settings, data=data, target=2,
                                  sources=[0, 1])
    settings['lags_pid'] = [n * 3, 0]
    with pytest.raises(RuntimeError):  # Test lag > no. samples
        pid.analyse_single_target(settings=settings, data=data, target=2,
                                  sources=[0, 1])
    settings['lags_pid'] = [n, 0]
    with pytest.raises(RuntimeError):  # Test lag == no. samples
        pid.analyse_single_target(settings=settings, data=data, target=2,
                                  sources=[0, 1])
    settings['lags_pid'] = [0, 0]
    with pytest.raises(RuntimeError):  # Test target in sources
        pid.analyse_single_target(settings=settings, data=data, target=2,
                                  sources=[2, 3])
    with pytest.raises(IndexError):  # Test target not in processes
        pid.analyse_single_target(settings=settings, data=data, target=5,
                                  sources=[0, 1])

    # Tests for Multivariate case
    n = 20
    alph = 2
    s1 = np.random.randint(0, alph, n)
    s2 = np.random.randint(0, alph, n)
    s3 = np.random.randint(0, alph, n)
    s4 = np.random.randint(0, alph, n)
    s5 = np.random.randint(0, alph, n)
    z  = s1 + s2 + s3 + s4 + s5
    data = Data(np.vstack((s1, s2, s3, s4, s5, z)), 'ps', normalise=False)
    # Test two-tailed significance test
    settings = {'pid_estimator': 'SxPID', 'tail': 'two', 'lags_pid': [0, 0, 0, 0],
                'verbose': False}
    pid = MultivariatePartialInformationDecomposition()

    with pytest.raises(RuntimeError):  # Test number of sources over limit (N=4)
        pid.analyse_single_target(settings=settings, data=data, target=5,
                                  sources=[0, 1, 2, 3, 4])

def test_network_analysis():
    """Test call to network_analysis method."""
    # Test Bivariate case
    n = 1000
    alph = 2
    x = np.random.randint(0, alph, n)
    y = np.random.randint(0, alph, n)
    z = np.logical_xor(x, y).astype(int)
    data = Data(np.vstack((x, y, z)), 'ps', normalise=False)

    # Run SxPID  estimator
    pid = MultivariatePartialInformationDecomposition()
    settings = {'pid_estimator': 'SxPID', 'tail': 'two',
                'lags_pid': [[0, 0], [0, 0]]}
    est_goettingen = pid.analyse_network(settings=settings,
                                    data=data, targets=[0, 2],
                                    sources=[[1, 2], [0, 1]])
    assert 0.39 < est_goettingen._single_target[2]['avg'][((1,2,),)][2] <= 0.42, (
        'SxPID estimator incorrect synergy: {0}, should approx. 0.415...'.format(
        est_goettingen._single_target[2]['avg'][((1,2,),)][2]))

    # Test Multivairate case
    n = 1000
    alph = 2
    s1 = np.random.randint(0, alph, n)
    s2 = np.random.randint(0, alph, n)
    s3 = np.random.randint(0, alph, n)
    s4 = np.random.randint(0, alph, n)
    target1 = np.logical_xor(s1, s2).astype(int)
    target2 = np.logical_xor(s3, s4).astype(int)
    tri_target = np.logical_xor(target1, s3).astype(int)
    quad_target = np.logical_xor(target1, target2).astype(int)

    tri_data = Data(np.vstack((s1, s2, s3, tri_target)), 'ps', normalise=False)
    quad_data = Data(np.vstack((s1, s2, s3, s4, quad_target)), 'ps', normalise=False)

    # Trivariate
    pid = MultivariatePartialInformationDecomposition()
    tri_settings = {'pid_estimator': 'SxPID', 'tail': 'two',
                    'lags_pid': [[0, 0, 0], [0, 0, 0]]}
    est_goettingen = pid.analyse_network(settings=tri_settings,
                                    data=tri_data, targets=[0, 3],
                                    sources=[[1, 2, 3], [0, 1, 2]])
    assert 0.23 < est_goettingen._single_target[3]['avg'][((1,2,3,),)][2] <= 0.26, (
        'SxPID estimator incorrect synergy: {0}, should approx. 0.2451...'.format(
        est_goettingen._single_target[2]['avg'][((1,2,),)][2]))

    # Quad-variate
    quad_settings = {'pid_estimator': 'SxPID', 'tail': 'two',
                    'lags_pid': [[0, 0, 0, 0], [0, 0, 0, 0]]}
    est_goettingen = pid.analyse_network(settings=quad_settings,
                                    data=quad_data, targets=[0, 4],
                                    sources=[[1, 2, 3, 4], [0, 1, 2, 3]])
    assert 0.15 < est_goettingen._single_target[4]['avg'][((1,2,3,4,),)][2] <= 0.18, (
        'SxPID estimator incorrect synergy: {0}, should approx. 0.1682...'.format(
        est_goettingen._single_target[2]['avg'][((1,2,),)][2]))


def test_analyse_single_target():
    """Test call to network_analysis method."""
    n = 1000
    alph = 2
    x = np.random.randint(0, alph, n)
    y = np.random.randint(0, alph, n)
    z = np.logical_xor(x, y).astype(int)
    data = Data(np.vstack((x, y, z)), 'ps', normalise=False)

    # Run Tartu estimator
    pid = MultivariatePartialInformationDecomposition()
    settings = {'pid_estimator': 'SxPID',
                'tail': 'two',
                'lags_pid': [0, 0],
                'verbose': False}
    est_goettingen = pid.analyse_single_target(settings=settings, data=data,
                                               target=2, sources=[0, 1])
    assert 0.39 < est_goettingen._single_target[2]['avg'][((1,2,),)][2] <= 0.42, (
        'SxPID estimator incorrect synergy: {0}, should approx. 0.415...'.format(
        est_goettingen._single_target[2]['avg'][((1,2,),)][2]))
    assert 0.56 < est_goettingen._single_target[2]['avg'][((1,),)][2] <= 0.6, (
        'SxPID estimator incorrect unique s1: {0}, should approx. 0.5896...'.format(
        est_goettingen._single_target[2]['avg'][((1,),)][2]))
    assert 0.56 < est_goettingen._single_target[2]['avg'][((2,),)][2] <= 0.6, (
        'SxPID estimator incorrect unique s2: {0}, should approx. 0.5896...'.format(
        est_goettingen._single_target[2]['avg'][((2,),)][2]))


if __name__ == '__main__':
    test_pid_user_input()
    test_network_analysis()
    test_analyse_single_target()

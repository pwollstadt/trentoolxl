"""Test data class."""
import pytest
import numpy as np
from idtxl.data import Data
import idtxl.idtxl_utils as utils


def test_data_properties():
    """Test data properties attributes."""
    n = 10
    d = Data(np.arange(n), 's', normalise=False)
    real_time = d.n_realisations_samples()
    assert (real_time == n), 'Realisations in time are not returned correctly.'
    cv = (0, 8)
    real_time = d.n_realisations_samples(current_value=cv)
    assert (real_time == (n - cv[1])), ('Realisations in time are not '
                                        'returned correctly when current value'
                                        ' is set.')


def test_set_data():
    """Test if data is written correctly into a Data instance."""
    source = np.expand_dims(np.repeat(1, 30), axis=1)
    target = np.expand_dims(np.arange(30), axis=1)

    data = Data(normalise=False)
    data.set_data(np.vstack((source.T, target.T)), 'ps')

    assert (data.data[0, :].T == source.T).all(), ('Class data does not match '
                                                   'input (source).')
    assert (data.data[1, :].T == target.T).all(), ('Class data does not match '
                                                   'input (target).')

    d = Data()
    data = np.arange(10000).reshape((2, 1000, 5))  # random data with correct
    d = Data(data, dim_order='psr')               # order od dimensions
    assert (d.data.shape[0] == 2), ('Class data does not match input, number '
                                    'of processes wrong.')
    assert (d.data.shape[1] == 1000), ('Class data does not match input, '
                                       'number of samples wrong.')
    assert (d.data.shape[2] == 5), ('Class data does not match input, number '
                                    'of replications wrong.')
    data = np.arange(3000).reshape((3, 1000))  # random data with incorrect
    d = Data(data, dim_order='ps')            # order of dimensions
    assert (d.data.shape[0] == 3), ('Class data does not match input, number '
                                    'of processes wrong.')
    assert (d.data.shape[1] == 1000), ('Class data does not match input, '
                                       'number of samples wrong.')
    assert (d.data.shape[2] == 1), ('Class data does not match input, number '
                                    'of replications wrong.')
    data = np.arange(5000)
    d.set_data(data, 's')
    assert (d.data.shape[0] == 1), ('Class data does not match input, number '
                                    'of processes wrong.')
    assert (d.data.shape[1] == 5000), ('Class data does not match input, '
                                       'number of samples wrong.')
    assert (d.data.shape[2] == 1), ('Class data does not match input, number '
                                    'of replications wrong.')


def test_data_normalisation():
    """Test if data are normalised correctly when stored in a Data instance."""
    a_1 = 100
    a_2 = 1000
    source = np.random.randint(a_1, size=1000)
    target = np.random.randint(a_2, size=1000)

    data = Data(normalise=True)
    data.set_data(np.vstack((source.T, target.T)), 'ps')

    source_std = utils.standardise(source)
    target_std = utils.standardise(target)
    assert (source_std == data.data[0, :, 0]).all(), ('Standardising the '
                                                      'source did not work.')
    assert (target_std == data.data[1, :, 0]).all(), ('Standardising the '
                                                      'target did not work.')


def test_get_realisations():
    """Test low-level function for data retrieval."""
    data = Data()
    data.generate_mute_data()
    idx_list = [(0, 4), (0, 6)]
    current_value = (0, 3)
    with pytest.raises(RuntimeError):
        data.get_realisations(current_value, idx_list)

    # Test retrieved data for one/two replications in time (i.e., the current
    # value is equal to the last sample)
    n = 7
    d = Data(np.arange(n + 1), 's', normalise=False)
    current_value = (0, n)
    realisations = d.get_realisations(current_value, [(0, 1)])
    assert (realisations[0][0] == 1)
    assert (realisations.shape == (1, 1))
    d = Data(np.arange(n + 2), 's', normalise=False)
    current_value = (0, n)
    realisations = d.get_realisations(current_value, [(0, 1)])
    assert (realisations[0][0] == 1)
    assert (realisations[1][0] == 2)
    assert (realisations.shape == (2, 1))
    n_realisations = 2
    data = np.arange(10).reshape(n_realisations, 5)
    d = Data(data, 'rs', normalise=False)
    current_value = (0, 1)    
    realisations = d.get_realisations(current_value, [(0, 0)])
    assert np.array_equal(realisations, np.array([[0],[1], [2], [3], [5], [6], [7], [8]]))

    # Test retrieval of realisations of the current value.
    n = 7
    d = Data(np.arange(n), 's', normalise=False)
    current_value = (0, n - 1)
    realisations = d.get_realisations(current_value, [current_value])


def test_permute_replications():
    """Test surrogate creation by permuting replications."""
    n = 20
    data = Data(np.vstack((np.zeros(n),
                           np.ones(n) * 1,
                           np.ones(n) * 2,
                           np.ones(n) * 3)).astype(int),
                'rs',
                normalise=False)
    current_value = (0, n - 1)
    l = [(0, 1), (0, 3), (0, 7)]
    perm = data.permute_replications(current_value=current_value,
                                                 idx_list=l)
    assert (np.all(perm[:, [0]] == perm)), 'Samples have been swapped within \
                                            replication.'

    # Assert that samples have been swapped within the permutation range for
    # the first replication.
    rng = 3
    current_value = (0, 3)
    l = [(0, 0), (0, 1), (0, 2)]
    # data = Data(np.arange(n), 's', normalise=False)
    data = Data(np.vstack((np.arange(n),
                           np.arange(n))).astype(int),
                'rs',
                normalise=False)
    perm_settings = {
        'perm_type': 'local',
        'perm_range': rng
    }
    perm = data.permute_samples(current_value=current_value,
                                            idx_list=l,
                                            perm_settings=perm_settings)
    samples = np.arange(rng)
    i = 0
    n_per_repl = int(data.n_realisations(current_value) / data.n_replications)
    for p in range(n_per_repl // rng):
        assert (np.unique(perm[i:i + rng, 0]) == samples).all(), (
                                    'The permutation range was not respected.')
        samples += rng
        i += rng
    rem = n_per_repl % rng
    if rem > 0:
        assert (np.unique(perm[i:i + rem, 0]) == samples[0:rem]).all(), (
                        'The remainder did not contain the same realisations.')


def test_permute_samples():
    """Test surrogate creation by permuting samples."""
    n = 20
    data = Data(np.arange(n), 's', normalise=False)

    # Test unkown permutation type
    with pytest.raises(ValueError):
        settings = {'perm_type': 'test'}
        perm = data.permute_samples(current_value=(0, 0),
                                    idx_list=[(0, 0)],
                                    perm_settings=settings)

    # Test random permutation
    settings = {'perm_type': 'random'}
    perm = data.permute_samples(current_value=(0, 0),
                                idx_list=[(0, 0)],
                                perm_settings=settings)
    assert (sorted(np.squeeze(perm)) == np.arange(n)).all(), (
                            'Permutation did not contain the correct values.')

    # Test circular shifting
    settings = {'perm_type': 'circular', 'max_shift': 4}
    perm = data.permute_samples(current_value=(0, 0),
                                idx_list=[(0, 0)],
                                perm_settings=settings)
    idx_start = np.where(np.squeeze(perm) == 0)[0][0]
    assert (np.squeeze(np.vstack((perm[idx_start:], perm[:idx_start]))) ==
            np.arange(n)).all(), ('Circular shifting went wrong.')

    # Test shifting of data blocks
    block_size = round(n / 10)
    settings = {'perm_type': 'block', 'block_size': block_size,
                'perm_range': round(n / block_size)}
    perm = data.permute_samples(current_value=(0, 0),
                                idx_list=[(0, 0)],
                                perm_settings=settings)
    block_size = int(round(n / 10))
    for b in range(0, n, block_size):
        assert perm[b + 1] - perm[b] == 1, 'Block permutation went wrong.'

    # Test shifting of data blocks with n % block_size != 0
    block_size = 3
    settings = {'perm_type': 'block', 'block_size': block_size,
                'perm_range': round(n / block_size)}
    perm = data.permute_samples(current_value=(0, 0),
                                idx_list=[(0, 0)],
                                perm_settings=settings)
    for b in range(0, n, settings['block_size']):
        assert perm[b + 1] - perm[b] == 1, 'Block permutation went wrong.'

    settings = {'perm_type': 'block', 'block_size': 3, 'perm_range': 2}
    perm = data.permute_samples(current_value=(0, 0),
                                idx_list=[(0, 0)],
                                perm_settings=settings)

    # Test local shifting
    perm_range = int(round(n / 10))
    settings = {'perm_type': 'local', 'perm_range': perm_range}
    perm = data.permute_samples(current_value=(0, 0),
                                idx_list=[(0, 0)],
                                perm_settings=settings)
    for b in range(0, n, perm_range):
        assert abs(perm[b + 1] - perm[b]) == 1, 'Local shifting went wrong.'

    # Test assertions that perm_range is not too low or too high.
    current_value = (0, 3)
    l = [(0, 0), (0, 1), (0, 2)]
    perm_settings = {'perm_type': 'local', 'perm_range': 1}
    # Test Assertion if perm_range too small
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)

    # Test TypeError if settings are no integers
    perm_settings['perm_range'] = np.inf
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)
    perm_settings['perm_range'] = 'foo'
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)
    perm_settings['perm_type'] = 'block'
    perm_settings['block_size'] = 3
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)
    perm_settings['block_size'] = 3.5
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)
    perm_settings['block_size'] = -1
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)
    perm_settings['perm_range'] = -1
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)
    perm_settings['perm_type'] = 'circular'
    perm_settings['max_shift'] = 3.5
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)
    perm_settings['max_shift'] = -1
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)
    perm_settings['perm_type'] = 'local'
    perm_settings['max_shift'] = -1
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_settings=perm_settings)

def test_permute_large_array():
    """Assert correct shuffling of a large array with multiple replication and processess"""
    n = 30
    p = 20
    r = 10
    rng = np.random.default_rng(42)
    data_array = rng.integers(0, 10, size=(p, n, r))
    data = Data(data_array, 'psr', normalise=False, seed=42)

    current_value = (0, 10)
    idx_list = [(1, 1), (2, 7), (4, 3), (9, 7)]

    # Get unshuffled data
    rlz_unshuffled = data.get_realisations(current_value, idx_list)
    rlz_unshuffled_reshaped = rlz_unshuffled.reshape(r, n-current_value[1], len(idx_list))[:]

    # Permute replications
    rlz_perm = data.permute_replications(current_value=current_value, idx_list=idx_list)
    rlz_perm = rlz_perm.reshape(r, n-current_value[1], len(idx_list))
    assert _is_permutation(rlz_unshuffled_reshaped, rlz_perm, axis=0), 'Replications are not permuted correctly.'

    # Permute samples
    perm_settings = {'perm_type': 'random'}
    rlz_perm = data.permute_samples(current_value=current_value, idx_list=idx_list, perm_settings=perm_settings)
    rlz_perm = rlz_perm.reshape(r, n-current_value[1], len(idx_list))
    assert _is_permutation(rlz_unshuffled_reshaped, rlz_perm, axis=1), 'Samples are not permuted correctly.'

    # Permute blocks
    perm_settings = {'perm_type': 'block', 'block_size': 3, 'perm_range': 2}
    rlz_perm = data.permute_samples(current_value=current_value, idx_list=idx_list, perm_settings=perm_settings)
    rlz_perm = rlz_perm.reshape(r, n-current_value[1], len(idx_list))[:]
    assert _is_permutation(rlz_unshuffled_reshaped, rlz_perm, axis=1), 'Blocks are not permuted correctly.'

    # Permute local
    perm_settings = {'perm_type': 'local', 'perm_range': 3}
    rlz_perm = data.permute_samples(current_value=current_value, idx_list=idx_list, perm_settings=perm_settings)
    rlz_perm = rlz_perm.reshape(r, n-current_value[1], len(idx_list))[:]
    assert _is_permutation(rlz_unshuffled_reshaped, rlz_perm, axis=1), 'Local shuffling is not permuted correctly.'

def _is_permutation(a, b, axis=0):
    """Check if two arrays are permutations of each other."""

    if a.shape != b.shape:
        return False
    
    # Ensure arrays are not identical
    if np.all(a == b):
        return False

    return np.all(np.sort(a, axis=axis) == np.sort(b, axis=axis))

def test_get_data_slice():
    n = 10
    n_replications = 3
    d = Data(np.vstack((np.zeros(n).astype(int),
                        np.ones(n).astype(int),
                        2 * np.ones(n).astype(int))),
             'rs', normalise=False)
    [s, i] = d._get_data_slice(process=0, offset_samples=0, shuffle=False)

    # test unshuffled slicing
    for r in range(n_replications):
        assert s[0][r] == i[r], 'Replication index {0} is not correct.'.format(
                                                                            r)
    # test shuffled slicing
    [s, i] = d._get_data_slice(process=0, offset_samples=0, shuffle=True)
    for r in range(n_replications):
        assert s[0][r] == i[r], 'Replication index {0} is not correct.'.format(
                                                                            r)

    offset = 3
    d = Data(np.arange(n), 's', normalise=False)
    [s, i] = d._get_data_slice(process=0, offset_samples=offset, shuffle=False)
    assert s.shape[0] == (n - offset), 'Offset not handled correctly.'

def test_data_type():
    """Test if data class always returns the correct data type."""
    # Change data type for the same object instance.
    d_int = np.random.randint(0, 10, size=(3, 50))
    orig_type = type(d_int[0][0])
    data = Data(d_int, dim_order='ps', normalise=False)
    # The concrete type depends on the platform:
    # https://mail.scipy.org/pipermail/numpy-discussion/2011-November/059261.html
    # Hence, compare against the type automatically assigned by Python or
    # against np.integer
    assert data.data_type is orig_type, 'Data type did not change.'
    assert issubclass(type(data.data[0, 0, 0]), np.integer), (
        'Data type is not an int.')
    d_float = np.random.randn(3, 50)
    data.set_data(d_float, dim_order='ps')
    assert data.data_type is np.float64, 'Data type did not change.'
    assert issubclass(type(data.data[0, 0, 0]), float), (
        'Data type is not a float.')

    # Check if data returned by the object have the correct type.
    d_int = np.random.randint(0, 10, size=(3, 50, 5))
    data = Data(d_int, dim_order='psr', normalise=False)
    real = data.get_realisations((0, 5), [(1, 1), (1, 3)])
    assert issubclass(type(real[0, 0]), np.integer), (
        'Realisations type is not an int.')
    sl = data._get_data_slice(0)[0]
    assert issubclass(type(sl[0, 0]), np.integer), (
        'Data slice type is not an int.')
    settings = {'perm_type': 'random'}
    samples = data.permute_samples((0, 5), [(1, 1), (1, 3)], settings)
    assert issubclass(type(samples[0, 0]), np.integer), (
        'Permuted samples type is not an int.')


def test_setting_random_seed():
    """Test fixing of random seed for data generation"""
    seed = 0
    n_samples = 100
    data1 = Data(seed=seed)
    data1.generate_mute_data(n_samples=n_samples, n_replications=1)
    data2 = Data(seed=seed)
    data2.generate_mute_data(n_samples=n_samples, n_replications=1)
    data3 = Data(seed=seed+1)
    data3.generate_mute_data(n_samples=n_samples, n_replications=1)
    assert np.array_equal(data1._data, data2._data), (
        'Data with fixed random seed not equal')
    assert not np.array_equal(data1._data, data3._data), (
        'Data with fixed different random seed equal')

    data1 = Data(seed=seed)
    data1.generate_logistic_maps_data(n_samples=n_samples, n_replications=1)
    data2 = Data(seed=seed)
    data2.generate_logistic_maps_data(n_samples=n_samples, n_replications=1)
    data3 = Data(seed=seed+1)
    data3.generate_logistic_maps_data(n_samples=n_samples, n_replications=1)
    assert np.array_equal(data1._data, data2._data), (
        'Data with fixed random seed not equal')
    assert not np.array_equal(data1._data, data3._data), (
        'Data with fixed different random seed equal')

    data1 = Data(seed=seed)
    data1.generate_var_data(n_samples=n_samples, n_replications=1)
    data2 = Data(seed=seed)
    data2.generate_var_data(n_samples=n_samples, n_replications=1)
    data3 = Data(seed=seed+1)
    data3.generate_var_data(n_samples=n_samples, n_replications=1)
    assert np.array_equal(data1._data, data2._data), (
        'Data with fixed random seed not equal')
    assert not np.array_equal(data1._data, data3._data), (
        'Data with fixed different random seed equal')


if __name__ == '__main__':
    test_data_properties()
    test_set_data()
    test_data_normalisation()
    test_get_realisations()
    test_permute_replications()
    test_permute_samples()
    test_permute_large_array()
    test_get_data_slice()
    test_data_type()
    test_setting_random_seed()

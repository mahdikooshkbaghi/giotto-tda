from sklearn.utils.validation import check_is_fitted
from sklearn.base import BaseEstimator, TransformerMixin

import numpy as np
import pandas as pd
import datetime as dt


class Resampler(BaseEstimator, TransformerMixin):
    # FIXME: (doc) transformer output type
    """Data sampling transformer that returns a sampled Pandas dataframe
    with a datetime index.

    Parameters
    ----------
    sampling_type : str, optional, default: 'periodic'
        The type of sampling. Its value can be either 'periodic' or 'fixed':

        - 'periodic':
            It means sampling with a constant ``sampling_period``.
        - 'fixed':
            It entails that the list of sampling times has to be provided
            via the parameter ``sampling_times``.

    sampling_period : str, optional, default: '2h'
        The sampling period for periodic sampling. Used only if
        ``sampling_type`` is 'periodic'.

    sampling_times : list of datetime, optional, default: [dt.time(0,0,0)]
        dt.Datetime at which the samples should be taken. Used only if
        ``sampling_type`` is 'fixed'.

    remove_weekends : boolean, optional, default: True
        Option to remove week-ends from the time series pd.DataFrame.

    Attributes
    ----------
    _n_features : int
        Number of features (i.e. number fo time series) passed as an input
        of the resampler.

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> from giotto.time_series import Resampler
    >>> # Create a noisy signal sampled
    >>> signal = np.asarray([np.sin(x /40) - 0.5 + np.random.random()
    ... for x in range(0, 300)])
    >>> plt.plot(signal)
    >>> plt.show()
    >>> # Set up the DataFrame of the z-projection of the simulated solution
    >>> df = pd.DataFrame(signal)
    >>> df.index = pd.to_datetime(df.index, utc=True, unit='h')
    >>> # Set up the Resampler
    >>> sampling_period = '10h'
    >>> periodic_sampler = Resampler(sampling_type='periodic',
    >>> sampling_period=sampling_period, remove_weekends=False)
    >>> # Fit and transform the DataFrame
    >>> periodic_sampler.fit(df)
    >>> signal_resampled = periodic_sampler.transform(df)
    >>> plt.plot(signal_resampled)

    """
    valid_sampling_types = ['periodic', 'fixed']

    def __init__(self, sampling_type='periodic', sampling_period='2h',
                 sampling_times=None, remove_weekends=True):
        if sampling_times is None:
            sampling_times = [dt.time(0, 0, 0)]
        self.sampling_type = sampling_type
        self.sampling_period = sampling_period
        self.sampling_times = sampling_times
        self.remove_weekends = remove_weekends

    def get_params(self, deep=True):
        """Get parameters for this estimator.

        Parameters
        ----------
        deep : boolean, optional, default: True
            Behaviour not yet implemented.

        Returns
        -------
        params : mapping of string to any
            Parameter names mapped to their values.

        """
        return {'sampling_type': self.sampling_type,
                'sampling_period': self.sampling_period,
                'sampling_times': self.sampling_times,
                'remove_weekends': self.remove_weekends}

    @staticmethod
    def _validate_params(sampling_type):
        """A class method that checks whether the hyperparameters and the
        input parameters of the :meth:``fit`` are valid.
        """
        if sampling_type not in Resampler.valid_sampling_types:
            raise ValueError('The sampling type %s is not supported' %
                             sampling_type)

    def fit(self, X, y=None):
        """Do nothing and return the estimator unchanged.
        This method is just there to implement the usual API and hence
        work in pipelines.

        Parameters
        ----------
        X : DataFrame, shape (n_samples, n_features)
            Input data.

        y : None
            Ignored.

        Returns
        -------
        self : object
            Returns self.

        """
        self._validate_params(self.sampling_type)

        self._n_features = len(X.columns)
        self._is_fitted = True
        return self

    def transform(self, X, y=None):
        """Resample X according to the 'sampling_type'.

        Parameters
        ----------
        X : DataFrame, shape (n_samples, n_features)
            Input data.

        y : None
            There is no need of a target in a transformer, yet the pipeline API
            requires this parameter.

        Returns
        -------
        X_transformed : ndarray, shape (n_samples_new, n_features)
            The resampled array. ``n_samples_new`` depends on
            ``sampling_period`` if ``sampling_type`` is 'periodic' or on the
            number of ``sampling_times`` if ``sampling_type`` is 'fixed'.

        """
        # Check if fit had been called
        check_is_fitted(self, ['_is_fitted'])

        if self.sampling_type == 'periodic':
            X = X.resample(self.sampling_period).first()
        elif self.sampling_type == 'fixed':
            X = X.iloc[np.isin(X.index.time, self.sampling_times)].copy()

        if self.remove_weekends:
            X = X[:][X.index.dayofweek < 5]

        X_transformed = X.iloc[:, 0].values.reshape((-1, self._n_features))
        return X_transformed


class Stationarizer(BaseEstimator, TransformerMixin):
    # FIXME: (doc) transformer output type
    """Data sampling transformer that returns a stationarized Pandas
    dataframe with a datetime index.

    Parameters
    ----------
    stationarization_type : str, default: 'return'
        The type of stationarization technique with which to stationarize
        the time series. It can have two values:

        - 'return':
            This option transforms the time series :math:`{X_t}_t` into the
            time series of relative returns, i.e. the ratio :math:`(X_t-X_{
            t-1})/X_t`.

        - 'log-return':
            This option transforms the time series :math:`{X_t}_t` into the
            time series of relative log-returns, i.e. :math:`\\log(X_t/X_{
            t-1})`.

    Examples
    --------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> from giotto.time_series import Stationarizer
    >>> # Create a noisy signal sampled
    >>> signal = np.asarray([np.sin(x /40) - 0.5 + np.random.random()
    >>> for x in range(0, 300)]).reshape(-1, 1)
    >>> # Initialize the stationarizer
    >>> stationarizer = Stationarizer(stationarization_type='return')
    >>> stationarizer.fit(signal)
    >>> signal_stationarized = stationarizer.transform(signal)
    >>> plt.plot(signal_stationarized)

    """
    valid_stationarization_types = ['return', 'log-return']

    def __init__(self, stationarization_type='return'):
        self.stationarization_type = stationarization_type

    def get_params(self, deep=True):
        """Get parameters for this estimator.

        Parameters
        ----------
        deep : boolean, optional, default: True
            Behaviour not yet implemented.

        Returns
        -------
        params : mapping of string to any
            Parameter names mapped to their values.
        """
        return {'stationarization_type': self.stationarization_type}

    @staticmethod
    def _validate_params(stationarization_type):
        """A class method that checks whether the hyperparameters and the
        input parameters of the :meth:`fit` are valid.

        """
        if stationarization_type not in \
                Stationarizer.valid_stationarization_types:
            raise ValueError(
                'The transformation type %s is not supported' %
                stationarization_type)

    def fit(self, X, y=None):
        """Do nothing and return the estimator unchanged.

        This method is just there to implement the usual API and hence
        work in pipelines.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)
            Input data.

        y : None
            Ignored.

        Returns
        -------
        self : object
            Returns self.

        """
        self._validate_params(self.stationarization_type)

        self._is_fitted = True
        return self

    def transform(self, X, y=None):
        """Stationarize X according to ``stationarization_type``.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)
            Input data.

        y : None
            There is no need of a target in a transformer, yet the pipeline API
            requires this parameter.

        Returns
        -------
        X_transformed : ndarray, shape (n_samples - 1, n_features)
            The array containing the stationarized inputs.

        """
        # Check if fit had been called
        check_is_fitted(self, ['_is_fitted'])

        X_transformed = X
        if 'return' in self.stationarization_type:
            X_transformed = np.diff(X_transformed, n=1,
                                    axis=0) / X_transformed[1:, :]

        if 'log' in self.stationarization_type:
            X_transformed = np.log(X_transformed)

        return X_transformed

#!/usr/bin/env python
from kaggle_dataset_cifar import kaggle_cifar10
from pylearn2.utils import serial
from pylearn2.datasets import preprocessing
from theano import tensor as T
from theano import function
import numpy as np


def process(mdl, ds, batch_size=100):
    # This batch size must be evenly divisible into number of total samples!
    mdl.set_batch_size(batch_size)
    X = mdl.get_input_space().make_batch_theano()
    Y = mdl.fprop(X)
    y = T.argmax(Y, axis=1)
    f = function([X], y)
    yhat = []
    for i in xrange(ds.X.shape[0] / batch_size):
        x_arg = ds.X[i * batch_size:(i + 1) * batch_size, :]
        x_arg = ds.get_topological_view(x_arg)
        yhat.append(f(x_arg))
    return np.array(yhat)

preprocessor = preprocessing.ZCA()
ds = kaggle_cifar10(one_hot=True,
                    axes=('c', 0, 1, 'b'))
ds.apply_preprocessor(preprocessor=preprocessor, can_fit=True)
mdl = serial.load('cifar10_maxout_zca.pkl')
yhat = process(mdl, ds)
print yhat
print "Train(%): ", (ds.y.argmax(axis=1).reshape(yhat.shape) == yhat).mean()
#!/usr/bin/env python
from pylearn2.models import mlp, maxout
from pylearn2.costs.mlp.dropout import Dropout
from pylearn2.training_algorithms import sgd, learning_rule
from pylearn2.termination_criteria import EpochCounter
from pylearn2.datasets import cifar10
from kaggle_dataset import kaggle_cifar10
from pylearn2.datasets.preprocessing import Pipeline, ZCA
from pylearn2.datasets.preprocessing import GlobalContrastNormalization
from pylearn2.space import Conv2DSpace
from pylearn2.train import Train
from pylearn2.train_extensions import best_params, window_flip
from pylearn2.utils import serial

trn = kaggle_cifar10('train',
                     one_hot=True,
                     datapath='/home/kkastner/kaggle_data/kaggle-cifar10',
                     max_count=40000,
                     axes=('c', 0, 1, 'b'))

tst = cifar10.CIFAR10('test',
                      toronto_prepro=False,
                      one_hot=True,
                      axes=('c', 0, 1, 'b'))

in_space = Conv2DSpace(shape=(32, 32),
                       num_channels=3,
                       axes=('c', 0, 1, 'b'))

l1 = maxout.MaxoutConvC01B(layer_name='l1',
                           pad=4,
                           tied_b=1,
                           W_lr_scale=.05,
                           b_lr_scale=.05,
                           num_channels=96,
                           num_pieces=2,
                           kernel_shape=(8, 8),
                           pool_shape=(4, 4),
                           pool_stride=(2, 2),
                           irange=.005,
                           max_kernel_norm=.9,
                           partial_sum=33)

l2 = maxout.MaxoutConvC01B(layer_name='l2',
                           pad=3,
                           tied_b=1,
                           W_lr_scale=.05,
                           b_lr_scale=.05,
                           num_channels=192,
                           num_pieces=2,
                           kernel_shape=(8, 8),
                           pool_shape=(4, 4),
                           pool_stride=(2, 2),
                           irange=.005,
                           max_kernel_norm=1.9365,
                           partial_sum=15)

l3 = maxout.MaxoutConvC01B(layer_name='l3',
                           pad=3,
                           tied_b=1,
                           W_lr_scale=.05,
                           b_lr_scale=.05,
                           num_channels=192,
                           num_pieces=2,
                           kernel_shape=(5, 5),
                           pool_shape=(2, 2),
                           pool_stride=(2, 2),
                           irange=.005,
                           max_kernel_norm=1.9365)

l4 = maxout.Maxout(layer_name='l4',
                   irange=.005,
                   num_units=500,
                   num_pieces=5,
                   max_col_norm=1.9)

output = mlp.Softmax(layer_name='y',
                     n_classes=10,
                     irange=.005,
                     max_col_norm=1.9365)

layers = [l1, l2, l3, l4, output]

mdl = mlp.MLP(layers,
              input_space=in_space)

trainer = sgd.SGD(learning_rate=.17,
                  batch_size=128,
                  learning_rule=learning_rule.Momentum(.5),
                  # Remember, default dropout is .5
                  cost=Dropout(input_include_probs={'l1': .8},
                               input_scales={'l1': 1.}),
                  termination_criterion=EpochCounter(max_epochs=475),
                  monitoring_dataset={'valid': tst,
                                      'train': trn})

preprocessor = Pipeline([GlobalContrastNormalization(scale=55.), ZCA()])
trn.apply_preprocessor(preprocessor=preprocessor, can_fit=True)
tst.apply_preprocessor(preprocessor=preprocessor, can_fit=False)
serial.save('kaggle_cifar10_preprocessor.pkl', preprocessor)

watcher = best_params.MonitorBasedSaveBest(
    channel_name='valid_y_misclass',
    save_path='kaggle_cifar10_maxout_zca.pkl')

velocity = learning_rule.MomentumAdjustor(final_momentum=.65,
                                          start=1,
                                          saturate=250)

decay = sgd.LinearDecayOverEpoch(start=1,
                                 saturate=500,
                                 decay_factor=.01)

win = window_flip.WindowAndFlipC01B(pad_randomized=8,
                                    window_shape=(32, 32),
                                    randomize=[trn],
                                    center=[tst])

experiment = Train(dataset=trn,
                   model=mdl,
                   algorithm=trainer,
                   extensions=[watcher, velocity, decay, win])

experiment.main_loop()

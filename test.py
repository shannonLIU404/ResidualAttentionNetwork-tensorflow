import tensorflow as tf
import keras
from keras.datasets import cifar10
from keras.datasets import cifar100
import Attention as net
import numpy as np
import sys
from keras.preprocessing.image import ImageDataGenerator
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

device_name = tf.test.gpu_device_name()
if device_name is not '':
    print('Found GPU Device!')
else:
    print('Found GPU Device Failed!')

config = {
    'init_conv_filters': 64,
    'init_conv_kernel_size': 3,
    'init_conv_strides': 1,
    'init_pooling_pool_size': 3,
    'init_pooling_strides': 2,

    # downsampling times of first attention
    'first_attention_downsampling_times': 3,

    # hyperparameters 'p', 't', 'r' in paper
    'ptr': [1, 2, 1],

    # number of attention module in [stage1 stage2 stage3]
    'attention_module_list': [1, 1, 1]
}

mean = np.array([123.68, 116.779, 103.979]).reshape((1, 1, 1, 3))
data_shape = (32, 32, 3)
num_train = 50000
num_test = 10000
num_classes = 10
train_batch_size = 64
test_batch_size = 200
epochs = 310
weight_decay = 1e-4
lr = 0.1

(x_train, y_train), (x_test, y_test) = cifar10.load_data()
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)
train_gen = ImageDataGenerator(
    horizontal_flip=True,
    width_shift_range=0.1,
    height_shift_range=0.1,
    shear_range=0.1,
    zoom_range=0.1,
).flow(x_train, y_train, batch_size=train_batch_size)
test_gen = ImageDataGenerator().flow(x_test, y_test, batch_size=test_batch_size)

reduce_lr_epoch = [123, 185]
testnet = net.Attention(config, data_shape, num_classes, weight_decay, 'channels_last')
for epoch in range(epochs):
    print('-'*20, 'epoch', epoch, '-'*20)
    train_acc = []
    train_loss = []
    test_acc = []
    # reduce learning rate
    if epoch in reduce_lr_epoch:
        lr = lr * 0.1
        print('reduce learning rate =', lr, 'now')
    # train one epoch
    for iter in range(num_train//train_batch_size):
        # get and preprocess image
        images, labels = train_gen.next()
        images = images - mean
        # train_one_batch also can accept your own session
        loss, acc = testnet.train_one_batch(images, labels, lr)
        train_acc.append(acc)
        train_loss.append(loss)
        sys.stdout.write("\r>> train "+str(iter+1)+'/'+str(num_train//train_batch_size)+' loss '+str(loss)+' acc '+str(acc))
    mean_train_loss = np.mean(train_loss)
    mean_train_acc = np.mean(train_acc)
    sys.stdout.write("\n")
    print('>> epoch', epoch, 'train mean loss', mean_train_acc, 'train mean acc', mean_train_acc)

    # validate one epoch
    for iter in range(num_test//test_batch_size):
        # get and preprocess image
        images, labels = test_gen.next()
        images = images - mean
        # validate_one_batch also can accept your own session
        logit, acc = testnet.validate_one_batch(images, labels)
        test_acc.append(acc)
        sys.stdout.write("\r>> test "+str(iter+1)+'/'+str(num_test//test_batch_size)+' acc '+str(acc))
    mean_val_acc = np.mean(test_acc)
    sys.stdout.write("\n")
    print('>> epoch', epoch, ' test mean acc', mean_val_acc)

    # logit = testnet.test(images)
    # testnet.save_weight(self, mode, path, sess=None)
    # testnet.load_weight(self, mode, path, sess=None)



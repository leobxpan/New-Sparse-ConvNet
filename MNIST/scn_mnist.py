# This script constructs a Sparse ConvNet and runs on the MNIST dataset
# Written by Caesar

##################################################################################################################################################################
#
#                                                                   Import Section
#
##################################################################################################################################################################

import pdb
import tensorflow as tf
import numpy as np
from scipy import ndimage
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.contrib.learn.python.learn.datasets.mnist import DataSet

##################################################################################################################################################################
#
#                                                                   Function Definition Section
#
##################################################################################################################################################################

def weight_variable(shape):
    initial = tf.random_normal(shape, dtype=tf.float32, stddev=0.05)
    return tf.Variable(initial)

def bias_variable(shape):
    initial = tf.constant(0, dtype=tf.float32, shape=shape)
    return tf.Variable(initial)

def conv2d(x, W):
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

def max_pool_2x2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')

def enlarge_train_set_by_shift(origin_train_img, origin_train_label, bottom, ceil, bg_value=0, times=1):

    """
    This function enlarges the training dataset through shifting.
    origin_train_set: the training set before enlargement
    bottom: the lower bound of the range from which the shifting distance is generated
    ceil: the upper bound of the range from which the shifting distance is generated
    bg_value: filled background value, default is 0 (blank space)
    times: the times that the training set is enlarged, or the number of shifting actions applied.
    """

    expanded_images = []
    expanded_labels = []

    j = 0                                                                           # Counter
    for x, y in zip(origin_train_img, origin_train_label):
        j = j + 1
        if j % 100 == 0:
            print ('expanding data : %03d / %03d' % (j, np.size(origin_train_img,0)))

        # First append original data
        expanded_images.append(x)
        expanded_labels.append(y)

        # Reshape image from 784 to 28*28
        image = np.reshape(x, (-1, 28))

        for i in range(times):
            # Shift the image with random distance
            shift = np.random.randint(bottom, ceil, 2)                              # Generate 2 numbers for the 2 axes separately
            new_img = ndimage.shift(image, shift, cval=bg_value)

            # Append new training data
            expanded_images.append(np.reshape(new_img, 784))                        # Reshape back to 784
            expanded_labels.append(y)
    
    # Images and labels are concatenated then shuffled
    expanded_train_ndarray = np.concatenate((expanded_images, expanded_labels), axis=1)
    np.random.shuffle(expanded_train_ndarray)                                       # Note this function is in-place so the set doesn't need to be explicitly assigned the new value

    return expanded_train_ndarray

##################################################################################################################################################################
#
#                                                                   Command Section
#
##################################################################################################################################################################

# Read in dataset
print("Loading dataset...")
mnist = input_data.read_data_sets('MNIST_data', one_hot=True)
print("Dataset has been loaded.")

# Training data augmentation
print("Augmenting training set...")
expanded_train_ndarray = enlarge_train_set_by_shift(mnist.train.images, mnist.train.labels, -2, 2)

expanded_train_images = expanded_train_ndarray[:, :784].reshape([expanded_train_ndarray.shape[0], 28, 28, 1])
expanded_train_labels = expanded_train_ndarray[:, 784:794]
expanded_train_set = DataSet(expanded_train_images, expanded_train_labels)
print("Training set has been augmented.")

# Real data
x = tf.placeholder(tf.float32, shape=[None, 784])
y_ = tf.placeholder(tf.float32, shape=[None, 10])

### Construct the network
# First layer pair (1 layer pair = 1 conv layer + (dropout) + 1 pooling layer)
W_conv1 = weight_variable([3, 3, 1, 60])
b_conv1 = bias_variable([60])

x_image = tf.reshape(x, [-1, 28, 28, 1])

h_conv1 = tf.nn.leaky_relu(conv2d(x_image, W_conv1) + b_conv1, alpha=0.33)
h_pool1 = max_pool_2x2(h_conv1)

# Second layer pair
W_conv2 = weight_variable([2, 2, 60, 120])
b_conv2 = bias_variable([120])

h_conv2 = tf.nn.leaky_relu(conv2d(h_pool1, W_conv2) + b_conv2, alpha=0.33)
h_pool2 = max_pool_2x2(h_conv2)

# Third layer pair
W_conv3 = weight_variable([2, 2, 120, 180])
b_conv3 = bias_variable([180])

h_conv3 = tf.nn.leaky_relu(conv2d(h_pool2, W_conv3) + b_conv3, alpha=0.33)
keep_prob3 = tf.placeholder(tf.float32)
h_conv3_drop = tf.nn.dropout(h_conv3, keep_prob3)
h_pool3 = max_pool_2x2(h_conv3_drop)

# Fourth layer pair
W_conv4 = weight_variable([2, 2, 180, 240])
b_conv4 = bias_variable([240])

h_conv4 = tf.nn.leaky_relu(conv2d(h_pool3, W_conv4) + b_conv4, alpha=0.33)
keep_prob4 = tf.placeholder(tf.float32)
h_conv4_drop = tf.nn.dropout(h_conv4, keep_prob4)
h_pool4 = max_pool_2x2(h_conv4_drop)

# Fifth layer pair
W_conv5 = weight_variable([2, 2, 240, 300])
b_conv5 = bias_variable([300])

h_conv5 = tf.nn.leaky_relu(conv2d(h_pool4, W_conv5) + b_conv5, alpha=0.33)
keep_prob5 = tf.placeholder(tf.float32)
h_conv5_drop = tf.nn.dropout(h_conv5, keep_prob5)
h_pool5 = max_pool_2x2(h_conv5_drop)

# Sixth conv layer
W_conv6 = weight_variable([2, 2, 300, 360])
b_conv6 = bias_variable([360])

h_conv6 = tf.nn.leaky_relu(conv2d(h_pool5, W_conv6) + b_conv6, alpha=0.33)
keep_prob6 = tf.placeholder(tf.float32)
h_conv6_drop = tf.nn.dropout(h_conv6, keep_prob6)
h_conv6_flat = tf.reshape(h_conv6_drop, [-1, 1*1*360])

# Softmax classification layer
W_sm = weight_variable([1*1*360, 10])
b_sm = bias_variable([10])

y_conv = tf.matmul(h_conv6_flat, W_sm) + b_sm
cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y_conv))

## Training step configuration
learning_rate = tf.placeholder(tf.float32, shape=[])
train_step = tf.train.MomentumOptimizer(learning_rate=learning_rate, momentum=0.99).minimize(cross_entropy)  # lr = 0.003*exp(-0.01*epoch)

# Accuracy definition
correct_prediction = tf.equal(tf.argmax(y_conv,1), tf.argmax(y_,1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

# Training
print("Training...")
sess = tf.Session()
sess.run(tf.global_variables_initializer())
for i in range(110000):                                                              # Run 200 epochs
    batch = mnist.train.next_batch(100)                                       # 20000 * 50 != 55000 * n?
    if i % 100 == 0:
        train_accuracy = accuracy.eval(session=sess, feed_dict={x: batch[0], y_: batch[1], keep_prob3: 1.0, keep_prob4: 1.0, keep_prob5: 1.0, keep_prob6: 1.0})
        print("step %d, training accuracy %g" % (i, train_accuracy))
    train_step.run(session=sess, feed_dict={x: batch[0], y_: batch[1], learning_rate: 0.003 * np.exp(-0.01*(i/550+1)), keep_prob3: 0.5, keep_prob4: 0.5, keep_prob5: 0.5, keep_prob6: 0.5})
print("Training finished.")

# Test accuracy computation
print("test accuracy %g" % accuracy.eval(session=sess, feed_dict={x: mnist.test.images, y_: mnist.test.labels, keep_prob3: 1.0, keep_prob4: 1.0, keep_prob5: 1.0, keep_prob6: 1.0}))


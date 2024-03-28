'''Module containing model implementation'''

from pathlib import Path

import cv2
import numpy as np

from keras import backend as tfback

from keras.layers import Conv2D, ZeroPadding2D, Activation, Input, concatenate
from keras.models import Model
from keras.layers import BatchNormalization
from keras.layers import MaxPooling2D, AveragePooling2D
from keras.layers import Lambda, Flatten, Dense

tfback.set_image_data_format('channels_first')


def conv2d_bn(x, layer_name, filters, kernel_size=(1, 1), strides=(1, 1), i='', epsilon=0.00001):
    '''2D Convolutional Block with Batch normalization and ReLU activation.

    Args:
        x (tf.Tensor): Input tensor.
        layer_name (str): Name of layer.
        filters (int): Number of filters to apply in 1st convolutional operation.
        kernel_size (Tuple[int, int]): Kernel size of filter to apply.
        strides (Tuple[int, int]): Strides of filter.
        i (str): index to append layer name, eg. 2 for conv2.
        epsilon (float): epsilon for batch normalization

    Returns:
        tensor (tf.Tensor): Tensor with graph applied.
    '''
    if layer_name:
        conv_name = f'{layer_name}_conv{i}'
        bn_name = f'{layer_name}_bn{i}'
    else:
        conv_name = f'conv{i}'
        bn_name = f'bn{i}'
    tensor = Conv2D(
        filters, kernel_size, strides=strides, data_format='channels_first', name=conv_name
    )(x)
    tensor = BatchNormalization(axis=1, epsilon=epsilon, name=bn_name)(tensor)
    tensor = Activation('relu')(tensor)
    return tensor


def inception_block_4a(X):
    # 3x3 Block
    X_3x3 = conv2d_bn(X, 'inception_4a_3x3', 96, i='1')
    X_3x3 = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_3x3)
    X_3x3 = conv2d_bn(X_3x3, 'inception_4a_3x3', 128, kernel_size=(3, 3), i='2')

    # 5x5 Block
    X_5x5 = conv2d_bn(X, 'inception_4a_5x5', 16, i='1')
    X_5x5 = ZeroPadding2D(padding=(2, 2), data_format='channels_first')(X_5x5)
    X_5x5 = conv2d_bn(X_5x5, 'inception_4a_5x5', 32, kernel_size=(5, 5), i='2')

    # Max Pooling Block
    X_pool = MaxPooling2D(pool_size=3, strides=2, data_format='channels_first')(X)
    X_pool = conv2d_bn(X_pool, 'inception_4a_pool', 32)
    X_pool = ZeroPadding2D(padding=((3, 4), (3, 4)), data_format='channels_first')(X_pool)

    # 1x1 Block
    X_1x1 = conv2d_bn(X, 'inception_4a_1x1', 64)

    return concatenate([X_3x3, X_5x5, X_pool, X_1x1], axis=1)


def inception_block_4b(X):
    # 3x3 Block
    X_3x3 = conv2d_bn(X, 'inception_4b_3x3', 96, i='1')
    X_3x3 = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_3x3)
    X_3x3 = conv2d_bn(X_3x3, 'inception_4b_3x3', 128, kernel_size=(3, 3), i='2')

    # 5x5 Block
    X_5x5 = conv2d_bn(X, 'inception_4b_5x5', 32, i='1')
    X_5x5 = ZeroPadding2D(padding=(2, 2), data_format='channels_first')(X_5x5)
    X_5x5 = conv2d_bn(X_5x5, 'inception_4b_5x5', 64, kernel_size=(5, 5), i='2')

    # Average Pooling Block
    X_pool = AveragePooling2D(pool_size=(3, 3), strides=(3, 3), data_format='channels_first')(X)
    X_pool = conv2d_bn(X_pool, 'inception_4b_pool', 64)
    X_pool = ZeroPadding2D(padding=(4, 4), data_format='channels_first')(X_pool)

    # 1x1 Block
    X_1x1 = conv2d_bn(X, 'inception_4b_1x1', 64)

    return concatenate([X_3x3, X_5x5, X_pool, X_1x1], axis=1)


def inception_block_4c(X):
    # 3x3 Block
    X_3x3 = conv2d_bn(X, 'inception_4c_3x3', 128, i='1')
    X_3x3 = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_3x3)
    X_3x3 = conv2d_bn(X_3x3, 'inception_4c_3x3', 256, kernel_size=(3, 3), strides=(2, 2), i='2')

    # 5x5 Block
    X_5x5 = conv2d_bn(X, 'inception_4c_5x5', 32, i='1')
    X_5x5 = ZeroPadding2D(padding=(2, 2), data_format='channels_first')(X_5x5)
    X_5x5 = conv2d_bn(X_5x5, 'inception_4c_5x5', 64, kernel_size=(5, 5), strides=(2, 2), i='2')

    # Max Pooling Block
    X_pool = MaxPooling2D(pool_size=3, strides=2, data_format='channels_first')(X)
    X_pool = ZeroPadding2D(padding=((0, 1), (0, 1)), data_format='channels_first')(X_pool)

    return concatenate([X_3x3, X_5x5, X_pool], axis=1)


def inception_block_5a(X):
    # 3x3 Block
    X_3x3 = conv2d_bn(X, 'inception_5a_3x3', 96, i='1')
    X_3x3 = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_3x3)
    X_3x3 = conv2d_bn(X_3x3, 'inception_5a_3x3', 192, kernel_size=(3, 3), i='2')

    # 5x5 Block
    X_5x5 = conv2d_bn(X, 'inception_5a_5x5', 32, i='1')
    X_5x5 = ZeroPadding2D(padding=(2, 2), data_format='channels_first')(X_5x5)
    X_5x5 = conv2d_bn(X_5x5, 'inception_5a_5x5', 64, kernel_size=(5, 5), i='2')

    # Average Pooling Block
    X_pool = AveragePooling2D(pool_size=(3, 3), strides=(3, 3), data_format='channels_first')(X)
    X_pool = conv2d_bn(X_pool, 'inception_5a_pool', 128)
    X_pool = ZeroPadding2D(padding=(2, 2), data_format='channels_first')(X_pool)

    # 1x1 Block
    X_1x1 = conv2d_bn(X, 'inception_5a_1x1', 256)

    return concatenate([X_3x3, X_5x5, X_pool, X_1x1], axis=1)


def inception_block_5b(X):
    # 3x3 Block
    X_3x3 = conv2d_bn(X, 'inception_5b_3x3', 160, i='1')
    X_3x3 = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_3x3)
    X_3x3 = conv2d_bn(X_3x3, 'inception_5b_3x3', 256, kernel_size=(3, 3), strides=(2, 2), i='2')

    # 5x5 Block
    X_5x5 = conv2d_bn(X, 'inception_5b_5x5', 64, i='1')
    X_5x5 = ZeroPadding2D(padding=(2, 2), data_format='channels_first')(X_5x5)
    X_5x5 = conv2d_bn(X_5x5, 'inception_5b_5x5', 128, kernel_size=(5, 5), strides=(2, 2), i='2')

    # Max Pooling Block
    X_pool = MaxPooling2D(pool_size=3, strides=2, data_format='channels_first')(X)
    X_pool = ZeroPadding2D(padding=((0, 1), (0, 1)), data_format='channels_first')(X_pool)

    return concatenate([X_3x3, X_5x5, X_pool], axis=1)


def inception_block_6a(X):
    # 3x3 Block
    X_3x3 = conv2d_bn(X, 'inception_6a_3x3', 96, i='1')
    X_3x3 = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_3x3)
    X_3x3 = conv2d_bn(X_3x3, 'inception_6a_3x3', 384, kernel_size=(3, 3), i='2')

    # Average Pooling Block
    X_pool = AveragePooling2D(pool_size=(3, 3), strides=(3, 3), data_format='channels_first')(X)
    X_pool = conv2d_bn(X_pool, 'inception_6a_pool', 96)
    X_pool = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_pool)

    # 1x1 Block
    X_1x1 = conv2d_bn(X, 'inception_6a_1x1', 256)

    return concatenate([X_3x3, X_pool, X_1x1], axis=1)


def inception_block_6b(X):
    # 3x3 Block
    X_3x3 = conv2d_bn(X, 'inception_6b_3x3', 96, i='1')
    X_3x3 = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_3x3)
    X_3x3 = conv2d_bn(X_3x3, 'inception_6b_3x3', 384, kernel_size=(3, 3), i='2')

    # Max Pooling Block
    X_pool = MaxPooling2D(pool_size=3, strides=2, data_format='channels_first')(X)
    X_pool = conv2d_bn(X_pool, 'inception_6b_pool', 96)
    X_pool = ZeroPadding2D(padding=(1, 1), data_format='channels_first')(X_pool)

    # 1x1 Block
    X_1x1 = conv2d_bn(X, 'inception_6b_1x1', 256)

    return concatenate([X_3x3, X_pool, X_1x1], axis=1)


def facenet_model(input_shape):
    '''Implementation of the Inception model used for FaceNet.

    Arguments:
    input_shape (Tuple[int]): Shape of the images of the dataset.

    Returns:
    model (keras.models.Model): FaceNet model.
    '''

    # Define the input as a tensor with shape input_shape
    X_input = Input(input_shape)

    # Zero-Padding
    X = ZeroPadding2D((3, 3))(X_input)

    # First Block
    X = conv2d_bn(X, '', 64, kernel_size=(7, 7), strides=(2, 2), i='1', epsilon=0.001)

    # Zero-Padding + MAXPOOL
    X = ZeroPadding2D((1, 1))(X)
    X = MaxPooling2D((3, 3), strides=2)(X)

    # Second Block
    X = conv2d_bn(X, '', 64, i='2')

    # Zero-Padding + MAXPOOL
    X = ZeroPadding2D((1, 1))(X)

    # Third Block
    X = conv2d_bn(X, '', 192, kernel_size=(3, 3), i='3')

    # Zero-Padding + MAXPOOL
    X = ZeroPadding2D((1, 1))(X)
    X = MaxPooling2D(pool_size=3, strides=2)(X)

    # Fourth Block (Inception)
    X = inception_block_4a(X)
    X = inception_block_4b(X)
    X = inception_block_4c(X)

    # Fifth Block (Inception)
    X = inception_block_5a(X)
    X = inception_block_5b(X)

    # Sixth Block (Inception)
    X = inception_block_6a(X)
    X = inception_block_6b(X)

    # Top layer
    X = AveragePooling2D(pool_size=(3, 3), strides=(1, 1), data_format='channels_first')(X)
    X = Flatten()(X)
    X = Dense(128, name='dense')(X)

    # L2 normalization
    X = Lambda(lambda x: tfback.l2_normalize(x, axis=1))(X)

    # Create model instance
    model = Model(inputs=X_input, outputs=X, name='FaceNetModel')

    weight_fpath = Path(__file__).parent.joinpath('weights', 'facenet_weights.h5')
    model.load_weights(weight_fpath)

    return model


def img_to_encoding(image, model):
    '''Calculates encoding from the image data'''
    # Resize for model
    resized = cv2.resize(image, (96, 96))
    # Swap channel dimensions
    input_img = resized[..., ::-1]
    # Switch to channels first and round to specific precision.
    input_img = np.around(np.divide(np.transpose(input_img, (2, 0, 1)), 255.0), decimals=12)
    x_train = np.array([input_img])
    embedding = model.predict_on_batch(x_train)
    return embedding

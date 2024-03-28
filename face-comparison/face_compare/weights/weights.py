import numpy as np
from pathlib import Path


WEIGHTS = [
  'conv1', 'bn1', 'conv2', 'bn2', 'conv3', 'bn3',
  'inception_3a_1x1_conv', 'inception_3a_1x1_bn',
  'inception_3a_pool_conv', 'inception_3a_pool_bn',
  'inception_3a_5x5_conv1', 'inception_3a_5x5_conv2', 'inception_3a_5x5_bn1', 'inception_3a_5x5_bn2',
  'inception_3a_3x3_conv1', 'inception_3a_3x3_conv2', 'inception_3a_3x3_bn1', 'inception_3a_3x3_bn2',
  'inception_3b_3x3_conv1', 'inception_3b_3x3_conv2', 'inception_3b_3x3_bn1', 'inception_3b_3x3_bn2',
  'inception_3b_5x5_conv1', 'inception_3b_5x5_conv2', 'inception_3b_5x5_bn1', 'inception_3b_5x5_bn2',
  'inception_3b_pool_conv', 'inception_3b_pool_bn',
  'inception_3b_1x1_conv', 'inception_3b_1x1_bn',
  'inception_3c_3x3_conv1', 'inception_3c_3x3_conv2', 'inception_3c_3x3_bn1', 'inception_3c_3x3_bn2',
  'inception_3c_5x5_conv1', 'inception_3c_5x5_conv2', 'inception_3c_5x5_bn1', 'inception_3c_5x5_bn2',
  'inception_4a_3x3_conv1', 'inception_4a_3x3_conv2', 'inception_4a_3x3_bn1', 'inception_4a_3x3_bn2',
  'inception_4a_5x5_conv1', 'inception_4a_5x5_conv2', 'inception_4a_5x5_bn1', 'inception_4a_5x5_bn2',
  'inception_4a_pool_conv', 'inception_4a_pool_bn',
  'inception_4a_1x1_conv', 'inception_4a_1x1_bn',
  'inception_4e_3x3_conv1', 'inception_4e_3x3_conv2', 'inception_4e_3x3_bn1', 'inception_4e_3x3_bn2',
  'inception_4e_5x5_conv1', 'inception_4e_5x5_conv2', 'inception_4e_5x5_bn1', 'inception_4e_5x5_bn2',
  'inception_5a_3x3_conv1', 'inception_5a_3x3_conv2', 'inception_5a_3x3_bn1', 'inception_5a_3x3_bn2',
  'inception_5a_pool_conv', 'inception_5a_pool_bn',
  'inception_5a_1x1_conv', 'inception_5a_1x1_bn',
  'inception_5b_3x3_conv1', 'inception_5b_3x3_conv2', 'inception_5b_3x3_bn1', 'inception_5b_3x3_bn2',
  'inception_5b_pool_conv', 'inception_5b_pool_bn',
  'inception_5b_1x1_conv', 'inception_5b_1x1_bn',
  'dense'
]

SHAPES = {
  'conv1': [64, 3, 7, 7],
  'conv2': [64, 64, 1, 1],
  'conv3': [192, 64, 3, 3],
  'inception_3a_1x1_conv': [64, 192, 1, 1],
  'inception_3a_pool_conv': [32, 192, 1, 1],
  'inception_3a_5x5_conv1': [16, 192, 1, 1],
  'inception_3a_5x5_conv2': [32, 16, 5, 5],
  'inception_3a_3x3_conv1': [96, 192, 1, 1],
  'inception_3a_3x3_conv2': [128, 96, 3, 3],
  'inception_3b_3x3_conv1': [96, 256, 1, 1],
  'inception_3b_3x3_conv2': [128, 96, 3, 3],
  'inception_3b_5x5_conv1': [32, 256, 1, 1],
  'inception_3b_5x5_conv2': [64, 32, 5, 5],
  'inception_3b_pool_conv': [64, 256, 1, 1],
  'inception_3b_1x1_conv': [64, 256, 1, 1],
  'inception_3c_3x3_conv1': [128, 320, 1, 1],
  'inception_3c_3x3_conv2': [256, 128, 3, 3],
  'inception_3c_5x5_conv1': [32, 320, 1, 1],
  'inception_3c_5x5_conv2': [64, 32, 5, 5],
  'inception_4a_3x3_conv1': [96, 640, 1, 1],
  'inception_4a_3x3_conv2': [192, 96, 3, 3],
  'inception_4a_5x5_conv1': [32, 640, 1, 1,],
  'inception_4a_5x5_conv2': [64, 32, 5, 5],
  'inception_4a_pool_conv': [128, 640, 1, 1],
  'inception_4a_1x1_conv': [256, 640, 1, 1],
  'inception_4e_3x3_conv1': [160, 640, 1, 1],
  'inception_4e_3x3_conv2': [256, 160, 3, 3],
  'inception_4e_5x5_conv1': [64, 640, 1, 1],
  'inception_4e_5x5_conv2': [128, 64, 5, 5],
  'inception_5a_3x3_conv1': [96, 1024, 1, 1],
  'inception_5a_3x3_conv2': [384, 96, 3, 3],
  'inception_5a_pool_conv': [96, 1024, 1, 1],
  'inception_5a_1x1_conv': [256, 1024, 1, 1],
  'inception_5b_3x3_conv1': [96, 736, 1, 1],
  'inception_5b_3x3_conv2': [384, 96, 3, 3],
  'inception_5b_pool_conv': [96, 736, 1, 1],
  'inception_5b_1x1_conv': [256, 736, 1, 1],
  'dense': (128, 736)
}

def load_weights(model):
    '''Loads weights to given FaceNet model

    Args:
        model (keras.models.Models): FaceNet model.
    '''

    weights_dir = Path(__file__).parent.joinpath('weights')

    for layer_name in WEIGHTS:
        print(f'loading layer {layer_name}')
        if 'conv' in layer_name:
            model.get_layer(layer_name).set_weights(get_conv_weights(weights_dir, layer_name))
        elif 'bn' in layer_name:
            model.get_layer(layer_name).set_weights(get_batch_norm_weights(weights_dir, layer_name))
        elif 'dense' in layer_name:
            model.get_layer(layer_name).set_weights(get_dense_weights(weights_dir, layer_name))


def get_conv_weights(weights_dir, layer_name):
    '''Loads convolutional layer's weights and biases
        given the root weight directory, and the layer name.
    '''
    weight_path = weights_dir.joinpath(f'{layer_name}_w.csv')
    conv_weight = np.genfromtxt(weight_path, delimiter=',', dtype=None)
    conv_weight = np.reshape(conv_weight, SHAPES[layer_name])
    conv_weight = np.transpose(conv_weight, (2, 3, 1, 0))

    bias_path = weights_dir.joinpath(f'{layer_name}_b.csv')
    conv_bias = np.genfromtxt(bias_path, delimiter=',', dtype=None)

    return [conv_weight, conv_bias]

def get_batch_norm_weights(weights_dir, layer_name):
    '''Loads batch normalization weights from file'''
    bn_weight = np.genfromtxt(
        weights_dir.joinpath(f'{layer_name}_w.csv'), delimiter=',', dtype=None
    )
    bn_bias = np.genfromtxt(
        weights_dir.joinpath(f'{layer_name}_b.csv'), delimiter=',', dtype=None
    )
    bn_mean = np.genfromtxt(
        weights_dir.joinpath(f'{layer_name}_m.csv'), delimiter=',', dtype=None
    )
    bn_var = np.genfromtxt(
        weights_dir.joinpath(f'{layer_name}_v.csv'), delimiter=',', dtype=None
    )
    return [bn_weight, bn_bias, bn_mean, bn_var]
    
def get_dense_weights(weights_dir, layer_name):
    '''Loads dense layer weights from file'''
    dense_weight = np.genfromtxt(
        weights_dir.joinpath(f'{layer_name}_w.csv'), delimiter=',', dtype=None
    )
    dense_weight = np.reshape(dense_weight, SHAPES[layer_name])
    dense_weight = np.transpose(dense_weight, (1, 0))
    dense_bias = np.genfromtxt(
        weights_dir.joinpath(f'{layer_name}_b.csv'), delimiter=',', dtype=None
    )
    return [dense_weight, dense_bias]
    
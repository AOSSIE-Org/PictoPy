import tensorflow as tf
import numpy as np

def apply_random_transformations(image, number_of_transformations=2):
    # randomly select two image transformations
    np.random.shuffle(transformations)

    for i in range(number_of_transformations):
        if np.random.random_sample() > 0.5:
            image = transformations[i](image)

    return image

def random_hue(image):
    return tf.image.random_hue(image, max_delta=0.1)

def random_saturation(image):
    return tf.image.random_saturation(image, lower=0.5, upper=1.5)

def random_contrast(image):
    return tf.image.random_contrast(image, lower=0.5, upper=1.5)

def random_brightness(image):
    return tf.image.random_brightness(image, max_delta=32. / 255.)

transformations = np.array([random_contrast, random_brightness, random_saturation, random_hue])

def tf_record_parser(record, to_grayscale=False):
    keys_to_features = {
        "Xi": tf.FixedLenFeature((), tf.string, default_value=""),
        'Xj': tf.FixedLenFeature([], tf.string),
        "label": tf.FixedLenFeature((), tf.int64),
        "height": tf.FixedLenFeature((), tf.int64),
        "width": tf.FixedLenFeature((), tf.int64)
    }

    features = tf.parse_single_example(record, keys_to_features)

    Xi = tf.decode_raw(features['Xi'], tf.uint8)
    Xj = tf.decode_raw(features['Xj'], tf.uint8)

    label = tf.cast(features['label'], tf.int32)
    height = tf.cast(features['height'], tf.int32)
    width = tf.cast(features['width'], tf.int32)

    # reshape input and annotation images
    Xi = tf.reshape(Xi, (height, width, 3), name="image_reshape")
    Xj = tf.reshape(Xj, (height, width, 3), name="annotation_reshape")

    if to_grayscale:
        Xi = tf.image.rgb_to_grayscale(Xi)
        Xj = tf.image.rgb_to_grayscale(Xj)

    return tf.to_float(Xi) / 255., tf.to_float(Xj) / 255., label


def random_resize_and_crop(Xi, Xj, label, crop_size=128):
    input_shape = tf.shape(Xi)[0:2]
    n_channels = tf.shape(Xi)[-1]
    input_shape_float = tf.to_float(input_shape)

    scale = tf.random_uniform(shape=[1],
                              minval=0.9,
                              maxval=1.1)

    scaled_shape = tf.to_int32(tf.round(input_shape_float * scale))

    Xi = tf.image.resize_images(Xi, scaled_shape,
                                method=tf.image.ResizeMethod.BILINEAR)

    Xj = tf.image.resize_images(Xj, scaled_shape,
                                method=tf.image.ResizeMethod.BILINEAR)

    Xi = tf.random_crop(Xi, (crop_size, crop_size, n_channels))
    Xj = tf.random_crop(Xj, (crop_size, crop_size, n_channels))
    return Xi, Xj, label


def random_image_rotation(Xi, Xj, label):
    rotation = tf.random_uniform(shape=[1],
                                 minval=-0.2,
                                 maxval=0.2)
    Xi = tf.contrib.image.rotate(Xi, rotation, interpolation='NEAREST')
    Xj = tf.contrib.image.rotate(Xj, rotation, interpolation='NEAREST')

    return Xi, Xj, label

def random_distortions(Xi, Xj, label):
    Xi = tf.clip_by_value(tf.py_func(apply_random_transformations, [Xi], tf.float32), 0.0, 1.0)
    Xj = tf.clip_by_value(tf.py_func(apply_random_transformations, [Xj], tf.float32), 0.0, 1.0)
    return Xi, Xj, label

def random_flip_left_right(Xi, Xj, label):
    Xi = tf.image.random_flip_left_right(Xi)
    Xj = tf.image.random_flip_left_right(Xj)
    return Xi, Xj, label


def normalizer(Xi, Xj, label):
    Xi = tf.subtract(Xi, 0.5)
    Xi = tf.multiply(Xi, 2.0)

    Xj = tf.subtract(Xj, 0.5)
    Xj = tf.multiply(Xj, 2.0)
    return Xi, Xj, label

def central_image_crop(Xi, Xj, label, crop_size=128):
    return tf.image.resize_image_with_crop_or_pad(Xi, target_height=crop_size, target_width=crop_size), \
           tf.image.resize_image_with_crop_or_pad(Xj, target_height=crop_size, target_width=crop_size), \
           label

def denormalize(image):
    return tf.add(tf.divide(image, 2), 0.5)

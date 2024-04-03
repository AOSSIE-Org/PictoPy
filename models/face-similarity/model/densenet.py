import tensorflow as tf

l2 = tf.keras.regularizers.l2


class TransitionLayer(tf.keras.Model):
    def __init__(self, theta, depth, weight_decay, momentum=0.99, epsilon=0.001):
        super(TransitionLayer, self).__init__()
        self.bn1 = tf.keras.layers.BatchNormalization(momentum=momentum, epsilon=epsilon)
        self.conv1 = tf.keras.layers.Conv2D(filters=int(theta * depth), use_bias=False, kernel_size=1, activation=None,
                                            kernel_initializer="he_normal", kernel_regularizer=l2(weight_decay),
                                            strides=1, padding="same")

        self.pool1 = tf.keras.layers.AveragePooling2D(pool_size=2, strides=2, padding="same")

    def call(self, inputs, training):
        net = self.bn1(inputs, training=training)
        net = tf.nn.relu(net)
        net = self.conv1(net)
        net = self.pool1(net)
        return net


class DenseUnit(tf.keras.Model):
    def __init__(self, k, weight_decay, momentum=0.99, epsilon=0.001):
        super(DenseUnit, self).__init__()

        self.bn1 = tf.keras.layers.BatchNormalization(momentum=momentum, epsilon=epsilon)
        self.conv1 = tf.keras.layers.Conv2D(filters=4 * k, use_bias=False, kernel_size=1, strides=1,
                                            padding="same", name="unit_conv", activation=None,
                                            kernel_initializer="he_normal", kernel_regularizer=l2(weight_decay))

        self.bn2 = tf.keras.layers.BatchNormalization(momentum=momentum, epsilon=epsilon)
        self.conv2 = tf.keras.layers.Conv2D(filters=k, use_bias=False, kernel_size=3, strides=1, padding="same",
                                            activation=None, kernel_initializer="he_normal",
                                            kernel_regularizer=l2(weight_decay))

    def call(self, inputs, training):
        net = self.bn1(inputs, training=training)
        net = tf.nn.relu(net)
        net = self.conv1(net)
        net = self.bn2(net, training=training)
        net = tf.nn.relu(net)
        net = self.conv2(net)
        return net


class DenseBlock(tf.keras.Model):
    def __init__(self, k, weight_decay, number_of_units, momentum=0.99, epsilon=0.001):
        super(DenseBlock, self).__init__()
        self.number_of_units = number_of_units
        self.units = self._add_cells([DenseUnit(k, weight_decay=weight_decay, momentum=momentum, epsilon=epsilon) for i in range(number_of_units)])

    def _add_cells(self, cells):
        # "Magic" required for keras.Model classes to track all the variables in
        # a list of layers.Layer objects.
        for i, c in enumerate(cells):
            setattr(self, "cell-%d" % i, c)
        return cells

    def call(self, x, training):
        x = self.units[0](x, training=training)
        for i in range(1, int(self.number_of_units)):
            output = self.units[i](x, training=training)
            x = tf.concat([x, output], axis=3)

        return x


class DenseNet(tf.keras.Model):
    def __init__(self, k, units_per_block, weight_decay=1e-4, num_outputs=10, theta=1.0, momentum=0.99, epsilon=0.001,
                 initial_pool=True):
        super(DenseNet, self).__init__()
        self.initial_pool = initial_pool
        # The initial convolution layer comprises 2k convolutions of size 7×7 with stride 2;
        self.conv1 = tf.keras.layers.Conv2D(filters=2 * k, kernel_size=7, strides=2, padding="same",
                                            kernel_initializer="he_normal",
                                            kernel_regularizer=l2(weight_decay))

        if self.initial_pool:
            self.pool1 = tf.keras.layers.MaxPool2D(pool_size=2, strides=2, padding="same")

        self.number_of_blocks = len(units_per_block)
        self.dense_blocks = self._add_cells([DenseBlock(k=k, number_of_units=units_per_block[i], weight_decay=weight_decay,
                               momentum=momentum, epsilon=epsilon) for i in range(self.number_of_blocks)])

        self.transition_layers = self._add_cells([TransitionLayer(theta=theta, depth=k * units_per_block[i], weight_decay=weight_decay,
                                        momentum=momentum, epsilon=epsilon) for i in range(self.number_of_blocks-1)])

        self.glo_avg_pool = tf.keras.layers.GlobalAveragePooling2D()
        self.logits = tf.keras.layers.Dense(units=num_outputs)

    def _add_cells(self, cells):
        # "Magic" required for keras.Model classes to track all the variables in
        # a list of layers.Layer objects.
        for i, c in enumerate(cells):
            setattr(self, "cell-%d" % i, c)
        return cells

    @tf.contrib.eager.defun
    def call(self, input, training):
        """Run the model."""
        net = self.conv1(input)

        if self.initial_pool:
            net = self.pool1(net)

        for block, transition in zip(self.dense_blocks[:-1], self.transition_layers):
            net = block(net, training=training)
            net = transition(net, training=training)

        net = self.dense_blocks[-1](net, training=training)
        net = self.glo_avg_pool(net)

        return self.logits(net)

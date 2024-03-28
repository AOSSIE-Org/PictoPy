# Face-similarity
Face-similarity CNN using Tensorflow Eager execution.

Medium article: [How to train your own FaceID ConvNet using TensorFlow Eager execution](https://medium.freecodecamp.org/how-to-train-your-own-faceid-cnn-using-tensorflow-eager-execution-6905afe4fd5a)

This implementation uses DenseNets with contrastive loss.

Reference Papers: 
- [Densely Connected Convolutional Networks](https://arxiv.org/abs/1608.06993)
- [Dimensionality Reduction by Learning an Invariant Mapping](https://ieeexplore.ieee.org/document/1640964)

## Dependencies:
- Python 3.6.x
- Tensorflow 1.10.1

## Inference

### Google Colaboratory

- Just open the `inference.ipynb` and select the option to open on Colab.

### Running locally

1- Download the pre-trained model using the following link.
  * Place the `tboard_logs` folder in the root folder of the project.
  
- [Tensorflow pre-trained model](https://www.dropbox.com/sh/qgz0gw6pqkn64gq/AAAi4eQ97f2yNo8wRQ4FEx-3a?dl=0)

2- Download the following test dataset (TfRecords format).
  * Place the `dataset` folder in the root folder of the project.

- [Download test dataset](https://www.dropbox.com/sh/qgz0gw6pqkn64gq/AAAi4eQ97f2yNo8wRQ4FEx-3a?dl=0)

3- Run the jupyter notebook `inference.ipynb`
  * Run the notebook. Adjust the dataset paths accordingly. 
  
  
## Results

![Results](./images/demo.png)

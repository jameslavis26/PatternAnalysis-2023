"""
Data loader + preprocessing
Jack Cashman - 47431748
"""
from tensorflow.keras.preprocessing import image_dataset_from_directory
import matplotlib.pyplot as plt

def prep_data(path, img_dim, batch_size, rgb=True, validation_split=None, subset=None, seed=None, shift=0):
    """
    Load and preprocess the image data
    :param path: Path to unzipped data
    :param img_dim: Dimension of the square images
    :param batch_size: Size of each batch
    :param rgb: Whether or not the images are rgb
    :param validation_split: Portion of data reserved for validation set
    :param subset: Whether to load train/val set if using a split
    :param seed: Random seed to ensure no dataleakage due to train/val splot
    :param shift: Normalisation const.
    :return: tf.data.Dataset object
    """
    img_data = image_dataset_from_directory(path,
                                            label_mode=None,
                                            image_size=(img_dim, img_dim),
                                            color_mode='rgb' if RBG else 'grayscale',
                                            color_mode='rgb',
                                            batch_size=batch_size,
                                            shuffle=True,
                                            validation_split=validation_split,
                                            subset=subset,
                                            seed=seed)

    return img_data.map(lambda x: (x / float(img_dim)) - shift)
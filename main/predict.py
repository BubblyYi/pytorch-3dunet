import importlib
import os

from datasets.hdf5 import get_test_loaders
from unet3d import utils
from unet3d.config import load_config
from unet3d.model import get_model

logger = utils.get_logger('UNet3DPredictor')


def _get_output_file(dataset, suffix='_predictions'):
    return f'{os.path.splitext(dataset.file_path)[0]}{suffix}.h5'


def _get_dataset_names(config, number_of_datasets, prefix='predictions'):
    dataset_names = config.get('dest_dataset_name')
    if dataset_names is not None:
        if isinstance(dataset_names, str):
            return [dataset_names]
        else:
            return dataset_names
    else:
        if number_of_datasets == 1:
            return [prefix]
        else:
            return [f'{prefix}{i}' for i in range(number_of_datasets)]


def _get_predictor(model, loader, output_file, config):
    predictor_config = config.get('predictor', {})
    class_name = predictor_config.get('name', 'StandardPredictor')

    m = importlib.import_module('unet3d.predictor')
    predictor_class = getattr(m, class_name)

    return predictor_class(model, loader, output_file, config, **predictor_config)


def main():
    # Load configuration
    config = load_config()

    # Create the model
    model = get_model(config)

    # Load model state
    model_path = config['model_path']
    logger.info(f'Loading model from {model_path}...')
    utils.load_checkpoint(model_path, model)
    logger.info(f"Sending the model to '{config['device']}'")
    model = model.to(config['device'])

    logger.info('Loading HDF5 datasets...')
    for test_loader in get_test_loaders(config):
        logger.info(f"Processing '{test_loader.dataset.file_path}'...")

        output_file = _get_output_file(test_loader.dataset)

        predictor = _get_predictor(model, test_loader, output_file, config)
        # run the model prediction on the entire dataset and save to the 'output_file' H5
        predictor.predict()


if __name__ == '__main__':
    main()

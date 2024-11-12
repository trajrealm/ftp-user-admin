import csv 
import conf.app_config as app_config


def get_datasets_from_csv():
    datasets = []
    with open(app_config.DATA_LINKS_CSV_FILEPATH, 'r') as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            datasets.append(row[0])
    return datasets


def get_dataset_reverse_map():
    datasetmap = dict()
    with open(app_config.DATA_LINKS_CSV_FILEPATH, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        
        for row in reader:
            fn = row[2].split("/")[-1]
            prefix = "_".join(fn.split("_")[:-2])
            datasetmap[prefix] = row[0]
    return datasetmap


def get_dataset_files_paths():
    dataset_map = dict()
    with open(app_config.DATA_LINKS_CSV_FILEPATH, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if 'nosedol' in row[2]:
                path  = '/'.join(row[2].split('/')[:-2]) + '/'
            else:
                path = '/'.join(row[2].split('/')[:-1]) + '/'

            dataset_map[row[0]] = path
    return dataset_map


def parse_dataset(filename):
    prefix = "_".join(filename.split("_")[:-2])
    return prefix


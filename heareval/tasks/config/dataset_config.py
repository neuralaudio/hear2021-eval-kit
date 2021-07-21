"""
Generic configuration used by all tasks
"""


class DatasetConfig:
    """
    A base class config class for HEAR datasets.

    Args:
        task_name: Unique name for this task
        version: version string for the dataset
    """

    def __init__(self, task_name: str, version: str):
        self.task_name = task_name
        self.version = version

        # For deterministic dataset generation
        self.seed = 43

        # Number of CPU works for Luigi jobs
        self.num_workers = 4

        # Default sample rates for HEAR evaluation. If you
        # only use one sample rate this can be a list with
        # only a single rate in it.
        self.sample_rates = [48000, 44100, 22050, 16000]


class PartitionConfig:
    """
    A configuration class for creating named partitions in a dataset

    Args:
        name: name of the partition
        max_files: an integer number of samples to cap this partition at,
            defaults to None for no maximum.
    """

    def __init__(self, name: str, max_files: int = None):
        self.name = name
        self.max_files = max_files
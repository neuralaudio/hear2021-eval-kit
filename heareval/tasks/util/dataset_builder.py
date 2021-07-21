"""
A builder class that helps to construct luigi dataset pre-processing pipelines
"""
import os
from urllib.parse import urlparse
from typing import Any, Dict, List, Union
from types import new_class
from functools import partial

import luigi

from heareval.tasks.config import DatasetConfig, get_config
import heareval.tasks.util.luigi as luigi_util


class DatasetBuilder:
    def __init__(self, task_config: Union[str, DatasetConfig]):
        if isinstance(task_config, str):
            self.config = get_config(task_config)
        elif isinstance(task_config, DatasetConfig):
            self.config = task_config
        else:
            raise TypeError(
                f"task_config must be a str or a DataConfig object, "
                f"received {type(task_config)}."
            )

        # Set the task name for all luigi WorkTasks
        luigi_util.WorkTask.task_name = self.config.task_name

    @staticmethod
    def add_requirements(requirements: Union[luigi.Task, List, Dict], namespace: Dict):
        """
        Given a namespace this adds a requires() class method that returns
        the requirments object passed in.

        Args:
            requirements: A requirements object to return in the new class method
            namespace: namespace to add the requires method to
        """
        namespace["requires"] = lambda self: requirements

    def build_task(
        self,
        base: Any,
        name: str = None,
        requirements: Union[luigi.Task, List, Dict] = None,
        kwargs: Dict[str, Any] = None,
    ) -> Any:
        """
        Dynamically creates a luigi work task with the passed in requirements

        Args:
            base: Base class for this task
            name: Optional unique name for the new task class. Defaults to the
                same name as the base class. If you need a separate output folder
                for this task if there are multiple, or a uniquely named class
                then make sure to set this.
            requirements: Optional requirements that will be returned by the requires()
                method of the newly created class.
            kwargs: keyword args to used to construct the newly created task class

        Returns:
            A new class that derives from the base class

        """
        name = base.__name__ if name is None else name
        task_class = new_class(
            name=name,
            bases=(base,),
            exec_body=partial(self.add_requirements, requirements),
        )

        # Make sure the task name is correct for the config
        task_class.task_name = self.config.task_name

        # Instantiate the new class with the keyword args
        kwargs = dict() if kwargs is None else kwargs
        return task_class(**kwargs)

    def download_and_extract_tasks(self) -> Dict[str, luigi_util.WorkTask]:
        """
        Builds the download and extract tasks from a dictionary of download urls
        """
        tasks = {}

        # For each required download in the config, creates a new ExtractArchive
        # class with the correct Download requirement. The new ExtractArchive tasks
        # are returned as a list of tasks.
        for name, url in self.config.download_urls.items():
            filename = os.path.basename(urlparse(url).path)
            task = self.build_task(
                base=luigi_util.ExtractArchive,
                name=f"ExtractArchive{name.lower().title()}",
                requirements={
                    "download": luigi_util.DownloadCorpus(url=url, outfile=filename)
                },
                kwargs={"infile": filename},
            )
            tasks[name] = task

        return tasks

    def prepare_audio_from_metadata_task(self, metadata_task: luigi.Task) -> luigi.Task:

        # Subsample each partition
        subsample_tasks = {}
        for partition in self.config.partitions:
            task = self.build_task(
                luigi_util.SubsamplePartition,
                requirements={"meta": metadata_task},
                kwargs={"partition": partition.name, "max_files": partition.max_files},
            )
            subsample_tasks[partition.name] = task

        # Convert each audio file to a mono wav file of the correct length.
        # MonoWavTrimCorpus only needs one requirement called "corpus" in order
        # to locate the workdir. But we also need it to wait for the remainder of
        # the partition subsample tasks.
        partitions = list(subsample_tasks.keys())
        requirements = {"corpus": subsample_tasks[partitions[0]]}
        for name in partitions[1:]:
            requirements[name] = subsample_tasks[name]

        mono_trim_wav = self.build_task(
            luigi_util.MonoWavTrimCorpus,
            requirements=requirements,
            kwargs={"duration": self.config.sample_duration},
        )

        split_audio = self.build_task(
            # TODO: Rename SplitTrainTestCorpus
            luigi_util.SplitTrainTestCorpus,
            requirements={
                "corpus": mono_trim_wav,
                "meta": metadata_task,
            },
        )

        split_metadata = self.build_task(
            # Todo: Rename SplitTrainTestMetadata
            luigi_util.SplitTrainTestMetadata,
            requirements={
                "traintestcorpus": split_audio,
                "meta": metadata_task,
            },
        )

        metadata_vocab = self.build_task(
            luigi_util.MetadataVocabulary,
            requirements={"traintestmeta": split_metadata},
        )

        # Build up all the resampling tasks for each partition
        resample_tasks = []
        for partition in self.config.partitions:
            for sr in self.config.sample_rates:
                task = self.build_task(
                    luigi_util.ResampleSubCorpus,
                    requirements={"traintestcorpus": split_audio},
                    kwargs={"sr": sr, "partition": partition.name},
                )
                resample_tasks.append(task)

        finalize_corpus = self.build_task(
            luigi_util.FinalizeCorpus,
            requirements={
                "resample": resample_tasks,
                "traintestmeta": split_metadata,
                "vocabmeta": metadata_vocab,
            },
        )

        return finalize_corpus
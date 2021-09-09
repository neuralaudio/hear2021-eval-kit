![HEAR2021](https://neuralaudio.ai/assets/img/hear-header-sponsor.jpg)
# hear-eval-kit

Evaluation kit for HEAR 2021 NeurIPS competition, using tasks from
[hear-preprocess](https://github.com/neuralaudio/hear-preprocess).

If you have any questions or comments:
* 

Summary:
* Embedding
* Prediction + evaluation. Speed only dependent upon embedding size (with GPUs its non-linear) and hopsize (only for events).
[also, max_epochs + grid points]

[multi GPU], single GPU, how to specify the GPU you want.

Where to find CSVs.

ignore messages about:
Warning: Leaking Caffe2 thread-pool after fork. (function pthreadpool)

TF and Torch versions.

RAM requirements.

GPU memory requirements.

You are welcome to futz with stuff but this is all known to work
on the following setup, which is the canonical setup:


## Requirements

Tested with Python 3.7 and 3.8. Python 3.9 is not officially supported
because pip3 installs are very finicky, but it might work.

## Quickstart

Here is a simple quickstart to evaluate the naive `hearbaseline`. It isn't guaranteed to use your GPU. More detailed instructions are below. If you have any questions

```

## Installation

```
pip3 install heareval
```

## Evaluation

### Setup

#### Docker

#### Cloud GPUs

The easiest way to do evaluation is to launch a Spotty GCP instance.
You can easily adapt Spotty also for AWS GPU instances.

Prepare a `spotty.yaml` file with the provided template file:
```
cp spotty.yaml.tmpl spotty.yaml
```
Change the instance name in the copied file. Specifically, change `"USERNAME"` 
suffix in `instances: name` to allow for multiple users in the same project 
to make separate gcp instances and volumes to avoid conflicts within the project.

Run spotty:
```
spotty start
spotty sh
```

This requires the heareval Docker image, which is pre-built and
published on Dockerhub for your convenience.

Please refer to `README.spotty` for more details.

### Download Open Tasks

google cloud

HTTP

[how to stop and restart, continuing where you left off, how to clean]
[lightning_logs, etc.]

### Computing embeddings

Once a set of tasks has been generated, embeddings can be computed
using any audio embedding model that follows the [HEAR
API](https://neuralaudio.ai/hear2021-holistic-evaluation-of-audio-representations.html#common-api).

To compute embeddings using the [HEAR
baseline](https://github.com/neuralaudio/hear-baseline):

1) Install the hearbaseline and download the model weights:
```
pip3 install hearbaseline
wget https://github.com/neuralaudio/hear-baseline/raw/main/saved_models/naive_baseline.pt
```

If you want to use your pip HEAR module, substitute `hearbaseline`
and `./naive_baseline.pt` below with your pip module name and model
weight path.

2) Compute the embeddings for all the tasks ("all") or one task:
```
python3 -m heareval.embeddings.runner hearbaseline --model ./naive_baseline.pt
    [--tasks-dir tasks]
    [--task task]
    [--embeddings-dir embeddings]
```

This assumes that your current working directory contains a folder
called `tasks` produced by `heareval.tasks.runner`. If this directory
is in a different location or named something different you can use
the option `--tasks-dir`. 

By default embeddings will be computed in a folder named `embeddings`
in the current working directory. To generate in a different location
use the option `--embeddings-dir`.

### Downstream Evaluation

For evaluation of each task, a shallow model will be trained on the
embeddings followed by task specific evaluations. The names of the
scoring functions used for these task specific evalutions can be
found in the `task_metadata.json` inside every task directory.

1) Train the shallow model and generate the test set predictions
for all tasks or one task:
```
python3 -m heareval.predictions.runner hearbaseline --model ./naive_baseline.pt \
    [--embeddings-dir embeddings]
    [--task task]
    [--gpus INT]
    [--in-memory False]
```
`--in-memory False` will memmap the embeddings from disk, which
will use less standard memory, but also be slower.

2) Evaluate the generated predictions for the test set for one or
all modules and for one or all tasks:
```
python3 -m heareval.evaluation.runner \
    [module]
    [--embeddings-dir embeddings]
    [--task task]
```

By default, both the steps above assume a folder named `embeddings`,
generated in the compute embeddings step. If this directory is
different, the option `--embeddings-dir` can be used.

Running the above will generate `evaluation_results.json` in the
current working directory containing the evalution scores for each
task.

## Development

Clone repo:
```
git clone https://github.com/neuralaudio/hear-eval-kit
cd hear-eval-kit
```

Install in development mode:
```
pip3 install -e ".[dev]"
```

Make sure you have pre-commit hooks installed:
```
pre-commit install
```

Running tests:
```
python3 -m pytest
```

### Docker Development

# Genomics Workflows with FSx for Lustre

Demonstration code that shows how Amazon FSx for Lustre can be used with genomics workflows.

## Overview

This demo implements a simple genomics workflow using:

* bwa-mem
* samtools
* bcftools

to convert raw whole genome sequencing data (FASTQ) to called variants (VCF).

The workflow uses containerized versions of the tools above and is orchestrated by AWS Step Functions and AWS Batch.  For more information on this architecture see:

* https://aws.amazon.com/blogs/compute/building-high-throughput-genomics-batch-workflows-on-aws-introduction-part-1-of-4/
* https://aws.amazon.com/blogs/compute/building-simpler-genomics-workflows-on-aws-step-functions/
* https://docs.opendata.aws/genomics-workflows

The reference architectures above rely on per-job staging of data from/to S3 onto the host instance that the job is running on.  This requires building in capabilities into either your container image (e.g. adding the AWS CLI), or your workflow orchestration engine.

Many existing bioinformatics tools read and output files, and expect to interact with a POSIX compliant file system.  Similarly, existing genomics workflows may assume use of a shared file system across jobs.  Lastly, some tools have better performance when used in conjunction with high performance disk I/O.

Amazon FSx for Lustre provides a managed, performant, and POSIX compliant filesystem that also supports transparent data syncing with S3.  This demonstration shows how Amazon FSx for Lustre can be used as a shared filesystem across all jobs of a genomics workflow.

## Requirements

* Python 3.7
* Python Packages
  
  * boto3
  * awscli

Install python with your OS package manager of choice or using `conda` (recommended).

```bash
conda create -n fsx-demo python=3.7
```

Fulfill package requirements with:

```bash
pip install -U -r requirements.txt
```

## Deploy Tooling

**Note: You should only need to create this once**

Creates:

* Workflow job container images
* AWS Batch Job Definitions for workflow jobs
* AWS Step Functions state machine for workflow
* Lambda function for submitting workflow
* Required IAM roles and policies for all of the above

```bash
./deploy.sh tools
```

### Notes on Batch Job Definitions

The tooling creates the following AWS Batch Job definitions

| Name             | Description |
| :--------------- | :---------- |
| `bwa`            | Burrows-Wheeler Aligner.  Used to align raw sequencing data (i.e. FASTQ files) to a reference sequence.  Outputs a SAM file. |
| `samtools`       | Utilities for QC and processing SAM files.  Used to process a SAM file and output a sorted binary representation (a BAM file) and a corresponding index (aBAI file). |
| `bcftools`       | Utilities for generating and manipulating Variant Call Format (VCF) files and thier binary equivalent (BCF).  Used to generate variant calls - differences in sample sequence relative to reference.  Outputs GZIP'd MPILEUP and VCF files.  (_Note: For demonstration purposes, only Chromosome 21 is processed._) |
| `fsx-data-repo-task` | Used to archive FSx Lustre filesystems back to S3 when the workflow is complete.  Requires that the AWS CLI be installed on the host instance and mapped into the container. |

## Deploy Infrastructure

Creates:

* AWS VPC with 2 private subnets in 2 availability zones
* AWS Batch Compute Environment
* AWS Batch Job Queue
* FSx Lustre file systems for:
    * genome reference data - this uses the Broad References public dataset as a data repository and is therefore considered read-only.
    * workflow input data - this uses a public bucket with example raw whole genome sequencing data as a data repository and is therefor considered read-only.
    * workflow results data - this uses a pre-existing bucket your account as a data repository.  When the workflow is complete, any output data created is archived back to this bucket.
* Required IAM roles and policies for all of the above

The referenced CloudFormation template for the above infrastructure is fully self-contained and should not need parameter inputs beyond defaults.

Create the stack:
```bash
./deploy.sh infra create
```

Delete the stack:
```bash
./deploy.sh infra delete
```

Bounce the stack:
```bash
./deploy.sh infra reset
```

## Submit a workflow

Use the `execute.py` script and `inputs.json` file in the `./demo` folder to submit a workflow.

Options for this script are:

```text
usage: execute.py [-h] [--profile PROFILE] [--region REGION]
                  [--stack-queue-name STACK_QUEUE_NAME]
                  stack_name workflow_name inputs_json_file

positional arguments:
  stack_name            CloudFormation stack that contains a Batch Job Queue
                        for job execution. Will use the queue whose name
                        starts with "default" unless --stack-queue-name is
                        specified.
  workflow_name         Name of the workflow (Sfn State Machine) to execute
  inputs_json_file      Path to inputs.json file to provide to the workflow

optional arguments:
  -h, --help            show this help message and exit
  --profile PROFILE     AWS profile to use
  --region REGION       AWS region name to use
  --stack-queue-name STACK_QUEUE_NAME
                        Name of the Batch Job Queue in the stack specified by
                        stack_name to use for job execution. Regex patterns
                        are allowed.
```

The script automatically finds AWS Batch Job Queues in the Cfn stack specified.

You will need to determine the name of the AWS Step Functions State Machine to provide.

Submitting a workflow looks like this:

```bash
cd demo
python execute.py \
    gwf-fsx-infrastructure \
    example-genomics-workflow-20da0440-893d-11e9-8d64-06c01b62978e \
    ./inputs.json

[job queue]: default-a3e5f130-88b3-11e9-8b32-0adcdede1372
[workflow name]: example-genomics-workflow-20da0440-893d-11e9-8d64-06c01b62978e
[execution id]: e15fc224-c026-486e-a8ab-4f5adc126597
```

The example workflow takes about 6-8min to complete.  You can monitor its progress in the AWS Step Functions Console.

When it is complete, data generated by the workflow will be archived back to S3 using the following prefix pattern:

```text
s3://bucket-name/workflow-name/execution-id
```

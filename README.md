# Genomics Workflows with FSx for Lustre

Demonstration code that shows how to use FSx for Lustre with genomics workflows.

## Requirements

* Python 3.7
* boto3
* awscli

Fulfill these with:

```bash
pip install -U -r requirements.txt
```

## Deploy Tooling

**Note: You should only need to create this once**

Creates:

* workflow job container images
* AWS Batch Job Definitions for workflow jobs
* AWS Step Functions state machine for workflow
* Lambda function for submitting workflow

```bash
aws cloudformation create-stack \
    --stack-name gwf-fsx-tooling \
    --capabilities CAPABILITY_IAM \
    --template-body file://gwf-fsx-tooling.template.yaml
```

## Deploy Infrastructure

Creates:

* AWS Batch Compute Environment
* AWS Batch Job Queue
* FSx Lustre file systems for:
    * genome reference data - this uses the Broad References public dataset as a data repository and is therefore considered read-only.
    * workflow input data - this uses a public bucket with example raw whole genome sequencing data as a data repository and is therefor considered read-only.
    * workflow results data - this uses a pre-existing bucket your account as a data repository.  When the workflow is complete, any output data created is archived back to this bucket.

Modify the `deploy.sh` script as needed to suit your account.

Create the stack:
```bash
./deploy.sh create
```

Delete the stack:
```bash
./deploy.sh delete
```

Bounce the stack:
```bash
./deploy.sh reset
```

## Submit a workflow

Use the `execute.py` script and `inputs.json` file in the `./demo` to submit a workflow.

Options for this script are:

```text
usage: execute.py [-h] [--profile PROFILE] [--region REGION]
                  [--queue-name QUEUE_NAME] [--stack-name STACK_NAME]
                  [--stack-queue-name STACK_QUEUE_NAME]
                  workflow_name inputs_json_file

positional arguments:
  workflow_name         Name of the workflow (Sfn State Machine) to execute
  inputs_json_file      Path to inputs.json file to provide to the workflow

optional arguments:
  -h, --help            show this help message and exit
  --profile PROFILE     AWS profile to use
  --region REGION       AWS region name to use
  --queue-name QUEUE_NAME
                        Name of the Batch Job Queue for job execution
  --stack-name STACK_NAME
                        CloudFormation stack that contains a Batch Job Queue
                        for job execution. Will use the queue whose name
                        starts with "default" unless --stack-queue-name is
                        specified. Ignored if --queue-name is specified.
  --stack-queue-name STACK_QUEUE_NAME
                        Name of the Batch Job Queue in the stack specified by
                        --stack-name to use for job execution. Regex patterns
                        are allowed.
```

The script automatically finds AWS Batch Job Queues in the Cfn stack specified.

You will need to determine the name of the AWS Step Functions State Machine to provide.

Submitting a workflow looks like this:

```bash
cd demo
python execute.py \
    --stack-name gwf-fsx-infrastructure \
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

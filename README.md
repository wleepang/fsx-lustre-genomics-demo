# Genomics Workflows with FSx for Lustre

Demonstration code that shows how to use FSx for Lustre with genomics workflows.

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
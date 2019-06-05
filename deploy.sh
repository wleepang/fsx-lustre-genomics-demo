#!/bin/bash

CLI_INPUT_JSON=$(cat <<EOF
{
    "Parameters": [
        {
            "ParameterKey": "DockerImageAndMetadataVolumeSize", 
            "ParameterValue": "75"
        },
        {
            "ParameterKey": "KeyPairName", 
            "ParameterValue": "pwyming"
        },
        {
            "ParameterKey": "LaunchTemplateNamePrefix", 
            "ParameterValue": "fsx-lustre-genomics"
        },
        {
            "ParameterKey": "LustreStorageCapacity", 
            "ParameterValue": "3600"
        },
        {
            "ParameterKey": "S3ImportPath", 
            "ParameterValue": "s3://pwyming-tmp-us-west-2"
        },
        {
            "ParameterKey": "SubnetIds", 
            "ParameterValue": "subnet-d481a3b2,subnet-b4eaa8fc"
        },
        {
            "ParameterKey": "VpcId", 
            "ParameterValue": "vpc-6432d41d"
        },
        {
            "ParameterKey": "WorkflowOrchestrator", 
            "ParameterValue": "step-functions"
        }
    ], 
    "Capabilities": [
        "CAPABILITY_IAM"
    ]
}
EOF
)


function create() {
    aws cloudformation create-stack \
        --stack-name fsx-lustre-batch-test \
        --template-body file://gwf-fsx-lustre.template.yaml \
        --cli-input-json "$CLI_INPUT_JSON"
}

function update() {
    aws cloudformation update-stack \
        --stack-name fsx-lustre-batch-test \
        --template-body file://gwf-fsx-lustre.template.yaml \
        --cli-input-json "$CLI_INPUT_JSON"
}

function delete() {
    aws cloudformation delete-stack \
        --stack-name fsx-lustre-batch-test
}

function status() {
    aws cloudformation describe-stacks \
        --stack-name fsx-lustre-batch-test \
    | jq -r .Stacks[0].StackStatus
}

function reset() {
    delete

    state=$(status)
    while [ "$state" = "DELETE_IN_PROGRESS" ]
    do
        sleep 10
        state=$(status)
    done

    if [ "$state" = "DELETE_COMPLETE" ]
    then
        create
    else
        echo $state
    fi
}

$1
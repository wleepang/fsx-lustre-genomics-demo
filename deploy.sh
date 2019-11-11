#!/bin/bash

SHA=`date | shasum | cut -d " " -f 1 | head -c8`
REGION=us-east-2

ASSET=${1:-infra}
case $ASSET in
    tools|tooling)
        STACKNAME=gwf-fsx-tooling
        ;;
    infra|infrastructure)
        STACKNAME=gwf-fsx-infrastructure
        ;;
    *)
        echo "unrecognized asset"
        exit 1
esac

COMMAND=${2:-create}


if [ -z $PROFILE ]; then
    PROFILE=default
fi

CLI_INPUT_JSON=$(cat <<EOF
{
    "Capabilities": [
        "CAPABILITY_IAM"
    ]
}
EOF
)


function create() {
    aws --profile $PROFILE --region $REGION \
        cloudformation create-stack \
        --stack-name $STACKNAME \
        --template-body file://${STACKNAME}.template.yaml \
        --cli-input-json "$CLI_INPUT_JSON"
}

function update() {
    aws --profile $PROFILE --region $REGION \
        cloudformation update-stack \
        --stack-name $STACKNAME \
        --template-body file://${STACKNAME}.template.yaml \
        --cli-input-json "$CLI_INPUT_JSON"
}

function delete() {
    aws --profile $PROFILE --region $REGION \
        cloudformation delete-stack \
        --stack-name $STACKNAME
}

function status() {
    aws --profile $PROFILE --region $REGION \
        cloudformation describe-stacks \
        --stack-name $STACKNAME \
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

$COMMAND

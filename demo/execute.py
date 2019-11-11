#!/usr/bin/env python

"""
Executes the workflow with inputs
"""

import argparse
import warnings
import json
import re

import boto3


parser = argparse.ArgumentParser()
parser.add_argument(
    '--profile',
    type=str,
    help="""
        AWS profile to use
    """
)
parser.add_argument(
    '--region',
    type=str,
    help="""
        AWS region name to use
    """
)
parser.add_argument(
    'stack_name',
    type=str,
    help="""
        CloudFormation stack that contains a Batch Job Queue for job execution.
        Will use the queue whose name starts with "default" unless --stack-queue-name
        is specified.
    """
)
parser.add_argument(
    '--stack-queue-name',
    type=str,
    default="default.*",
    help="""
        Name of the Batch Job Queue in the stack specified by stack_name to use 
        for job execution.  Regex patterns are allowed.
    """
)
parser.add_argument(
    'workflow_name',
    type=str,
    help="""
        Name of the workflow (Sfn State Machine) to execute
    """
)
parser.add_argument(
    'inputs_json_file',
    type=str,
    help="""
        Path to inputs.json file to provide to the workflow
    """
)

def get_submitter_fun(session, args):
    cfn = session.client('cloudformation')

    exports = [
        export
        for export in cfn.list_exports()['Exports']
    ]

    submitter_funs = [
        export['Value']
        for export in exports
        if "LambdaWorkflowSubmissionFunction" in export['Name']
    ]

    if not submitter_funs:
        raise RuntimeError('no submission functions found')
    
    if len(submitter_funs) > 1:
        warnings.warn('multiple submission functions found, using the first', RuntimeWarning)

    submitter_fun = submitter_funs[0]

    return submitter_fun

def get_job_queue(session, args):
    cfn = session.client('cloudformation')

    stack_resources = cfn.list_stack_resources(StackName=args.stack_name)['StackResourceSummaries']
    queues = [
        resource
        for resource in stack_resources
        if resource['ResourceType'] == 'AWS::Batch::JobQueue'
    ]

    if not queues:
        raise RuntimeError('no Batch Job Queues found in stack')
    
    pattern = args.stack_queue_name
    queue = [
        q['PhysicalResourceId'] for q in queues
        if re.search(pattern, q['PhysicalResourceId'])
    ]

    if not queue:
        raise RuntimeError('no matching Batch Job Queues found in stack')
    elif len(queue) > 1:
        warnings.warn('multiple matching Batch Job Queues found, using the first')
    
    _, queue_name = queue[0].split("/")

    return queue_name


def main(args):
    session = boto3.Session(
        profile_name=args.profile, 
        region_name=args.region)
    
    fn = session.client('lambda')

    with open(args.inputs_json_file, 'r') as f:
        inputs = f.read()
    
    submitter_fun = get_submitter_fun(session, args)
    queue_name = get_job_queue(session, args)
    
    print('[job queue]:', queue_name)
    print('[workflow name]:', args.workflow_name)
    
    inputs = inputs.replace('${BatchJobQueue}', queue_name)
    
    payload = {
        "workflow_name": args.workflow_name,
        "input": inputs
    }

    response = fn.invoke(
        FunctionName=submitter_fun,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload).encode('utf-8')
    )
    response = json.loads(response['Payload'].read().decode('utf-8'))
    *_, execution_id = response['executionArn'].split(':')

    print('[execution id]:', execution_id)


if __name__ == "__main__":
    main(parser.parse_args())
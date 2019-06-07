"""
Executes the workflow with inputs
"""

import argparse
import warnings
import json

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
    'batch_job_queue',
    type=str,
    help="""
        Name of the AWS Batch Job Queue to submit the workflow to
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


def main(args):
    session = boto3.Session(
        profile_name=args.profile, 
        region_name=args.region)
    
    fn = session.client('lambda')

    with open(args.inputs_json_file, 'r') as f:
        inputs = f.read()
    
    submitter_funs = [
        fun['FunctionName']
        for fun in fn.list_functions()['Functions']
        if 'WorkflowSubmission' in fun['FunctionName']
    ]

    if not submitter_funs:
        raise RuntimeError('no submission functions found')
    
    if len(submitter_funs) > 1:
        warnings.warn('multiple submission functions found, using the first', RuntimeWarning)
    
    submitter_fun = submitter_funs[0]
    inputs = inputs.replace('${BatchJobQueue}', args.batch_job_queue)

    payload = {
        "workflow_name": args.workflow_name,
        "input": inputs
    }

    response = fn.invoke(
        FunctionName=submitter_fun,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload).encode('utf-8')
    )

    print(json.loads(response['Payload'].read().decode('utf-8')))


if __name__ == "__main__":
    main(parser.parse_args())
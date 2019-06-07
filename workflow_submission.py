import json
import uuid

import boto3

def handler(event, context):

    sfn = boto3.client('stepfunctions')

    workflow_name = event['workflow_name']
    execution_id = str(uuid.uuid4())

    machines = {
        machine['name']: machine['stateMachineArn']
        for machine in sfn.list_state_machines(maxResults=1000)['stateMachines']
    }

    # this injects the workflow_name and execution_id as environment variables
    # to be passed in as ContainerOverrides to Batch Job Submissions
    def object_hook(obj):
        if 'resources' in obj:
            obj['resources'].update({
                "Environment": [
                    { "Name": "WORKFLOW_NAME", "Value": workflow_name },
                    { "Name": "EXECUTION_ID", "Value": execution_id }
                ]
            })
        return obj
    
    workflow_input = json.loads(event['input'], object_hook=object_hook)
    workflow_input.update(
        workflow_name=workflow_name,
        execution_id=execution_id
    )

    response = sfn.start_execution(
        stateMachineArn=machines[workflow_name], 
        name=workflow_input['execution_id'],
        input=json.dumps(workflow_input)
    )

    # make the response json serializble
    response.update(startDate=str(response['startDate']))

    return response
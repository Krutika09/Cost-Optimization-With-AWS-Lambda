# boto3 is python module, using boto3 we can interact with AWS services.
import boto3

# These is main function 
def lambda_handler(event, context):
    ec2 = boto3.client('ec2') # these line create ec2 client and allow boto3 to interact with ec2

    # it list all snapshot inside your aws account
    response = ec2.describe_snapshots(OwnerIds=['self'])

    # this list all running instance
    instances_response = ec2.describe_instances(Filters=[
        {'Name': 'instance-state-name', 'Values': ['running']}
    ])

    # it collect ids of  all active instances
    active_instance_ids = set()
    for reservation in instances_response['Reservations']:
        for instance in reservation['Instances']:
            active_instance_ids.add(instance['InstanceId'])

    # Go through each snapshot and decide whether to delete
    for snapshot in response['Snapshots']: # Go through each snapshot one by one.
        snapshot_id = snapshot['SnapshotId']  # This gets the ID of the snapshot so we know which one we’re  working with
        volume_id = snapshot.get('VolumeId')  # This get id of volume from which snapshot is created.

        
        if not volume_id:
            ec2.delete_snapshot(SnapshotId=snapshot_id) # Delete that snapshot if volume id is not found 
            print(f"Deleted EBS snapshot {snapshot_id} as it was not attached to any volume.")
        else:
            try:
                volume_response = ec2.describe_volumes(VolumeIds=[volume_id])  # if attached to volume then check it still exist
                if not volume_response['Volumes'][0]['Attachments']:
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    print(f"Deleted EBS snapshot {snapshot_id} as it was from a volume not attached to any running instance.") # if volume is exist and not attached to instance then delete snapshot
            except ec2.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVolume.NotFound': # if volume is not found mean delted then delete snapshots.
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    print(f"Deleted EBS snapshot {snapshot_id} as its associated volume was not found.")

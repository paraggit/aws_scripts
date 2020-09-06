

from datetime import datetime, timedelta, timezone

import boto3
ec2 = boto3.resource(
    'ec2',
    aws_access_key_id='',
    aws_secret_access_key='',
    region_name='us-east-1'
)


"""
Deleting volumes from AWS
"""

vol_details = ec2.volumes.all()

# Remove volume one by one
for vol in vol_details:
    if vol.state == 'in-use':
        continue
    
    try:
        vobj = ec2.Volume(vol.id)
        vobj.delete()
        print(f"volume {vol.id} deleted successfully")
    except Exception as e:
         print(f"Error deleting volume {vol.id}")


"""
Deleting snapshots from AWS
"""

snapshots = ec2.snapshots.filter(OwnerIds=['self'])

for snapshot in snapshots:
        start_time = snapshot.start_time
        delete_time = datetime.now(tz=timezone.utc) - timedelta(days=1)

        if delete_time > start_time:
            try:
                snapshot.delete()
                print(f"snapshot with ID = {snapshot.snapshot_id} is deleted")
            except Exception as e:
                print(f"Error deleting snapshot {snapshot.snapshot_id} ")
                

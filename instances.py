import boto3


image="ami-065d0be9883aa064a"

ak=""
sk=""
key=""
it="t2.micro"

fl="ami"

amis=[]
with open(fl,"r") as fd:
    lines = fd.readlines()
    for line in lines:
        amis.append(line.strip())


ec2 = boto3.resource("ec2", aws_access_key_id=ak, aws_secret_access_key=sk, region_name="us-east-1")
for a in amis:
    out = ec2.create_instances(KeyName=key, InstanceType=it, ImageId=a, MinCount=1, MaxCount=1)

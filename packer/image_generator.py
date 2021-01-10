#!/usr/bin/env python3
"""A tool to iterate over lists of variables and create image config combinations"""
import itertools
import logging
import os.path
import random
import re
import sys
import os
import json
import boto3

import sh
from packerpy import PackerExecutable

logging.basicConfig(level=logging.INFO)
log = logging

# find where packer is located and set PackerExecutable
packer_location = sh.which("packer")
if packer_location is None:
    log.error("PACKER binary is not found. exiting...")
    sys.exit(1)



packer = PackerExecutable(packer_location)
source_ami = "ami-0c2dc55b4cbab3b75"
ssh_private_key_file = os.path.abspath("cloudigrade-parag-keypair.pem")
ssh_keypair_name = "cloudigrade-parag-keypair"


# Syspurpose config parameaters
roles = [
    "Red Hat Enterprise Linux Workstation",
    "Red Hat Enterprise Linux Server",
    "NA",
]
slas = ["Premium", "Standard", "NA"]
usages = ["Development/Test", "Production", "NA"]
service_types = [
#    "L1-L3",
#    "L3",
    "NA"
]


def build():
    """ """

    # AWS env
    AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

    ami_client = boto3.client(
        'ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    if (AWS_ACCESS_KEY is None) or (AWS_SECRET_KEY is None):
        log.error("AWS_ACCESS_KEY or AWS_SECRET_KEY is not set. exiting...")
        sys.exit(1)

    # get unique  possible combinations
    syspurpose_details = list(
        set(itertools.product(roles, slas, usages, service_types)))


    for item in syspurpose_details:
        _role = item[0]
        _slas = item[1]
        _usages = item[2]
        _sr = item[3]
        name = "packer"

        """ Look Already existing image in AWS"""
        ami_filters = [
            {'Name':'tag:role','Values':[f'{_role}']}, 
            {'Name':'tag:sla','Values':[f'{_slas}']}, 
            {'Name':'tag:usages','Values':[f'{_usages}']}, 
            {'Name':'tag:service_type','Values':[f'{_sr}']},
            {'Name':'tag:automation','Values':['packer']}
        ]

        """ checking if that configuration image is already in that AWS. if yes skipping image creation. """
        images = ami_client.describe_images(Owners=['self'], Filters = ami_filters)

        if len(images['Images']) > 0:
            log.info("AMI is already present for this tag")
            continue

        image_tags = {}
        image_tags["role"] = _role
        image_tags["sla"] = _slas
        image_tags["usages"] = _usages
        image_tags["service_request"] = _sr
        image_tags["automation"] = "packer"

        syspurpose_inline = []

        if _role is not "NA":
            syspurpose_inline.append(f"sudo syspurpose set-role '{_role}'")
            name += name+"_"+_role 

        if _slas is not "NA":
            syspurpose_inline.append(f"sudo syspurpose set-sla '{_slas}'")
            name = name+"_"+_slas

        if _usages is not "NA":
            syspurpose_inline.append(f"sudo syspurpose set-usage '{_usages}'")
            name = name+"_"+_usages

        if _sr is not "NA":
            syspurpose_inline.append(f"sudo syspurpose service-type '{_sr}'")
            name = name+"_"+_sr

        bld_json = {
            "name": name,
            "type": "amazon-ebs",
            "access_key": AWS_ACCESS_KEY,
            "secret_key": AWS_SECRET_KEY,
            "region": "us-east-1",
            "source_ami": source_ami,
            "tags": image_tags,
            "instance_type": "t2.micro",
            "ssh_username": "ec2-user",
            "ssh_password": "password123",
            "ssh_private_key_file": ssh_private_key_file,
            "ssh_keypair_name": ssh_keypair_name,
            "ami_name": name+" {{timestamp}}"    
        }

        provisioners_json = {
            "type": "shell",
            "inline": syspurpose_inline 
        }

        template_json = {
            "builders" : [ bld_json ],
            "provisioners" : [ provisioners_json ]
        }

        template_path = "/tmp/template.json"
        with open(template_path, "w") as fd:
            json.dump(template_json, fd)

        (ret, out, err) = packer.build(template_path)
        
        if ret == 0:
            log.info(f"AMI Created sucessfully. : {out}")
        else:
            log.error(f"Error Creating AMI: {err} ")


if __name__ == "__main__":
    build()
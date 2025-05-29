#!/usr/bin/env python3
import os
from aws_cdk import core as cdk
from photo_app_stack import PhotoAppStack

# Environment variables
env = cdk.Environment(
    account=os.environ.get('CDK_DEFAULT_ACCOUNT', ''),
    region=os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')
)

# CDK App
app = cdk.App()

# Deploy the PhotoAppStack
PhotoAppStack(app, "PhotoAppStack",
    env=env,
    description="Serverless photo application with API Gateway, Lambda, S3, and DynamoDB"
)

app.synth()
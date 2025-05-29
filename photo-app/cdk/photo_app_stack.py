from aws_cdk import (
    core as cdk,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigw_integrations,
    aws_iam as iam
)

class PhotoAppStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Environment name from context or default to 'dev'
        env_name = self.node.try_get_context("env") or "dev"

        # Create S3 bucket for storing photos
        photos_bucket = s3.Bucket(
            self, "PhotosBucket",
            bucket_name=f"photo-app-{env_name}-{cdk.Aws.ACCOUNT_ID}",
            removal_policy=cdk.RemovalPolicy.DESTROY if env_name == "dev" else cdk.RemovalPolicy.RETAIN,
            auto_delete_objects=True if env_name == "dev" else False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldObjects",
                    enabled=True,
                    expiration=cdk.Duration.days(365)  # Optional: Delete photos after 1 year
                )
            ]
        )

        # Create DynamoDB table for storing photo metadata
        photos_table = dynamodb.Table(
            self, "PhotosTable",
            table_name=f"photo-app-photos-{env_name}",
            partition_key=dynamodb.Attribute(
                name="photoId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY if env_name == "dev" else cdk.RemovalPolicy.RETAIN,
            encryption=dynamodb.TableEncryption.AWS_MANAGED
        )

        # Create HTTP API
        http_api = apigwv2.HttpApi(
            self, "PhotoAppApi",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigwv2.CorsHttpMethod.GET, apigwv2.CorsHttpMethod.POST, apigwv2.CorsHttpMethod.OPTIONS],
                allow_headers=["Content-Type"]
            )
        )

        # Environment variables for Lambda functions
        lambda_env = {
            "PHOTOS_BUCKET_NAME": photos_bucket.bucket_name,
            "PHOTOS_TABLE_NAME": photos_table.table_name,
            "PRESIGNED_URL_EXPIRATION": "3600"  # 1 hour
        }

        # Create Lambda function for uploading photos
        upload_photo_function = lambda_.Function(
            self, "UploadPhotoFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("src/upload_photo"),
            environment=lambda_env,
            description="Uploads photos to S3 and stores metadata in DynamoDB",
            memory_size=128,
            timeout=cdk.Duration.seconds(30)
        )

        # Create Lambda function for retrieving photos
        get_photo_function = lambda_.Function(
            self, "GetPhotoFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("src/get_photo"),
            environment=lambda_env,
            description="Retrieves photo metadata and generates pre-signed URL for download",
            memory_size=128,
            timeout=cdk.Duration.seconds(30)
        )

        # Grant permissions to Lambda functions
        photos_bucket.grant_put(upload_photo_function)
        photos_bucket.grant_delete(upload_photo_function)  # For cleanup if DynamoDB fails
        photos_table.grant_write_data(upload_photo_function)

        photos_bucket.grant_read(get_photo_function)
        photos_table.grant_read_data(get_photo_function)

        # Add routes to HTTP API
        http_api.add_routes(
            path="/photos",
            methods=[apigwv2.HttpMethod.POST],
            integration=apigw_integrations.LambdaProxyIntegration(
                handler=upload_photo_function
            )
        )

        http_api.add_routes(
            path="/photos/{photoId}",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigw_integrations.LambdaProxyIntegration(
                handler=get_photo_function
            )
        )

        # Outputs
        cdk.CfnOutput(
            self, "ApiEndpoint",
            value=http_api.url,
            description="API Gateway endpoint URL for the photo application"
        )

        cdk.CfnOutput(
            self, "PhotosBucketName",
            value=photos_bucket.bucket_name,
            description="S3 bucket for storing photos"
        )

        cdk.CfnOutput(
            self, "PhotosTableName",
            value=photos_table.table_name,
            description="DynamoDB table for storing photo metadata"
        )
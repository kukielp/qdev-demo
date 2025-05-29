import json
import os
import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET_NAME')
TABLE_NAME = os.environ.get('PHOTOS_TABLE_NAME')
URL_EXPIRATION = int(os.environ.get('PRESIGNED_URL_EXPIRATION', '3600'))  # Default 1 hour

def lambda_handler(event, context):
    """
    Lambda function to retrieve photo information and generate a pre-signed URL.
    
    This function:
    1. Extracts photoId from the path parameter
    2. Retrieves photo metadata from DynamoDB
    3. Generates a pre-signed URL for the S3 object
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with photo metadata and pre-signed URL
    """
    try:
        logger.info("Processing get photo request")
        
        # Extract photoId from path parameters
        if 'pathParameters' not in event or not event['pathParameters'] or 'photoId' not in event['pathParameters']:
            return build_response(400, {"error": "Missing photoId parameter"})
            
        photo_id = event['pathParameters']['photoId']
        
        # Get photo metadata from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        
        try:
            response = table.get_item(Key={'photoId': photo_id})
        except ClientError as e:
            logger.error(f"Error retrieving item from DynamoDB: {str(e)}")
            return build_response(500, {"error": "Failed to retrieve photo metadata"})
            
        # Check if photo exists
        if 'Item' not in response:
            return build_response(404, {"error": "Photo not found"})
            
        photo_metadata = response['Item']
        s3_key = photo_metadata['s3Key']
        
        # Generate pre-signed URL
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=URL_EXPIRATION
            )
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            return build_response(500, {"error": "Failed to generate download URL"})
        
        # Return photo metadata and pre-signed URL
        return build_response(200, {
            "photoId": photo_metadata['photoId'],
            "fileName": photo_metadata['fileName'],
            "uploadTimestamp": photo_metadata['uploadTimestamp'],
            "downloadUrl": presigned_url
        })
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return build_response(500, {"error": "Internal server error"})

def build_response(status_code, body):
    """
    Build a standardized API Gateway response
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        Formatted API Gateway response
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body)
    }
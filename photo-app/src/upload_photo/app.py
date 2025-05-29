import json
import os
import uuid
import boto3
from datetime import datetime
import base64

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PHOTOS_TABLE = os.environ.get('PHOTOS_TABLE')
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')

def lambda_handler(event, context):
    """
    Lambda function to handle photo uploads.
    
    This function:
    1. Receives photo data and metadata from API Gateway
    2. Generates a unique ID for the photo
    3. Uploads the photo to S3
    4. Stores metadata in DynamoDB
    5. Returns the photo ID and other relevant information
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with photo ID and status
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if 'photo' not in body or 'fileName' not in body:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing required fields: photo and fileName'})
            }
        
        # Extract photo data and metadata
        photo_data = body['photo']
        file_name = body['fileName']
        
        # Generate unique photo ID
        photo_id = str(uuid.uuid4())
        
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # Define S3 key
        s3_key = f"{photo_id}/{file_name}"
        
        # Decode base64 photo data
        try:
            # Check if the string starts with data:image prefix and extract the base64 part
            if photo_data.startswith('data:image'):
                photo_data = photo_data.split(',')[1]
            
            decoded_photo = base64.b64decode(photo_data)
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Invalid photo data: {str(e)}'})
            }
        
        # Upload photo to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=decoded_photo,
            ContentType='image/jpeg'  # Assuming JPEG format, adjust as needed
        )
        
        # Store metadata in DynamoDB
        table = dynamodb.Table(PHOTOS_TABLE)
        table.put_item(
            Item={
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp,
                's3Key': s3_key
            }
        )
        
        # Return success response
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp
            })
        }
        
    except Exception as e:
        # Log the error
        print(f"Error: {str(e)}")
        
        # Return error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }
import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import uuid
from datetime import datetime

# Add the src directory to the path so we can import the app module
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/upload_photo'))

# Import the app module
import app

class TestUploadPhoto(unittest.TestCase):
    """Test cases for the upload_photo Lambda function"""

    @patch('app.uuid.uuid4')
    @patch('app.datetime')
    @patch('app.dynamodb.Table')
    @patch('app.s3_client.put_object')
    @patch('app.base64.b64decode')
    def test_successful_upload(self, mock_b64decode, mock_put_object, mock_table, mock_datetime, mock_uuid):
        """Test successful photo upload"""
        # Mock UUID
        mock_uuid_value = '12345678-1234-5678-1234-567812345678'
        mock_uuid.return_value = mock_uuid_value
        
        # Mock datetime
        mock_timestamp = '2023-01-01T12:00:00'
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.isoformat.return_value = mock_timestamp
        mock_datetime.return_value = mock_datetime_instance
        mock_datetime.now.return_value.isoformat.return_value = mock_timestamp
        
        # Mock S3 and DynamoDB
        mock_put_object.return_value = {}
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.put_item.return_value = {}
        
        # Mock base64 decode
        mock_b64decode.return_value = b'decoded_photo_data'
        
        # Create test event
        test_event = {
            'body': json.dumps({
                'photo': 'base64encodedphotodata',
                'fileName': 'test_photo.jpg'
            })
        }
        
        # Call the lambda handler
        response = app.lambda_handler(test_event, {})
        
        # Assert response
        self.assertEqual(response['statusCode'], 201)
        
        # Parse response body
        response_body = json.loads(response['body'])
        
        # Assert response body
        self.assertEqual(response_body['photoId'], mock_uuid_value)
        self.assertEqual(response_body['fileName'], 'test_photo.jpg')
        self.assertEqual(response_body['uploadTimestamp'], mock_timestamp)
        
        # Assert S3 upload was called correctly
        mock_put_object.assert_called_once_with(
            Bucket=app.BUCKET_NAME,
            Key=f"{mock_uuid_value}/test_photo.jpg",
            Body=b'decoded_photo_data',
            ContentType='image/jpeg'
        )
        
        # Assert DynamoDB put_item was called correctly
        mock_table_instance.put_item.assert_called_once_with(
            Item={
                'photoId': mock_uuid_value,
                'fileName': 'test_photo.jpg',
                'uploadTimestamp': mock_timestamp,
                's3Key': f"{mock_uuid_value}/test_photo.jpg"
            }
        )

    def test_missing_required_fields(self):
        """Test error handling when required fields are missing"""
        # Test with missing photo
        test_event_missing_photo = {
            'body': json.dumps({
                'fileName': 'test_photo.jpg'
            })
        }
        
        response = app.lambda_handler(test_event_missing_photo, {})
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Missing required fields', json.loads(response['body'])['error'])
        
        # Test with missing fileName
        test_event_missing_filename = {
            'body': json.dumps({
                'photo': 'base64encodedphotodata'
            })
        }
        
        response = app.lambda_handler(test_event_missing_filename, {})
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Missing required fields', json.loads(response['body'])['error'])

    @patch('app.base64.b64decode')
    def test_invalid_photo_data(self, mock_b64decode):
        """Test error handling when photo data is invalid"""
        # Mock base64 decode to raise an exception
        mock_b64decode.side_effect = Exception('Invalid base64 data')
        
        # Create test event with invalid photo data
        test_event = {
            'body': json.dumps({
                'photo': 'invalid_base64_data',
                'fileName': 'test_photo.jpg'
            })
        }
        
        # Call the lambda handler
        response = app.lambda_handler(test_event, {})
        
        # Assert response
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Invalid photo data', json.loads(response['body'])['error'])

    @patch('app.s3_client.put_object')
    def test_s3_upload_error(self, mock_put_object):
        """Test error handling when S3 upload fails"""
        # Mock S3 put_object to raise an exception
        mock_put_object.side_effect = Exception('S3 upload failed')
        
        # Create test event
        test_event = {
            'body': json.dumps({
                'photo': 'base64encodedphotodata',
                'fileName': 'test_photo.jpg'
            })
        }
        
        # Call the lambda handler
        response = app.lambda_handler(test_event, {})
        
        # Assert response
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body'])['error'], 'Internal server error')

if __name__ == '__main__':
    unittest.main()
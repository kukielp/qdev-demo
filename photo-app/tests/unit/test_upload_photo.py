import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import uuid
import base64

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/upload_photo'))

# Import the Lambda function
import app

class TestUploadPhotoFunction(unittest.TestCase):
    """Test cases for the upload_photo Lambda function"""

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    @patch('uuid.uuid4')
    def test_successful_upload(self, mock_uuid, mock_table, mock_s3):
        """Test successful photo upload"""
        # Mock UUID
        mock_uuid_value = "12345678-1234-5678-1234-567812345678"
        mock_uuid.return_value = MagicMock(hex=mock_uuid_value, __str__=lambda self: mock_uuid_value)
        
        # Mock S3 client
        mock_s3.put_object.return_value = {}
        
        # Mock DynamoDB table
        mock_ddb_table = MagicMock()
        mock_table.return_value = mock_ddb_table
        mock_ddb_table.put_item.return_value = {}
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET_NAME'] = 'test-bucket'
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        
        # Create test event
        test_photo_data = base64.b64encode(b'test photo data').decode('utf-8')
        test_event = {
            'body': json.dumps({
                'photo': test_photo_data,
                'fileName': 'test.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 201)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], mock_uuid_value)
        self.assertEqual(response_body['message'], 'Photo uploaded successfully')
        
        # Verify S3 upload was called correctly
        mock_s3.put_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=f"{mock_uuid_value}/test.jpg",
            Body=base64.b64decode(test_photo_data),
            ContentType='image/jpg'
        )
        
        # Verify DynamoDB put_item was called correctly
        mock_ddb_table.put_item.assert_called_once()
        call_args = mock_ddb_table.put_item.call_args[1]
        self.assertEqual(call_args['Item']['photoId'], mock_uuid_value)
        self.assertEqual(call_args['Item']['fileName'], 'test.jpg')
        self.assertEqual(call_args['Item']['s3Key'], f"{mock_uuid_value}/test.jpg")
        self.assertIn('uploadTimestamp', call_args['Item'])

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_missing_required_fields(self, mock_table, mock_s3):
        """Test handling of missing required fields"""
        # Set environment variables
        os.environ['PHOTOS_BUCKET_NAME'] = 'test-bucket'
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        
        # Create test event with missing fileName
        test_event = {
            'body': json.dumps({
                'photo': 'test_photo_data'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify S3 and DynamoDB were not called
        mock_s3.put_object.assert_not_called()
        mock_table.return_value.put_item.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    def test_s3_upload_error(self, mock_table, mock_s3):
        """Test handling of S3 upload error"""
        # Mock S3 client to raise an exception
        mock_s3.put_object.side_effect = Exception("S3 error")
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET_NAME'] = 'test-bucket'
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        
        # Create test event
        test_photo_data = base64.b64encode(b'test photo data').decode('utf-8')
        test_event = {
            'body': json.dumps({
                'photo': test_photo_data,
                'fileName': 'test.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify DynamoDB was not called
        mock_table.return_value.put_item.assert_not_called()

    @patch('app.s3_client')
    @patch('app.dynamodb.Table')
    @patch('uuid.uuid4')
    def test_dynamodb_error(self, mock_uuid, mock_table, mock_s3):
        """Test handling of DynamoDB error"""
        # Mock UUID
        mock_uuid_value = "12345678-1234-5678-1234-567812345678"
        mock_uuid.return_value = MagicMock(hex=mock_uuid_value, __str__=lambda self: mock_uuid_value)
        
        # Mock S3 client
        mock_s3.put_object.return_value = {}
        
        # Mock DynamoDB table to raise an exception
        mock_ddb_table = MagicMock()
        mock_table.return_value = mock_ddb_table
        mock_ddb_table.put_item.side_effect = Exception("DynamoDB error")
        
        # Set environment variables
        os.environ['PHOTOS_BUCKET_NAME'] = 'test-bucket'
        os.environ['PHOTOS_TABLE_NAME'] = 'test-table'
        
        # Create test event
        test_photo_data = base64.b64encode(b'test photo data').decode('utf-8')
        test_event = {
            'body': json.dumps({
                'photo': test_photo_data,
                'fileName': 'test.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(test_event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        
        # Verify S3 delete_object was called to clean up
        mock_s3.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=f"{mock_uuid_value}/test.jpg"
        )

if __name__ == '__main__':
    unittest.main()
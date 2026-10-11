from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'success': False,
            'status_code': response.status_code,
            'errors': response.data
        }
        response.data = custom_data
    else:
        # Handle unexpected server errors (500)
        return Response({
            'success': False,
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'errors': {'detail': 'An internal server error occurred.'}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
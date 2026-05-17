from rest_framework.pagination import LimitOffsetPagination
from common.response import api_response
from rest_framework import status

class AnalyticsPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200
    
    def get_paginated_response(self, data):
        return api_response(
            status_code=status.HTTP_200_OK,
            data=data,
            meta={
                'total': self.count,
                'limit': self.limit,
                'offset': self.offset,
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            }
        )

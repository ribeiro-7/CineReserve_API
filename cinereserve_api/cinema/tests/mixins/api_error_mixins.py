class ApiErrorMixin:
    def extract_api_error(self, response):
        data = response.data
        if isinstance(data, dict):
            if 'error' in data:
                return str(data['error'])
            if 'detail' in data:
                detail = data['detail']
                if isinstance(detail, list):
                    return str(detail[0])
                return str(detail)
            for value in data.values():
                if isinstance(value, list) and value:
                    return str(value[0])
                if value is not None:
                    return str(value)
        if isinstance(data, list) and data:
            return str(data[0])
        return str(data)

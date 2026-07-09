from django.http import HttpResponse


class CORSMiddleware:
    """
    CORS middleware для поддержки кросс-доменных запросов от React-фронтенда.
    Перехватывает OPTIONS (preflight) запросы и возвращает 200 до того,
    как они дойдут до DRF вьюх.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Для preflight OPTIONS запросов сразу возвращаем ответ
        if request.method == 'OPTIONS':
            response = HttpResponse()
        else:
            response = self.get_response(request)

        # Добавляем CORS-заголовки
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'

        return response

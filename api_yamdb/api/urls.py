from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CategorieViewSet, CommentViewSet, GenreViewSet,
                    ReviewViewSet, TitleViewSet, UserViewSet, get_jwt_token,
                    send_confirmation_code)

app_name = 'api'

api_router = DefaultRouter()
api_router.register('users', UserViewSet, basename='users')
api_router.register('categories', CategorieViewSet, basename='categories')
api_router.register('genres', GenreViewSet, basename='genres')
api_router.register('titles', TitleViewSet, basename='titles')
api_router.register(r'^titles/(?P<title_id>\d+)/reviews',
                    ReviewViewSet,
                    basename='reviews')
api_router.register(
    r'^titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)
v1_auth_routes = [path('signup/', send_confirmation_code, name='register'),
                  path('token/', get_jwt_token, name='get_token'), ]

urlpatterns = [
    path('v1/', include(api_router.urls)),
    path('v1/auth/', include(v1_auth_routes)),
]

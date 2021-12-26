from smtplib import SMTPException

from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Categorie, Comment, Genre, Review, Title, User

from .filters import TitleFilter
from .permissions import (IsAdmin, IsAdminOrReadOnly, IsAuthor, IsModerator,
                          IsSuperuser)
from .serializers import (CategorieSerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer, TitleSerializer,
                          TitleWriteSerializer, UserSerializer)
from .utilities import send_confirmation_code_email


@api_view(['POST'])
def send_confirmation_code(request):
    email = request.data.get('email')
    username = request.data.get('username')
    data = {
        'email': email,
        'username': username
    }
    serializer = UserSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    confirmation_code = User.objects.get(username=username).confirmation_code
    try:
        send_confirmation_code_email(email, confirmation_code)
    except SMTPException:
        return Response('Ошибка при отправке email',
                        status=status.HTTP_400_BAD_REQUEST)
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
def get_jwt_token(request):
    username = request.data.get('username')
    if username is None:
        response = {'username': 'Вы забыли указать username'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    user = get_object_or_404(User, username=username)
    if user.confirmation_code != request.data.get('confirmation_code'):
        response = {'confirmation_code': 'Invalid confirmation code'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    token_refresh = RefreshToken.for_user(user)
    token = str(token_refresh.access_token)
    response = {'token': token}
    return Response(response, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter, )
    search_fields = ('username',)
    permission_classes = (IsAuthenticated, IsSuperuser | IsAdmin,)

    @action(detail=False, permission_classes=(permissions.IsAuthenticated,),
            methods=['GET', 'PATCH'], url_path='me')
    def get_or_patch_yourself(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(
            instance=request.user,
            data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateListDestroyMixin(mixins.CreateModelMixin, mixins.ListModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.GenericViewSet):
    pass


class CategorieViewSet(CreateListDestroyMixin):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly | IsSuperuser,)


class GenreViewSet(CreateListDestroyMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly | IsSuperuser,)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')).all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    permission_classes = (IsAdminOrReadOnly | IsSuperuser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleSerializer
        return TitleWriteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthor | IsModerator
                          | IsAdminOrReadOnly | IsSuperuser]

    def get_queryset(self):
        title = get_object_or_404(Title,
                                  pk=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs['title_id']
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user,
                        title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthor | IsModerator
                          | IsAdminOrReadOnly | IsSuperuser]

    def get_queryset(self):
        return Comment.objects.filter(review__id=self.kwargs['review_id'],
                                      title__id=self.kwargs['title_id'])

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs['review_id'],
                                   title__id=self.kwargs['title_id'])
        serializer.save(author=self.request.user,
                        title=review.title,
                        review=review)

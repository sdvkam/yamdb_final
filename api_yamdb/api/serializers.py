import datetime as dt

from rest_framework import serializers

from reviews.models import Categorie, Comment, Genre, Review, Title, User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'bio', 'email', 'first_name', 'last_name', 'role', 'username')
        model = User

    def validate_username(self, value):
        if value is None:
            raise serializers.ValidationError('Вы забыли написать username!')
        elif value == 'me':
            raise serializers.ValidationError('Нельзя давать username "me"!')
        return value


class CategorieSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Categorie


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Genre


class TitleSerializer(serializers.ModelSerializer):
    category = CategorieSerializer(source='categorie')
    genre = GenreSerializer(many=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = ('__all__')
        model = Title


class TitleWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Categorie.objects.all(),
        slug_field='slug',
        source='categorie'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = ('__all__')
        model = Title

    def validate_year(self, value):
        now_year = dt.date.today().year
        if value > now_year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего')
        return value

    def to_representation(self, instance):
        output_dict = super().to_representation(instance)
        categorie = Categorie.objects.get(slug=output_dict["category"])
        output_dict['category'] = {
            'name': categorie.name, 'slug': output_dict['category']
        }
        time_list = []
        for slug in output_dict['genre']:
            genre = Genre.objects.get(slug=slug)
            time_list.append(
                {'name': genre.name, 'slug': slug}
            )
        output_dict['genre'] = time_list
        return output_dict


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        exclude = ('title',)
        model = Review
        read_only_fields = ('title', 'category', 'genre')

    def validate(self, attrs):
        review_exists = Review.objects.filter(
            author=self.context['request'].user,
            title=self.context['view'].kwargs.get('title_id')).exists()
        if review_exists and self.context['request'].method == 'POST':
            raise serializers.ValidationError(
                'Вы уже оставили отзыв на это произведение')
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        exclude = ('title', 'review')
        model = Comment
        read_only_fields = ('title', 'review')

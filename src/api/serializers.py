from core import models
from rest_framework import serializers

from pprint import pprint

class AuthorSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Author
        fields = (
        'id',
        'salutation',
        'first_name',
        'middle_name',
        'last_name',
        'institution',
        'department',
        'country',
        'author_email',
        'biography',
        'orcid',
        'twitter',
        'linkedin',
        'facebook',
        'sequence',
        )

class EditorSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Editor
        fields = (
        'id',
        'salutation',
        'first_name',
        'middle_name',
        'last_name',
        'institution',
        'department',
        'country',
        'author_email',
        'biography',
        'orcid',
        'twitter',
        'linkedin',
        'facebook',
        'sequence',
        )

class KeywordSerializer(serializers.HyperlinkedModelSerializer):

     class Meta:
         model = models.Keyword
         fields = ('name',)

class SubjectSerializer(serializers.HyperlinkedModelSerializer):

     class Meta:
         model = models.Subject
         fields = ('name',)

class FileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.File
        fields = (
            'id',
            'label',
            'original_filename',
            'uuid_filename',
            'mime_type',
            'kind',
            'sequence',
        )

class FormatSerializer(serializers.HyperlinkedModelSerializer):

    file = FileSerializer(many=False)

    class Meta:
        model = models.Format
        fields = (
            'id',
            'file',
            'name',
            'identifier',
            'file_type',
            'sequence',
        )


class ChapterSerializer(serializers.HyperlinkedModelSerializer):

    file = FileSerializer(many=False)

    class Meta:
        model = models.Format
        fields = (
            'id',
            'file',
            'name',
            'identifier',
            'file_type',
            'sequence',
        )


class PhysicalFormatSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Format
        fields = (
            'id',
            'name',
            'file_type',
            'sequence',
        )

class StageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Stage
        fields = (
            'current_stage',
            'proposal',
            'submission',
            'review',
            'internal_review',
            'external_review',
            'editing',
            'production',
            'publication',
            'declined',
        )

class IdentiferSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Identifier
        fields = (
            'id',
            'identifier',
            'value',
            'displayed',
            'object_type',
            'object_id',
        )

class LanguageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Language
        fields = (
            'code',
            'display',
        )

class BookSerializer(serializers.HyperlinkedModelSerializer):
    license = serializers.ReadOnlyField(source='license.short_name')
    author = AuthorSerializer(many=True)
    editor = EditorSerializer(many=True)
    keywords = KeywordSerializer(many=True)
    subject = SubjectSerializer(many=True)
    identifier = IdentiferSerializer(many=True, source='identifier_set', required=False)

    class Meta:
        model = models.Book
        fields = (
            'id',
            'slug',
            'prefix',
            'title',
            'subtitle',
            'submission_date',
            'publication_date',
            #'series',
            'license',
            'pages',
            'book_type',
            'author',
            'editor',
            'description',
            'keywords',
            'subject',
            'review_type',
            'identifier',
            'peer_review_override',
            )

class JuraBookSerializer(serializers.HyperlinkedModelSerializer):
    """
    This serializer is used only by Ubiquity press
    """
    license = serializers.ReadOnlyField(source='license.code')
    author = AuthorSerializer(many=True)
    editor = EditorSerializer(many=True)
    keywords = KeywordSerializer(many=True)
    subject = SubjectSerializer(many=True)
    formats = FormatSerializer(many=True)
    chapters = ChapterSerializer(many=True, source='chapter_set')
    physical_formats = PhysicalFormatSerializer(many=True,  source='physicalformat_set')
    stage = StageSerializer(many=False)
    identifier = IdentiferSerializer(many=True, source='identifier_set', required=False)
    languages = LanguageSerializer(many=True)

    class Meta:
        model = models.Book
        fields = (
            'id',
            'slug',
            'prefix',
            'title',
            'subtitle',
            'cover',
            'submission_date',
            'publication_date',
            #'series',
            'license',
            'pages',
            'book_type',
            'author',
            'editor',
            'description',
            'keywords',
            'subject',
            'languages',
            'review_type',
            'formats',
            'chapters',
            'physical_formats',
            'stage',
            'identifier',
            'peer_review_override',
            )

    def create(self, validated_data):
        author_data = validated_data.pop('author')
        keyword_data = validated_data.pop('keywords')
        lang_data = validated_data.pop('languages')
        subject_data = validated_data.pop('subject')
        stage_data = validated_data.pop('stage')

        pprint(validated_data)

        book = models.Book.objects.create(**validated_data)

        stage = models.Stage.objects.create(book=book, current_stage="published")

        for author in author_data:
            author = models.Author.objects.create(book=book, **author_data)



        return book

class OMPSerializer(serializers.HyperlinkedModelSerializer):
    """
    This serializer is used only by Ubiquity press
    """
    license = serializers.ReadOnlyField(source='license.code')
    author = AuthorSerializer(many=True)
    keywords = KeywordSerializer(many=True)
    subject = SubjectSerializer(many=True)
    stage = StageSerializer(many=False)
    identifier = IdentiferSerializer(many=True, source='identifier_set', required=False)
    languages = LanguageSerializer(many=True)

    class Meta:
        model = models.Book
        fields = (
            'id',
            'slug',
            'prefix',
            'title',
            'subtitle',
            'cover',
            'submission_date',
            'publication_date',
            #'series',
            'license',
            'pages',
            'book_type',
            'author',
            'description',
            'keywords',
            'subject',
            'languages',
            'review_type',
            'stage',
            'identifier',
            )

    def create(self, validated_data):
        author_data = validated_data.pop('author')
        keyword_data = validated_data.pop('keywords')
        lang_data = validated_data.pop('languages')
        subject_data = validated_data.pop('subject')
        stage_data = validated_data.pop('stage')

        pprint(validated_data)
        book = models.Book.objects.create(**validated_data)
        stage = models.Stage.objects.create(current_stage="published")
        book.stage = stage

        for author in author_data:
            author = models.Author.objects.create(**author)
            book.author.add(author)

        for language in lang_data:
            lang, c = models.Language.objects.get_or_create(**language)
            book.languages.add(lang)

        for subject in subject_data:
            subj, c = models.Subject.objects.get_or_create(**subject)
            book.subject.add(subj)

        for keyword in keyword_data:
            keyw, c = models.Keyword.objects.get_or_create(**keyword)
            book.keywords.add(keyw)


        book.save()
        return book



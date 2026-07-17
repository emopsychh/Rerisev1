from rest_framework import serializers


class LessonProgressUpdateSerializer(serializers.Serializer):
    video_position_sec = serializers.IntegerField(min_value=0)

from rest_framework import serializers
from .models import Score, GolfRound, Player, GolfCourse, Hole

class PlayerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Player
        fields = '__all__'
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.second_name}"

class HoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hole
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    holes = HoleSerializer(many=True, read_only=True, source='hole_set')
    
    class Meta:
        model = GolfCourse
        fields = '__all__'

class RoundSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='hole_set.first.golf_course.name', read_only=True)
    
    class Meta:
        model = GolfRound
        fields = '__all__'

class ScoreSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.first_name', read_only=True)
    hole_number = serializers.IntegerField(source='hole.hole_number', read_only=True)
    hole_par = serializers.IntegerField(source='hole.par', read_only=True)
    
    class Meta:
        model = Score
        fields = [
            'id', 'shots_taken', 'stableford', 'sandy', 'handicap_index',
            'player', 'player_name', 'hole', 'hole_number', 'hole_par', 'golf_round'
        ]
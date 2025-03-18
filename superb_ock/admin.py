from django.contrib import admin
from .models import Hole, GolfRound, GolfCourse, Player, Score
# Register your models here.

admin.site.register(Hole)
admin.site.register(GolfRound)
admin.site.register(GolfCourse)
admin.site.register(Player)
admin.site.register(Score) 
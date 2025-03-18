from django.db import models

# Create your models here.

class GolfCourse(models.Model):
    
    name = models.CharField(max_length=20)
    country = models.CharField(max_length=20,null=True)
    tees = models.CharField(max_length=20,default='White')

class GolfRound(models.Model):

    event = models.CharField(max_length=20,null=True) # 
    holiday = models.BooleanField(default=False)
    date_started = models.DateField(blank=True,null=True)

class Hole(models.Model):
    
    hole_number = models.IntegerField(choices=[(x+1,x+1) for x in range(18)])
    golf_course = models.ForeignKey(GolfCourse,on_delete=models.CASCADE,null=True) # tees implied by choice 
    par = models.IntegerField(choices=[(3,3),(4,4),(5,5)],default=4)
    yards = models.IntegerField(default=400)

class Player(models.Model):

    first_name = models.CharField(max_length=20,null=True)
    second_name = models.CharField(max_length=20,null=True)
    ocks = models.IntegerField(default=0)

class Score(models.Model):

    shots_taken = models.IntegerField(blank=True,null=True)
    stableford = models.IntegerField(blank=True,null=True)
    hole = models.ForeignKey(Hole,on_delete=models.CASCADE,null=True)
    player = models.ForeignKey(Player,on_delete=models.CASCADE,null=True)
    golf_round = models.ForeignKey(GolfRound,on_delete=models.CASCADE,null=True)
    handicap_index = models.FloatField()
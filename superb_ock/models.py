from django.db import models

# Create your models here.

class GolfCourse(models.Model):
    
    name = models.CharField(max_length=20)
    country = models.CharField(max_length=20,null=True)
    tees = models.CharField(max_length=20,default='White')
    slope_rating = models.IntegerField(default=113)
    course_rating = models.DecimalField(decimal_places=1,max_digits=3,default=72)
    slug = models.SlugField(default="", null=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.tees} Tees"

class GolfEvent(models.Model):

    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name

class GolfRound(models.Model):

    event = models.ForeignKey(GolfEvent,on_delete=models.CASCADE,default=1)
    holiday = models.BooleanField(default=False)
    date_started = models.DateField(blank=True,null=True)

class Hole(models.Model):
    
    hole_number = models.IntegerField(choices=[(x+1,x+1) for x in range(18)])
    golf_course = models.ForeignKey(GolfCourse,on_delete=models.CASCADE,null=True) # tees implied by choice 
    par = models.IntegerField(choices=[(3,3),(4,4),(5,5)],default=4)
    yards = models.IntegerField(default=400)
    stroke_index = models.IntegerField(choices=[(x+1,x+1) for x in range(18)],default=1)

    def __str__(self):
        return f"{self.golf_course} - Hole {self.hole_number}"

class Player(models.Model):

    first_name = models.CharField(max_length=20,null=True)
    second_name = models.CharField(max_length=20,null=True)
    ocks = models.IntegerField(default=0)
    handedness = models.CharField(max_length=20,default='Right')
    picture = models.ImageField(blank=True,null=True)
    info = models.TextField(blank=True,null=True)
    slug = models.SlugField(default="", null=False)

    def __str__(self):
        return f"{self.first_name} {self.second_name}"

class Score(models.Model):

    shots_taken = models.IntegerField(blank=True,null=True)
    stableford = models.IntegerField(blank=True,null=True)
    hole = models.ForeignKey(Hole,on_delete=models.CASCADE,null=True)
    player = models.ForeignKey(Player,on_delete=models.CASCADE,null=True)
    golf_round = models.ForeignKey(GolfRound,on_delete=models.CASCADE,null=True)
    handicap_index = models.FloatField()
    sandy = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.player} {self.hole} {self.golf_round}"
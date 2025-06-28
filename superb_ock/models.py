from django.db import models

# Create your models here.

class CarouselImage(models.Model):
    title = models.CharField(max_length=100, help_text="Title displayed on the image")
    description = models.TextField(max_length=200, help_text="Description displayed on the image")
    image = models.ImageField(upload_to='carousel/', help_text="Upload carousel image")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    is_active = models.BooleanField(default=True, help_text="Show this image in the carousel")
    
    # Focal point controls (0-100 percentage)
    focal_point_x = models.PositiveIntegerField(
        default=50, 
        help_text="Horizontal focal point (0=left, 50=center, 100=right)"
    )
    focal_point_y = models.PositiveIntegerField(
        default=50, 
        help_text="Vertical focal point (0=top, 50=center, 100=bottom)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Carousel Image"
        verbose_name_plural = "Carousel Images"
    
    def __str__(self):
        return f"{self.title} (Order: {self.order})"

def hole_choice():
    return [(x+1,f'{x+1}') for x in range(18)]

class GolfCourse(models.Model):
    
    name = models.CharField(max_length=20)
    country = models.CharField(max_length=20,null=True)
    tees = models.CharField(max_length=20,default='White')
    slope_rating = models.IntegerField(default=113)
    course_rating = models.FloatField(default=72)
    par = models.IntegerField(default=72)
    slug = models.SlugField(default="", null=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.tees} Tees"

class GolfEvent(models.Model):

    format_choices = [
        ("best_three_of_five", "Best Three of All"),
        ("best_last_rounds_counts", "Best Two of First, Last Round Counts"),
    ]

    name = models.CharField(max_length=40)
    scoring = models.TextField(max_length=40,choices=format_choices,default='best_three_of_five')

    def __str__(self):
        return self.name

class GolfRound(models.Model):

    event = models.ForeignKey(GolfEvent,on_delete=models.CASCADE,default=1)
    date_started = models.DateField(blank=True,null=True)

    def __str__(self):
        return f"{self.event} - {self.pk}"

class Hole(models.Model):
    
    hole_number = models.IntegerField(choices=hole_choice())
    golf_course = models.ForeignKey(GolfCourse,on_delete=models.CASCADE,null=True) # tees implied by choice 
    par = models.IntegerField(choices=[(3,'3'),(4,'4'),(5,'5')],default=4)
    yards = models.IntegerField(default=400)
    stroke_index = models.IntegerField(choices=hole_choice(),default=1)

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
    
class Highlight(models.Model):
    title = models.CharField(max_length=40)
    video = models.FileField(upload_to='highlights')
    thumbnail = models.ImageField(blank=True)

    def __str__(self):
        return self.title

class Score(models.Model):

    shots_taken = models.IntegerField(blank=True,null=True)
    stableford = models.IntegerField(blank=True,null=True)
    hole = models.ForeignKey(Hole,on_delete=models.CASCADE,null=True)
    player = models.ForeignKey(Player,on_delete=models.CASCADE,null=True)
    golf_round = models.ForeignKey(GolfRound,on_delete=models.CASCADE,null=True)
    handicap_index = models.FloatField()
    sandy = models.BooleanField(default=False)
    highlight = models.ManyToManyField(Highlight,blank=True)

    def __str__(self):
        return f"{self.player} {self.hole} {self.golf_round}"
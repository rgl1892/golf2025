from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.views.decorators.csrf import csrf_exempt

from requests import request
from collections import defaultdict
import json

from .models import *
from .forms import *


def jsonify(query):
    return json.dumps(list(query), cls=DjangoJSONEncoder)


# Create your views here.
def getWeather(lat, long):
    weather_codes = {
        "0": "Clear sky ☀️",
        "1": "Mainly Clear ☀️",
        "2": "Partly Cloudy",
        "3": "Overcast",
        "45": "Fog",
        "48": "Depositing Rime Fog",
        "51": "Light Drizzle",
        "53": "Moderate Drizzle",
        "55": "Dense Drizzle",
        "56": "Light Freezing Dizzle",
        "57": "Dense Freezing Drizzle",
        "61": "Slight Rain",
        "63": "Moderate Rain",
        "65": "Heavy Rain",
        "66": "Light Freezing Rain",
        "67": "Heavy Freezing Rain",
        "71": "Slight Snowfall",
        "73": "Moderate Snowfall",
        "75": "Heavy Snowfall",
        "77": "Snow Grains",
        "80": "Slight Rain Showers",
        "81": "Moderate Rain Showers",
        "82": "Violent Rain Showers",
        "85": "Sight Snow Showers",
        "95": "Slight Thunderstorms",
        "96": "Moderate Thunderstorms",
        "99": "Thunderstorms with hail",
    }

    weather = request(
        "GET",
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&current=temperature_2m,weather_code",
    ).json()
    return [weather, weather_codes[f"{weather['current']['weather_code']}"]]


def signUpUser(request):
    if request.method == "GET":

        return render(
            request, "superb_ock/auth/signUpUser.html", {"form": EditUserForm()}
        )

    else:
        if request.POST["password1"] == request.POST["password2"]:
            try:
                user = User.objects.create_user(
                    request.POST["username"], password=request.POST["password1"]
                )
                user.save()
                login(request, user)
                return redirect("home")
            except IntegrityError:
                return render(
                    request,
                    "superb_ock/auth/signUpUser.html",
                    {"form": EditUserForm(), "error": "Username Already Taken"},
                )

        else:

            return render(
                request,
                "superb_ock/auth/signUpUser.html",
                {"form": EditUserForm(), "error": "Passwords did not match"},
            )


def logOutUser(request):
    logout(request)
    return redirect("home")


def logInUser(request):
    if request.method == "GET":
        return render(request, "superb_ock/auth/login.html", {"form": EditAuthForm()})

    else:
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if user == None:
            return render(
                request,
                "superb_ock/auth/login.html",
                {"form": EditAuthForm(), "error": "Unknown User / Incorrect Password"},
            )
        else:
            login(request, user)
            return redirect("home")


class Home(View):

    template_name = "superb_ock/homepage/home.html"

    def get_context(self):
        context = {"test": "Test"}
        return context

    def get(self, request):

        return render(request, self.template_name, context=self.get_context())


class NewRound(View):

    template_name = "superb_ock/new_round/new_round.html"

    def get_context(self):

        courses = GolfCourse.objects.values()
        courses = jsonify(courses)

        players = Player.objects.order_by("first_name").values()
        players = jsonify(players)

        events = GolfEvent.objects.order_by("name").values()

        context = {
            "courses": courses,
            "players": players,
            "events": events,
        }
        return context

    def get(self, request):
        return render(request, self.template_name, context=self.get_context())

    def post(self, request):

        course_id = request.POST.get("courseId")

        # Extract players from request data (avoids unnecessary dictionary creation)
        players = [
            {
                "id": request.POST.get(f"player_{x+1}"),
                "index": request.POST.get(f"player_{x+1}_index"),
            }
            for x in range(4)
            if request.POST.get(f"player_{x+1}")
        ]

        # Create the golf round
        golf_round = GolfRound.objects.create(event_id=request.POST.get("eventId"))

        # Fetch all holes for the course in a single query, indexed by hole_number
        holes = {
            hole.hole_number: hole
            for hole in Hole.objects.filter(golf_course_id=course_id)
        }

        # Create Score objects efficiently
        score_objects = [
            Score(
                shots_taken=None,
                stableford=None,
                hole=holes.get(x + 1),  # Efficient lookup in the dictionary
                player_id=player["id"],
                golf_round_id=golf_round.pk,
                handicap_index=player["index"],
                sandy=False,
            )
            for player in players
            for x in range(18)
            if holes.get(x + 1)  # Ensures hole exists before creating a Score
        ]

        # Bulk create to reduce database hits
        Score.objects.bulk_create(score_objects)
        course = GolfCourse.objects.filter(id=course_id).get()

        player_objects = list(
            Player.objects.filter(id__in=[player["id"] for player in players]).values()
        )

        # Create a lookup dictionary for fast access
        player_index_lookup = {
            int(person["id"]): float(person["index"]) for person in players
        }

        # Update player objects with handicap calculations
        for player in player_objects:
            player_id = int(player["id"])
            if player_id in player_index_lookup:
                player["index"] = player_index_lookup[player_id]
                player["handicap"] = round(
                    player["index"] * (float(course.slope_rating) / 113)
                    + float(course.course_rating)
                    - float(course.par)
                )

        context = {"course": course, "players": player_objects}

        # Return response
        return render(
            request, "superb_ock/new_round/round_created.html", context=context
        )


class RoundsOverview(View):

    template_name = "superb_ock/rounds/overview.html"

    def convert_to_dict(self, d):
        if isinstance(d, defaultdict):
            return {k: self.convert_to_dict(v) for k, v in d.items()}
        return d

    def group_scores(self, data):
        grouped = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(lambda: {"shots_taken": 0, "stableford": 0})
                )
            )
        )

        for entry in data:
            event = entry["golf_round__event__name"]
            course = f"{entry['hole__golf_course__name']} - {entry['hole__golf_course__tees']}{entry['golf_round_id']:05}"
            id = entry["golf_round_id"]
            player = entry["player__first_name"]

            grouped[event][course][id][player]["shots_taken"] += (
                entry["shots_taken"] if entry["shots_taken"] else 0
            )
            grouped[event][course][id][player]["stableford"] += (
                entry["stableford"] if entry["stableford"] else 0
            )

        return self.convert_to_dict(grouped)

    def get(self, request):
        scores = (
            Score.objects.all()
            .order_by("-golf_round__event__name", "golf_round_id", "player__first_name")
            .values(
                "player__first_name",
                "shots_taken",
                "stableford",
                "golf_round__event__name",
                "hole__golf_course__name",
                "hole__golf_course__tees",
                "golf_round_id",
            )
        )
        grouped_data = self.group_scores(scores)

        return render(request, self.template_name, context={"rounds": grouped_data})


class GolfRoundView(View):

    template_name = "superb_ock/rounds/round.html"

    def get(self, request, round_id):
        scores = (
            Score.objects.filter(golf_round__id=round_id)
            .select_related()
            .order_by("player__first_name")
            .values(
                "player_id",
                "shots_taken",
                "stableford",
                "player__first_name",
                "hole__hole_number",
                "hole__par",
                "hole__yards",
                "hole__stroke_index",
            )
        )

        grouped_summary = defaultdict(
            lambda: {"total_shots": 0, "total_stableford": 0, "scores": []}
        )
        for item in scores:
            player_id = item["player__first_name"]
            grouped_summary[player_id]["total_shots"] += (
                item["shots_taken"] if item["shots_taken"] else 0
            )
            grouped_summary[player_id]["total_stableford"] += (
                item["stableford"] if item["stableford"] else 0
            )
            grouped_summary[player_id]["scores"].append(item)
        grouped_data = dict(grouped_summary)

        return render(
            request,
            self.template_name,
            context={"scores": grouped_data, "round_id": round_id},
        )


class EditScore(View):

    template_name = "superb_ock/rounds/edit_score_2.html"

    def get_context_data(self, round_id, hole_number):

        scores = (
            Score.objects.filter(golf_round=round_id)
            .order_by("player__first_name")
            .values(
                "shots_taken",
                "stableford",
                "id",
                "hole__hole_number",
                "hole__yards",
                "hole__par",
                "player__first_name",
                "player__second_name",
                "handicap_index",
                "sandy",
                "golf_round",
                "hole__stroke_index",
                "hole__golf_course__slope_rating",
                "hole__golf_course__course_rating",
                "hole__golf_course__par",
            )
        )

        scores_per_hole = [
            [score for score in scores if score["hole__hole_number"] == x + 1]
            for x in range(18)
        ]
        context = {
            "scores_per_hole": scores_per_hole,
            "round_id": round_id,
            "hole_number": hole_number,
        }
        return context

    def get(self, request, round_id, hole_number):

        if request.user.is_authenticated:
            return render(
                request,
                self.template_name,
                self.get_context_data(round_id, hole_number),
            )
        else:
            return redirect("golf_round",round_id=round_id)

    # @csrf_exempt
    # def submit_scores(request):
    #     if request.method == "POST":
    #         hole_id = request

    def post(self, request, round_id, hole_number):
        post_data = request.POST

        formatted_data = {
            
        }

        # Temporary dict to hold player data
        players = defaultdict(lambda: {'shots': None, 'stable': None})

        for key in post_data:
            if key.startswith('shots_') or key.startswith('stable_'):
                # Get player ID from the key
                prefix, player_id_str = key.split('_')
                player_id = int(player_id_str)
                
                # Get the value and convert it from list to int
                value = int(post_data.getlist(key)[0])
                
                # Update the appropriate field
                if prefix == 'shots':
                    players[player_id]['shots'] = value
                elif prefix == 'stable':
                    players[player_id]['stable'] = value

        # Merge the player data into the final structure
        formatted_data.update(players)

        print(formatted_data)
        
        for score_id,points in formatted_data.items():
            Score.objects.filter(pk=score_id).update(shots_taken=points['shots'],stableford=points['stable'])
        return render(
            request, self.template_name, self.get_context_data(round_id, hole_number)
        )

class HeatMap(View):

    def get(self,request):
        return render(
            request, 'superb_ock/stats/heatmap.html'
        )
    
class EventView(View):

    template_name = 'superb_ock/events/overview.html'

    def get(self,request,event_id):
        # get scores
        scores = list(Score.objects.filter(golf_round__event=event_id).values(
            'player__first_name', 'player__second_name','stableford', 'golf_round_id', 'hole_id',
            'shots_taken','hole__golf_course__name','hole__golf_course__tees','golf_round__event__scoring'
            ))

        # manip the data to get infor per player per round
        player_rounds = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'course': ''}))

        for score in scores:
            name = f"{score['player__first_name']} {score['player__second_name']}"
            round_id = score['golf_round_id']
            course = f"{score['hole__golf_course__name']} - {score['hole__golf_course__tees']}"
            
            player_rounds[name][round_id]['total'] += score['stableford']
            player_rounds[name][round_id]['course'] = course  
            player_rounds[name][round_id]['scoring'] = score['golf_round__event__scoring']  
            
    

        # get the totals
        leaderboard = []

        for player__first_name, round_scores in player_rounds.items():
            top3_scores = sorted(
                round_scores.values(), 
                key=lambda x: x['total'], 
                reverse=True
            )[:3]
            leaderboard.append({
                'player__first_name': player__first_name,
                'round_totals': dict(round_scores),
                'best_3_total': sum(r['total'] for r in top3_scores),

            })

        # Step 4: Sort leaderboard
        leaderboard = sorted(leaderboard, key=lambda x: x['best_3_total'], reverse=True)
        all_round_numbers = set()
        for player in leaderboard:
            all_round_numbers.update(player['round_totals'].keys())
        round_numbers = sorted(all_round_numbers)

        cleaned_leaderboard = []
        for player in leaderboard:
            rounds = []
            round_dict = player['round_totals']
            
            best_round_score = max([r['total'] for r in round_dict.values()] or [0])
            
            for round_num in round_numbers:
                round_info = round_dict.get(round_num)
                if round_info:
                    rounds.append({
                        'num': round_num,
                        'total': round_info['total'],
                        'course': round_info['course'],
                        'is_best': round_info['total'] == best_round_score
                    })
                else:
                    rounds.append({
                        'num': round_num,
                        'total': None,
                        'course': None,
                        'is_best': False
                    })
            
            cleaned_leaderboard.append({
                'player': player['player__first_name'],
                'rounds': rounds,
                'best_3_total': player['best_3_total']
            })
        courses = []
        for rounds in cleaned_leaderboard[0]['rounds']:
            courses.append({'course':rounds['course'],'id':rounds['num']})

            
        context = {
            'leaderboard': cleaned_leaderboard,
            'round_numbers': round_numbers,
            'courses':courses
        }

        return render(request,self.template_name,context=context)
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection

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
            .order_by("golf_round__event__name", "golf_round_id", "player__first_name")
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

        return render(request, self.template_name, context={"scores": grouped_data})

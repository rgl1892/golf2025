from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from requests import request
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
        
        scores = list(Score.objects.filter(golf_round__event=3).values(
            'player__first_name', 'player__second_name','stableford', 'golf_round_id', 'hole_id',
            'shots_taken','hole__golf_course__name','hole__golf_course__tees','golf_round__event__scoring'
            ))

        # manip the data to get infor per player per round
        player_rounds = {}

        for score in scores:
            name = f"{score['player__first_name']} {score['player__second_name']}"
            round_id = score['golf_round_id']
            course = f"{score['hole__golf_course__name']} - {score['hole__golf_course__tees']}"
            
            if name not in player_rounds:
                player_rounds[name] = {}
            if round_id not in player_rounds[name]:
                player_rounds[name][round_id] = {'total': 0, 'course': ''}
            
            player_rounds[name][round_id]['total'] += score['stableford'] or 0
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
                'best_3_total': sum(int(r['total']) if r['total'] is not None else 0 for r in top3_scores),

            })

        # Get event scoring format for determining counting rounds (hardcoded event 3 for homepage)
        event = GolfEvent.objects.get(id=3)
        scoring_format = event.scoring

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
            
            # Determine counting rounds based on scoring format
            valid_rounds = [{'num': k, 'total': v['total']} for k, v in round_dict.items() if v['total'] is not None]
            
            if scoring_format == "best_three_of_five":
                # Best 3 rounds overall
                counting_rounds = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
                counting_round_ids = [r['num'] for r in counting_rounds]
            elif scoring_format == "best_last_rounds_counts":
                # Best 2 of first rounds + last round counts
                if len(valid_rounds) >= 3:
                    sorted_rounds = sorted(valid_rounds, key=lambda x: x['num'])
                    last_round = sorted_rounds[-1]
                    first_rounds = sorted_rounds[:-1]
                    best_first_two = sorted(first_rounds, key=lambda x: x['total'], reverse=True)[:2]
                    counting_round_ids = [r['num'] for r in best_first_two] + [last_round['num']]
                else:
                    counting_round_ids = [r['num'] for r in valid_rounds]
            else:
                # Default to best 3
                counting_rounds = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
                counting_round_ids = [r['num'] for r in counting_rounds]
            
            best_round_score = max([r['total'] for r in round_dict.values()] or [0])
            
            for round_num in round_numbers:
                round_info = round_dict.get(round_num)
                if round_info:
                    rounds.append({
                        'num': round_num,
                        'total': round_info['total'],
                        'course': round_info['course'],
                        'is_best': round_info['total'] == best_round_score,
                        'is_counting': round_num in counting_round_ids
                    })
                else:
                    rounds.append({
                        'num': round_num,
                        'total': None,
                        'course': None,
                        'is_best': False,
                        'is_counting': False
                    })
            
            cleaned_leaderboard.append({
                'player': player['player__first_name'],
                'rounds': rounds,
                'best_3_total': player['best_3_total']
            })
        courses = []
        if cleaned_leaderboard:
            for rounds in cleaned_leaderboard[0]['rounds']:
                courses.append({'course':rounds['course'],'id':rounds['num']})

            
        # Get active carousel images
        carousel_images = CarouselImage.objects.filter(is_active=True).order_by('order', '-created_at')
        
        context = {
            'leaderboard': cleaned_leaderboard,
            'round_numbers': round_numbers,
            'courses': courses,
            'carousel_images': carousel_images
        }
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
        golf_round = GolfRound.objects.create(
            event_id=request.POST.get("eventId"),
            date_started=timezone.now().date()
        )

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
        if isinstance(d, dict):
            return {k: self.convert_to_dict(v) for k, v in d.items()}
        return d

    def group_scores(self, data):
        grouped = {}

        for entry in data:
            event = entry["golf_round__event__name"]
            course = f"{entry['hole__golf_course__name']} - {entry['hole__golf_course__tees']}{entry['golf_round_id']:05}"
            id = entry["golf_round_id"]
            player = entry["player__first_name"]

            if event not in grouped:
                grouped[event] = {}
            if course not in grouped[event]:
                grouped[event][course] = {}
            if id not in grouped[event][course]:
                grouped[event][course][id] = {}
            if player not in grouped[event][course][id]:
                grouped[event][course][id][player] = {"shots_taken": 0, "stableford": 0}

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
                "golf_round__event_id",
            )
        )
        
        # Get the current round's event ID for cross-round summary
        current_round = GolfRound.objects.get(id=round_id)
        event_id = current_round.event.pk
        
        # Get summary of other concurrent rounds in the same event (same day only)
        other_rounds_summary = (
            Score.objects.filter(
                golf_round__event_id=event_id,
                golf_round__date_started=current_round.date_started
            )
            .exclude(golf_round__id=round_id)
            .values("golf_round_id", "player__first_name")
            .annotate(
                total_stableford=models.Sum("stableford"),
                total_shots=models.Sum("shots_taken"),
                holes_played=models.Count("id", filter=models.Q(shots_taken__isnull=False))
            )
            .order_by("golf_round_id", "-total_stableford")
        )
        
        # Group other rounds data
        other_rounds = {}
        for summary in other_rounds_summary:
            round_id_key = summary["golf_round_id"]
            if round_id_key not in other_rounds:
                other_rounds[round_id_key] = {
                    "players": [],
                    "max_holes_played": 0
                }
            other_rounds[round_id_key]["players"].append({
                "player": summary["player__first_name"],
                "total_stableford": summary["total_stableford"] or 0,
                "total_shots": summary["total_shots"] or 0,
                "holes_played": summary["holes_played"]
            })
            # Track max holes played for this round
            other_rounds[round_id_key]["max_holes_played"] = max(
                other_rounds[round_id_key]["max_holes_played"],
                summary["holes_played"]
            )

        grouped_summary = {}
        for item in scores:
            player_id = item["player__first_name"]
            if player_id not in grouped_summary:
                grouped_summary[player_id] = {"total_shots": 0, "total_stableford": 0, "scores": []}
            grouped_summary[player_id]["total_shots"] += (
                item["shots_taken"] if item["shots_taken"] else 0
            )
            grouped_summary[player_id]["total_stableford"] += (
                item["stableford"] if item["stableford"] else 0
            )
            grouped_summary[player_id]["scores"].append(item)
        grouped_data = dict(grouped_summary)
        summary_data = {}
        for player, data in grouped_data.items():
            summary_data[player] = {
                'front_nine': 0,
                'back_nine': 0,
                'total_shots': 0,
                'front_nine_stableford': 0,
                'back_nine_stableford': 0, 
                'total_stableford': 0,
            }
            for score in data.get('scores', []):
                if score['hole__hole_number'] < 10:
                    summary_data[player]['front_nine'] += score['shots_taken'] if score['shots_taken'] else 0
                    summary_data[player]['total_shots'] += score['shots_taken'] if score['shots_taken'] else 0
                    summary_data[player]['front_nine_stableford'] += score['stableford'] if score['stableford'] else 0
                    summary_data[player]['total_stableford'] += score['stableford'] if score['stableford'] else 0
                else:
                    summary_data[player]['back_nine'] += score['shots_taken'] if score['shots_taken'] else 0
                    summary_data[player]['total_shots'] += score['shots_taken'] if score['shots_taken'] else 0
                    summary_data[player]['back_nine_stableford'] += score['stableford'] if score['stableford'] else 0
                    summary_data[player]['total_stableford'] += score['stableford'] if score['stableford'] else 0

        return render(
            request,
            self.template_name,
            context={
                "scores": grouped_data,
                "round_id": round_id,
                "summary": summary_data,
                "other_rounds": other_rounds
                },
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
        players = {}

        for key in post_data:
            if key.startswith('shots_') or key.startswith('stable_'):
                # Get player ID from the key
                prefix, player_id_str = key.split('_')
                player_id = int(player_id_str)
                
                # Get the value and convert it from list to int
                value = int(post_data.getlist(key)[0])
                
                # Update the appropriate field
                if player_id not in players:
                    players[player_id] = {'shots': None, 'stable': None}
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
        player_rounds = {}

        for score in scores:
            name = f"{score['player__first_name']} {score['player__second_name']}"
            round_id = score['golf_round_id']
            course = f"{score['hole__golf_course__name']} - {score['hole__golf_course__tees']}"
            
            if name not in player_rounds:
                player_rounds[name] = {}
            if round_id not in player_rounds[name]:
                player_rounds[name][round_id] = {'total': 0, 'course': ''}
            
            player_rounds[name][round_id]['total'] += score['stableford'] or 0
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
                'best_3_total': sum(int(r['total']) if r['total'] is not None else 0 for r in top3_scores),

            })

        # Get event scoring format for determining counting rounds
        event = GolfEvent.objects.get(id=event_id)
        scoring_format = event.scoring

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
            
            # Determine counting rounds based on scoring format
            valid_rounds = [{'num': k, 'total': v['total']} for k, v in round_dict.items() if v['total'] is not None]
            
            if scoring_format == "best_three_of_five":
                # Best 3 rounds overall
                counting_rounds = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
                counting_round_ids = [r['num'] for r in counting_rounds]
            elif scoring_format == "best_last_rounds_counts":
                # Best 2 of first rounds + last round counts
                if len(valid_rounds) >= 3:
                    sorted_rounds = sorted(valid_rounds, key=lambda x: x['num'])
                    last_round = sorted_rounds[-1]
                    first_rounds = sorted_rounds[:-1]
                    best_first_two = sorted(first_rounds, key=lambda x: x['total'], reverse=True)[:2]
                    counting_round_ids = [r['num'] for r in best_first_two] + [last_round['num']]
                else:
                    counting_round_ids = [r['num'] for r in valid_rounds]
            else:
                # Default to best 3
                counting_rounds = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
                counting_round_ids = [r['num'] for r in counting_rounds]
            
            best_round_score = max([r['total'] for r in round_dict.values()] or [0])
            
            for round_num in round_numbers:
                round_info = round_dict.get(round_num)
                if round_info:
                    rounds.append({
                        'num': round_num,
                        'total': round_info['total'],
                        'course': round_info['course'],
                        'is_best': round_info['total'] == best_round_score,
                        'is_counting': round_num in counting_round_ids
                    })
                else:
                    rounds.append({
                        'num': round_num,
                        'total': None,
                        'course': None,
                        'is_best': False,
                        'is_counting': False
                    })
            
            cleaned_leaderboard.append({
                'player': player['player__first_name'],
                'rounds': rounds,
                'best_3_total': player['best_3_total']
            })
        courses = []
        if cleaned_leaderboard:
            for rounds in cleaned_leaderboard[0]['rounds']:
                courses.append({'course':rounds['course'],'id':rounds['num']})

            
        # Generate cumulative data for chart
        cumulative_data = self.generate_cumulative_data(cleaned_leaderboard, round_numbers)
        
        # Calculate max holes for chart (usually 54 holes for 3 counting rounds)
        max_holes = max([len(player['data']) for player in cumulative_data]) if cumulative_data else 0
        hole_labels = list(range(1, max_holes + 1))
        
        context = {
            'leaderboard': cleaned_leaderboard,
            'round_numbers': round_numbers,
            'courses': courses,
            'cumulative_data': json.dumps(cumulative_data),
            'hole_labels_json': json.dumps(hole_labels),
            'max_holes': max_holes
        }

        return render(request,self.template_name,context=context)
    
    def generate_cumulative_data(self, leaderboard, round_numbers):
        """Generate cumulative scoring data for chart - by hole progression"""
        from django.db.models import Q
        
        cumulative_data = []
        
        # Get event scoring format
        event_id = self.kwargs.get('event_id')
        event = GolfEvent.objects.get(id=event_id)
        scoring_format = event.scoring
        
        # Get all hole-by-hole scores for this event
        all_hole_scores = Score.objects.filter(
            golf_round__event=event_id
        ).select_related('player', 'golf_round', 'hole').order_by(
            'golf_round_id', 'hole__hole_number'
        )
        
        # Group scores by player and round
        player_round_scores = {}
        for score in all_hole_scores:
            player_name = f"{score.player.first_name} {score.player.second_name}"
            if player_name not in player_round_scores:
                player_round_scores[player_name] = {}
            if score.golf_round_id not in player_round_scores[player_name]:
                player_round_scores[player_name][score.golf_round_id] = []
            
            player_round_scores[player_name][score.golf_round_id].append({
                'hole': score.hole.hole_number,
                'stableford': score.stableford or 0
            })
        
        # Calculate round totals and determine counting rounds for each player
        for player_data in leaderboard:
            player_name = player_data['player']
            rounds = player_data['rounds']
            
            # Determine counting rounds based on scoring format
            valid_rounds = [r for r in rounds if r.get('total') is not None]
            
            if scoring_format == "best_three_of_five":
                # Best 3 rounds overall
                counting_rounds = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
                counting_round_ids = [r['num'] for r in counting_rounds]
            elif scoring_format == "best_last_rounds_counts":
                # Best 2 of first rounds + last round counts
                if len(valid_rounds) >= 3:
                    # Sort by round ID to get chronological order
                    sorted_rounds = sorted(valid_rounds, key=lambda x: x['num'])
                    last_round = sorted_rounds[-1]  # Last round always counts
                    first_rounds = sorted_rounds[:-1]  # All except last
                    
                    # Best 2 of the first rounds
                    best_first_two = sorted(first_rounds, key=lambda x: x['total'], reverse=True)[:2]
                    
                    counting_rounds = best_first_two + [last_round]
                    counting_round_ids = [r['num'] for r in counting_rounds]
                else:
                    # Not enough rounds, use all available
                    counting_round_ids = [r['num'] for r in valid_rounds]
            else:
                # Default to best 3
                counting_rounds = sorted(valid_rounds, key=lambda x: x['total'], reverse=True)[:3]
                counting_round_ids = [r['num'] for r in counting_rounds]
            
            if player_name not in player_round_scores:
                continue
            
            # Get hole-by-hole data for counting rounds only, in chronological order
            all_counting_holes = []
            # Sort counting round IDs chronologically (by round ID)
            counting_round_ids_sorted = sorted(counting_round_ids)
            
            for round_id in counting_round_ids_sorted:
                if round_id in player_round_scores[player_name]:
                    round_holes = player_round_scores[player_name][round_id]
                    # Sort holes within each round (1-18)
                    round_holes.sort(key=lambda x: x['hole'])
                    # Add round_id to each hole for reference
                    for hole in round_holes:
                        hole['round_id'] = round_id
                    all_counting_holes.extend(round_holes)
            
            # Build cumulative progression by re-indexed hole position
            player_cumulative = []
            cumulative_total = 0
            
            for i, hole_data in enumerate(all_counting_holes):
                cumulative_total += hole_data['stableford']
                
                player_cumulative.append({
                    'hole_number': i + 1,  # Re-indexed position (1, 2, 3, ...)
                    'actual_hole': hole_data['hole'],  # Original hole number (1-18)
                    'round_id': hole_data['round_id'],  # Which round this hole is from
                    'hole_score': hole_data['stableford'],
                    'cumulative': cumulative_total
                })
            
            cumulative_data.append({
                'player': player_name,
                'data': player_cumulative,
                'final_total': cumulative_total
            })
        
        return cumulative_data
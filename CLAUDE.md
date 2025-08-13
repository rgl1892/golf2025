# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Django web application for golf score tracking and statistics called "golf2025". The main app is named `superb_ock` and provides comprehensive golf round management, player statistics, and highlight video features.

## Development Commands

### Core Django Commands
- `python manage.py runserver` - Start development server
- `python manage.py migrate` - Apply database migrations
- `python manage.py makemigrations` - Create new migrations
- `python manage.py createsuperuser` - Create admin user
- `python manage.py collectstatic` - Collect static files

### Custom Management Commands
- `python manage.py load_highlights` - Import highlights from CSV files and link to scores
- `python manage.py setup_carousel` - Set up carousel images
- `python manage.py generate_thumbnails` - Generate thumbnails for highlight videos

### Database
- Uses SQLite database (`db.sqlite3`) for development
- Database includes models for golf courses, players, rounds, scores, highlights, and carousel images

## Architecture Overview

### Models (superb_ock/models.py)
Key models include:
- **GolfCourse** - Golf course information with tees, slope rating, course rating
- **Player** - Player profiles with handicap tracking
- **GolfRound** - Individual golf rounds linked to events and players
- **Score** - Individual hole scores with detailed statistics
- **Highlight** - Video highlights linked to specific scores
- **CarouselImage** - Homepage carousel management

### Views Structure
- **Main views** (`views.py`) - Core application views for rounds, scores, highlights
- **Statistics views** (`views_stats/`) - Separated statistics functionality:
  - `stats.py` - General statistics and heatmap data
  - `player_stats.py` - Player-specific statistics
  - `course_stats.py` - Course-specific statistics
- **Admin views** (`admin_views.py`) - Custom admin functionality for highlight management

### URL Structure
- Root: Homepage with carousel
- `/new_round` - Create new golf round
- `/rounds` - Rounds overview
- `/rounds/<id>` - Individual round details
- `/rounds/<id>/<hole>` - Edit specific hole score
- `/highlights/` - Video highlights gallery
- `/heatmap/` - Score heatmap visualization
- `/event/<id>` - Event overview

### Templates
Uses Bootstrap-based templates with:
- Base template with navigation and theming
- Modular partials for golf score tables
- Separate authentication templates
- Admin templates for highlight management

### Static Files
- Bootstrap CSS and custom styling
- JavaScript for charts, round entry, and theme management
- Carousel and highlight media management

### Media Handling
- Carousel images stored in `media/carousel/`
- Highlight videos in `media/highlights/`
- Auto-generated thumbnails and previews for video content

## Key Features
- Golf round scoring with detailed hole-by-hole tracking
- Player statistics and performance analytics
- Course-specific statistics and ratings
- Video highlight system with thumbnail generation
- Responsive design with dark/light theme support
- Admin interface for content management
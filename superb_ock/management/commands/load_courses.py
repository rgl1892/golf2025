import csv
from django.core.management.base import BaseCommand
from superb_ock.models import GolfCourse, Hole


class Command(BaseCommand):
    help = 'Load golf courses and holes from CSV files'

    def handle(self, *args, **options):
        self.stdout.write('Loading golf courses and holes from CSV files...')

        # Load golf courses first
        courses_file = 'new_course.csv'
        try:
            with open(courses_file, 'r') as f:
                reader = csv.DictReader(f)
                courses_created = 0
                courses_updated = 0

                for row in reader:
                    # CSV headers: id,course_name,location,tee_color,rating,slope,slug,par
                    # Note: CSV has rating(float) then slope(int)
                    course_id = int(row['id']) if row['id'] else None

                    # Create or update course
                    course, created = GolfCourse.objects.update_or_create(
                        id=course_id,
                        defaults={
                            'name': row['course_name'],
                            'country': row['location'],
                            'tees': row['tee_color'],
                            'course_rating': float(row['rating']),
                            'slope_rating': int(row['slope']),
                            'slug': row['slug'],
                            'par': int(row['par']),
                        }
                    )

                    if created:
                        courses_created += 1
                    else:
                        courses_updated += 1

                self.stdout.write(self.style.SUCCESS(
                    f'✓ Courses: {courses_created} created, {courses_updated} updated'
                ))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'✗ File not found: {courses_file}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error loading courses: {str(e)}'))
            return

        # Load holes
        holes_file = 'holes.csv'
        try:
            with open(holes_file, 'r') as f:
                reader = csv.DictReader(f)
                holes_created = 0
                holes_updated = 0

                for row in reader:
                    hole_id = int(row['id']) if row['id'] else None
                    golf_course_id = int(row['golf_course_id'])

                    # Get the golf course
                    try:
                        golf_course = GolfCourse.objects.get(id=golf_course_id)
                    except GolfCourse.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'⚠ Golf course with id {golf_course_id} not found for hole {hole_id}'
                        ))
                        continue

                    # Create or update hole
                    hole, created = Hole.objects.update_or_create(
                        id=hole_id,
                        defaults={
                            'hole_number': int(row['hole_number']),
                            'golf_course': golf_course,
                            'par': int(row['par']),
                            'yards': int(row['yards']),
                            'stroke_index': int(row['stroke_index']),
                        }
                    )

                    if created:
                        holes_created += 1
                    else:
                        holes_updated += 1

                self.stdout.write(self.style.SUCCESS(
                    f'✓ Holes: {holes_created} created, {holes_updated} updated'
                ))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'✗ File not found: {holes_file}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error loading holes: {str(e)}'))
            return

        self.stdout.write(self.style.SUCCESS('\n✓ Import complete!'))

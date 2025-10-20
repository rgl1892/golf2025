# Golf2025 Test Suite

This directory contains the comprehensive test suite for the golf2025 application.

## Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── factories.py                # Factory Boy factories for test data
├── test_models.py              # Model tests
├── test_views.py               # View tests
├── test_forms.py               # Form tests
├── test_services/              # Service layer tests
│   └── __init__.py
└── fixtures/                   # JSON fixtures (if needed)
```

## Running Tests

### Run all tests
```bash
python -m pytest
```

### Run with verbose output
```bash
python -m pytest -v
```

### Run specific test file
```bash
python -m pytest superb_ock/tests/test_models.py
```

### Run specific test class
```bash
python -m pytest superb_ock/tests/test_models.py::TestGolfCourse
```

### Run specific test method
```bash
python -m pytest superb_ock/tests/test_models.py::TestGolfCourse::test_create_golf_course
```

### Run with coverage report
```bash
python -m pytest --cov=superb_ock --cov-report=html
```

Then open `htmlcov/index.html` in your browser to see the coverage report.

### Run only unit tests
```bash
python -m pytest -m unit
```

### Run only integration tests
```bash
python -m pytest -m integration
```

### Skip slow tests
```bash
python -m pytest -m "not slow"
```

## Test Markers

Tests can be marked with custom markers to categorize them:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests

## Factories

We use Factory Boy to create test data. This provides more flexibility than JSON fixtures.

### Example Usage

```python
from superb_ock.tests.factories import (
    GolfCourseFactory,
    PlayerFactory,
    create_complete_course_with_holes,
    create_complete_round_with_scores,
)

# Create a single golf course
course = GolfCourseFactory()

# Create a golf course with all 18 holes
course, holes = create_complete_course_with_holes("St Andrews")

# Create a complete round with 4 players and all scores
golf_round, scores = create_complete_round_with_scores()
```

## Writing New Tests

### Model Tests

Model tests should verify:
- Object creation
- String representations
- Model methods
- Relationships
- Validation rules

Example:
```python
@pytest.mark.django_db
class TestMyModel:
    def test_create_model(self):
        instance = MyModelFactory()
        assert instance.id is not None
```

### View Tests

View tests should verify:
- URL routing
- HTTP status codes
- Template usage
- Context data
- Permissions

Example:
```python
@pytest.mark.django_db
class TestMyView:
    def test_view_loads(self, client):
        response = client.get(reverse('my_view'))
        assert response.status_code == 200
```

### Form Tests

Form tests should verify:
- Field validation
- Form submission
- Error messages
- Custom validation logic

Example:
```python
@pytest.mark.django_db
class TestMyForm:
    def test_form_valid_data(self):
        form = MyForm(data={'field': 'value'})
        assert form.is_valid()
```

## Continuous Integration

Tests should be run automatically in CI/CD pipelines before deployment.

## Coverage Goals

- Overall coverage target: **70%+**
- Critical business logic: **90%+**
- Views: **70%+**
- Models: **80%+**
- Forms: **80%+**

## Best Practices

1. **Use factories** instead of creating objects manually
2. **Mark tests** with appropriate markers (unit, integration, slow)
3. **Write descriptive test names** that explain what is being tested
4. **Keep tests isolated** - each test should be independent
5. **Use fixtures** for common setup code
6. **Test edge cases** not just happy paths
7. **Mock external services** to keep tests fast and reliable

## Troubleshooting

### Database errors
Make sure you're using the `@pytest.mark.django_db` decorator on tests that access the database.

### Import errors
Ensure all test modules have unique names and don't conflict with Django app names.

### Slow tests
Use the `--durations=10` flag to see the 10 slowest tests:
```bash
python -m pytest --durations=10
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-django documentation](https://pytest-django.readthedocs.io/)
- [Factory Boy documentation](https://factoryboy.readthedocs.io/)
- [Django testing documentation](https://docs.djangoproject.com/en/stable/topics/testing/)

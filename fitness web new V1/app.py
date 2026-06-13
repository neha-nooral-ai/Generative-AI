from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from functools import wraps
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# Configuration
load_dotenv()
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
MODEL_ID = os.getenv('MODEL_ID', 'openai/gpt-3.5-turbo')

# Simple in-memory user storage (since no database requested)
users_db = {}

def parse_duration_to_days(duration):
    """
    Parse duration string and return exact number of days.
    Examples: "1 week" -> 7, "2 weeks" -> 14, "1 month" -> 30, "6 weeks" -> 42
    """
    import re

    if not duration:
        return 7  # Default fallback

    # Extract number and unit using regex
    match = re.search(r'(\d+)\s*(week|month|day)s?', duration.lower().strip())

    if not match:
        return 7  # Default fallback for unrecognized format

    number = int(match.group(1))
    unit = match.group(2)

    if unit == 'week':
        return number * 7
    elif unit == 'month':
        return number * 30  # Approximate month as 30 days
    elif unit == 'day':
        return number
    else:
        return 7  # Default fallback

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def query_openrouter(prompt, system_prompt=None, max_tokens=2000, temperature=0.7, max_retries=3):
    """
    Query the OpenRouter API with the given prompt and parameters.
    Includes retry logic for network issues.
    """
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'your-openrouter-api-key-here':
        raise ValueError("OpenRouter API key not configured. Please set a valid OPENROUTER_API_KEY in the .env file")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Fitness App"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    for attempt in range(max_retries):
        try:
            print(f"Attempting API call (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60  # Increased timeout
            )
            response.raise_for_status()

            # Check if response has the expected structure
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                print(f"✅ API call successful on attempt {attempt + 1}")
                return response_data["choices"][0]["message"]["content"]
            else:
                raise ValueError("Invalid response structure from OpenRouter API")

        except requests.exceptions.Timeout:
            print(f"⏰ Timeout on attempt {attempt + 1}. Retrying...")
            if attempt == max_retries - 1:
                raise ValueError("API request timed out after multiple attempts. Please check your internet connection.")
            continue

        except requests.exceptions.ConnectionError:
            print(f"🌐 Connection error on attempt {attempt + 1}. Retrying...")
            if attempt == max_retries - 1:
                raise ValueError("Connection failed after multiple attempts. Please check your internet connection and try again.")
            continue

        except requests.exceptions.RequestException as e:
            print(f"❌ Request error on attempt {attempt + 1}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text}")

            # Don't retry on authentication or client errors
            if hasattr(e, 'response') and e.response is not None:
                if 400 <= e.response.status_code < 500:
                    raise ValueError(f"API request failed: {e.response.status_code} - {e.response.text}")

            if attempt == max_retries - 1:
                raise ValueError(f"API request failed after {max_retries} attempts: {str(e)}")
            continue

        except (KeyError, ValueError) as e:
            print(f"📝 Response parsing error on attempt {attempt + 1}: {str(e)}")
            raise ValueError(f"Invalid API response format: {str(e)}")

        except Exception as e:
            print(f"💥 Unexpected error on attempt {attempt + 1}: {str(e)}")
            raise

    # This should never be reached, but just in case
    raise ValueError("API request failed after all retry attempts")

def generate_workout_plan(data):
    try:
        duration = data.get('duration', '4 weeks')
        age = data.get('age', '25')
        gender = data.get('gender', 'male')
        weight = data.get('weight', '70')
        height = data.get('height', '175')
        fitness_level = data.get('fitness_level', 'intermediate')
        goal = data.get('goal', 'general_fitness')
        workout_days = data.get('workout_days', '3')

        prompt = f"""Create a complete {duration} workout plan for a {age}-year-old {gender}
weighing {weight}kg and {height}cm tall. Fitness level: {fitness_level}, Goal: {goal}.
They can work out {workout_days} days per week with basic gym equipment.

IMPORTANT: Generate the FULL {duration} plan, not just one day or one week.
Structure the response exactly as follows:

Title: Personalized {duration} Workout Plan

Summary:
- Duration: {duration}
- Fitness Level: {fitness_level}
- Goal: {goal}
- Workout Days: {workout_days} per week

Week 1:
Day 1: [Focus Area]
Warm-up: [warm-up description]
Exercises:
* Exercise Name | Sets x Reps | Rest Period | Instructions
* Exercise Name | Sets x Reps | Rest Period | Instructions
* Exercise Name | Sets x Reps | Rest Period | Instructions
Cool-down: [cool-down description]

Day 2: [Focus Area]
Warm-up: [warm-up description]
Exercises:
* Exercise Name | Sets x Reps | Rest Period | Instructions
* Exercise Name | Sets x Reps | Rest Period | Instructions
Cool-down: [cool-down description]

Day 3: [Focus Area]
Warm-up: [warm-up description]
Exercises:
* Exercise Name | Sets x Reps | Rest Period | Instructions
* Exercise Name | Sets x Reps | Rest Period | Instructions
Cool-down: [cool-down description]

Week 2:
[Repeat the same structure for Week 2 with progressive overload]

Week 3:
[Repeat the same structure for Week 3 with progressive overload]

Week 4:
[Repeat the same structure for Week 4 with progressive overload]

Make sure to include ALL weeks and ALL days for the {duration} duration."""

        system_prompt = """You are a professional fitness trainer. Generate a complete, detailed workout plan
for the full duration specified. Include all weeks and all workout days. Use progressive overload
where appropriate. Format exactly as requested with clear sections."""

        return query_openrouter(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=3000,  # Increased for full plan
            temperature=0.7
        )

    except Exception as e:
        error_msg = f"Error generating workout plan: {str(e)}"
        print(error_msg)
        return f"Error: {error_msg}"

def parse_workout_plan_text(plan_text, user_data):
    """Parse the AI's text response into a structured format for the template."""
    try:
        lines = plan_text.strip().split('\n')
        plan_data = {
            'title': 'Personalized Workout Plan',
            'summary': {
                'duration': user_data.get('duration', '4 Weeks'),
                'level': user_data.get('fitness_level', 'Intermediate'),
                'goal': user_data.get('goal', 'General Fitness'),
                'days_per_week': user_data.get('workout_days', '3')
            },
            'weeks': []
        }

        current_week = None
        current_day = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check for week headers
            if line.lower().startswith('week'):
                # Extract week number
                week_parts = line.lower().replace('week', '').strip()
                try:
                    week_num = int(week_parts.split()[0]) if week_parts.split() else len(plan_data['weeks']) + 1
                except:
                    week_num = len(plan_data['weeks']) + 1

                current_week = {
                    'week_number': week_num,
                    'days': []
                }
                plan_data['weeks'].append(current_week)
                current_day = None
                i += 1
                continue

            # Check for day headers
            elif line.lower().startswith('day'):
                day_info = line.split(':')
                if len(day_info) >= 2:
                    focus = day_info[1].strip()
                else:
                    focus = 'Full Body'

                # Try to extract day number from the line
                day_num_match = __import__('re').search(r'day\s*(\d+)', line.lower())
                day_num = int(day_num_match.group(1)) if day_num_match else len(current_week['days']) + 1 if current_week else 1

                current_day = {
                    'day_number': day_num,
                    'focus': focus,
                    'warm_up': '5-10 minutes of light cardio and dynamic stretching',
                    'exercises': [],
                    'cool_down': '5-10 minutes of static stretching'
                }
                if current_week:
                    current_week['days'].append(current_day)
                i += 1
                continue

            # Check for warm-up
            elif 'warm-up' in line.lower() and current_day:
                current_day['warm_up'] = line.replace('Warm-up:', '').replace('warm-up:', '').strip()
                i += 1
                continue

            # Check for cool-down
            elif 'cool-down' in line.lower() and current_day:
                current_day['cool_down'] = line.replace('Cool-down:', '').replace('cool-down:', '').strip()
                i += 1
                continue

            # Check for exercises section
            elif line.lower().startswith('exercises:') or line.lower() == 'exercises':
                i += 1
                # Parse exercises until next section
                while i < len(lines):
                    exercise_line = lines[i].strip()
                    if not exercise_line or exercise_line.startswith('*') is False:
                        break

                    if exercise_line.startswith('*'):
                        # Parse exercise information: "Exercise Name | Sets x Reps | Rest Period | Instructions"
                        parts = exercise_line.replace('*', '').strip().split('|')
                        if len(parts) >= 3:
                            exercise = {
                                'name': parts[0].strip(),
                                'sets_reps': parts[1].strip(),
                                'rest': parts[2].strip(),
                                'notes': parts[3].strip() if len(parts) > 3 else 'Follow proper form'
                            }
                            current_day['exercises'].append(exercise)
                    i += 1
                continue

            i += 1

        # If no structured data was found, this indicates an error
        if not plan_data['weeks']:
            raise ValueError("No valid workout plan structure found in AI response")

        return plan_data

    except Exception as e:
        print(f"Error parsing workout plan text: {str(e)}")
        # Instead of fallback, raise the error so user sees the actual problem
        raise ValueError(f"Failed to parse workout plan: {str(e)}")
def generate_nutrition_plan(data):
    try:
        duration = data.get('duration', '1 week')
        meals_per_day_str = data.get('meals_per_day', '3')

        # Safely convert meals_per_day to integer
        try:
            meals_per_day = int(meals_per_day_str)
        except (ValueError, TypeError):
            meals_per_day = 3  # Default fallback

        # Calculate number of days based on duration using flexible parser
        num_days = parse_duration_to_days(duration)

        prompt = f"""Create a COMPLETE {duration} nutrition plan for someone with the following details:
        - Age: {data['age']}
        - Gender: {data['gender']}
        - Weight: {data['weight']} kg
        - Height: {data['height']} cm
        - Activity Level: {data['activity_level']}
        - Dietary Preference: {data['dietary_preference']}
        - Food Allergies: {data.get('allergies', 'None')}
        - Daily Meals: {meals_per_day}
        - Goal: {data['goal']}

        CRITICAL REQUIREMENTS:
        1. Generate EXACTLY {num_days} days for the complete {duration} period
        2. Each day must have {meals_per_day} meals (breakfast, lunch, dinner, etc.)
        3. Include portion sizes, macronutrient breakdown, and calorie estimates

        FORMAT EXACTLY LIKE THIS for ALL {num_days} days:

        DAY 1: [Day Name or Date]
        Breakfast: [Meal description with portions and macros]
        Lunch: [Meal description with portions and macros]
        Dinner: [Meal description with portions and macros]

        DAY 2: [Day Name or Date]
        Breakfast: [Meal description with portions and macros]
        Lunch: [Meal description with portions and macros]
        Dinner: [Meal description with portions and macros]

        DAY 3: [Day Name or Date]
        Breakfast: [Meal description with portions and macros]
        Lunch: [Meal description with portions and macros]
        Dinner: [Meal description with portions and macros]

        ...continue this pattern for ALL {num_days} days...

        DAY {num_days}: [Day Name or Date]
        Breakfast: [Meal description with portions and macros]
        Lunch: [Meal description with portions and macros]
        Dinner: [Meal description with portions and macros]

        IMPORTANT: Generate the COMPLETE plan for all {num_days} days of the {duration} period."""

        system_prompt = """You are a professional nutritionist creating detailed meal plans.
        Generate EXACTLY the number of days specified ({num_days} days for {duration}).
        Each day must have {meals_per_day} complete meals with portions and nutritional info.
        Format each day starting with "DAY X:" followed by the meals for that day."""

        return query_openrouter(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=4000,  # Significantly increased for full multi-day plans
            temperature=0.7
        )

    except Exception as e:
        error_msg = f"Error generating nutrition plan: {str(e)}"
        print(error_msg)
        return error_msg

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/workout-plan', methods=['GET', 'POST'])
@login_required
def workout_plan():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            if not all(k in data for k in ['age', 'gender', 'weight', 'height', 'fitness_level', 'goal', 'duration']):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('workout_plan'))
                
            plan_text = generate_workout_plan(data)
            if plan_text.startswith('Error'):
                flash(plan_text, 'error')
                return redirect(url_for('workout_plan'))

            # Convert the text response to a structured format for the template
            try:
                plan_data = parse_workout_plan_text(plan_text, data)
            except ValueError as e:
                flash(f'Error processing workout plan: {str(e)}', 'error')
                return redirect(url_for('workout_plan'))

            return render_template('result.html',
                               title=plan_data.get('title', 'Your Workout Plan'),
                               plan=plan_data)
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('workout_plan'))
            
    return render_template('workout_plan.html')

@app.route('/nutrition-plan', methods=['GET', 'POST'])
@login_required
def nutrition_plan():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            if not all(k in data for k in ['age', 'gender', 'weight', 'height', 'activity_level', 'dietary_preference', 'goal', 'duration', 'meals_per_day']):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('nutrition_plan'))
                
            plan = generate_nutrition_plan(data)
            if plan.startswith('Error'):
                flash(plan, 'error')
                return redirect(url_for('nutrition_plan'))

            # Create plan summary data
            plan_summary = {
                'duration': data.get('duration', '1 week'),
                'meals_per_day': data.get('meals_per_day', '3'),
                'dietary_preference': data.get('dietary_preference', 'balanced'),
                'goal': data.get('goal', 'general_fitness'),
                'activity_level': data.get('activity_level', 'moderate')
            }

            return render_template('nutrition_result.html',
                                   title="Your Nutrition Plan",
                                   plan=plan,
                                   summary=plan_summary,
                                   error=None)
        except Exception as e:
            error_msg = f'An error occurred while generating your nutrition plan: {str(e)}'
            print(f"Nutrition plan error: {error_msg}")
            flash(error_msg, 'error')
            return render_template('nutrition_result.html',
                                 title="Error",
                                 plan=None,
                                 summary=None,
                                 error=error_msg)
            
    return render_template('nutrition_plan.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('login'))
        
        # Check if user exists and password is correct
        user = users_db.get(email)
        if user and user['password'] == password:
            session['user_id'] = email
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password or not confirm_password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if email in users_db:
            flash('Email already registered. Please use a different email or login with your existing account.', 'error')
            return redirect(url_for('register'))
        
        # Register new user
        users_db[email] = {
            'username': username,
            'password': password
        }
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True)

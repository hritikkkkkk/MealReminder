import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from datetime import datetime, timedelta
import json
import os

# Try to import plyer for notifications
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("Plyer not available - notifications disabled")

kivy.require('2.0.0')

class ColoredBackground(Widget):
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class MealReminderApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # App configuration
        self.daily_calories = 2500
        self.meals_per_day = 5
        self.calories_per_meal = self.daily_calories // self.meals_per_day  # 500 kcal
        self.meal_interval_hours = 3.5  # 3.5 hours between meals
        
        # App state
        self.current_meal = 1
        self.calories_consumed_today = 0
        self.last_meal_time = None
        self.timer_event = None
        
        # Load saved state
        self.load_state()
        
        # Color palette - vibrant and modern
        self.colors = {
            'primary': get_color_from_hex('#FF6B6B'),      # Coral red
            'secondary': get_color_from_hex('#4ECDC4'),    # Turquoise
            'accent': get_color_from_hex('#45B7D1'),       # Sky blue
            'success': get_color_from_hex('#96CEB4'),      # Mint green
            'warning': get_color_from_hex('#FFEAA7'),      # Light yellow
            'background': get_color_from_hex('#DDA0DD'),   # Plum
            'text_dark': get_color_from_hex('#2D3436'),    # Dark gray
            'text_light': get_color_from_hex('#FFFFFF'),   # White
        }
    
    def build(self):
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Background
        bg = ColoredBackground(self.colors['background'])
        main_layout.add_widget(bg)
        
        # Title
        title = Label(
            text='🍽️ MealReminder',
            font_size='32sp',
            bold=True,
            color=self.colors['text_light'],
            size_hint_y=0.15
        )
        main_layout.add_widget(title)
        
        # Current meal info
        self.meal_info_label = Label(
            text=self.get_meal_info_text(),
            font_size='20sp',
            color=self.colors['text_light'],
            size_hint_y=0.15,
            halign='center'
        )
        self.meal_info_label.bind(size=self.meal_info_label.setter('text_size'))
        main_layout.add_widget(self.meal_info_label)
        
        # Calories remaining for current meal
        self.current_meal_calories = Label(
            text=f'Current Meal: {self.calories_per_meal} kcal remaining',
            font_size='24sp',
            bold=True,
            color=self.colors['accent'],
            size_hint_y=0.1
        )
        main_layout.add_widget(self.current_meal_calories)
        
        # Progress bar for daily calories
        progress_layout = BoxLayout(orientation='vertical', size_hint_y=0.15, spacing=5)
        
        daily_progress_label = Label(
            text='Daily Progress',
            font_size='16sp',
            color=self.colors['text_light'],
            size_hint_y=0.3
        )
        progress_layout.add_widget(daily_progress_label)
        
        self.daily_progress = ProgressBar(
            max=self.daily_calories,
            value=self.calories_consumed_today,
            size_hint_y=0.7
        )
        progress_layout.add_widget(self.daily_progress)
        
        main_layout.add_widget(progress_layout)
        
        # Daily calories remaining
        self.daily_calories_label = Label(
            text=self.get_daily_calories_text(),
            font_size='18sp',
            color=self.colors['success'],
            size_hint_y=0.1
        )
        main_layout.add_widget(self.daily_calories_label)
        
        # Next meal timer
        self.timer_label = Label(
            text=self.get_timer_text(),
            font_size='16sp',
            color=self.colors['warning'],
            size_hint_y=0.1
        )
        main_layout.add_widget(self.timer_label)
        
        # I Ate button
        ate_button = Button(
            text='🍴 I Ate!',
            font_size='24sp',
            bold=True,
            background_color=self.colors['primary'],
            color=self.colors['text_light'],
            size_hint_y=0.15
        )
        ate_button.bind(on_press=self.on_ate_button_press)
        main_layout.add_widget(ate_button)
        
        # Reset day button
        reset_button = Button(
            text='🔄 Reset Day',
            font_size='16sp',
            background_color=self.colors['secondary'],
            color=self.colors['text_light'],
            size_hint_y=0.1
        )
        reset_button.bind(on_press=self.reset_day)
        main_layout.add_widget(reset_button)
        
        # Start the timer
        self.start_timer()
        
        return main_layout
    
    def get_meal_info_text(self):
        meal_names = ['Breakfast', 'Mid-Morning', 'Lunch', 'Afternoon', 'Dinner']
        if self.current_meal <= len(meal_names):
            meal_name = meal_names[self.current_meal - 1]
        else:
            meal_name = f'Meal {self.current_meal}'
        
        return f'Current: {meal_name} (Meal {self.current_meal}/{self.meals_per_day})'
    
    def get_daily_calories_text(self):
        remaining = self.daily_calories - self.calories_consumed_today
        return f'Daily: {remaining} kcal remaining ({self.calories_consumed_today}/{self.daily_calories})'
    
    def get_timer_text(self):
        if self.last_meal_time is None:
            return 'Timer: Not started - press "I Ate!" to begin'
        
        now = datetime.now()
        next_meal_time = self.last_meal_time + timedelta(hours=self.meal_interval_hours)
        
        if now >= next_meal_time:
            return '⏰ Time for next meal!'
        else:
            time_left = next_meal_time - now
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            return f'Next meal in: {hours}h {minutes}m'
    
    def on_ate_button_press(self, instance):
        # Update calories consumed
        self.calories_consumed_today += self.calories_per_meal
        
        # Update last meal time
        self.last_meal_time = datetime.now()
        
        # Move to next meal
        self.current_meal += 1
        
        # Update UI
        self.update_ui()
        
        # Save state
        self.save_state()
        
        # Send notification
        self.send_ate_notification()
        
        # Check if day is complete
        if self.current_meal > self.meals_per_day:
            self.send_day_complete_notification()
    
    def update_ui(self):
        # Update all UI elements
        self.meal_info_label.text = self.get_meal_info_text()
        
        if self.current_meal <= self.meals_per_day:
            self.current_meal_calories.text = f'Current Meal: {self.calories_per_meal} kcal remaining'
        else:
            self.current_meal_calories.text = 'All meals completed for today! 🎉'
        
        self.daily_progress.value = self.calories_consumed_today
        self.daily_calories_label.text = self.get_daily_calories_text()
        self.timer_label.text = self.get_timer_text()
    
    def start_timer(self):
        # Update timer every minute
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_timer, 60)
    
    def update_timer(self, dt):
        self.timer_label.text = self.get_timer_text()
        
        # Check if it's time for next meal
        if self.last_meal_time and self.current_meal <= self.meals_per_day:
            now = datetime.now()
            next_meal_time = self.last_meal_time + timedelta(hours=self.meal_interval_hours)
            
            if now >= next_meal_time:
                self.send_meal_reminder()
    
    def send_meal_reminder(self):
        if not NOTIFICATIONS_AVAILABLE:
            return
        
        meal_names = ['Breakfast', 'Mid-Morning', 'Lunch', 'Afternoon', 'Dinner']
        if self.current_meal <= len(meal_names):
            meal_name = meal_names[self.current_meal - 1]
        else:
            meal_name = f'Meal {self.current_meal}'
        
        try:
            notification.notify(
                title='🍽️ MealReminder',
                message=f'Time for {meal_name}! ({self.calories_per_meal} kcal)',
                timeout=10,
                toast=True
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def send_ate_notification(self):
        if not NOTIFICATIONS_AVAILABLE:
            return
        
        remaining_calories = self.daily_calories - self.calories_consumed_today
        
        try:
            notification.notify(
                title='✅ Meal Logged!',
                message=f'Great! {remaining_calories} kcal remaining today',
                timeout=5,
                toast=True
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def send_day_complete_notification(self):
        if not NOTIFICATIONS_AVAILABLE:
            return
        
        try:
            notification.notify(
                title='🎉 Day Complete!',
                message='Congratulations! You\'ve completed all meals for today!',
                timeout=10,
                toast=True
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def reset_day(self, instance):
        self.current_meal = 1
        self.calories_consumed_today = 0
        self.last_meal_time = None
        self.update_ui()
        self.save_state()
    
    def save_state(self):
        state = {
            'current_meal': self.current_meal,
            'calories_consumed_today': self.calories_consumed_today,
            'last_meal_time': self.last_meal_time.isoformat() if self.last_meal_time else None,
            'date': datetime.now().date().isoformat()
        }
        
        try:
            with open('meal_reminder_state.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def load_state(self):
        try:
            if os.path.exists('meal_reminder_state.json'):
                with open('meal_reminder_state.json', 'r') as f:
                    state = json.load(f)
                
                # Check if it's a new day
                saved_date = datetime.fromisoformat(state.get('date', '1970-01-01')).date()
                today = datetime.now().date()
                
                if saved_date == today:
                    # Same day, restore state
                    self.current_meal = state.get('current_meal', 1)
                    self.calories_consumed_today = state.get('calories_consumed_today', 0)
                    last_meal_str = state.get('last_meal_time')
                    if last_meal_str:
                        self.last_meal_time = datetime.fromisoformat(last_meal_str)
                else:
                    # New day, reset state
                    self.reset_to_defaults()
            else:
                self.reset_to_defaults()
        except Exception as e:
            print(f"Error loading state: {e}")
            self.reset_to_defaults()
    
    def reset_to_defaults(self):
        self.current_meal = 1
        self.calories_consumed_today = 0
        self.last_meal_time = None

if __name__ == '__main__':
    MealReminderApp().run()

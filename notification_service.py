"""
Enhanced notification service for Android background notifications
"""
import json
import os
from datetime import datetime, timedelta

try:
    from plyer import notification
    from kivy.clock import Clock
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

class NotificationService:
    def __init__(self, app_instance):
        self.app = app_instance
        self.notification_sound = True
        self.notification_vibration = True
        
    def schedule_meal_reminder(self, meal_number, meal_name, delay_hours=3.5):
        """Schedule a meal reminder notification"""
        if not NOTIFICATIONS_AVAILABLE:
            return
            
        def send_reminder(dt):
            self.send_meal_notification(meal_number, meal_name)
        
        # Schedule notification
        Clock.schedule_once(send_reminder, delay_hours * 3600)
    
    def send_meal_notification(self, meal_number, meal_name):
        """Send meal reminder notification with sound and vibration"""
        if not NOTIFICATIONS_AVAILABLE:
            return
            
        try:
            # Create notification with enhanced features
            notification.notify(
                title='🍽️ MealReminder',
                message=f'Time for {meal_name}! (Meal {meal_number}/5 - 500 kcal)',
                app_name='MealReminder',
                timeout=15,
                toast=True,
                # Android specific features
                ticker='Time for your next meal!',
            )
            
            # Try to trigger vibration (Android specific)
            try:
                from plyer import vibrator
                vibrator.vibrate(time=1)  # 1 second vibration
            except:
                pass
                
        except Exception as e:
            print(f"Notification error: {e}")
    
    def send_progress_notification(self, calories_remaining, meals_left):
        """Send progress update notification"""
        if not NOTIFICATIONS_AVAILABLE:
            return
            
        try:
            notification.notify(
                title='📊 Progress Update',
                message=f'{calories_remaining} kcal remaining • {meals_left} meals left',
                app_name='MealReminder',
                timeout=8,
                toast=True
            )
        except Exception as e:
            print(f"Progress notification error: {e}")
    
    def send_day_complete_notification(self):
        """Send day completion notification"""
        if not NOTIFICATIONS_AVAILABLE:
            return
            
        try:
            notification.notify(
                title='🎉 Daily Goal Achieved!',
                message='Congratulations! You completed all 5 meals (2500 kcal)',
                app_name='MealReminder',
                timeout=20,
                toast=True
            )
            
            # Celebration vibration pattern
            try:
                from plyer import vibrator
                vibrator.vibrate(time=0.5)
            except:
                pass
                
        except Exception as e:
            print(f"Completion notification error: {e}")
    
    def send_late_meal_warning(self, meal_name, hours_late):
        """Send warning for late meals"""
        if not NOTIFICATIONS_AVAILABLE:
            return
            
        try:
            notification.notify(
                title='⚠️ Meal Overdue',
                message=f'{meal_name} is {hours_late:.1f}h overdue. Don\'t skip meals!',
                app_name='MealReminder',
                timeout=12,
                toast=True
            )
        except Exception as e:
            print(f"Late meal warning error: {e}")
    
    def test_notifications(self):
        """Test notification system"""
        if not NOTIFICATIONS_AVAILABLE:
            print("Notifications not available - install plyer")
            return False
            
        try:
            notification.notify(
                title='🧪 Test Notification',
                message='MealReminder notifications are working!',
                app_name='MealReminder',
                timeout=5,
                toast=True
            )
            return True
        except Exception as e:
            print(f"Test notification failed: {e}")
            return False

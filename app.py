import customtkinter as ctk
from functools import partial
import pandas as pd
import qi
import argparse
import sys
from motion import lookForward
from robot_auth import AuthenticatorFactory

class RobotControlApp(ctk.CTk):
    def __init__(self, session):
        super().__init__()

        self.session = session
        self.motion_service = self.session.service("ALMotion")
        self.tts = self.session.service("ALTextToSpeech")
        self.atts = self.session.service("ALAnimatedSpeech")

        self.tts.setLanguage("English")

        self.title("Pepper Robot Control")
        self.geometry("800x600")

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # --- Top Frame ---
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.top_frame.grid_columnconfigure(0, weight=0) # Say it frame
        self.top_frame.grid_columnconfigure(1, weight=1) # Dialogue frame
        self.top_frame.grid_rowconfigure(0, weight=1)

        # --- Bottom Frame (for movement) ---
        self.movement_frame = ctk.CTkFrame(self)
        self.movement_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # --- Say It Section (Top-Left) ---
        self.say_it_frame = ctk.CTkFrame(self.top_frame)
        self.say_it_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.say_entry = ctk.CTkEntry(self.say_it_frame, height=300, width=300, placeholder_text="Enter text for Pepper to say")
        self.say_entry.pack(pady=10, padx=10)
        
        self.say_button = ctk.CTkButton(self.say_it_frame, width=300, text="Say it", command=self.say_it)
        self.say_button.pack(pady=10, padx=10)

        # --- Dialogue Options (Top-Right) ---
        self.dialogue_frame = ctk.CTkScrollableFrame(self.top_frame, label_text="Dialogue Options")
        self.dialogue_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.create_dialogue_buttons()

        # --- Movement Controls (Bottom-Center) ---
        self.create_movement_controls()

    def create_dialogue_buttons(self):
        try:
            # Explicitly define the separator and engine for robustness
            df = pd.read_csv("dialogue_options.csv", sep=',', engine='python')
            
            # Strip any whitespace from column names
            df.columns = df.columns.str.strip()
            
            print("CSV Columns found:", df.columns.tolist())  # Debugging print

            if 'button_text' not in df.columns or 'dialogue' not in df.columns:
                raise KeyError("CSV must have 'button_text' and 'dialogue' columns.")

            for index, row in df.iterrows():
                button = ctk.CTkButton(self.dialogue_frame, text=row['button_text'], command=partial(self.paste_text, row['dialogue']))
                button.pack(padx=5, pady=5, fill="x")
        except FileNotFoundError:
            label = ctk.CTkLabel(self.dialogue_frame, text="dialogue_options.csv not found.")
            label.pack()
        except Exception as e:
            print(f"An error occurred while reading the CSV: {e}")
            label = ctk.CTkLabel(self.dialogue_frame, text=f"Error reading CSV: {e}")
            label.pack()

    def create_movement_controls(self):
        self.movement_frame.grid_columnconfigure((0, 1, 2), weight=1) # Center the middle column

        # --- Driving Frame ---
        drive_frame = ctk.CTkFrame(self.movement_frame)
        drive_frame.grid(row=0, column=0, padx=10, pady=10)

        self.forward_entry = ctk.CTkEntry(drive_frame, placeholder_text="Meters")
        self.forward_entry.pack(pady=5)
        self.forward_button = ctk.CTkButton(drive_frame, text="Forward", command=self.move_forward)
        self.forward_button.pack(pady=5)

        self.backward_button = ctk.CTkButton(drive_frame, text="Backward", command=self.move_backward)
        self.backward_button.pack(pady=5)

        # --- Turning Frame ---
        turn_frame = ctk.CTkFrame(self.movement_frame)
        turn_frame.grid(row=0, column=2, padx=10, pady=10)

        self.turn_entry = ctk.CTkEntry(turn_frame, placeholder_text="Degrees")
        self.turn_entry.pack(pady=5)
        
        turn_buttons_frame = ctk.CTkFrame(turn_frame)
        turn_buttons_frame.pack(pady=5)

        self.left_button = ctk.CTkButton(turn_buttons_frame, text="Turn Left", command=self.turn_left)
        self.left_button.pack(side="left", padx=5)
        self.right_button = ctk.CTkButton(turn_buttons_frame, text="Turn Right", command=self.turn_right)
        self.right_button.pack(side="left", padx=5)

    def paste_text(self, text):
        self.say_entry.delete(0, "end")
        self.say_entry.insert(0, text)

    def say_it(self):
        text_to_say = self.say_entry.get()
        if text_to_say:
            print(f"Saying: {text_to_say}")
            self.atts.say(text_to_say)

    def move_forward(self):
        try:
            meters = float(self.forward_entry.get())
            print(f"Moving forward {meters}m")
            self.motion_service.moveTo(meters, 0.0, 0.0)
        except ValueError:
            print("Invalid distance for forward movement.")

    def move_backward(self):
        try:
            meters = float(self.forward_entry.get())
            print(f"Moving backward {meters}m")
            self.motion_service.moveTo(-meters, 0.0, 0.0)
        except ValueError:
            print("Invalid distance for backward movement.")

    def turn_left(self):
        try:
            degrees = float(self.turn_entry.get())
            radians = degrees * 0.017453
            print(f"Turning left {degrees} degrees")
            self.motion_service.moveTo(0.0, 0.0, radians)
        except ValueError:
            print("Invalid angle for turning.")

    def turn_right(self):
        try:
            degrees = float(self.turn_entry.get())
            radians = degrees * 0.017453
            print(f"Turning right {degrees} degrees")
            self.motion_service.moveTo(0.0, 0.0, -radians)
        except ValueError:
            print("Invalid angle for turning.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="172.28.2.200", help="Robot IP address")
    parser.add_argument("--port", type=int, default=9503, help="Naoqi port number")
    parser.add_argument("--user", type=str, default="nao", help="Username for authentication")
    parser.add_argument("--password", type=str, default="nao", help="Password for authentication")
    parser.add_argument("--language", type=str, default="English", choices=["Polski", "English"], help="Language for the robot")
    args = parser.parse_args()

    try:
        connection_url = f"tcps://{args.ip}:{args.port}"
        app_qi = qi.Application(url=connection_url)
        session = app_qi.session

        factory = AuthenticatorFactory(*(args.user, args.password))

        
        session.setClientAuthenticatorFactory(factory)
        app_qi.start()
        print("Connected to the robot.")
        session.service("ALAutonomousLife").setAutonomousAbilityEnabled("BasicAwareness", False)  
        motion_service = session.service("ALMotion")
        
        # Initialize services and modules
        # motion_service.wakeUp()
        # lookForward(motion_service)

        print("Initializing GUI application.")
        app_gui = RobotControlApp(session)
        print("Starting GUI application.")
        app_gui.mainloop()

    except Exception as e:
        print(f"Failed to connect or run application: {e}")
    finally:
        if 'session' in locals() and session.isConnected():
            session.close()
        app_qi.stop()

if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"Error starting QiApplication: {e}")

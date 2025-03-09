#!/usr/bin/env python3
import argparse
from test_openai import gardenbot_response, initialize_sheet, display_weather_advice

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='GardenBot CLI')
    parser.add_argument('--weather', action='store_true', 
                       help='Display weather forecast and plant care advice on startup')
    args = parser.parse_args()

    # Initialize the sheet
    initialize_sheet()

    # Display weather forecast if enabled
    if args.weather:
        display_weather_advice()

    print("GardenBot is ready! Type 'exit' to end the conversation.")
    
    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = input(">>> ").strip()
            
            # Check for exit command
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            
            # Get and print response
            response = gardenbot_response(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 
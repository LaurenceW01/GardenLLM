#!/usr/bin/env python3
"""
Test script to see what format the AI generates for plant care information.
"""

from config import openai_client

def test_ai_format():
    """Test the AI response format for plant care information."""
    
    prompt = (
        "Provide care information for a tomato plant in Houston, Texas. "
        "Focus on practical advice for the specified locations: Houston, Texas. "
        "IMPORTANT: Use EXACTLY the section format shown below with double asterisks and colons:\n"
        "**Description:**\n"
        "**Light:**\n"
        "**Soil:**\n"
        "**Watering:**\n"
        "**Temperature:**\n"
        "**Pruning:**\n"
        "**Mulching:**\n"
        "**Fertilizing:**\n"
        "**Winter Care:**\n"
        "**Spacing:**"
    )
    
    print("Sending prompt to AI...")
    print(f"Prompt: {prompt}")
    print("-" * 50)
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a gardening expert assistant. Provide detailed, practical plant care guides with specific instructions. CRITICAL: Use the EXACT section format provided with double asterisks (**Section:**) - do not use markdown headers (###)."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content or ""
        print("AI Response:")
        print(ai_response)
        print("-" * 50)
        
        # Test the parsing
        from ai_and_sheets_core import parse_care_guide
        care_details = parse_care_guide(ai_response)
        
        print("Parsed care details:")
        for field, value in care_details.items():
            if value:  # Only show non-empty fields
                print(f"{field}: {value[:100]}...")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ai_format() 
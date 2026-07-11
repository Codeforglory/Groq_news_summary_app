import os
from groq import Groq
import dotenv
import json


dotenv.load_dotenv()

client = Groq()

if __name__ == "__main__":
        

        messages = [
            {
                "role": "user",
                "content": "What is the weather like in New York City?"
            }
        ]
        with open("./tools.json", "r") as f:
            tools = json.load(f)
        # tools = json.dumps("./tools.json")
        print(tools['tools'][0])
        response = client.chat.completions.create(
            model="groq-2", 
            tools = tools,
            messages=messages
        )
        
        if response.choices[0].tool_calls:
            tool_call = response.choices[0].tool_calls[0]

            print(f"Tool called: {tool_call.name}")
            print(f"Arguments: {tool_call.arguments}")
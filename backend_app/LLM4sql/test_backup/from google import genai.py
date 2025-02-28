from google import genai
from google.genai import types
import base64
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'D:\api\gemini2.0.json'

def generate():
    client = genai.Client(
        vertexai=True,
        project="gen-lang-client-0000496465",
        location="us-central1"
    )

    model = "gemini-2.0-flash-exp"

    contents = [types.Content(parts=[
            types.Part.from_text("python是甚麼?")
        ], role="user")
    ]
    generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 0.95,
    max_output_tokens = 8192,
    response_modalities = ["TEXT"])

    response = client.models.generate_content(
            model = model,
            contents = contents,
            config = generate_content_config)
    return(response.text)

response = generate()
print(f'回覆:{response}')
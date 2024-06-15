import openai

openai.api_key = ""

response = openai.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Who won the world series in 2020?"},
  ]
)

response = response.choice[0].message['content']

print(f'Response: {response}')


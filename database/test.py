import ollama

prompt = 'Explain why the sky is blue.'

response = ollama.chat(
    model='llama3',
    messages=[
        {'role' : 'system', 'content': f'Summary this inputs into something shorter less than 100 characters: {prompt}'}
    ]
)

response = response['message']['content']

print(f'Response: {response}')  
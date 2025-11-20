from openai import OpenAI
import os

base_url = "https://api.uniapi.io/v1"  # 如果使用 UniAPI，请确保设置正确的 baseURL
api_key = os.getenv("OPENAI_API_KEY") # 从环境变量中获取 API 密钥
client = OpenAI(base_url=base_url, api_key=api_key)

response = client.chat.completions.create(
  model="gpt-4.1",
  messages=[
    {
      "role": "user",
      "content": "Write a one-sentence bedtime story about a unicorn."
    }
  ]
)

print(response.choices[0].message.content)
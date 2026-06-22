from openai import OpenAI

client = OpenAI(api_key="OPENAI_API_KEY")

res = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role":"user","content":"Say hello"}]
)

print(res.choices[0].message.content)

import yaml
import json
import random
import asyncio
import aiohttp
from prompts import SYSTEM_PROMPT, get_user_prompt

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

API_KEY = config['llm']['llm_api']
BASE_URL = config['llm']['url']
MODEL = config['llm']['model']

# set max concurrent vol
MAX_CONCURRENT_REQUESTS = 20 

class TriageDataGenerator:
    def __init__(self, total_count=3000):
        self.total_count = total_count
        self.results = []
        self.ats_levels = [1, 2, 3, 4, 5]
        self.specialties = ["General Medical", "Trauma", "Paediatric", "Older Person", "Mental Health", "Pregnancy"]
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    def generate_balanced_metadata(self):
        metadata_list = []
        count_per_ats = self.total_count // 5
        for ats in self.ats_levels:
            for i in range(count_per_ats):
                spec = random.choice(self.specialties)
                age = random.randint(18, 64) # 简化逻辑，实际可按需细化
                metadata_list.append({"id": f"{ats}-{i}", "target_ats": ats, "specialty": spec, "age": age})
        random.shuffle(metadata_list)
        return metadata_list

    async def call_llm(self, session, metadata):
        async with self.semaphore: # Control concurrent using signal vol
            payload = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": get_user_prompt(metadata)}
                ],
                "temperature": 0.8
            }
            headers = {"Authorization": f"Bearer {API_KEY}"}
            
            try:
                async with session.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        res_data = await resp.json()
                        content = res_data['choices'][0]['message']['content']
                        # JSON clean up
                        clean_json = content.replace("```json", "").replace("```", "").strip()
                        item = json.loads(clean_json)
                        self.results.append(item)
                        
                        # Save per every 10
                        if len(self.results) % 10 == 0:
                            with open('generated_scenarios.json', 'w', encoding='utf-8') as f:
                                json.dump(self.results, f, indent=2)
                            print(f"Progress: {len(self.results)}/{self.total_count} saved.")
                    elif resp.status == 429:
                        print("Rate limit hit, slowing down...")
                        await asyncio.sleep(2)
                    else:
                        print(f"Error {resp.status}")
            except Exception as e:
                print(f"Request error: {e}")

    async def run(self):
        metadata_list = self.generate_balanced_metadata()
        async with aiohttp.ClientSession() as session:
            tasks = [self.call_llm(session, meta) for meta in metadata_list]
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    generator = TriageDataGenerator(total_count=3000)
    asyncio.run(generator.run())
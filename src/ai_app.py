from graphRAG.ai_agent import GraphAIAgent
from dotenv import load_dotenv

load_dotenv()

import asyncio

if __name__ == "__main__":
    agent = GraphAIAgent(ai_model="gpt-oss", chunk_size=400, overlap=40)

    text = '''1. The Story of Amico’s Family: A Legacy of Love and Tradition
In the idyllic village of Santa Caterina, amidst the rolling hills and sun-kissed landscapes of Sicily, lies the genesis of the Caruso family, a lineage intertwined with the island's rich culinary tapestry. The Carusos were not mere inhabitants of the land; they were the keepers of a culinary heritage that spanned generations. Each family member contributed their unique flair, crafting a narrative of flavors that reflected their diverse experiences and deep-seated love for food.

Giovanni Caruso and Maria: The Founding Generation

Giovanni Caruso, Amico's great-grandfather, was a man of the earth. His calloused hands spoke of years spent cultivating the fertile soils of Santa Caterina, producing olives and grapes that were the pride of the region. Giovanni was not just a farmer but an alchemist of flavors, blending the fruits of his labor into exquisite oils and wines. His wife, Maria, was the soul of the kitchen. A masterful cook, Maria's dishes were a symphony of hearty stews and delicate pastries, passed down from her ancestors and refined with her own touch. The couple's home was a haven of culinary experimentation and love, where their children were introduced to the secrets of the Sicilian kitchen.

Antonio Caruso: The Storyteller and Innovator

Antonio, Giovanni and Maria's eldest son, inherited his parents' passion but added his flair for innovation. A charismatic storyteller, Antonio was known for captivating his family and the village with tales of their ancestry and the island's history. His culinary prowess was unmatched, blending traditional Sicilian flavors with inventive techniques he picked up from his travels across Italy. Antonio became the village's go-to chef for weddings and grand feasts, creating dishes that were both nostalgic and avant-garde. His most famous creation, a fusion of Sicilian and Tuscan flavors, laid the groundwork for what would later become Amico's signature style.

Pietro and Sofia: The Guardians of Tradition

Pietro, Antonio's eldest son, was a skilled fisherman who loved the sea as much as the kitchen. His daily catches were the freshest seafood in the village, a staple in the family trattoria he ran with his wife, Sofia. Sofia was a baker par excellence, known for her incredible pastries and bread. Together, they transformed the trattoria into a local institution, famous for its warm hospitality and authentic flavors. The trattoria was a microcosm of Sicilian culture, where stories were shared over plates of fresh pasta and glasses of homemade wine. Pietro and Sofia instilled in their children, including Amico, the values of hard work, respect for tradition, and the joy of feeding others.
'''

    async def main():
        graph_documents = await agent.plain_text_2_graph(text)
        print(f"Number of graph documents created: {len(graph_documents)}")
        print(graph_documents)

    asyncio.run(main())
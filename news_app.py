import os
from groq import Groq
import dotenv
import json
from crewai import LLM,Agent,Task,Crew,Process
from crewai_tools import SerperDevTool
from crewai.tools import tool
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from custom_news_tool import FetchNewsTool,NewsToolInput
dotenv.load_dotenv()


import requests

@tool("Fetch Latest News")
def get_news(query: str = "Latest news on AI and technologies") -> str:
    """Fetch the latest AI news articles from the Currents API."""
    api_key = os.getenv("NEWS_API_KEY")

    
    #print(api_key)
    url = "https://api.currentsapi.services/v1/latest-news"
    search_url = "https://api.currentsapi.services/v1/search?keywords={query}"
    search_params = {
        "keywords": query,
        "language": "en",
        "page_number": 1,
        "page_size": 5,
    }
    response = requests.get(search_url.format(query=query),headers={"Authorization": api_key},
                            params=search_params,timeout=10)
    data = response.json()
    return data['news']
if __name__ == "__main__":
    #print(get_news())
    
    fetch_news_tool = FetchNewsTool()
    llm = LLM(model="groq/llama-3.3-70b-versatile",temperature=0.0,
             max_tokens=2048,api_key=os.getenv("GROQ_API_KEY"))
     
    #ChatGroq(model="llama3-8b-8192",temperature=0.2,
    #         max_tokens=2048,api_key=os.getenv("GROQ_API_KEY"))
    search_tool = SerperDevTool()

    news_researcher = Agent(
        role = "News Researcher",
        goal='Extract the most accurate, current, and impactful news details based on query keywords. ',
        backstory=(
        "You are an elite, tech-savvy investigative journalist. You know exactly how to query structured inputs to filter out clickbait and gather core factual data."),
        llm = llm,
        max_iter = 3,#maximum number of iterations the agent will perform to achieve its goal, setting it to 3 means the agent will try up to 3 times to complete its task before giving up
        max_rpm = 5,#rate limit for the agent, setting it to 5 means the agent can make up to 5 requests per minute to the LLM or tools
        tools = [fetch_news_tool],
        allow_delegation=False, #task delegation allows the agent to assign tasks to other agents, setting it to False means the agent will handle all tasks itself
        verbose=True
    )
    writer = Agent(
    role = "Writer",
    goal='Craft engaging and insightful narratives about latest trends in AI and Technology',
    verbose=True,
    backstory=(
    "You are a skilled news writer with a passion for crafting engaging and insightful narratives about the latest trends in AI and Technology."
    " Your writing style is captivating, informative, and accessible to a wide audience. You have a knack for breaking down complex topics into easily understandable content that resonates with readers."
    " Your goal is to create compelling articles that not only inform but also inspire and engage your audience, highlighting the significance of the latest news in AI and Technology and connecting it to broader societal impacts."
    "Based on the output received from the news_researcher agent, craft a well-written article that highlights the significance of the latest news in AI and Technology, connecting it to broader societal impacts."
    "Use the research findings to create an engaging narrative that captures the attention of readers and provides valuable insights into the latest trends in AI and Technology. Your writing should be clear, concise, and compelling, making complex topics accessible and interesting to a wide audience."
    "Embed the news link returned by fetch_news_tool in the article for reference and further reading.Also keep date of the news"
    ),
    # tools = [get_news],
    llm = llm,
    max_iter = 3,
    max_rpm = 5,
    allow_delegation=False
    )

    #========
    # Define Tasks
    #========
    research_task = Task(
        name="Research News",
        description="Using the following query:Latest news on AI and technologies. Use the Fetch Latest News tool to gather relevant context. Filter out redundant data and compile the major storylines, facts, and sources.",
        expected_output="A structured bullet-point breakdown of the latest news stories including headlines, key facts, and originating sources.",
        agent=news_researcher,
        # tool=get_news,
    )

    write_task = Task(
        name="Write Article",
        description="Review the compiled research material. Craft a polished, professional news roundup. Organize it with an attention-grabbing main headline, followed by distinct summary sections for each major story.",
        expected_output="A clean, production-ready markdown string containing a headline and well-crafted news summaries optimized for a feed layout.",
        agent=writer,
        context = [research_task]
    )


    crew = Crew(
    agents = [news_researcher,writer],
    tasks = [research_task,write_task],
    process = Process.sequential,
    max_rpm = 3,
    cache=True
    )

    result = crew.kickoff()
    print(result)
    

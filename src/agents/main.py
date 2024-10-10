import os
import subprocess
import venv
from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Agent, Task, Crew, Process
from langchain.llms import Ollama

app = Flask(__name__)
CORS(app)

# Initialize Ollama LLMs with different models
ollama_host = 'http://localhost:11434'
llm_ceo = Ollama(model="llama2:1b", host=ollama_host)
llm_manager = Ollama(model="llama2:7b", host=ollama_host)
llm_researcher = Ollama(model="mistral", host=ollama_host)
llm_writer = Ollama(model="llama2:13b", host=ollama_host)

class AISystem:
    def __init__(self):
        self.ceo = Agent(
            role='CEO',
            goal='Analyze user requests and delegate tasks',
            backstory='You are the CEO of an AI company, responsible for understanding user needs and coordinating the team.',
            verbose=True,
            allow_delegation=True,
            llm=llm_ceo
        )
        
        self.manager = Agent(
            role='Manager',
            goal='Coordinate tasks and oversee their execution',
            backstory='You are a skilled project manager, responsible for breaking down tasks and ensuring their completion.',
            verbose=True,
            allow_delegation=True,
            llm=llm_manager
        )
        
        self.researcher = Agent(
            role='Researcher',
            goal='Gather and analyze information from various sources',
            backstory='You are an expert at finding and synthesizing information from the internet and other sources.',
            verbose=True,
            llm=llm_researcher
        )
        
        self.writer = Agent(
            role='Writer',
            goal='Create high-quality written content',
            backstory='You are a skilled writer, capable of producing engaging and informative content on various topics.',
            verbose=True,
            llm=llm_writer
        )

    def process_request(self, user_request):
        analyze_task = Task(
            description=f"Analyze the following user request and determine the necessary steps: {user_request}",
            agent=self.ceo
        )

        plan_task = Task(
            description="Create a detailed plan to fulfill the user request based on the CEO's analysis",
            agent=self.manager
        )

        research_task = Task(
            description="Conduct necessary research to support the plan",
            agent=self.researcher
        )

        execute_task = Task(
            description="Execute the plan and produce the required output",
            agent=self.writer
        )

        crew = Crew(
            agents=[self.ceo, self.manager, self.researcher, self.writer],
            tasks=[analyze_task, plan_task, research_task, execute_task],
            verbose=2,
            process=Process.sequential
        )

        result = crew.kickoff()
        return result

ai_system = AISystem()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data['message']
    response = ai_system.process_request(user_message)
    return jsonify({"response": response})

def setup_environment():
    venv_dir = os.path.join(os.getcwd(), "ai_agents_env")
    venv.create(venv_dir, with_pip=True)
    
    # Activate the virtual environment
    activate_this = os.path.join(venv_dir, 'Scripts', 'activate_this.py')
    exec(open(activate_this).read(), {'__file__': activate_this})
    
    # Install required packages
    subprocess.check_call(["pip", "install", "flask", "flask-cors", "crewai", "langchain", "ollama"])

def cleanup_environment():
    venv_dir = os.path.join(os.getcwd(), "ai_agents_env")
    subprocess.check_call(["rmdir", "/s", "/q", venv_dir], shell=True)

def check_ollama_connection():
    import requests
    try:
        response = requests.get(f"{ollama_host}/api/tags")
        if response.status_code == 200:
            print("Successfully connected to Ollama")
            print("Available models:", response.json())
        else:
            print(f"Failed to connect to Ollama. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error connecting to Ollama: {e}")

if __name__ == "__main__":
    setup_environment()
    check_ollama_connection()
    try:
        app.run(port=5000)
    finally:
        cleanup_environment()
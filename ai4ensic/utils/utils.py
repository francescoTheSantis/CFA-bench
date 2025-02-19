import json
import os

from dotenv import load_dotenv
load_dotenv()

# Set environment variables for project and scripts directories
PROJECT = os.environ.get("PROJECT")


def load_data():
    """Load the tasks information nedded by the driver

    Returns:
        list: collection of tasks
    """
    with open('data/tasks/data.json', 'r') as file:
        games = json.loads(file.read())
    return games['tasks']

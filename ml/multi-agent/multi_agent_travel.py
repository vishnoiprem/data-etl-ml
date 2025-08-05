from crewai import Agent, Task, Crew
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()


# Dummy API Simulation
class DummyTravelAPI:
    @staticmethod
    def search_flights(origin, destination, budget):
        return [
            {"airline": "Delta", "flight_no": "DL123", "price": 450},
            {"airline": "United", "flight_no": "UA456", "price": 420}
        ]

    @staticmethod
    def book_flight(flight):
        return {
            "confirmation": f"ABC123-{flight['flight_no']}",
            "status": "confirmed",
            "price": flight["price"]
        }


# Define Agents
researcher = Agent(
    role="Flight Researcher",
    goal="Find best flight deals",
    backstory="Expert in travel logistics",
    verbose=True  # Changed to boolean
)

booker = Agent(
    role="Travel Booker",
    goal="Secure reservations",
    backstory="Specialist in booking systems",
    verbose=True  # Changed to boolean
)

# Define Tasks
research_task = Task(
    description="Find flights from NYC to London under $500",
    agent=researcher,
    expected_output="List of flight options with prices",
    async_execution=False,
    action=lambda: DummyTravelAPI.search_flights("NYC", "LHR", 500)
)

booking_task = Task(
    description="Book the cheapest flight",
    agent=booker,
    expected_output="Booking confirmation details",
    context=[research_task],
    action=lambda: DummyTravelAPI.book_flight(
        min(research_task.output, key=lambda x: x["price"])
    )
)


# Create and Run Crew
def run_travel_crew():
    crew = Crew(
        agents=[researcher, booker],
        tasks=[research_task, booking_task],
        verbose=True  # Changed from 2 to True
    )

    result = crew.kickoff()
    print("\nFinal Result:")
    print(result)


if __name__ == "__main__":
    run_travel_crew()
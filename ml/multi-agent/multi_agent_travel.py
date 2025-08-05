# File: travel_agent_crew.py
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()


# Dummy API Simulation Functions
class DummyTravelAPI:
    @staticmethod
    def search_flights(origin, destination, budget, date):
        """Simulate flight search API"""
        print(f"Searching flights from {origin} to {destination} under ${budget}...")
        return [
            {"airline": "Delta", "flight_no": "DL123", "price": 450, "departure": "08:00"},
            {"airline": "United", "flight_no": "UA456", "price": 420, "departure": "10:30"}
        ]

    @staticmethod
    def book_flight(flight):
        """Simulate booking API"""
        print(f"Booking flight {flight['flight_no']}...")
        return {
            "confirmation": f"ABC123-{flight['flight_no']}",
            "status": "confirmed",
            "price": flight["price"]
        }

    @staticmethod
    def send_email(email, message):
        """Simulate email API"""
        print(f"Sending email to {email}: {message[:50]}...")
        return {"status": "sent", "timestamp": datetime.now().isoformat()}


# Define Agents
researcher = Agent(
    role="Flight Researcher",
    goal="Find the best flight deals within budget",
    backstory="Expert in finding optimal flight options based on budget and preferences",
    verbose=True
)

booker = Agent(
    role="Travel Booker",
    goal="Securely book travel arrangements",
    backstory="Specialist in handling reservations with optimal cancellation policies",
    verbose=True
)

notifier = Agent(
    role="Customer Notifier",
    goal="Send clear booking confirmations to customers",
    backstory="Professional communicator ensuring customers receive timely updates",
    verbose=True
)


# Define Tasks
def research_task():
    # Get tomorrow's date for demo purposes
    travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    return Task(
        description=f"Find flights from NYC to London for under $500 on {travel_date}",
        agent=researcher,
        expected_output="List of flight options with prices and times",
        async_execution=False,
        context=[],
        output_file="flight_options.json",
        action=lambda: DummyTravelAPI.search_flights(
            origin="NYC",
            destination="LHR",
            budget=500,
            date=travel_date
        )
    )


def booking_task(context):
    flight_options = context[0].result()
    best_flight = min(flight_options, key=lambda x: x["price"])

    return Task(
        description="Book the cheapest suitable flight",
        agent=booker,
        expected_output="Flight booking confirmation details",
        context=context,
        action=lambda: DummyTravelAPI.book_flight(best_flight)
    )


def notification_task(context):
    booking_result = context[1].result()
    message = f"""Your flight is confirmed!
    Confirmation: {booking_result['confirmation']}
    Price: ${booking_result['price']}
    """

    return Task(
        description="Send booking confirmation to customer",
        agent=notifier,
        expected_output="Email delivery confirmation",
        context=context,
        action=lambda: DummyTravelAPI.send_email(
            email="premvishnoisoft@gmail.com",
            message=message
        )
    )


# Create and Run Crew
def run_travel_crew():
    research = research_task()
    booking = booking_task([research])
    notification = notification_task([research, booking])

    crew = Crew(
        agents=[researcher, booker, notifier],
        tasks=[research, booking, notification],
        verbose=2
    )

    result = crew.kickoff()
    print("\nFinal Result:")
    print(result)


if __name__ == "__main__":
    run_travel_crew()
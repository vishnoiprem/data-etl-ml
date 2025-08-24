from crewai import Agent, Task, Crew
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
import os

# Load environment variables for API keys and user inputs
load_dotenv()

# Initialize Spark session for Databricks integration
spark = SparkSession.builder.appName("SongkranTravelETL").getOrCreate()

# Dummy Travel API Simulation for Demo
class DummyTravelAPI:
    @staticmethod
    def search_flights(origin, destination, budget, date):
        """Simulate flight search API for Songkran travel deals."""
        if not origin or not destination or budget <= 0:
            raise ValueError("Invalid origin, destination, or budget.")
        print(f"Searching flights from {origin} to {destination} under ${budget} on {date}...")
        flights = [
            {"airline": "Delta", "flight_no": "DL123", "price": 450, "departure": "08:00"},
            {"airline": "United", "flight_no": "UA456", "price": 420, "departure": "10:30"}
        ]
        # Store results in Delta Lake
        spark.createDataFrame(flights).write.format("delta").mode("overwrite").save("s3://lakehouse/songkran_flights")
        return flights

    @staticmethod
    def book_flight(flight):
        """Simulate booking API for selected flight."""
        if not flight:
            raise ValueError("No flight provided for booking.")
        print(f"Booking flight {flight['flight_no']}...")
        booking = {
            "confirmation": f"ABC123-{flight['flight_no']}",
            "status": "confirmed",
            "price": flight["price"]
        }
        # Store booking in Delta Lake
        spark.createDataFrame([booking]).write.format("delta").mode("append").save("s3://lakehouse/songkran_bookings")
        return booking

    @staticmethod
    def send_email(email, message):
        """Simulate sending confirmation email."""
        if not email or not message:
            raise ValueError("Invalid email or message.")
        print(f"Sending email to {email}: {message[:50]}...")
        return {"status": "sent", "timestamp": datetime.now().isoformat()}

# Define Agents for Travel Workflow
researcher = Agent(
    role="Flight Researcher",
    goal="Find the best flight deals within budget for Songkran travel",
    backstory="Expert in sourcing optimal flights for Thailand retail customers",
    verbose=True
)
booker = Agent(
    role="Travel Booker",
    goal="Securely book flights with customer-friendly policies",
    backstory="Specialist in handling reservations for seamless travel",
    verbose=True
)
notifier = Agent(
    role="Customer Notifier",
    goal="Send clear booking confirmations to customers",
    backstory="Ensures timely updates for Thailand retail travelers",
    verbose=True
)

# Define Tasks with Context
def research_task(origin="NYC", destination="LHR", budget=500):
    """Create task to search flights, storing results in Delta Lake."""
    travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return Task(
        description=f"Find flights from {origin} to {destination} for under ${budget} on {travel_date}",
        agent=researcher,
        expected_output="List of flight options with prices and times",
        async_execution=False,
        context=[],
        output_file="flight_options.json",
        action=lambda: DummyTravelAPI.search_flights(origin, destination, budget, travel_date)
    )

def booking_task(context, origin, destination):
    """Create task to book the cheapest flight, storing in Delta Lake."""
    flight_options = context[0].result()
    if not flight_options:
        raise ValueError("No flights found for booking.")
    best_flight = min(flight_options, key=lambda x: x["price"])
    return Task(
        description=f"Book the cheapest flight from {origin} to {destination}",
        agent=booker,
        expected_output="Flight booking confirmation details",
        context=context,
        action=lambda: DummyTravelAPI.book_flight(best_flight)
    )

def notification_task(context, email):
    """Create task to send booking confirmation email."""
    booking_result = context[1].result()
    message = f"""Your Songkran travel is confirmed!
    Confirmation: {booking_result['confirmation']}
    Price: ${booking_result['price']}
    """
    return Task(
        description="Send booking confirmation to customer",
        agent=notifier,
        expected_output="Email delivery confirmation",
        context=context,
        action=lambda: DummyTravelAPI.send_email(email, message)
    )

# Run the Travel Crew
def run_travel_crew(origin="NYC", destination="LHR", budget=500, email="customer@example.com"):
    """Orchestrate travel booking workflow with AI agents on Databricks."""
    try:
        research = research_task(origin, destination, budget)
        booking = booking_task([research], origin, destination)
        notification = notification_task([research, booking], email)

        crew = Crew(
            agents=[researcher, booker, notifier],
            tasks=[research, booking, notification],
            verbose=2
        )

        result = crew.kickoff()
        print("\nFinal Result:")
        print(result)
        # Query Delta Lake for results
        flights_df = spark.read.format("delta").load("s3://lakehouse/songkran_flights")
        bookings_df = spark.read.format("delta").load("s3://lakehouse/songkran_bookings")
        print("\nStored Flights in Delta Lake:")
        flights_df.show()
        print("Stored Bookings in Delta Lake:")
        bookings_df.show()

    except Exception as e:
        print(f"Error in travel crew: {str(e)}")

if __name__ == "__main__":
    run_travel_crew(email="premvishnoisoft@gmail.com")
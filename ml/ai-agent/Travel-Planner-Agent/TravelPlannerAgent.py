from agno import Agent
from agno.models import OpenAI
from agno.tools import WeatherTools, FlightTools, HotelTools


class TravelPlannerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Travel Planning Specialist",
            model=OpenAI(model="gpt-4"),
            tools=[
                WeatherTools(api_key="your_weather_api_key"),
                FlightTools(api_key="your_flight_api_key"),
                HotelTools(api_key="your_hotel_api_key"),
                self.calendar_integration,
                self.budget_tracker
            ],
            instructions=[
                "You are a professional travel planner.",
                "Always consider weather preferences and budget constraints.",
                "Create detailed itineraries with backup plans.",
                "Book only when all criteria are met."
            ]
        )

    def calendar_integration(self, dates):
        """Check user's calendar for conflicts"""
        # Your calendar API integration
        return f"Calendar checked for {dates}"

    def budget_tracker(self, expenses):
        """Track expenses against budget"""
        # Your budget tracking logic
        return f"Budget analysis: {expenses}"


# Usage
travel_agent = TravelPlannerAgent()
result = travel_agent.run(
    "Book a 7-day London trip in May with 4+ sunny days, budget $3000"
)
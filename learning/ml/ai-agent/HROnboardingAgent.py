from agno import Agent
from agno.models import OpenAI
from agno.tools import SlackTools, OutlookTools, JiraTools


class HROnboardingAgent(Agent):
    def __init__(self):
        super().__init__(
            name="HR Onboarding Specialist",
            model=OpenAI(model="gpt-4"),
            tools=[
                SlackTools(),
                OutlookTools(),
                JiraTools(),
                self.hr_system_integration,
                self.inventory_management
            ],
            instructions=[
                "You are an HR specialist responsible for complete employee onboarding.",
                "Always follow company policies and ensure all steps are completed.",
                "Create detailed welcome plans and execute them systematically.",
                "Coordinate with multiple departments for seamless onboarding."
            ]
        )

    def hr_system_integration(self, employee_data):
        """Create employee profile in HR management system"""
        # Your HR API integration here
        return f"Employee profile created for {employee_data['name']}"

    def inventory_management(self, item_type, employee_id):
        """Order equipment through inventory system"""
        # Your inventory API integration here
        return f"Equipment order placed for employee {employee_id}"


# Usage: Just one simple command
hr_agent = HROnboardingAgent()
result = hr_agent.run("Onboard new intern John Smith starting Monday, needs laptop and standard access")
from agno import Agent
from agno.models import GPT4
from agno.tools import EMRTools, CalendarTools, NotificationTools


class HealthcareAssistant(Agent):
    def __init__(self):
        super().__init__(
            name="Healthcare Assistant",
            model=GPT4(),
            tools=[
                EMRTools(),  # Electronic Medical Records
                CalendarTools(),
                NotificationTools(),
                self.lab_integration,
                self.pharmacy_system
            ],
            instructions=[
                "You are a healthcare administrative assistant.",
                "Never provide medical diagnoses or treatment advice.",
                "Always prioritize urgent cases and flag emergencies.",
                "Maintain strict patient confidentiality."
            ],
            guardrails=[
                "No medical advice beyond scheduling and reminders",
                "Escalate any emergency symptoms immediately",
                "Verify patient identity before accessing records"
            ]
        )

    def lab_integration(self, patient_id, test_type):
        """Schedule lab tests and track results"""
        # Your lab system integration
        return f"Lab test scheduled for patient {patient_id}"

    def pharmacy_system(self, prescription_id):
        """Check prescription status and refills"""
        # Your pharmacy integration
        return f"Prescription status checked: {prescription_id}"


# Usage for patient care coordination
healthcare_agent = HealthcareAssistant()
result = healthcare_agent.run(
    "Patient John Doe needs annual checkup, lab work, and prescription refills coordinated"
)
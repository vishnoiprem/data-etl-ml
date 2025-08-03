from agno import Agent
from agno.models import Claude
from agno.tools import ZendeskTools, SlackTools, DatabaseTools


class CustomerServiceAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Customer Support Specialist",
            model=Claude(model="claude-3-sonnet"),
            tools=[
                ZendeskTools(),
                SlackTools(),
                DatabaseTools(),
                self.crm_integration,
                self.billing_system
            ],
            instructions=[
                "You are a senior customer support specialist.",
                "Always escalate billing issues above $500 to humans.",
                "Proactively identify and solve related issues.",
                "Follow up on resolutions within 24 hours."
            ]
        )

    def crm_integration(self, customer_id):
        """Get customer history and preferences"""
        # Your CRM API calls
        return f"Customer profile retrieved for {customer_id}"

    def billing_system(self, action, amount=None):
        """Handle billing operations with guardrails"""
        if amount and amount > 500:
            return "Escalated to human agent - amount exceeds limit"
        # Your billing system integration
        return f"Billing action completed: {action}"


# This agent can handle entire support workflows autonomously
support_agent = CustomerServiceAgent()
result = support_agent.run(
    "Customer complaint: charged twice for premium plan, wants refund and account review"
)
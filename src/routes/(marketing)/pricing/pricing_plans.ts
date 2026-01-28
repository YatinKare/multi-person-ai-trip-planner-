export const defaultPlanId = "free"

export const pricingPlans = [
  {
    id: "free",
    name: "Free",
    description: "A free plan to get you started!",
    price: "$0",
    priceIntervalName: "per month",
    features: ["MIT Licence", "Fast Performance", "Full Access"],
  },
  {
    id: "pro",
    name: "Pro",
    description: "A pro plan with additional features for power users.",
    price: "$5",
    priceIntervalName: "per month",
    features: [
      "Everything in Free",
      "Priority Support",
      "Advanced Features",
    ],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    description: "Enterprise plan for teams and organizations.",
    price: "$15",
    priceIntervalName: "per month",
    features: [
      "Everything in Pro",
      "Dedicated Support",
      "Custom Integrations",
    ],
  },
]

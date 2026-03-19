"""
Evaluation Dataset
5 ground truth Q&A pairs based on company_policy.txt
Used by both RAGAS and TruLens evaluations.
"""

EVAL_DATASET = [
    {
        "question": "How many days of paid sick leave are employees entitled to per year?",
        "ground_truth": "Employees are entitled to 10 days of paid sick leave per year. Sick leave cannot be carried forward and does not accumulate."
    },
    {
        "question": "What is the notice period for resignation?",
        "ground_truth": "The notice period is 1 month for regular employees and 3 months for senior and managerial roles."
    },
    {
        "question": "What is the minimum password length required by the company policy?",
        "ground_truth": "All system passwords must be at least 12 characters long and include a combination of uppercase letters, lowercase letters, numbers, and special characters. Passwords must be changed every 90 days."
    },
    {
        "question": "What is the daily meal allowance cap during business travel?",
        "ground_truth": "Meal allowances during business travel are capped at USD 50 per day. This includes breakfast, lunch, and dinner. Alcohol expenses are not reimbursable under any circumstances."
    },
    {
        "question": "How many days of annual paid leave are employees entitled to?",
        "ground_truth": "Each employee is entitled to 20 days of paid annual leave per year. Unused leave can be carried forward up to a maximum of 10 days to the following year."
    }
]
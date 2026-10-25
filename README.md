# Customer Churn Analysis

A synthetic dataset with customer retention and revenue at risk analysis.  Cleaned and analyzed 10,000 customer records and tested 24 factors that may be associated with customer churning.  Python file churn_analysis.py shows all 24 factors tested for association with customer churned.  The result show four waring signs associated with customers churning and a look at how much the company loses when customers churn. 

## Key findings

1.  The first six months are the riskiest. New customers churned at 28.1%, more than three times the 7.7–8.8% rate of longer-term customers.

2.  CSAT scores (customer satisfaction) show customers who rate a one or two in this category had an associated 23.5% and 26.0% chance of churning, more than three times the 6.7% to 7.9% rate of customers who rated three, four, or five.

3.  Customers who experience two or more payment failures (customers whose payment does not go through) also were associated with three times churn rate than  customers with  zero or one payment failure.  At 24.7% and 8.7%, respectively, a pronounced difference.

4.  Monthly logins (or the number of times a customer logins) show customers who login thirteen or less times a month was associated with 1.6 times more likely to churn than customers who logged in more frequently.  Splitting the login numbers, which ranged from 0-54, across four equal sized quartile showed the first quadrant with logins between 0-13 had a 14.3% of associated churn rate compared to the other quadrants which ranged from 8% to 9%.
5.  The monthly fees of churned customers totalled $35,300 per month, which is 10.1% of total revenue for the company.  In one year, the company would lose an estimated $424,000 revenue due to churned customers.

## Recommendations

1.  Customers churn at 28% in their first six months.  Provide stronger onboarding program with welcome guide, setup help, checkins after 30 and 90 days to ensure customers concerns come to light and are addressed quickly.
2.  Customer with a one or two dissatisfaction score should have a followup question of why the customer is dissatisfied.  Since customers who give a rating of one or two have a 25% rate os churning.  Understanding the source of their dissatifaction at the time of survey will allow staff to adress the issue and rectify the situation before the customer chooses to churn.
3.  Failed payments may be due to expired credit cards.  The set up of automatic customers reminders prior to card expirations date will prevent many failed payment problems.  Further automatic alerts to staff after a second failed payment to followup promptly with customer to get payment resolved may reduce the number of customers who churn after second payment failure.
4.  Low logins is also associated with churned customers 14.3% but more than 2700 customers are affected (which is double the number of customers affected than the above 3 factors).   Low logins (less than 13) per month may trigger emails to be sent to customers showing different features the customer may not know about.  Or emails with helpful tips or training will resonate with customers and engage them to use the services.  
5.  Offering fee discount is not an effective retention tool.  In initial p-value evaluation on monthly fee, discounts and price increases showed no link to churn.

## Skills demonstrated
Using Python with pandas throughout the analysis to quantify and calculate the counts and percentages of the factors that were associated with churned customers. 

## How I worked
I used Claude Code, an AI coding assistant, to draft the Python code.  I set the questions and data checks, reviewed the results of each phase before approving changes, and challenged the approach where needed.  For example, I tested login grouples a second way (equal-width bands), which confirmed the finding.  
Claude did not work autonomously, I provide the human in the loop in this analysis to regulate the direction of the analysis and possible oversights.  For example, I spotted small group problem in payment failure and suggested dividing into 2 categories instead of five to address the low numbers in some of the categories. 

## Data and decisions

2.  

## Files
# Close API Take-Home Project

This project contains a python script that
1. Imports companies and contacts from a CSV file, into Close
2. Finds all imported leads that have a company founded date within a user-specifed range
3. Segments the leads by state and generates a summary CSV

----

## Non-Technical Explanation

# A. Import leads and contacts from CSV
- Takes a CSV where each row is a contact, containing information about that contact and about the company.
- Companies are then grouped by company name from the file and the script creates one lead for each unique company name
- For each contact with that company name, we attach the contact to the Lead

- We have checkers to make sure each row contains valid data, and if not, it skips the row

# B. Find leads within a date range
- after importing the file, the user will be prompted to enter a start founded date and an end founded date
- The script searches the Lead database for Leads with a founded date that is greater than the start date and less than the end date
- We return the total number of leads within the date range

# C. Segment by state and generate report
- Using the leads found in part B, the script groups each Lead by the State associated with it.
- It then calculates the total number of leads in that state, the lead with the highest revenue, the total revenue of all leads in the state, and the media revenue for all qualifying leads in the state
- To find the most revenue, we sort the list of leads in that state by revenue and select the first lead in the sorted list

## How to run the script
1. place the script and the CSV in the same file
2. name the CSV "companies.csv"
3. Make sure python is installed
4. run pip install requests if it is not already installed
5. Update your API key within the file
6. run the script with python close_script.py

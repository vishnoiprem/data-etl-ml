import pandas as pd
import great_expectations as ge

# Step 1: Initialize a Great Expectations Context
# This assumes you've already initialized Great Expectations in your project
context = ge.data_context.DataContext()

# Step 2: Load Your Data
# For this example, we'll create a simple Pandas DataFrame
data = {
    "name": ["Alice", "Bob", "Charlie", None],
    "age": [25, 30, 35, 40],
    "salary": [70000, 80000, None, 100000]
}
df = pd.DataFrame(data)

# Convert Pandas DataFrame to a Great Expectations DataFrame
ge_df = ge.from_pandas(df)

# Step 3: Define Expectations
# Example Expectations for data quality checks
ge_df.expect_column_values_to_not_be_null("name")
ge_df.expect_column_values_to_be_between("age", 18, 60)
ge_df.expect_column_mean_to_be_between("salary", 60000, 120000)

# Step 4: Validate the DataFrame
validation_results = ge_df.validate()

# Step 5: Review the Validation Results
# This will print out the results of the data validation
print(validation_results)

# Optionally: Save the validation results to a file for further review
with open("validation_results.json", "w") as file:
    file.write(str(validation_results))
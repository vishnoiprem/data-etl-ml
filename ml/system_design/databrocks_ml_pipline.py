from  pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from  pyspark.ml.feature import StringIndexer,VectorAssembler,MinMaxScaler
from pyspark.ml.classification import LogisticRegression
from  pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.sql.functions import  col

# Step 1: Initialize Spark Session

spark = SparkSession.builder.appName("DataBrocks").getOrCreate()

# Step 2: Load Data

data = spark.read.csv("databricks_cust_data.csv", header=True, inferSchema=True)
data.printSchema()

data = data.na.fill({"age": data.agg({"age": "mean"}).collect()[0][0]})
print(data.show())


# Convert categorical column "gender" into numerical using StringIndexer
gender_indexer = StringIndexer(inputCol="gender", outputCol="gender_index")

# Assemble features into a single vector
feature_columns = ["age", "gender_index", "tenure", "balance"]
assembler = VectorAssembler(inputCols=feature_columns, outputCol="features_raw")

# Normalize the features
scaler = MinMaxScaler(inputCol="features_raw", outputCol="features")
# Step 4: Train-Test Split
train_data, test_data = data.randomSplit([0.8, 0.2], seed=42)

# Step 5: Model Training
# Define a Logistic Regression model
lr = LogisticRegression(featuresCol="features", labelCol="churn")


# Create a pipeline
pipeline = Pipeline(stages=[gender_indexer, assembler, scaler, lr])

# Fit the pipeline on training data
model = pipeline.fit(train_data)

# Step 6: Model Evaluation
# Predict on the test data
predictions = model.transform(test_data)

# Evaluate using Binary Classification Evaluator
evaluator = BinaryClassificationEvaluator(
    labelCol="churn",
    rawPredictionCol="rawPrediction",
    metricName="areaUnderROC"
)
roc_auc = evaluator.evaluate(predictions)
print(f"ROC-AUC: {roc_auc}")

# Additional metrics: Accuracy
accuracy = predictions.filter(col("churn") == col("prediction")).count() / test_data.count()
print(f"Accuracy: {accuracy}")

# Step 7: Save the Model
model.save("path_to_save_model")

# Stop Spark Session
spark.stop()






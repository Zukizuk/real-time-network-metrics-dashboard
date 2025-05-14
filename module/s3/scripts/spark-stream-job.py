import sys
import logging
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Set up logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)

# Get job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME', 
    'kinesis_stream_arn',
    'window_size',
    'output_path'
])

# Initialize Spark and Glue contexts
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Create Glue job
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

logger.info("Job initialized successfully.")

# Define schema for the incoming data
schema = StructType([
    StructField("hour", StringType(), True),
    StructField("lat", DoubleType(), True),
    StructField("long", DoubleType(), True),
    StructField("signal", IntegerType(), True),
    StructField("network", StringType(), True),
    StructField("operator", StringType(), True),
    StructField("status", IntegerType(), True),
    StructField("description", StringType(), True),
    StructField("speed", DoubleType(), True),
    StructField("satellites", DoubleType(), True),
    StructField("precission", DoubleType(), True),
    StructField("provider", StringType(), True),
    StructField("activity", StringType(), True),
    StructField("postal_code", DoubleType(), True)
])

# Create data source using Spark Structured Streaming instead of DynamicFrame
logger.info(f"Connecting to Kinesis stream: {args['kinesis_stream_arn']}")
try:
    # Extract stream name from ARN
    stream_name = args['kinesis_stream_arn'].split("/")[-1]
    
    kinesis_stream = spark.readStream \
        .format("kinesis") \
        .option("streamName", stream_name) \
        .option("endpointUrl", "https://kinesis.us-east-1.amazonaws.com") \
        .option("awsUseInstanceProfile", "true") \
        .option("startingPosition", "latest") \
        .load()
    
    logger.info("Successfully connected to Kinesis stream.")
except Exception as e:
    logger.error(f"Error connecting to Kinesis stream: {str(e)}")
    raise

# Parse the JSON data with the defined schema
logger.info("Parsing incoming Kinesis data...")
parsed_df = kinesis_stream.selectExpr("CAST(data AS STRING) as json_data") \
    .select(from_json("json_data", schema).alias("parsed_data")) \
    .select("parsed_data.*")

# Add processing timestamp column
df_with_timestamp = parsed_df.withColumn(
    "processing_time", 
    current_timestamp()
)

# Add year, month, day, hour columns for partitioning
df_with_partitions = df_with_timestamp \
    .withColumn("year", year("processing_time")) \
    .withColumn("month", month("processing_time")) \
    .withColumn("day", dayofmonth("processing_time")) \
    .withColumn("hour", hour("processing_time")) \
    .withColumn("postal_code_str", col("postal_code").cast("string"))

# Add watermark to handle late data
df_with_watermark = df_with_partitions \
    .withWatermark("processing_time", "1 minute")

# Write raw data to Parquet with partitioning
raw_data_path = f"{args['output_path']}/raw"
logger.info(f"Writing raw data to: {raw_data_path}")

try:
    query_raw = df_with_partitions \
        .writeStream \
        .format("parquet") \
        .partitionBy("year", "month", "day", "hour") \
        .option("checkpointLocation", f"{raw_data_path}/_checkpoints/raw") \
        .option("path", raw_data_path) \
        .trigger(processingTime=f"{args['window_size']} seconds") \
        .start()
    logger.info(f"Raw data writing started successfully to {raw_data_path}.")
except Exception as e:
    logger.error(f"Error writing raw data: {str(e)}")
    raise

# KPI 1: Average Signal Strength per Operator
avg_signal_df = df_with_watermark \
    .groupBy("operator", "year", "month", "day", "hour") \
    .agg(avg("signal").alias("avg_signal_strength"))

avg_signal_path = f"{args['output_path']}/metrics/signal_strength"
logger.info(f"Writing signal strength data to: {avg_signal_path}")

try:
    query_signal = avg_signal_df \
    .writeStream \
    .outputMode("update") \
    .format("parquet") \
    .partitionBy("year", "month", "day", "hour", "operator") \
    .option("checkpointLocation", f"{avg_signal_path}/_checkpoints") \
    .option("path", avg_signal_path) \
    .trigger(processingTime=f"{args['window_size']} seconds") \
    .start()

    logger.info(f"Signal strength writing started successfully to {avg_signal_path}.")
except Exception as e:
    logger.error(f"Error writing signal strength data: {str(e)}")
    raise

# KPI 2: Average GPS Precision per Operator
avg_gps_df = df_with_watermark \
    .groupBy("operator", "year", "month", "day", "hour") \
    .agg(avg("precission").alias("avg_gps_precision"))

avg_gps_path = f"{args['output_path']}/metrics/gps_precision"
logger.info(f"Writing GPS precision data to: {avg_gps_path}")

try:
    query_gps = avg_gps_df \
    .writeStream \
    .outputMode("update") \
    .format("parquet") \
    .partitionBy("year", "month", "day", "hour", "operator") \
    .option("checkpointLocation", f"{avg_gps_path}/_checkpoints") \
    .option("path", avg_gps_path) \
    .trigger(processingTime=f"{args['window_size']} seconds") \
    .start()

    logger.info(f"GPS precision writing started successfully to {avg_gps_path}.")
except Exception as e:
    logger.error(f"Error writing GPS precision data: {str(e)}")
    raise

# KPI 3: Count of Network Statuses per Postal Code
status_count_df = df_with_watermark \
    .groupBy("postal_code_str", "description", "year", "month", "day", "hour") \
    .count() \
    .withColumnRenamed("count", "status_count")

status_count_path = f"{args['output_path']}/metrics/network_status"
logger.info(f"Writing network status data to: {status_count_path}")

try:
    query_status = status_count_df \
    .writeStream \
    .outputMode("update") \
    .format("parquet") \
    .partitionBy("year", "month", "day", "hour", "postal_code_str") \
    .option("checkpointLocation", f"{status_count_path}/_checkpoints") \
    .option("path", status_count_path) \
    .trigger(processingTime=f"{args['window_size']} seconds") \
    .start()

    logger.info(f"Network status writing started successfully to {status_count_path}.")
except Exception as e:
    logger.error(f"Error writing network status data: {str(e)}")
    raise

# Wait for all queries to terminate
logger.info("Waiting for all streams to terminate...")
try:
    spark.streams.awaitAnyTermination()  # Better approach than waiting on individual queries
    logger.info("All queries completed successfully.")
except Exception as e:
    logger.error(f"Error during stream termination: {str(e)}")
    raise

# End the Glue job
logger.info("Committing Glue job.")
job.commit()
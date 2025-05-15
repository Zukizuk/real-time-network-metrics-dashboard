import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql import DataFrame, Row
import datetime
from awsglue import DynamicFrame
import gs_null_rows
from awsglue.gluetypes import *
from awsglue.dynamicframe import DynamicFrame
from awsglue import DynamicFrame
from pyspark.sql import functions as SqlFuncs

def _find_null_fields(ctx, schema, path, output, nullStringSet, nullIntegerSet, frame):
    if isinstance(schema, StructType):
        for field in schema:
            new_path = path + "." if path != "" else path
            output = _find_null_fields(ctx, field.dataType, new_path + field.name, output, nullStringSet, nullIntegerSet, frame)
    elif isinstance(schema, ArrayType):
        if isinstance(schema.elementType, StructType):
            output = _find_null_fields(ctx, schema.elementType, path, output, nullStringSet, nullIntegerSet, frame)
    elif isinstance(schema, NullType):
        output.append(path)
    else:
        x, distinct_set = frame.toDF(), set()
        for i in x.select(path).distinct().collect():
            distinct_ = i[path.split('.')[-1]]
            if isinstance(distinct_, list):
                distinct_set |= set([item.strip() if isinstance(item, str) else item for item in distinct_])
            elif isinstance(distinct_, str) :
                distinct_set.add(distinct_.strip())
            else:
                distinct_set.add(distinct_)
        if isinstance(schema, StringType):
            if distinct_set.issubset(nullStringSet):
                output.append(path)
        elif isinstance(schema, IntegerType) or isinstance(schema, LongType) or isinstance(schema, DoubleType):
            if distinct_set.issubset(nullIntegerSet):
                output.append(path)
    return output

def drop_nulls(glueContext, frame, nullStringSet, nullIntegerSet, transformation_ctx) -> DynamicFrame:
    nullColumns = _find_null_fields(frame.glue_ctx, frame.schema(), "", [], nullStringSet, nullIntegerSet, frame)
    return DropFields.apply(frame=frame, paths=nullColumns, transformation_ctx=transformation_ctx)

def sparkAggregate(glueContext, parentFrame, groups, aggs, transformation_ctx) -> DynamicFrame:
    aggsFuncs = []
    for column, func in aggs:
        aggsFuncs.append(getattr(SqlFuncs, func)(column))
    result = parentFrame.toDF().groupBy(*groups).agg(*aggsFuncs) if len(groups) > 0 else parentFrame.toDF().agg(*aggsFuncs)
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Script generated for node Metrics Data Stream
dataframe_MetricsDataStream_node1747154758682 = glueContext.create_data_frame.from_options(connection_type="kinesis",connection_options={"typeOfData": "kinesis", "streamARN": "arn:aws:kinesis:eu-west-1:12345678910:stream/metric-stream", "classification": "json", "startingPosition": "earliest", "inferSchema": "true"}, transformation_ctx="dataframe_MetricsDataStream_node1747154758682")

def processBatch(data_frame, batchId):
    if (data_frame.count() > 0):
        MetricsDataStream_node1747154758682 = DynamicFrame.fromDF(data_frame, glueContext, "from_data_frame")
        # Script generated for node Drop Null Fields
        DropNullFields_node1747157765331 = drop_nulls(glueContext, frame=MetricsDataStream_node1747154758682, nullStringSet={"", "null"}, nullIntegerSet={-1}, transformation_ctx="DropNullFields_node1747157765331")

        # Script generated for node Remove Null Rows
        RemoveNullRows_node1747157839170 = DropNullFields_node1747157765331.gs_null_rows(extended=True)

        # Script generated for node Change Schema
        ChangeSchema_node1747156852191 = ApplyMapping.apply(frame=RemoveNullRows_node1747157839170, mappings=[("hour", "string", "hour", "string"), ("lat", "string", "lat", "string"), ("long", "string", "long", "string"), ("signal", "string", "signal", "int"), ("network", "string", "network", "string"), ("operator", "string", "operator", "string"), ("status", "string", "status", "string"), ("description", "string", "description", "string"), ("speed", "string", "speed", "string"), ("satellites", "string", "satellites", "string"), ("precission", "string", "precission", "double"), ("provider", "string", "provider", "string"), ("activity", "string", "activity", "string"), ("postal_code", "string", "postal_code", "string"), ("$remove$record_timestamp$_temporary$", "timestamp", "$remove$record_timestamp$_temporary$", "timestamp")], transformation_ctx="ChangeSchema_node1747156852191")

        # Script generated for node Aggreates for Operator
        AggreatesforOperator_node1747157246661 = sparkAggregate(glueContext, parentFrame = ChangeSchema_node1747156852191, groups = ["operator"], aggs = [["signal", "avg"], ["precission", "avg"]], transformation_ctx = "AggreatesforOperator_node1747157246661")

        # Script generated for node Aggregate for postal code
        Aggregateforpostalcode_node1747158408881 = sparkAggregate(glueContext, parentFrame = ChangeSchema_node1747156852191, groups = ["postal_code", "description"], aggs = [["status", "count"]], transformation_ctx = "Aggregateforpostalcode_node1747158408881")

        now = datetime.datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour

        # Script generated for node Amazon S3
        AmazonS3_node1747157915260_path = "s3://your-bucket/raw" + "/ingest_year=" + "{:0>4}".format(str(year)) + "/ingest_month=" + "{:0>2}".format(str(month)) + "/ingest_day=" + "{:0>2}".format(str(day)) + "/ingest_hour=" + "{:0>2}".format(str(hour))  + "/"
        AmazonS3_node1747157915260 = glueContext.write_dynamic_frame.from_options(frame=MetricsDataStream_node1747154758682, connection_type="s3", format="glueparquet", connection_options={"path": AmazonS3_node1747157915260_path, "partitionKeys": []}, format_options={"compression": "uncompressed"}, transformation_ctx="AmazonS3_node1747157915260")

        # Script generated for node Average Target
        AverageTarget_node1747159038518_path = "s3://your-bucket/processed/average_by_operator" + "/ingest_year=" + "{:0>4}".format(str(year)) + "/ingest_month=" + "{:0>2}".format(str(month)) + "/ingest_day=" + "{:0>2}".format(str(day)) + "/ingest_hour=" + "{:0>2}".format(str(hour))  + "/"
        AverageTarget_node1747159038518 = glueContext.write_dynamic_frame.from_options(frame=AggreatesforOperator_node1747157246661, connection_type="s3", format="glueparquet", connection_options={"path": AverageTarget_node1747159038518_path, "partitionKeys": []}, format_options={"compression": "uncompressed"}, transformation_ctx="AverageTarget_node1747159038518")

        # Script generated for node Count Target
        CountTarget_node1747159186992_path = "s3://your-bucket/processed/status_by_postal_code" + "/ingest_year=" + "{:0>4}".format(str(year)) + "/ingest_month=" + "{:0>2}".format(str(month)) + "/ingest_day=" + "{:0>2}".format(str(day)) + "/ingest_hour=" + "{:0>2}".format(str(hour))  + "/"
        CountTarget_node1747159186992 = glueContext.write_dynamic_frame.from_options(frame=Aggregateforpostalcode_node1747158408881, connection_type="s3", format="glueparquet", connection_options={"path": CountTarget_node1747159186992_path, "partitionKeys": []}, format_options={"compression": "snappy"}, transformation_ctx="CountTarget_node1747159186992")

glueContext.forEachBatch(frame = dataframe_MetricsDataStream_node1747154758682, batch_function = processBatch, options = {"windowSize": "100 seconds", "checkpointLocation": args["TempDir"] + "/" + args["JOB_NAME"] + "/checkpoint/"})
job.commit()
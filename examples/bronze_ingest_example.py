"""Reference shape for a bronze ingest job.

This is the file `new-bronze-ingest` points new tables at. It is deliberately
small. Real ingests add: source-specific schema, secrets, error handling, and
Asset Bundle wiring.
"""

from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StringType,
    StructField,
    StructType,
    TimestampType,
)


# 1. Explicit schema. No inference in prod.
RAW_SCHEMA = StructType(
    [
        StructField("equipment_id", StringType(), nullable=False),
        StructField("event_ts", StringType(), nullable=True),  # raw string in bronze
        StructField("status_code", StringType(), nullable=True),
        StructField("payload", StringType(), nullable=True),
    ]
)


def run(
    spark: SparkSession,
    source_path: str,
    target_table: str,
    run_id: str,
) -> None:
    raw = (
        spark.read.schema(RAW_SCHEMA)
        .option("badRecordsPath", f"{source_path}/_quarantine/{run_id}")
        .json(source_path)
    )

    bronze = (
        raw.withColumn("_ingested_at", F.current_timestamp().cast(TimestampType()))
        .withColumn("_source_file", F.input_file_name())
        .withColumn("_ingest_run_id", F.lit(run_id))
        .withColumn("_ingested_date", F.current_date())
    )

    # Append-only. Re-running the same source files is idempotent because
    # _source_file is part of every row; downstream dedup uses it.
    (
        bronze.write.format("delta")
        .mode("append")
        .partitionBy("_ingested_date")
        .saveAsTable(target_table)
    )


if __name__ == "__main__":
    spark = SparkSession.builder.appName("bronze_ingest_example").getOrCreate()
    run(
        spark,
        source_path="s3://example-bucket/equipment-events/",
        target_table="bronze.operations.equipment_events",
        run_id="local-dev",
    )

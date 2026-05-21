"""Reference shape for a gold-layer KPI table.

One table, one analytical use case. Aggregated grain documented at top.
Z-ORDER on the column the BI tool filters by.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


# Grain: one row per (equipment_id, date). Refresh: daily.
TARGET = "gold.operations.equipment_daily_status"


def build(spark: SparkSession) -> DataFrame:
    silver = spark.read.table("silver.operations.equipment_status")

    return (
        silver.filter("is_current = true OR effective_to IS NULL")
        .withColumn("event_date", F.to_date("event_timestamp"))
        .groupBy("equipment_id", "event_date")
        .agg(
            F.count("*").alias("event_count"),
            F.countDistinct("status").alias("distinct_statuses"),
            F.last("status", ignorenulls=True).alias("end_of_day_status"),
        )
    )


def write(spark: SparkSession, df: DataFrame) -> None:
    # Merge on grain key, not full overwrite. Daily refresh stays cheap.
    df.createOrReplaceTempView("_incoming")
    spark.sql(
        f"""
        MERGE INTO {TARGET} t
        USING _incoming s
        ON t.equipment_id = s.equipment_id AND t.event_date = s.event_date
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    # ZORDER on the column the BI dashboard filters by.
    spark.sql(f"OPTIMIZE {TARGET} ZORDER BY (equipment_id)")


if __name__ == "__main__":
    spark = SparkSession.builder.appName("gold_kpi_example").getOrCreate()
    df = build(spark)
    write(spark, df)

"""Reference shape for a silver transform.

Renames + casts are explicit. Dedup is deterministic. Merge is idempotent.
SCD2 history columns included.
"""

from __future__ import annotations

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F


# Every silver transform has one of these. Code review checks it.
BRONZE_TO_SILVER_MAP: dict[str, tuple[str, str]] = {
    # bronze_col: (silver_col, target_type)
    "equipment_id": ("equipment_id", "string"),
    "event_ts": ("event_timestamp", "timestamp"),
    "status_code": ("status", "string"),
}


def transform(bronze: DataFrame) -> DataFrame:
    # 1. Rename + cast, explicitly.
    df = bronze
    for src, (dst, typ) in BRONZE_TO_SILVER_MAP.items():
        df = df.withColumn(dst, F.col(src).cast(typ))
    df = df.select(*[dst for dst, _ in BRONZE_TO_SILVER_MAP.values()], "_ingested_at")

    # 2. Deterministic dedup on natural key, keeping latest.
    w = Window.partitionBy("equipment_id", "event_timestamp").orderBy(
        F.col("_ingested_at").desc()
    )
    df = (
        df.withColumn("_rn", F.row_number().over(w))
        .filter("_rn = 1")
        .drop("_rn")
    )

    # 3. SCD2 columns. effective_to and is_current are set at merge time.
    return df.withColumn(
        "_silver_loaded_at", F.current_timestamp()
    ).withColumn("is_current", F.lit(True))


def merge_into_silver(
    spark: SparkSession,
    source: DataFrame,
    target_table: str,
) -> None:
    target = DeltaTable.forName(spark, target_table)

    # Close out previous current rows whose values changed.
    (
        target.alias("t")
        .merge(
            source.alias("s"),
            "t.equipment_id = s.equipment_id "
            "AND t.is_current = true "
            "AND t.status <> s.status",
        )
        .whenMatchedUpdate(
            set={
                "is_current": F.lit(False),
                "effective_to": F.col("s._silver_loaded_at"),
            }
        )
        .execute()
    )

    # Insert new current rows.
    (
        target.alias("t")
        .merge(
            source.alias("s"),
            "t.equipment_id = s.equipment_id AND t.is_current = true",
        )
        .whenNotMatchedInsertAll()
        .execute()
    )


if __name__ == "__main__":
    spark = SparkSession.builder.appName("silver_transform_example").getOrCreate()
    bronze = spark.read.table("bronze.operations.equipment_events")
    silver = transform(bronze)
    merge_into_silver(spark, silver, "silver.operations.equipment_status")

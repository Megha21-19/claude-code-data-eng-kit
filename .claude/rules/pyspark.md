---
description: PySpark idioms and anti-patterns. Loads when editing files under src/**/*.py.
globs:
  - "src/**/*.py"
  - "examples/**/*.py"
---

# PySpark idioms

## Use DataFrame, not RDD

RDD APIs (`map`, `flatMap` on the RDD object) are legacy. Stay in
DataFrame / Dataset APIs. The Catalyst optimizer can't help RDD code.

## Avoid `collect()` and `toPandas()` on anything that isn't already aggregated

If you `collect()` a 100M-row DataFrame, the driver dies. Aggregate first,
or use `take(n)` for sampling. `toPandas()` is fine on small aggregated results
only.

## Prefer column expressions to UDFs

```python
# Bad — Python UDF, no Catalyst optimization, serialization tax
@udf("string")
def upper_name(s): return s.upper() if s else None

# Good — column expression
from pyspark.sql import functions as F
df.withColumn("name_upper", F.upper("name"))
```

If a UDF is truly required, use a Pandas UDF (`@pandas_udf`) for vectorization.

## Schema is mandatory on read

Bronze ingests must specify schema explicitly. Don't let Spark infer schema
on production data — schemas drift silently and inferred reads cost a full scan.

```python
schema = StructType([...])
spark.read.schema(schema).json(path)  # not spark.read.json(path)
```

## Delta writes use merge, not overwrite

For idempotent updates on a primary key:

```python
from delta.tables import DeltaTable

target = DeltaTable.forName(spark, "silver.equipment")
(target.alias("t")
   .merge(source.alias("s"), "t.id = s.id")
   .whenMatchedUpdateAll()
   .whenNotMatchedInsertAll()
   .execute())
```

Full overwrites are only OK on bronze refresh-from-source loads where the
source is the source of truth and bronze is a mirror.

## Partitioning

- Partition by a low-cardinality column that's used in WHERE clauses
  (typically a date column).
- Do not partition by high-cardinality columns (user_id, equipment_id).
  You'll create millions of tiny files.
- Use `OPTIMIZE` + `ZORDER BY` for high-cardinality query patterns instead.

## Broadcast joins

If one side of a join is small (rule of thumb: under ~10MB after filter),
broadcast it:

```python
from pyspark.sql.functions import broadcast
fact.join(broadcast(dim), "key")
```

Don't broadcast multi-GB tables. Spark will OOM the driver.

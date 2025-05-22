# spark_transformer.py: (Legacy) Spark-based address normalization for large-scale data processing.
# Not used in current workflow, but kept for reference or future scalability needs.
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode
from pyspark.sql.types import (
    StructType, StructField, StringType, ArrayType, DoubleType
)

class SparkTransformer:
    def __init__(self, spark):
        """
        Initialize with a SparkSession.
        """
        self.spark = spark

    def create_dataframe(self, data, schema):
        """
        Create a Spark DataFrame from data and schema.
        """
        return self.spark.createDataFrame(data, schema=schema)

    def transform_dataframe(self, df):
        """
        Explode and flatten nested address data for tabular analysis.
        """
        df_exploded = df.withColumn("addresses", explode(col("d.addresses")))
        df_exploded = df_exploded.withColumn("localizedAddresses", explode(col("addresses.localizedAddresses")))
        return self.select_and_flatten(df_exploded)

    def select_and_flatten(self, df):
        """
        Select and alias all relevant address fields for output.
        """
        return df.select(
            col("_id"),
            col("localizedAddresses.reportedAddress.addressLines").alias("reportedAddress_addressLines"),
            col("localizedAddresses.reportedAddress.city").alias("reportedAddress_city"),
            col("localizedAddresses.reportedAddress.phoneNumbers").alias("reportedAddress_phoneNumbers"),
            col("localizedAddresses.reportedAddress.faxNumbers").alias("reportedAddress_faxNumbers"),
            col("localizedAddresses.reportedAddress.postCode").alias("reportedAddress_postCode"),
            col("localizedAddresses.standardizedAddress.addressLines").alias("standardizedAddress_addressLines"),
            col("localizedAddresses.standardizedAddress.provider").alias("standardizedAddress_provider"),
            col("localizedAddresses.standardizedAddress.verificationCode").alias("standardizedAddress_verificationCode"),
            col("localizedAddresses.standardizedAddress.qualityIndex").alias("standardizedAddress_qualityIndex"),
            col("localizedAddresses.standardizedAddress.countryName").alias("standardizedAddress_countryName"),
            col("localizedAddresses.standardizedAddress.ISO31662").alias("standardizedAddress_ISO31662"),
            col("localizedAddresses.standardizedAddress.ISO31663").alias("standardizedAddress_ISO31663"),
            col("localizedAddresses.standardizedAddress.ISO3166N").alias("standardizedAddress_ISO3166N"),
            col("localizedAddresses.standardizedAddress.superAdministrativeArea").alias("standardizedAddress_superAdministrativeArea"),
            col("localizedAddresses.standardizedAddress.administrativeArea").alias("standardizedAddress_administrativeArea"),
            col("localizedAddresses.standardizedAddress.locality").alias("standardizedAddress_locality"),
            col("localizedAddresses.standardizedAddress.dependentLocality").alias("standardizedAddress_dependentLocality"),
            col("localizedAddresses.standardizedAddress.thoroughfare").alias("standardizedAddress_thoroughfare"),
            col("localizedAddresses.standardizedAddress.building").alias("standardizedAddress_building"),
            col("localizedAddresses.standardizedAddress.premise").alias("standardizedAddress_premise"),
            col("localizedAddresses.standardizedAddress.subBuilding").alias("standardizedAddress_subBuilding"),
            col("localizedAddresses.standardizedAddress.longitude").alias("standardizedAddress_longitude"),
            col("localizedAddresses.standardizedAddress.latitude").alias("standardizedAddress_latitude"),
            col("localizedAddresses.standardizedAddress.postalCode").alias("standardizedAddress_postalCode"),
            col("localizedAddresses.standardizedAddress.postalCodePrimary").alias("standardizedAddress_postalCodePrimary"),
            col("localizedAddresses.standardizedAddress.postBox").alias("standardizedAddress_postBox")
        )

    @staticmethod
    def define_schema():
        """
        Define the Spark schema for the nested MongoDB address documents.
        """
        return StructType([
            StructField('_id', StringType(), True),
            StructField('d', StructType([
                StructField('addresses', ArrayType(StructType([
                    StructField('localizedAddresses', ArrayType(StructType([
                        StructField('reportedAddress', StructType([
                            StructField('addressLines', ArrayType(StringType()), True),
                            StructField('city', StringType(), True),
                            StructField('phoneNumbers', ArrayType(StringType()), True),
                            StructField('faxNumbers', ArrayType(StringType()), True),
                            StructField('postCode', StringType(), True)
                        ]), True),
                        StructField('standardizedAddress', StructType([
                            StructField('addressLines', ArrayType(StringType()), True),
                            StructField('provider', StringType(), True),
                            StructField('verificationCode', StringType(), True),
                            StructField('qualityIndex', StringType(), True),
                            StructField('countryName', StringType(), True),
                            StructField('ISO31662', StringType(), True),
                            StructField('ISO31663', StringType(), True),
                            StructField('ISO3166N', StringType(), True),
                            StructField('superAdministrativeArea', StringType(), True),
                            StructField('administrativeArea', StringType(), True),
                            StructField('locality', StringType(), True),
                            StructField('dependentLocality', StringType(), True),
                            StructField('thoroughfare', StringType(), True),
                            StructField('building', StringType(), True),
                            StructField('premise', StringType(), True),
                            StructField('subBuilding', StringType(), True),
                            StructField('longitude', DoubleType(), True),
                            StructField('latitude', DoubleType(), True),
                            StructField('postalCode', StringType(), True),
                            StructField('postalCodePrimary', StringType(), True),
                            StructField('postBox', StringType(), True)
                        ]), True)
                    ]), True))
                ]), True))
            ]), True)
        ])

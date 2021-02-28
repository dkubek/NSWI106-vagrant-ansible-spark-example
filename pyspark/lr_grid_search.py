from pyspark.ml.linalg import Vectors
from pyspark.ml.feature import VectorAssembler
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import PolynomialExpansion
from pyspark.sql import SparkSession
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

def prepare_data(filename):
    """ 
    Transform data for ML learning algorithm

    Input: Data to be transformed (DataFrame)
    Returns: Transformed data (DataFrame)
    """

    data = spark.read.format("csv").option('header', 'true').option('inferSchema', 'true').load(filename)

    data = data.withColumnRenamed('medv', 'label')
    # get columns that represent features
    features_list = data.columns
    # pop last column since it is our target
    features_list.remove('label')

    # make a new column with a vector of features
    v_assembler = VectorAssembler(inputCols=features_list, outputCol='features')

    return v_assembler.transform(data)

if __name__ == "__main__":
    train_ratio = 0.8
    test_ratio = 1 - train_ratio

    # create SparkSession - the entry to the cluster
    spark = SparkSession.builder.master("spark://192.168.50.10:7077").appName("Linear regression with pipeline - Boston").getOrCreate()

    data = prepare_data("BostonHousing.csv")

    # split data into train and test DataFrames
    train, test = data.randomSplit([train_ratio, test_ratio])

    poly_exp = PolynomialExpansion(inputCol="features", outputCol="poly_features")

    lr = LinearRegression(featuresCol="poly_features")

    pipeline = Pipeline(stages=[poly_exp, lr])

    evaluator = RegressionEvaluator()

    grid = ParamGridBuilder().addGrid(
        poly_exp.degree, [1, 2, 3, 4]
    ).addGrid(
        lr.regParam, [0.0001, 0.001, 0.01, 0.1, 1, 10, 50, 100, 1000]
    ).build()

    cv = CrossValidator(estimator=pipeline, estimatorParamMaps=grid,
        evaluator=evaluator, numFolds=3)
    # fit the model
    model = cv.fit(train)
    # model = pipeline.fit(train)

    prediction_and_labels = model.transform(train).select("prediction", "label")
    print("Precision train: " + str(evaluator.evaluate(prediction_and_labels)))

    prediction_and_labels = model.transform(test).select("prediction", "label")
    print("Precision test: " + str(evaluator.evaluate(prediction_and_labels)))

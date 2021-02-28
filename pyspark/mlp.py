from pyspark.sql import SparkSession
from pyspark.ml.classification import MultilayerPerceptronClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.linalg import Vectors
from pyspark.ml.feature import VectorAssembler

def prepare_mnist_data(filename):
    """
    Transform data for ML learning algorithm

    Input: Data to be transformed (DataFrame)
    Returns: Transformed data (DataFrame)
    """
    # in format label, pixels...
    data = spark.read.format("csv").option('header', 'false').option('inferSchema', 'true').load(filename)

    data = data.withColumnRenamed('_c0', 'label')
    # get columns that represent features
    features_list = data.columns
    # pop last column since it is our target

    features_list.remove('label')

    # make a new column with a vector of features
    v_assembler = VectorAssembler(inputCols=features_list, outputCol='features')

    return v_assembler.transform(data)

if __name__ == "__main__":

    # create SparkSession - the entry to the cluster
    spark = SparkSession.builder.master("spark://192.168.50.10:7077").appName("MLP - MNIST").getOrCreate()

    train = prepare_mnist_data("mnist_train.csv")
    test = prepare_mnist_data("mnist_test.csv")


    mlp = MultilayerPerceptronClassifier(layers=[28*28, 50, 10])

    model = mlp.fit(train)

    evaluator = MulticlassClassificationEvaluator(metricName="accuracy")

    prediction_and_labels = model.transform(train).select("prediction", "label")
    print("Precision train: " + str(evaluator.evaluate(prediction_and_labels)))

    prediction_and_labels = model.transform(test).select("prediction", "label")
    print("Precision test: " + str(evaluator.evaluate(prediction_and_labels)))





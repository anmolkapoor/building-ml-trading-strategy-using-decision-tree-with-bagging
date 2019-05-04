import numpy as np
np.seterr(divide='ignore', invalid='ignore')
import random as random
from scipy import stats


class RTLearner(object):

    def __init__(self, leaf_size=1, verbose=False):
        self.leaf_size = leaf_size
        self.verbose = verbose
        self.tree = None

    def addEvidence(self, dataX, dataY):
        """
        @summary: Add training data to learner
        @param dataX: X values of data to add
        @param dataY: the Y training values
        """
        self.tree = self.learn_with_max_depth(dataX, dataY)

    def query(self, points):
        """
        @summary: Estimate a set of test points given the model we built.
        @param points: should be a numpy array with each row corresponding to a specific query.
        @returns the estimated values according to the saved model.
        """
        response_of_all = []
        for record_row_number in xrange(0, points.shape[0]):
            test_record = points[record_row_number, :]
            estimated_answer = self.query_for_one_sample(test_record)
            response_of_all.append(float(estimated_answer))
        return response_of_all

    def query_for_one_sample(self, test_record):
        given_node = self.tree
        while not given_node.isLeaf:
            best_feature_col = given_node.splitCol
            best_feature_split_value = given_node.splitValue
            if float(test_record[best_feature_col]) <= float(best_feature_split_value):
                given_node = given_node.left
            else:
                given_node = given_node.right
        # output
        return given_node.splitValue

    def partition_classes(self, dataX, dataY, split_attribute, split_val):
        X_left = []
        X_right = []
        y_left = []
        y_right = []

        for i in xrange(len(dataX)):
            if float(dataX[i][split_attribute]) <= split_val:
                X_left.append(dataX[i])
                y_left.append(dataY[i])
            else:
                X_right.append(dataX[i])
                y_right.append(dataY[i])

        return X_left, X_right, y_left, y_right

    def learn_with_max_depth(self, dataX, dataY):

        ## leaf node case

        if (dataX.shape[0] <= self.leaf_size) or np.all(dataY[0] == dataY[:]):
            node = Node()
            node.isLeaf = True
            node.splitCol = -1
            if stats.mode(dataY).mode.shape[0] != 0:
                node.splitValue = stats.mode(dataY)[0][0][0]
            else:
                node.splitValue = 0
            node.left = None
            node.right = None
            return node


        best_split_feature_col = random.randint(0, dataX.shape[1] - 1)  ##randint is inclusive
        best_split_value = np.median(dataX[:, best_split_feature_col])

        if best_split_value == max(dataX[:,best_split_feature_col]):
            node = Node()
            node.isLeaf = True
            node.splitCol = -1
            node.splitValue = np.mean(dataY)
            node.left = None
            node.right = None
            return node

        X_left, X_right, y_left, y_right = self.partition_classes(dataX, dataY, best_split_feature_col,
                                                                  best_split_value)

        node = Node()
        node.isLeaf = False
        node.splitCol = best_split_feature_col
        node.splitValue = best_split_value
        node.left = self.learn_with_max_depth(np.array(X_left), np.array(y_left))
        node.right = self.learn_with_max_depth(np.array(X_right), np.array(y_right))

        return node

class Node:

    def __init__(self):
        self.isLeaf = False
        self.splitCol = -1
        self.splitValue = 0
        self.left = None
        self.right = None

    def __repr__(self):
        return "[L:" + str(self.isLeaf) + \
               " C: " + str(self.splitCol) + " V:" + str(self.splitValue) + " \n Left: " + str(
            self.left) + " \n Right : " + str(self.right) + "]"

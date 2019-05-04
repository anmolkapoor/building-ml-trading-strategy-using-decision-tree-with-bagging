
import numpy as np

from scipy import stats
np.seterr(divide='ignore', invalid='ignore')

class BagLearner(object):

    def __init__(self, learner, kwargs={"leaf_size": 1}, bags=20, boost=False, verbose=False):
        self.learner = learner
        self.learner_list = []
        for i in xrange(0, bags):
            self.learner_list.append(learner(**kwargs))
        self.bags = bags

    def addEvidence(self, dataX, dataY):

        for learner in self.learner_list:
            dataX_sample, dataY_sample = self.getRandomSampleSet(dataX, dataY, dataY.shape[0])
            learner.addEvidence(dataX_sample, dataY_sample)

    def query(self, points):
        results = []
        for learner in self.learner_list:
            results.append(learner.query(points))
        # results_np_array =  np.mean(np.array(results), axis=0)

        results_np_array =  np.squeeze(stats.mode(np.array(results),axis=0).mode,axis=0)
        return results_np_array.tolist()

    def getRandomSampleSet(self, dataX, dataY, sampleSize):
        random_indexes = np.random.randint(low=0, high=dataX.shape[0], size=sampleSize)
        # print(random_indexes)
        dataX_sample = dataX[random_indexes]
        dataY_sample = dataY[random_indexes]
        # print(dataX_sample.shape,"::",dataY_sample.shape)
        return dataX_sample,dataY_sample

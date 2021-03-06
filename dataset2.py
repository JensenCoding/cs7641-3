import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance
from scipy.stats import kurtosis
import os
from time import clock

# ml package
from sklearn.cross_validation import cross_val_score
from sklearn.cross_validation import train_test_split
from pylab import rcParams
from DataLoader import DataLoader
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA, FastICA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.random_projection import SparseRandomProjection
from sklearn.neural_network import MLPClassifier

rcParams['figure.figsize'] = 10, 7

# load data
output_path = 'outputs\\Heart'
dl = DataLoader('data\\Heart.csv', output_path, 'Heart')
dl.load_data()
dl.scaled_data()
X, y = dl.get_data()


# k-means clustering
# Expectation Maximization
# PCA
# ICA
# Randomized Projections
# LDA
def clustering_algo(X, y, cluster, n_c=2, n_i=10):
    if cluster == 'KM':
        clf = KMeans(n_clusters=n_c, n_init=n_i).fit(X)
    elif cluster == 'EM':
        clf = GaussianMixture(n_components=n_c, n_init=n_i).fit(X)
    y_pred = clf.predict(X)

    return (max(sum(y == y_pred) / len(y), 1 - sum(y == y_pred) / len(y)))


def dim_reduce(X, y, algo):

    if algo == 'PCA':
        transformer = PCA(n_components=2)
    elif algo == 'ICA':
        transformer = FastICA(n_components=2)
    elif algo == 'SparseRandomProjection':
        transformer = SparseRandomProjection(n_components=2)
    elif algo == 'LDA':
        transformer = LinearDiscriminantAnalysis(n_components=2)

    return transformer.fit(X, y).transform(X), transformer.fit(X, y)


# part 1
acc_km = clustering_algo(X, y, cluster='KM', n_c=2, n_i=10)
acc_em = clustering_algo(X, y, cluster='EM', n_c=2, n_i=30)
print('benchmark', max(sum(y) / len(y), 1 - sum(y) / len(y)))
print('acc_km: ', acc_km)
print('acc_em: ', acc_em)

# part 2
x_PCA, n_pca = dim_reduce(X, y, algo='PCA')
x_ICA, n_ica = dim_reduce(X, y, algo='ICA')
x_SRP, n_srp = dim_reduce(X, y, algo='SparseRandomProjection')
x_LDA, n_lda = dim_reduce(X, y, algo='LDA')
print('PCA Eigenvalues', n_pca.explained_variance_ratio_)
print('ICA Kurtosis', kurtosis(x_ICA))


# part 3
df_acc_label, df_acc_comp, df_acc_km, df_acc_em = [], [], [], []

for name, X_temp in zip(['Raw', 'PCA', 'ICA', 'SRP', 'LDA'], [X, x_PCA, x_ICA, x_SRP, x_LDA]):
    acc_km = clustering_algo(X_temp, y, cluster='KM', n_c=2, n_i=10)
    acc_em = clustering_algo(X_temp, y, cluster='EM', n_c=2, n_i=30)

    df_acc_label.append(name)
    df_acc_comp.append(len(X.T))
    df_acc_km.append(acc_km)
    df_acc_em.append(acc_em)

    print(name + ': components ' + str(len(X.T)))
    # print('benchmark', max(sum(y)/len(y), 1-sum(y)/len(y)))
    print('acc_km: ', acc_km)
    print('acc_em: ', acc_em)

df_acc = pd.DataFrame(data={'Algo': df_acc_label, '# of Component': df_acc_comp, 'KM Accuracy': df_acc_km, 'EM Accuracy': df_acc_em}, columns=['Algo', '# of Component', 'KM Accuracy', 'EM Accuracy'])


def compute_aic_bic(kmeans, X):
    """
    Computes the BIC metric for a given clusters

    Parameters:
    -----------------------------------------
    kmeans:  List of clustering object from scikit learn

    X     :  multidimension np array of data points

    Returns:
    -----------------------------------------
    BIC value
    """
    # assign centers and labels
    centers = [kmeans.cluster_centers_]
    labels = kmeans.labels_
    # number of clusters
    m = kmeans.n_clusters
    # size of the clusters
    n = np.bincount(labels)
    # size of data set
    N, d = X.shape

    # compute variance for all clusters beforehand
    cl_var = (1.0 / (N - m) / d) * sum([sum(distance.cdist(X[np.where(labels == i)], [centers[0][i]],
                                                           'euclidean') ** 2) for i in range(m)])

    ln_likelihood = np.sum([n[i] * np.log(n[i]) -
                            n[i] * np.log(N) -
                            ((n[i] * d) / 2) * np.log(2 * np.pi * cl_var) -
                            ((n[i] - 1) * d / 2) for i in range(m)])

    AIC = 2 * m - 2 * ln_likelihood
    BIC = m * np.log(N) * (d + 1) - 2 * ln_likelihood

    return AIC, BIC


X = np.array(X)


def best_km_cluster(X, max_cluster=None, title=None):
    ks = range(1, max_cluster)

    kms = [KMeans(n_clusters=i, init="k-means++").fit(X) for i in ks]

    clst, aic, bic = [], [], []
    for i in range(len(kms)):
        temp = compute_aic_bic(kms[i], X)
        clst.append(ks[i])
        aic.append(temp[0])
        bic.append(temp[1])

    df_cluster = pd.DataFrame(data={'cluster': clst, 'aic': aic, 'bic': bic}, columns=['cluster', 'aic', 'bic'])

    plt.close()
    plt.figure()
    plt.plot(df_cluster['cluster'], df_cluster['aic'], '-o', label='AIC')
    plt.plot(df_cluster['cluster'], df_cluster['bic'], '-o', label='BIC')
    plt.grid()
    plt.legend()
    if title == None:
        plt.title('K Means')
    else:
        plt.title('K Means:' + title)
    plt.savefig(os.path.join(output_path, '{}_best_KM.png'.format(title)), dpi=150)

    return df_cluster


def best_em_cluster(X, max_cluster=None, title=None):
    ks = range(1, max_cluster)

    gmm = [GaussianMixture(n_components=i).fit(X) for i in ks]

    clst, aic, bic = [], [], []
    for i in range(len(gmm)):
        # temp = compute_aic_bic(KMeans[i],X)
        clst.append(ks[i])
        aic.append(gmm[0].aic(X))
        bic.append(gmm[0].bic(X))

    df_cluster = pd.DataFrame(data={'cluster': clst, 'aic': aic, 'bic': bic}, columns=['cluster', 'aic', 'bic'])

    plt.close()
    plt.figure()
    plt.plot(df_cluster['cluster'], df_cluster['aic'], '-o', label='AIC')
    plt.plot(df_cluster['cluster'], df_cluster['bic'], '-o', label='BIC')
    plt.grid()
    plt.legend()
    if title == None:
        plt.title('EM')
    else:
        plt.title('EM:' + title)

    plt.savefig(os.path.join(output_path, '{}_best_EM.png'.format(title)), dpi=150)

    return df_cluster


df_cluster_km = best_km_cluster(X, max_cluster=10, title=None)
df_cluster_em = best_em_cluster(X, max_cluster=10, title=None)

for name, X_temp in zip(['Raw', 'PCA', 'ICA', 'SRP', 'LDA'], [X, x_PCA, x_ICA, x_SRP, x_LDA]):
    best_km_cluster(np.array(X_temp), max_cluster=10, title=name)
    best_em_cluster(np.array(X_temp), max_cluster=10, title=name)

print(df_acc)

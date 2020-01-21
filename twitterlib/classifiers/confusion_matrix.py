import itertools
import numpy as np
import matplotlib.pyplot as plt


def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    cm2 = np.vstack((cm, cm.sum(0, keepdims=True)))
    cm2 = np.hstack((cm2, cm2.sum(1, keepdims=True)))
    cm3 = cm2.copy();
    cm3[:,-1] = 1.0 * cm.max() * cm3[:,-1] / cm2.max()
    cm3[-1,:-1] = 1.0 * cm.max() * cm3[-1,:-1] / cm2.max()
    plt.imshow(cm3, interpolation='nearest', cmap=plt.cm.Reds)
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    
    plt.xlim([-0.5, max(classes) + 1.5])
    plt.ylim([-0.5, max(classes) + 1.5])
    tick_marks = np.arange(0, max(classes) + 2)
    plt.xticks(tick_marks, classes + ['t'], rotation=45)
    plt.yticks(tick_marks, classes + ['t'])

    plt.title(title)
    plt.colorbar()

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm2.shape[0]), range(cm2.shape[1])):
        plt.text(j, i, cm2[i, j],
                 horizontalalignment="center",
                 color="white" if cm2[i, j] > thresh else "black")
    
    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')

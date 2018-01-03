from data import BwDataset


class NumpyBwDataset(BwDataset):

    def __init__(self, name, array, samplenames=None, cachedir=None):

        self.data = array
        if samplenames:
            self.samplenames = samplenames

        self.cachedir = cachedir

        BwDataset.__init__(self, '{}'.format(name))

    def __repr__(self):
        return 'NumpyBwDataset("{}", <np.array>)'.format(self.name)

    def __len__(self):
        return len(self.data)

    @property
    def shape(self):
        return self.data.shape

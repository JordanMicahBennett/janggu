"""Genomic Indexer"""

import numpy as np
from HTSeq import GenomicInterval

from janggu.utils import _get_genomic_reader


class GenomicIndexer(object):
    """GenomicIndexer maps genomic positions to the respective indices

    Indexing a GenomicIndexer object returns a GenomicInterval
    for the associated index.

    Parameters
    ----------
    regions : str
        Bed- or GFF-filename.
    binsize : int
        Interval size in bins.
    stepsize : int
        stepsize (step size) for traversing the region.
    """

    _stepsize = None
    _binsize = None
    _flank = None
    chrs = None
    offsets = None
    inregionidx = None
    strand = None
    rel_end = None

    @classmethod
    def create_from_file(cls, regions, binsize, stepsize, flank=0,
                         fixed_size_batches=True):
        """Creates a GenomicIndexer object.

        This method constructs a GenomicIndexer from
        a given BED or GFF file.

        Parameters
        ----------
        regions : str
            Path to a BED or GFF file.
        binsize : int
            Binsize in base pairs.
        stepsize : int
            Stepsize in base pairs.
        fixed_size_batches : bool
            Indicates that all regions must be equally long, as given by
            the binsize. If False, variable region lengths are allowed.
        """

        regions_ = _get_genomic_reader(regions)

        gind = cls(binsize, stepsize, flank)

        chrs = []
        offsets = []
        inregionidx = []
        strand = []
        rel_end = []
        for reg in regions_:
            if stepsize <= binsize:
                val = (reg.iv.end - reg.iv.start - binsize + stepsize)
            else:
                val = (reg.iv.end - reg.iv.start)
            reglen = val // stepsize
            chrs += [reg.iv.chrom] * reglen
            offsets += [reg.iv.start] * reglen
            rel_end += [binsize] * reglen
            strand += [reg.iv.strand] * reglen
            inregionidx += range(reglen)
            # if there is a variable length fragment at the end,
            # we record the remaining fragment length
            if not fixed_size_batches and val % stepsize > 0:
                chrs += [reg.iv.chrom]
                offsets += [reg.iv.start]
                rel_end += [val - (val//stepsize) * stepsize]
                strand += [reg.iv.strand]
                inregionidx += [reglen]

        gind.chrs = chrs
        gind.offsets = offsets
        gind.inregionidx = inregionidx
        gind.strand = strand
        gind.rel_end = rel_end
        return gind

    def __init__(self, binsize, stepsize, flank=0):

        self.binsize = binsize
        self.stepsize = stepsize
        self.flank = flank

    def __len__(self):
        return len(self.chrs)

    def __repr__(self):  # pragma: no cover
        return "GenomicIndexer(<regions>, " \
            + "binsize={}, stepsize={}, flank={})".format(self.binsize,
                                                          self.stepsize,
                                                          self.flank)

    def __getitem__(self, index):
        if isinstance(index, int):
            start = (self.offsets[index] +
                     self.inregionidx[index]*self.stepsize)
            val = self.rel_end[index]
            end = start + (val if val > 0 else 1)
            return GenomicInterval(self.chrs[index], start - self.flank,
                                   end + self.flank, self.strand[index])

        raise IndexError('Index support only for "int". Given {}'.format(
            type(index)))

    @property
    def binsize(self):
        """binsize of the intervals"""
        return self._binsize

    @binsize.setter
    def binsize(self, value):
        if value <= 0:
            raise ValueError('binsize must be positive')
        self._binsize = value

    @property
    def stepsize(self):
        """stepsize (step size)"""
        return self._stepsize

    @stepsize.setter
    def stepsize(self, value):
        if value <= 0:
            raise ValueError('stepsize must be positive')
        self._stepsize = value

    @property
    def flank(self):
        """Flanking bins"""
        return self._flank

    @flank.setter
    def flank(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError('_flank must be a non-negative integer')
        self._flank = value


    def tostr(self):
        """Returns representing the region."""
        return ['{}:{}-{}'.format(iv.chrom, iv.start, iv.end) for iv in self]

    def idx_by_chrom(self, include=None, exclude=None):
        """idx_by_chrom filters for chromosome ids.

        It takes a list of chromosome ids which should be included
        or excluded and returns the indices associated with the
        compatible intervals after filtering.

        Parameters
        ----------
        include : list(str)
            List of chromosome names to be included. Default: [] means
            all chromosomes are included.
        exclude : list(str)
            List of chromosome names to be excluded. Default: [].

        Returns
        -------
        list(int)
            List of compatible indices.
        """

        if isinstance(include, str):
            include = [include]

        if isinstance(exclude, str):
            exclude = [exclude]

        if not include:
            idxs = set(range(len(self)))
        else:
            idxs = set()
            for inc in include:
                idxs.update(np.where(np.asarray(self.chrs) == inc)[0])

        if exclude:
            for exc in exclude:
                idxs = idxs.difference(
                    np.where(np.asarray(self.chrs) == exc)[0])

        return list(idxs)
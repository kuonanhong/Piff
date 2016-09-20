# Copyright (c) 2016 by Mike Jarvis and the other collaborators on GitHub at
# https://github.com/rmjarvis/Piff  All rights reserved.
#
# Piff is free software: Redistribution and use in source and binary forms
# with or without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the disclaimer given in the accompanying LICENSE
#    file.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the disclaimer given in the documentation
#    and/or other materials provided with the distribution.

"""
.. module:: decam_wavefront_psf
"""

from __future__ import print_function

import numpy as np
import fitsio

from ..star import Star, StarFit, StarData
from ..model import Model
from ..interp import Interp
from ..outliers import Outliers
from ..psf import PSF

from ..gaussian_model import Gaussian
from ..optical_model import Optical
from .decam_wavefront import DECamWavefront
from .decaminfo import DECamInfo

class DECamWavefrontPSF(PSF):
    """A PSF class that uses the decam wavefront to model the PSF

    Then, it should take another PSF to fit the residual...

    We need to fit the following variables:
        Constant optical sigma or kolmogorov, g1, g2 in model
        misalignments in interpolant: these are the interp.misalignment terms
    """
    def __init__(self, knn_file_name, knn_extname, pupil_plane_im=None,  extra_interp_properties=None, weights=np.array([0.5, 1, 1]), minuit_kwargs={}, interp_kwargs={}, model_kwargs={}):
        """



        :param extra_interp_properties:     A list of any extra properties that will be used for
                                            the interpolation in addition to (u,v).
                                            [default: None]
        :param weights:                     Array or list of weights for comparing gaussian shapes in fit
                                            [default: [0.5, 1, 1], so downweight size]
        :param minuit_kwargs:               kwargs to pass to minuit
        """
        self.interp = DECamWavefront(knn_file_name, knn_extname, **interp_kwargs)
        self.model = Optical(template='des', pupil_plane_im=pupil_plane_im, **model_kwargs)
        self.model_comparer = Gaussian()

        self.decaminfo = DECamInfo()

        self.weights = np.array(weights)
        # normalize weights
        self.weights /= self.weights.sum()

        if extra_interp_properties is None:
            self.extra_interp_properties = []
        else:
            self.extra_interp_properties = extra_interp_properties

        self.kwargs = {
            'pupil_plane_im': pupil_plane_im,
            'knn_file_name': knn_file_name,
            'knn_extname': knn_extname,
            'minuit': minuit_kwargs,
            }

        # put in the variable names and initial values
        # TODO: This should be called from function
        self.minuit_kwargs = {
            'throw_nan': False,
            'pedantic': True,
            'print_level': 2,
            'errordef': 1,

            'r0': 0.1, 'fix_r0': False, 'limit_r0': (0.08, 0.25), 'error_r0': 1e-2,
            'g1': 0, 'fix_g1': False, 'limit_g1': (-0.2, 0.2), 'error_g1': 1e-2,
            'g2': 0, 'fix_g2': False, 'limit_g2': (-0.2, 0.2), 'error_g2': 1e-2,
            'z04d': 0, 'fix_z04d': False, 'limit_z04d': (-2, 2), 'error_z04d': 1e-2,
            'z04x': 0, 'fix_z04x': False, 'limit_z04x': (-2, 2), 'error_z04x': 1e-4,
            'z04y': 0, 'fix_z04y': False, 'limit_z04y': (-2, 2), 'error_z04x': 1e-4,
            'z05d': 0, 'fix_z05d': False, 'limit_z05d': (-2, 2), 'error_z05d': 1e-2,
            'z05x': 0, 'fix_z05x': False, 'limit_z05x': (-2, 2), 'error_z05x': 1e-4,
            'z05y': 0, 'fix_z05y': False, 'limit_z05y': (-2, 2), 'error_z05x': 1e-4,
            'z06d': 0, 'fix_z06d': False, 'limit_z06d': (-2, 2), 'error_z06d': 1e-2,
            'z06x': 0, 'fix_z06x': False, 'limit_z06x': (-2, 2), 'error_z06x': 1e-4,
            'z06y': 0, 'fix_z06y': False, 'limit_z06y': (-2, 2), 'error_z06x': 1e-4,
            'z07d': 0, 'fix_z07d': False, 'limit_z07d': (-2, 2), 'error_z07d': 1e-2,
            'z07x': 0, 'fix_z07x': False, 'limit_z07x': (-2, 2), 'error_z07x': 1e-4,
            'z07y': 0, 'fix_z07y': False, 'limit_z07y': (-2, 2), 'error_z07x': 1e-4,
            'z08d': 0, 'fix_z08d': False, 'limit_z08d': (-2, 2), 'error_z08d': 1e-2,
            'z08x': 0, 'fix_z08x': False, 'limit_z08x': (-2, 2), 'error_z08x': 1e-4,
            'z08y': 0, 'fix_z08y': False, 'limit_z08y': (-2, 2), 'error_z08x': 1e-4,
            'z09d': 0, 'fix_z09d': False, 'limit_z09d': (-2, 2), 'error_z09d': 1e-2,
            'z09x': 0, 'fix_z09x': False, 'limit_z09x': (-2, 2), 'error_z09x': 1e-4,
            'z09y': 0, 'fix_z09y': False, 'limit_z09y': (-2, 2), 'error_z09x': 1e-4,
            'z10d': 0, 'fix_z10d': False, 'limit_z10d': (-2, 2), 'error_z10d': 1e-2,
            'z10x': 0, 'fix_z10x': False, 'limit_z10x': (-2, 2), 'error_z10x': 1e-4,
            'z10y': 0, 'fix_z10y': False, 'limit_z10y': (-2, 2), 'error_z10x': 1e-4,
            'z11d': 0, 'fix_z11d': False, 'limit_z11d': (-2, 2), 'error_z11d': 1e-2,
            'z11x': 0, 'fix_z11x': False, 'limit_z11x': (-2, 2), 'error_z11x': 1e-4,
            'z11y': 0, 'fix_z11y': False, 'limit_z11y': (-2, 2), 'error_z11x': 1e-4,
                              }

        self.minuit_kwargs.update(self.kwargs['minuit'])
        self.update_psf_params(**self.minuit_kwargs)


    def fit(self, stars, wcs, pointing,
            chisq_threshold=0.1, max_iterations=300, skip_fit=False, logger=None):
        """Fit interpolated PSF model to star data using standard sequence of operations.

        :param stars:           A list of Star instances.
        :param wcs:             A dict of WCS solutions indexed by chipnum.
        :param pointing:        A galsim.CelestialCoord object giving the telescope pointing.
                                [Note: pointing should be None if the WCS is not a CelestialWCS]
        :param chisq_threshold: Change in reduced chisq at which iteration will terminate.
                                [default: 0.1]
        :param max_iterations:  Maximum number of iterations to try. [default: 300]
        :param skip_fit:        If True, do not run migrad fit [default: False]
        :param logger:          A logger object for logging debug info. [default: None]
        """
        if logger:
            logger.info("Start fitting DECAMWavefrontPSF using %s stars", len(stars))
        from iminuit import Minuit

        self.stars = stars
        self.wcs = wcs
        self.pointing = pointing

        # get the moments of the stars for comparison
        self._stars = [self.model_comparer.fit(star) for star in stars]
        self._shapes = np.array([star.fit.params for star in self._stars])

        self._minuit = Minuit(self._fit_func, **self.minuit_kwargs)
        # run the fit and solve! This will update the interior parameters
        self._minuit.migrad(ncall=max_iterations)
        # these are the best fit parameters
        self._fitarg = self._minuit.fitarg
        # update params to best values
        self.update_psf_params(**self._minuit.values)
        # save params and errors to the kwargs
        self.kwargs['minuit'].update(self._fitarg)

    def update_psf_params(self,
                          r0=np.nan, g1=np.nan, g2=np.nan,
                          z04d=np.nan, z04x=np.nan, z04y=np.nan,
                          z05d=np.nan, z05x=np.nan, z05y=np.nan,
                          z06d=np.nan, z06x=np.nan, z06y=np.nan,
                          z07d=np.nan, z07x=np.nan, z07y=np.nan,
                          z08d=np.nan, z08x=np.nan, z08y=np.nan,
                          z09d=np.nan, z09x=np.nan, z09y=np.nan,
                          z10d=np.nan, z10x=np.nan, z10y=np.nan,
                          z11d=np.nan, z11x=np.nan, z11y=np.nan, **kwargs):
        # update model
        if r0 == r0:
            self.model.kolmogorov_kwargs['r0'] = r0
        if g1 == g1:
            self.model.g1 = g1
        if g2 == g2:
            self.model.g2 = g2
        # update the misalignment
        misalignment = np.array([
                  [z04d, z04x, z04y],
                  [z05d, z05x, z05y],
                  [z06d, z06x, z06y],
                  [z07d, z07x, z07y],
                  [z08d, z08x, z08y],
                  [z09d, z09x, z09y],
                  [z10d, z10x, z10y],
                  [z11d, z11x, z11y],
                  ])
        old_misalignment = self.interp.misalignment
        misalignment = np.where(misalignment == misalignment, misalignment, old_misalignment)
        self.interp.misalignment = misalignment

    def _fit_func(self,
                  r0, g1, g2,
                  z04d, z04x, z04y,
                  z05d, z05x, z05y,
                  z06d, z06x, z06y,
                  z07d, z07x, z07y,
                  z08d, z08x, z08y,
                  z09d, z09x, z09y,
                  z10d, z10x, z10y,
                  z11d, z11x, z11y,
                  ):

        # update psf
        self.update_psf_params(r0, g1, g2,
                               z04d, z04x, z04y,
                               z05d, z05x, z05y,
                               z06d, z06x, z06y,
                               z07d, z07x, z07y,
                               z08d, z08x, z08y,
                               z09d, z09x, z09y,
                               z10d, z10x, z10y,
                               z11d, z11x, z11y,)

        # get shapes
        shapes = np.array([self.model_comparer.fit(self.drawStar(star)).fit.params for star in self._stars])

        # calculate chisq
        # TODO: are there any errors from the shape measurements I could put in?
        chi2 = np.sum(self.weights * np.square(shapes - self._shapes))
        dof = shapes.size
        return chi2 / dof

    def drawStar(self, star):
        """Generate PSF image for a given star.

        :param star:        Star instance holding information needed for interpolation as
                            well as an image/WCS into which PSF will be rendered.

        :returns:           Star instance with its image filled with rendered PSF
        """
        # put in the focal coordinates
        star = self.decaminfo.pixel_to_focal(star)
        # Interpolate parameters to this position/properties:
        star = self.interp.interpolate(star)
        # Render the image
        return self.model.draw(star)
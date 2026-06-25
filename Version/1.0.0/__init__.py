# -*- coding: utf-8 -*-

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load EasyFeatureSelection class from file EasyFeatureSelection.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .easyfeatureselection import EasyFeatureSelection
    return EasyFeatureSelection(iface)

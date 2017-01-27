"""Test some code."""

import nose.tools
import data_transformer


def setup():
    """Setup."""
    ds = data_transformer.datastore.Datastore()
    print "SETUP!"

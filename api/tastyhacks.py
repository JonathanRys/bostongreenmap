from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.geos import GEOSGeometry
from django.utils import simplejson

from tastypie.bundle import Bundle
from tastypie.fields import ApiField, CharField
from tastypie.resources import ModelResource

import gpolyencode


class GeometryApiField(ApiField):
    """
    Custom ApiField for dealing with data from GeometryFields (by serializing them as GeoJSON).
    """
    dehydrated_type = 'geometry'
    help_text = 'Geometry data.'

    def hydrate(self, bundle):
        value = super(GeometryApiField, self).hydrate(bundle)
        if value is None:
            return value
        return simplejson.dumps(value)
    
    def dehydrate(self, obj):
        return self.convert(super(GeometryApiField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None

        if isinstance(value, dict):
            return value

        # Get ready-made geojson serialization and then convert it _back_ to a Python object
        # so that Tastypie can serialize it as part of the bundle
        return simplejson.loads(value.geojson)


class GeoResource(ModelResource):
    """
    ModelResource subclass that handles geometry fields as GeoJSON.
    """

    @classmethod
    def api_field_from_django_field(cls, f, default=CharField):
        """
        Overrides default field handling to support custom GeometryApiField.
        """
        if isinstance(f, GeometryField):
            return GeometryApiField
    
        return super(GeoResource, cls).api_field_from_django_field(f, default)


class EncodedGeometryApiField(ApiField):
    """
    Custom ApiField for dealing with data from GeometryFields (by serializing them as Encoded Geometries).
    """
    dehydrated_type = 'geometry'
    help_text = 'Geometry data.'

    
    def dehydrate(self, obj):
        return self.convert(super(EncodedGeometryApiField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None

        if isinstance(value, dict):
            return value

        encoder = gpolyencode.GPolyEncoder()
        geom = GEOSGeometry(value)
        # support multipart geometetries
        geom_encoded = {}
        for key, part in enumerate(geom):
            geom_encoded[key] = encoder.encode(part[0])
        return geom_encoded


class EncodedGeoResource(ModelResource):
    """
    ModelResource subclass that handles geometry fields as Encoded Geometries.
    Improves performance for rendering complex geometries on Google Maps,
    see http://facstaff.unca.edu/mcmcclur/GoogleMaps/EncodePolyline/ for more information.
    """

    @classmethod
    def api_field_from_django_field(cls, f, default=CharField):
        """
        Overrides default field handling to support custom EncodedGeometryApiField.
        """
        if isinstance(f, GeometryField):
            return EncodedGeometryApiField
    
        return super(EncodedGeoResource, cls).api_field_from_django_field(f, default)
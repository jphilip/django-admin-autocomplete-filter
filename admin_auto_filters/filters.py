from django.contrib.admin.widgets import AutocompleteSelectMultiple
from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor, ManyToManyDescriptor
from django.forms.widgets import Media, MEDIA_TYPES


class AutocompleteFilter(admin.SimpleListFilter):
    template = 'django-admin-autocomplete-filter/autocomplete-filter.html'
    title = ''
    field_name = ''
    field_pk = 'id'
    is_placeholder_title = False
    widget_attrs = {}
    rel_model = None
    form_field = forms.ModelMultipleChoiceField

    class Media:
        js = (
            'django-admin-autocomplete-filter/js/autocomplete_filter_qs.js',
        )
        css = {
            'screen': (
                'django-admin-autocomplete-filter/css/autocomplete-fix.css',
            ),
        }

    def __init__(self, request, params, model, model_admin):
        self.parameter_name = '{}__{}__in'.format(
            self.field_name, self.field_pk)
        super().__init__(request, params, model, model_admin)

        if self.rel_model:
            model = self.rel_model

        remote_field = model._meta.get_field(self.field_name).remote_field

        widget = AutocompleteSelectMultiple(
            remote_field, model_admin.admin_site)
        form_field = self.get_form_field()
        field = form_field(
            queryset=self.get_queryset_for_field(model, self.field_name),
            widget=widget,
            required=False,
        )

        self._add_media(model_admin, widget)

        attrs = self.widget_attrs.copy()
        attrs['id'] = 'id-%s-dal-filter' % self.field_name
        if self.is_placeholder_title:
            # Upper case letter P as dirty hack for bypass django2 widget force placeholder value as empty string ("")
            attrs['data-Placeholder'] = self.title
        self.rendered_widget = field.widget.render(
            name=self.parameter_name,
            value=self.value(),
            attrs=attrs
        )

    def get_queryset_for_field(self, model, name):
        field_desc = getattr(model, name)
        if isinstance(field_desc, ManyToManyDescriptor):
            related_model = field_desc.rel.related_model if field_desc.reverse else field_desc.rel.model
        elif isinstance(field_desc, ReverseManyToOneDescriptor):
            related_model = field_desc.rel.related_model
        else:
            return field_desc.get_queryset()
        return related_model.objects.get_queryset()

    def get_form_field(self):
        """Return the type of form field to be used."""
        return self.form_field

    def _add_media(self, model_admin, widget):
        if not hasattr(model_admin, 'Media'):
            raise ImproperlyConfigured(
                'Add empty Media class to %s. Sorry about this bug.' % model_admin)

        def _get_media(obj):
            return Media(media=getattr(obj, 'Media', None))

        class FilterMedia:
            js = (
                'admin/js/jquery.init.js',
                'django-admin-autocomplete-filter/js/autocomplete_filter_qs.js',
            )
            css = {
                'screen': (
                    'django-admin-autocomplete-filter/css/autocomplete-fix.css',
                ),
            }

        media = _get_media(model_admin) + widget.media + Media(FilterMedia)

        for name in MEDIA_TYPES:
            setattr(model_admin.Media, name, getattr(media, "_" + name))

    def has_output(self):
        return True

    def lookups(self, request, model_admin):
        return ()

    def value(self):
        if self.used_parameters.get(self.parameter_name):
            return self.used_parameters.get(self.parameter_name).split(',')
        else:
            return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.parameter_name: self.value()})
        else:
            return queryset

    def get_autocomplete_url(self, request, model_admin):
        '''
            Hook to specify your custom view for autocomplete,
            instead of default django admin's search_results.
        '''
        return None

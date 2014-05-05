# -*- encoding: utf-8 -*-
try:
    from django.conf.urls import patterns, url, include
except ImportError:
    from django.conf.urls.defaults import patterns, url, include
from django.views.generic.base import TemplateView

url_prefix = 'tinymce/images/'

urlpatterns = patterns('tinymce_images.views',
    #url(r'download/$', tiny_views.download),
    #url(r'^$', tiny_views.all),
    url(r'^new_folder/(?P<name>\w+)/(?P<path>[a-zA-Z0-9_/]*)$',
        'new_folder', {}, 'new_folder'),
    url(r'^show_path/(?P<type>\w+)/(?P<path>[a-zA-Z0-9_/]*)$',
        'show_path', {}, 'show_path'),
    url(r'^show_tree/(?P<type>\w+)/(?P<path>[a-zA-Z0-9_/]*)$',
        'show_tree', {}, 'show_tree'),
    url(r'^show_dir/(?P<type>\w+)/(?P<path>[a-zA-Z0-9_/]*)$',
        'show_dir', {}, 'show_dir'), 
    url(r'^del_folder/(?P<path>[a-zA-Z0-9_/]*)$',
        'del_folder', {}, 'del_folder'), 
    url(r'^upload_file/$', 'upload_file', {}, 'upload_file'),
    url(r'^del_file/$', 'del_file', {}, 'del_file'),
    url(r'^sid/$', 'sid', {}, 'sid'),
)


class ConnectorView(TemplateView):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context,
                                       content_type='text/javascript')

urlpatterns = patterns("",
    url(r'^%s' % url_prefix, include(urlpatterns)),
    url(r'^%s$' % url_prefix,
        ConnectorView.as_view(template_name='connector_url.js'),
        name='connector_url'),
)

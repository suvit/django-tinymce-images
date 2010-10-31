from django.conf.urls.defaults import *
import views as tiny_views
urlpatterns = patterns('tinymce_images.view',
    #url(r'download/$', tiny_views.download),
    #url(r'^$', tiny_views.all),
    url(r'^new_folder/(?P<name>\w+)/(?P<path>[a-zA-Z0-9_/]*)$', 'new_folder', {}, 'new_folder'),
    url(r'^show_path/(?P<type>\w+)/(?P<path>[a-zA-Z0-9_/]*)$', 'show_path', {}, 'show_path'),
    url(r'^show_tree/(?P<type>\w+)/(?P<path>[a-zA-Z0-9_/]*)$', 'show_tree', {}, 'show_tree'),
    url(r'^show_dir/(?P<type>\w+)/(?P<path>[a-zA-Z0-9_/]*)$', 'show_dir', {}, 'show_dir'), 
    url(r'^del_folder/(?P<path>[a-zA-Z0-9_/]*)$', 'del_folder', {}, 'del_folder'), 
    url(r'^upload_file/$', 'upload_file', {}, 'upload_file'),
    url(r'^del_file/$', 'del_file', {}, 'del_file'),
    url(r'^sid/$', 'sid', {}, 'sid'),
)

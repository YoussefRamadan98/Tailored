from django.conf.urls import url
from tailored import views
from django.contrib.auth.views import password_change

app_name = 'tailored'
urlpatterns = [
	url(r'^$', views.trending, name = 'index'),
	url(r'^user_profile/$', views.user_profile, name = "user_profile"),
	url(r'^search/new/(?P<search>[-\w]+)/$', views.new_in, name = 'new_in'),
	url(r'^search/$', views.search_bar, name = 'search'),
	url(r'^search/(?P<search>.+)/$', views.search_bar, name = 'search'),
	url(r'^profile/(?P<seller_username>[-\w]+)/$', views.show_seller_profile, name = 'show_seller_profile'),
	url(r'^item/(?P<itemID>[-\w]+)/$', views.show_item, name = 'show_item'),
	url(r'^delete/(?P<itemID>[-\w]+)/$', views.delete, name = 'delete'),
	url(r'^terms_and_conditions/$', views.terms_and_conditions, name = 'terms_and_conditions')
]
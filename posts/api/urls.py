"""
URLs para las APIs del sistema de tags inteligente.
"""

from django.urls import path
from . import views

app_name = 'posts_api'

urlpatterns = [
    # APIs de tags
    path('tags/suggest/', views.TagSuggestView.as_view(), name='tag-suggest'),
    path('tags/keywords/', views.KeywordExtractView.as_view(), name='tag-keywords'),
    path('tags/related/', views.RelatedTagsView.as_view(), name='related-tags'),
    path('tags/popular/', views.PopularTagsView.as_view(), name='popular-tags'),
    path('tags/trending/', views.TrendingTagsView.as_view(), name='trending-tags'),
    path('tags/stats/', views.TagStatsView.as_view(), name='tag-stats'),
    path('tags/validate/', views.TagValidateView.as_view(), name='tag-validate'),
]
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.urls import path
from .views import CategoryView,CourseView,CourseDetailView,CourseChapterView,CourseCommentView,QuestionView

urlpatterns = [
    path('category/', CategoryView.as_view()),
    path('list/',CourseView.as_view()),
    path('detail/<int:pk>', CourseDetailView.as_view()),
    path('chapter/<int:pk>', CourseChapterView.as_view()),
    path('comment/<int:pk>', CourseCommentView.as_view()),
    path('question/<int:pk>', QuestionView.as_view())
]

from django.urls import path, include
from rest_framework_nested import routers
from glitchtip.routers import BulkSimpleRouter
from .views import IssueViewSet, EventViewSet

router = BulkSimpleRouter()
router.register(r"issues", IssueViewSet)

issues_router = routers.NestedSimpleRouter(router, r"issues", lookup="issue")
issues_router.register(r"events", EventViewSet, basename="event-issues")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
    path("", include(issues_router.urls)),
]

from django.urls import path, include
from rest_framework_nested import routers
from issues.views import IssueViewSet, EventViewSet
from .views import ProjectViewSet, ProjectKeyViewSet

router = routers.SimpleRouter()
router.register(r"projects", ProjectViewSet)

projects_router = routers.NestedSimpleRouter(router, r"projects", lookup="project")
projects_router.register(r"keys", ProjectKeyViewSet, base_name="project-keys")
projects_router.register(r"issues", IssueViewSet, base_name="project-issues")
projects_router.register(r"events", EventViewSet, base_name="project-events")

urlpatterns = [path("", include(router.urls)), path("", include(projects_router.urls))]


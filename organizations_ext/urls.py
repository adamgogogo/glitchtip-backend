from django.urls import path, include
from rest_framework_nested import routers
from issues.views import IssueViewSet
from .views import OrganizationViewSet

router = routers.SimpleRouter()
router.register(r"organizations", OrganizationViewSet)

organizations_router = routers.NestedSimpleRouter(
    router, r"organizations", lookup="organization"
)
organizations_router.register(r"issues", IssueViewSet, base_name="organization-issues")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(organizations_router.urls)),
]
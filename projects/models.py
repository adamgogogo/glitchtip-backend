from urllib.parse import urlparse
from uuid import uuid4
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django_extensions.db.fields import AutoSlugField


class Project(models.Model):
    """
    Projects are permission based namespaces which generally
    are the top level entry point for all data.
    """

    slug = AutoSlugField(populate_from=["name", "organization_id"], max_length=30)
    name = models.CharField(max_length=64)
    organization = models.ForeignKey(
        "organizations_ext.Organization",
        on_delete=models.CASCADE,
        related_name="projects",
    )
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    platform = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        unique_together = (("organization", "slug"),)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        first = False
        if not self.pk:
            first = True
        super().save(*args, **kwargs)
        if first:
            ProjectKey.objects.create(project=self)

    def slugify_function(self, content):
        """
        Make the slug the project name. Validate uniqueness with both name and org id.
        This works because when it runs on organization_id it returns an empty string.
        """
        if isinstance(content, str):
            return slugify(self.name)
        return ""


class ProjectKey(models.Model):
    """ Authentication key for a Project """

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    label = models.CharField(max_length=64, blank=True)
    public_key = models.UUIDField(default=uuid4, unique=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    rate_limit_count = models.PositiveSmallIntegerField(blank=True, null=True)
    rate_limit_window = models.PositiveSmallIntegerField(blank=True, null=True)
    data = JSONField(blank=True, null=True)

    def __str__(self):
        return str(self.public_key)

    @classmethod
    def from_dsn(cls, dsn):
        urlparts = urlparse(dsn)

        public_key = urlparts.username
        project_id = urlparts.path.rsplit("/", 1)[-1]

        try:
            return ProjectKey.objects.get(public_key=public_key, project=project_id)
        except ValueError:
            # ValueError would come from a non-integer project_id,
            # which is obviously a DoesNotExist. We catch and rethrow this
            # so anything downstream expecting DoesNotExist works fine
            raise ProjectKey.DoesNotExist("ProjectKey matching query does not exist.")

    @property
    def public_key_hex(self):
        """ The public key without dashes """
        return self.public_key.hex

    def dsn(self):
        return self.get_dsn()

    def get_dsn(self):
        key = self.public_key_hex
        urlparts = settings.GLITCHTIP_DOMAIN

        # If we do not have a scheme or domain/hostname, dsn is never valid
        if not urlparts.netloc or not urlparts.scheme:
            return ""

        return "%s://%s@%s/%s" % (
            urlparts.scheme,
            key,
            urlparts.netloc + urlparts.path,
            self.project_id,
        )

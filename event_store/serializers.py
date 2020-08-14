from typing import List, Tuple
from urllib.parse import urlparse
from datetime import datetime
from django.db import transaction, connection
from rest_framework import serializers
from sentry.eventtypes.error import ErrorEvent
from sentry.eventtypes.base import DefaultEvent
from issues.models import EventType, Event, Issue, EventTagKey
from .event_tag_processors import TAG_PROCESSORS
from .event_context_processors import EVENT_CONTEXT_PROCESSORS


class FlexibleDateTimeField(serializers.DateTimeField):
    """ Supports both DateTime and unix epoch timestamp """

    def to_internal_value(self, timestamp):
        try:
            return datetime.fromtimestamp(float(timestamp))
        except ValueError:
            return super().to_internal_value(timestamp)


class RequestSerializer(serializers.Serializer):
    env = serializers.DictField(
        child=serializers.CharField(allow_blank=True), required=False
    )
    headers = serializers.DictField(
        child=serializers.CharField(allow_blank=True), required=False
    )
    url = serializers.CharField(required=False, allow_blank=True)
    method = serializers.CharField(required=False, allow_blank=True)
    query_string = serializers.CharField(required=False, allow_blank=True)


class StoreDefaultSerializer(serializers.Serializer):
    """
    Default serializer. Used as both a base class and for default error types
    """

    type = EventType.DEFAULT
    breadcrumbs = serializers.JSONField(required=False)
    contexts = serializers.JSONField(required=False)
    event_id = serializers.UUIDField()
    extra = serializers.JSONField(required=False)
    level = serializers.CharField(required=False)
    logentry = serializers.JSONField(required=False)
    message = serializers.CharField(required=False)
    platform = serializers.CharField()
    release = serializers.CharField(required=False)
    request = RequestSerializer(required=False)
    sdk = serializers.JSONField()
    timestamp = FlexibleDateTimeField(required=False)
    transaction = serializers.CharField(required=False, allow_null=True)
    modules = serializers.JSONField(required=False)

    def get_eventtype(self):
        """ Get event type class from self.type """
        if self.type is EventType.DEFAULT:
            return DefaultEvent()
        if self.type is EventType.ERROR:
            return ErrorEvent()

    def modify_exception(self, exception):
        """ OSS Sentry does this, I have no idea why """
        if exception:
            for value in exception.get("values", []):
                value.pop("module", None)
                if value.get("stacktrace") and value["stacktrace"].get("frames"):
                    frames = value["stacktrace"]["frames"]
                    # If in_app is always true, make it false ¯\_(ツ)_/¯
                    if all(x.get("in_app") for x in frames):
                        for frame in frames:
                            frame["in_app"] = False
        return exception

    def generate_tags(self, event, data):
        """ Determine and ddd tag relational data """
        tags: List[Tuple[str, str]] = []
        for Processor in TAG_PROCESSORS:
            processor = Processor()
            value = processor.get_tag_values(data)
            if value:
                tags.append((processor.tag, value))
        self.save_tags(event, tags)

    def save_tags(self, event, tags: List[Tuple[str, str]]):
        """ Commit tags to database """
        tag_key_values = []
        # Get tag keys with 1 query (New ones are rarely created)
        event_tag_keys = EventTagKey.objects.filter(key__in=[tag[0] for tag in tags])
        for tag, value in tags:
            tag_key = next((x for x in event_tag_keys if x.key == tag), None)
            if tag_key is None:  # If there's a new tag key, create it
                tag_key, _ = EventTagKey.objects.get_or_create(key=tag)
            tag_key_values.append((tag_key.id, value))

        # add_event_tags adds event tag value (if necessary) and into event.tags
        if tag_key_values:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select add_event_tags(%s::uuid, %s::tag_key_value[]);",
                    [event.event_id, tag_key_values],
                )

    def annotate_contexts(self, event):
        """
        SDK events may contain contexts. This function adds additional contexts data
        """
        contexts = event.get("contexts")
        for Processor in EVENT_CONTEXT_PROCESSORS:
            processor = Processor()
            if contexts is None or not contexts.get(processor.name):
                processor_contexts = processor.get_context(event)
                if processor_contexts:
                    if contexts is None:
                        contexts = {}
                    contexts[processor.name] = processor_contexts
        return contexts

    def get_message(self, data):
        return data.get("logentry", {}).get("message", "")

    def create(self, project_id: int, data):
        eventtype = self.get_eventtype()
        metadata = eventtype.get_metadata(data)
        title = eventtype.get_title(metadata)
        culprit = eventtype.get_location(data)
        request = data.get("request")
        exception = self.modify_exception(data.get("exception"))
        if request:
            headers = request.get("headers")
            if headers:
                request["inferred_content_type"] = headers.get("Content-Type")
                request["headers"] = sorted([pair for pair in headers.items()])
        contexts = self.annotate_contexts(data)
        data["contexts"] = contexts

        with transaction.atomic():
            issue, _ = Issue.objects.get_or_create(
                title=title,
                culprit=culprit,
                project_id=project_id,
                type=self.type,
                defaults={"metadata": metadata},
            )
            params = {
                "event_id": data["event_id"],
                "issue": issue,
                "timestamp": data.get("timestamp"),
                "data": {
                    "contexts": contexts,
                    "culprit": culprit,
                    "exception": exception,
                    "metadata": metadata,
                    "message": self.get_message(data),
                    "modules": data.get("modules"),
                    "platform": data["platform"],
                    "request": request,
                    "sdk": data["sdk"],
                    "title": title,
                    "type": self.type.label,
                },
            }
            event = Event.objects.create(**params)
        issue.check_for_status_update()
        self.generate_tags(event, data)
        return event


class StoreErrorSerializer(StoreDefaultSerializer):
    """ Primary difference is the presense of exception attribute """

    type = EventType.ERROR
    exception = serializers.JSONField(required=False)


class StoreCSPReportSerializer(serializers.Serializer):
    """
    CSP Report Serializer
    Very different format from others Store serializers.
    Does not extend base class due to differences.
    """

    type = EventType.CSP

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is done to support the hyphen
        self.fields.update({"csp-report": serializers.JSONField()})

    def create(self, project_id: int, data):
        csp = data["csp-report"]
        title = self.get_title(csp)
        culprit = self.get_culprit(csp)
        uri = self.get_uri(csp)
        directive = self.get_effective_directive(csp)
        metadata = {
            "message": title,
            "uri": uri,
            "directive": directive,
        }
        issue, _ = Issue.objects.get_or_create(
            title=title,
            culprit=culprit,
            project_id=project_id,
            type=EventType.CSP,
            defaults={"metadata": metadata},
        )
        # Convert - to _
        normalized_csp = dict((k.replace("-", "_"), v) for k, v in csp.items())
        if "effective_directive" not in normalized_csp:
            normalized_csp["effective_directive"] = directive
        params = {
            "issue": issue,
            "data": {
                "culprit": culprit,
                "csp": normalized_csp,
                "title": title,
                "metadata": metadata,
                "message": title,
                "type": EventType.CSP.label,
            },
        }
        return Event.objects.create(**params)

    def get_effective_directive(self, data):
        """
        Some browers return effective-directive and others don't.
        Infer missing ones from violated directive
        """
        if "effective-directive" in data:
            return data["effective-directive"]
        first_violation = data["violated-directive"].split()[0]
        return first_violation

    def get_uri(self, data):
        url = data["blocked-uri"]
        return urlparse(url).netloc

    def get_title(self, data):
        effective_directive = self.get_effective_directive(data)
        humanized_directive = effective_directive.replace("-src", "")
        uri = self.get_uri(data)
        return f"Blocked '{humanized_directive}' from '{uri}'"

    def get_culprit(self, data):
        # "style-src cdn.example.com"
        return data.get("violated-directive")

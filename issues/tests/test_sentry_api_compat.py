import json
from typing import List, Dict
from django.urls import reverse
from rest_framework.test import APITestCase
from model_bakery import baker
from event_store.test_data.django_error_factory import template_error
from event_store.test_data.js_error_factory import throw_error
from issues.models import Event


class SentryAPICompatTestCase(APITestCase):
    def setUp(self):
        self.user = baker.make("users.user")
        self.client.force_login(self.user)
        self.project = baker.make("projects.Project")
        key = self.project.projectkey_set.first().public_key
        self.event_store_url = (
            reverse("event_store", args=[self.project.id]) + "?sentry_key=" + key.hex
        )

    def assertCompareData(self, data1: Dict, data2: Dict, fields: List[str]):
        """ Compare data of two dict objects. Compare only provided fields list """
        for field in fields:
            self.assertEqual(
                data1[field], data2[field], f"Failed for field '{field}'",
            )

    def get_json_data(self, path: str):
        with open(path) as json_file:
            return json.load(json_file)

    def test_template_error(self):
        res = self.client.post(self.event_store_url, template_error, format="json")
        self.assertEqual(res.status_code, 200)

        event_id = res.data["id"]
        url = f"/api/0/projects/{self.project.organization.slug}/{self.project.slug}/events/{event_id}/"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        issue = Event.objects.get(event_id=event_id).issue

        data = self.get_json_data(
            "event_store/test_data/django_template_error_event.json"
        )
        self.assertCompareData(res.data, data, ["culprit", "title", "metadata"])
        import ipdb; ipdb.set_trace()
        res_frames = res.data["entries"][0]["data"]["values"][0]["stacktrace"]["frames"]
        frames = data["entries"][0]["data"]["values"][0]["stacktrace"]["frames"]
        self.assertEqual(
            res_frames[0]["vars"]["exc"],
            frames[0]["vars"]["exc"]
        )
        self.assertEqual(
            res_frames[0]["vars"]["request"],
            frames[0]["vars"]["request"]
        )
        # Memory address is different, truncate it
        self.assertEqual(
            res_frames[0]['vars']['get_response'][:-16],
            frames[0]['vars']['get_response'][:-16]
        )
        self.assertEqual(
            res_frames[0]["function"],
            frames[0]["function"]
        )
        self.assertEqual(
            res_frames[0]["filename"],
            frames[0]["filename"]
        )

        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        data = self.get_json_data(
            "event_store/test_data/django_template_error_issue.json"
        )
        self.assertCompareData(res.data, data, ["title", "metadata"])

    def test_throw_error(self):
        res = self.client.post(self.event_store_url, throw_error, format="json")
        self.assertEqual(res.status_code, 200)

        event_id = res.data["id"]
        url = f"/api/0/projects/{self.project.organization.slug}/{self.project.slug}/events/{event_id}/"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        issue = Event.objects.get(event_id=event_id).issue

        data = self.get_json_data("event_store/test_data/js_throw_error_event.json")
        self.assertCompareData(res.data, data, ["title"])
        self.assertEqual(
            res.data["culprit"],
            "viewWrappedDebugError(http://localhost:4200/vendor.js)",
            "Not perfect match, should really be viewWrappedDebugError(vendor)",
        )
        self.assertEqual(res.data["metadata"]["function"], data["metadata"]["function"])

        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        data = self.get_json_data("event_store/test_data/js_throw_error_issue.json")
        self.assertCompareData(res.data, data, ["title"])
        self.assertEqual(res.data["metadata"]["function"], data["metadata"]["function"])

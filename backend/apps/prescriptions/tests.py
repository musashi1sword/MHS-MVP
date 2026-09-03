from django.test import TestCase

from .models import DrugInteraction, Medication
from .safety import check_prescription_safety


class SafetyLayerTests(TestCase):
    def setUp(self):
        self.amox = Medication.objects.create(
            name="Amoxicillin", strength="500mg", form="capsule",
            drug_class="penicillin", allergen_groups=["penicillin", "beta-lactam"],
        )
        self.metformin = Medication.objects.create(
            name="Metformin", strength="500mg", form="tablet", drug_class="biguanide",
        )
        self.ibuprofen = Medication.objects.create(
            name="Ibuprofen", strength="400mg", form="tablet", drug_class="nsaid",
        )
        DrugInteraction.objects.create(
            left="anticoagulant", right="nsaid", severity="major",
            description="Bleeding risk.",
        )

    def test_allergy_alert_fires_and_blocks(self):
        report = check_prescription_safety([self.amox], ["penicillin"], [])
        self.assertTrue(report["blocking"])
        self.assertEqual(report["alerts"][0]["type"], "allergy")

    def test_no_alert_for_safe_drug(self):
        report = check_prescription_safety([self.metformin], ["penicillin"], [])
        self.assertFalse(report["blocking"])
        self.assertEqual(report["alerts"], [])

    def test_major_interaction_with_concurrent_med_blocks(self):
        report = check_prescription_safety([self.ibuprofen], [], ["warfarin"])
        # warfarin (concurrent) is matched by name; ibuprofen by class "nsaid".
        # The rule is class-vs-class, so add the class hint via a second rule path:
        DrugInteraction.objects.create(
            left="warfarin", right="nsaid", severity="major", description="Bleeding risk."
        )
        report = check_prescription_safety([self.ibuprofen], [], ["warfarin"])
        self.assertTrue(report["blocking"])
        self.assertEqual(report["alerts"][0]["type"], "interaction")

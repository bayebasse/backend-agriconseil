from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.cultures.models import (
    CommuneLocalite,
    CultureRef,
    CultureSuivie,
    Departement,
    Region,
    ReferentielAgronomique,
)
from apps.calendrier.models import (
    CalendrierAgricole,
    OperationAgricole,
    RegleOperationAgricole,
    Stade,
    StadeReference,
)
from apps.calendrier.services import build_stages, ensure_calendar


class StagesAreScopedToTrackedCropTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        farmer_a = user_model.objects.create_user(username="farmer-a")
        farmer_b = user_model.objects.create_user(username="farmer-b")
        region = Region.objects.create(nom="Region")
        department = Departement.objects.create(region=region, nom="Department")
        commune = CommuneLocalite.objects.create(
            departement=department,
            nom="Commune",
            type_localite="commune",
        )
        crop_ref = CultureRef.objects.create(nom="Mil", code="mil")
        reference = ReferentielAgronomique.objects.create(
            culture=crop_ref,
            source="FAO",
        )
        self.stage_reference = StadeReference.objects.create(
            referentiel=reference,
            nom="Installation",
            ordre=1,
            duree_jours=20,
        )
        self.crop_a = CultureSuivie.objects.create(
            agriculteur=farmer_a,
            culture=crop_ref,
            region=region,
            departement=department,
            commune=commune,
            superficie=Decimal("1.00"),
            date_semis=date(2026, 1, 1),
            type_sol="sableux",
        )
        self.crop_b = CultureSuivie.objects.create(
            agriculteur=farmer_b,
            culture=crop_ref,
            region=region,
            departement=department,
            commune=commune,
            superficie=Decimal("1.00"),
            date_semis=date(2026, 2, 1),
            type_sol="sableux",
        )

    def test_stage_dates_are_isolated_and_existing_rows_are_preserved(self):
        legacy_stage = Stade.objects.create(
            culture=self.crop_a.culture,
            reference=self.stage_reference,
            nom="Legacy stage",
            ordre=1,
            duree_jours=20,
            date_debut=date(2025, 1, 1),
            date_fin=date(2025, 1, 20),
        )

        stage_a = build_stages(self.crop_a)[0]
        stage_b = build_stages(self.crop_b)[0]

        self.assertEqual(stage_a.date_debut, date(2026, 1, 1))
        self.assertEqual(stage_b.date_debut, date(2026, 2, 1))
        self.assertNotEqual(stage_a.pk, stage_b.pk)
        self.assertTrue(Stade.objects.filter(pk=legacy_stage.pk).exists())
        self.assertEqual(Stade.objects.count(), 3)

    def test_calendar_refresh_preserves_operation_and_user_status(self):
        stage = build_stages(self.crop_a)[0]
        calendar = CalendrierAgricole.objects.create(culture_suivie=self.crop_a)
        operation = OperationAgricole.objects.create(
            calendrier=calendar,
            stade=stage,
            nom="Surveillance",
            description="Ancienne description",
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 1, 2),
            statut="terminee",
        )
        RegleOperationAgricole.objects.create(
            culture=self.crop_a.culture,
            stade_reference=self.stage_reference,
            nom="Surveillance",
            description="Description actualisée",
            declencheur="debut_stade",
        )

        ensure_calendar(self.crop_a)

        operation.refresh_from_db()
        self.assertEqual(OperationAgricole.objects.filter(calendrier=calendar).count(), 1)
        self.assertEqual(operation.statut, "terminee")
        self.assertEqual(operation.description, "Description actualisée")
        self.assertEqual(operation.stade.culture_suivie_id, self.crop_a.pk)

    def test_legacy_calendar_operation_is_reused_without_deletion(self):
        legacy_stage = Stade.objects.create(
            culture=self.crop_a.culture,
            reference=self.stage_reference,
            nom="Installation legacy",
            ordre=1,
            duree_jours=20,
            date_debut=date(2025, 1, 1),
            date_fin=date(2025, 1, 20),
        )
        calendar = CalendrierAgricole.objects.create(culture_suivie=self.crop_a)
        old_operation = OperationAgricole.objects.create(
            calendrier=calendar,
            stade=legacy_stage,
            nom="Surveillance",
            date_debut=date(2025, 1, 1),
            date_fin=date(2025, 1, 2),
            statut="terminee",
        )
        RegleOperationAgricole.objects.create(
            culture=self.crop_a.culture,
            stade_reference=self.stage_reference,
            nom="Surveillance",
            declencheur="debut_stade",
        )

        ensure_calendar(self.crop_a)

        self.assertEqual(OperationAgricole.objects.filter(calendrier=calendar).count(), 1)
        old_operation.refresh_from_db()
        self.assertEqual(old_operation.statut, "terminee")
        self.assertEqual(old_operation.stade.culture_suivie_id, self.crop_a.pk)
        self.assertTrue(Stade.objects.filter(pk=legacy_stage.pk).exists())

    def test_stage_calculation_without_referential_returns_no_shared_stage(self):
        crop_without_reference = CultureRef.objects.create(
            nom="Sorgho sans référentiel", code="sorgho-sans-reference"
        )
        self.crop_a.culture = crop_without_reference
        self.crop_a.save(update_fields=["culture"])
        self.assertEqual(build_stages(self.crop_a), [])

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsBuyerRole
from apps.transactions.models import Reservation
from .models import CultureSuivie, RecolteReelle, ReferenceRendement
from .prediction_service import (
    _get_reference,
    _harvest_period,
    _matching_yield_reference,
    estimated_production_kg,
)


def _buyer_crop_payload(crop, yield_candidates):
    reference = _matching_yield_reference(crop, candidates=yield_candidates)
    estimated_total_kg = estimated_production_kg(crop, reference)
    estimated_kg_ha = None
    if estimated_total_kg is not None:
        multiplier = Decimal("1000") if reference.rendement_unite == "tonne_ha" else Decimal("1")
        estimated_kg_ha = Decimal(reference.rendement_moyen) * multiplier

    start, end, _reason = _harvest_period(crop, _get_reference(crop), reference)
    harvested_kg = Decimal("0")
    has_harvest_record = False
    for harvest in crop.recoltes_reelles.all():
        has_harvest_record = True
        harvested_kg += Decimal(harvest.quantite) * (
            Decimal("1000") if harvest.unite == "tonne" else Decimal("1")
        )

    available_quantity = crop.quantite_disponible_vente
    available_kg = None
    if available_quantity is not None:
        available_kg = Decimal(available_quantity) * (
            Decimal("1000") if crop.unite_disponible_vente == "tonne" else Decimal("1")
        )

    today = timezone.localdate()
    if crop.statut_recolte == "available" and available_kg is not None and available_kg > 0:
        crop_status = "available"
    elif crop.statut_recolte == "available":
        crop_status = "exhausted"
    elif crop.statut_recolte == "harvested":
        crop_status = "harvested"
    elif crop.statut_recolte == "in_progress":
        crop_status = "in_progress"
    else:
        crop_status = crop.statut_recolte

    farmer = crop.agriculteur
    farmer_name = " ".join(part for part in (farmer.first_name, farmer.last_name) if part).strip()
    new_since = today - timedelta(days=7)
    return {
        "id": crop.pk,
        "culture_id": crop.culture_id,
        "culture_code": crop.culture.code,
        "culture_nom": crop.culture.nom,
        "agriculteur_id": farmer.pk,
        "agriculteur_prenom": farmer.first_name or None,
        "agriculteur_nom": farmer.last_name or None,
        "agriculteur_nom_complet": farmer_name or None,
        "agriculteur_telephone": farmer.telephone or None,
        "localisation": crop.commune.nom if crop.commune_id else None,
        "departement": crop.departement.nom if crop.departement_id else None,
        "region_id": crop.region_id,
        "region": crop.region.nom if crop.region_id else None,
        "superficie": str(crop.superficie) if crop.superficie is not None else None,
        "unite_superficie": crop.unite_superficie or None,
        "rendement_estime_kg_ha": str(estimated_kg_ha) if estimated_kg_ha is not None else None,
        "recolte_estimee_kg": str(estimated_total_kg) if estimated_total_kg is not None else None,
        "recolte_reelle_kg": str(harvested_kg) if has_harvest_record else None,
        "recolte_disponible": str(available_quantity) if available_quantity is not None else None,
        "recolte_disponible_kg": str(available_kg) if available_kg is not None else None,
        "statut_recolte": crop.statut_recolte,
        "prix_kg_fcfa": str(crop.prix_kg_fcfa) if crop.prix_kg_fcfa is not None else None,
        "unite_recolte_disponible": crop.unite_disponible_vente or None,
        "date_recolte_debut": start.isoformat() if start else None,
        "date_recolte_fin": end.isoformat() if end else None,
        "statut": crop_status,
        "date_ajout": crop.created_at.isoformat(),
        "nouvelle": crop.created_at.date() >= new_since,
        "variete": crop.variete or None,
        "systeme_culture": crop.systeme_culture or None,
    }


class BuyerCropCatalogView(APIView):
    permission_classes = [IsAuthenticated, IsBuyerRole]

    def get(self, request):
        queryset = (
            CultureSuivie.objects
            .select_related(
                "culture", "region", "departement", "commune", "agriculteur"
            )
            .prefetch_related("recoltes_reelles")
            .filter(agriculteur__role="farmer")
            .order_by("-created_at", "-id")
        )

        if request.query_params.get("culture"):
            queryset = queryset.filter(culture__code=request.query_params["culture"])
        if request.query_params.get("region"):
            queryset = queryset.filter(region_id=request.query_params["region"])
        if request.query_params.get("localisation"):
            queryset = queryset.filter(commune__nom__icontains=request.query_params["localisation"])

        crop_ids = set(queryset.values_list("culture_id", flat=True))
        candidates_by_crop = {}
        for reference in ReferenceRendement.objects.filter(culture_id__in=crop_ids).select_related("culture"):
            candidates_by_crop.setdefault(reference.culture_id, []).append(reference)

        crops = [
            _buyer_crop_payload(crop, candidates_by_crop.get(crop.culture_id, []))
            for crop in queryset
        ]

        crop_record_ids = [item["id"] for item in crops]
        reserved_by_crop = dict(
            Reservation.objects.filter(
                culture_suivie_id__in=crop_record_ids,
                type_reservation="firm",
                statut="confirmed",
            ).values("culture_suivie_id")
            .annotate(total=Sum("quantite_kg"))
            .values_list("culture_suivie_id", "total")
        )
        for item in crops:
            estimate = Decimal(item["recolte_estimee_kg"]) if item["recolte_estimee_kg"] is not None else None
            harvested = Decimal(item["recolte_reelle_kg"] or "0")
            item["quantite_previsionnelle_reservable_kg"] = (
                str(max(Decimal("0"), estimate - harvested - (reserved_by_crop.get(item["id"]) or Decimal("0"))))
                if estimate is not None else None
            )

        if request.query_params.get("statut"):
            crops = [item for item in crops if item["statut"] == request.query_params["statut"]]
        if request.query_params.get("date_debut"):
            crops = [
                item for item in crops
                if item["date_recolte_debut"]
                and item["date_recolte_debut"] >= request.query_params["date_debut"]
            ]
        if request.query_params.get("date_fin"):
            crops = [
                item for item in crops
                if item["date_recolte_fin"]
                and item["date_recolte_fin"] <= request.query_params["date_fin"]
            ]

        indicators = {
            "cultures_visibles": len(crops),
            "recoltes_prevues": sum(item["statut_recolte"] == "in_progress" for item in crops),
            "recoltes_disponibles": sum(item["statut"] == "available" for item in crops),
            "nouvelles_cultures": sum(item["nouvelle"] for item in crops),
        }
        page_size = min(max(int(request.query_params.get("page_size", 24)), 1), 100)
        page = max(int(request.query_params.get("page", 1)), 1)
        offset = (page - 1) * page_size
        return Response({
            "results": crops[offset:offset + page_size],
            "count": len(crops),
            "page": page,
            "page_size": page_size,
            "indicators": indicators,
        })

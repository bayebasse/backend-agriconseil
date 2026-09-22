from django.db import models
from apps.cultures.models import CultureRef, CultureSuivie
#   ANcien stade
# class Stade(models.Model):
#     culture = models.ForeignKey(CultureRef, on_delete=models.CASCADE, related_name="stades")
#     nom = models.CharField(max_length=80)
#     ordre = models.PositiveIntegerField()
#     duree_jours = models.PositiveIntegerField()
#     kc = models.DecimalField(max_digits=5, decimal_places=2)
#     def __str__(self): return f"{self.culture.nom} - {self.nom}"
#     class Meta: ordering = ["culture_id", "ordre"]




#Calendrier MOdéle
class StadeReference(models.Model):
    """
    Donnée agronomique de référence.
    Elle décrit les grandes phases de développement d'une culture.
    """

    referentiel = models.ForeignKey(
        "cultures.ReferentielAgronomique",
        on_delete=models.CASCADE,
        related_name="stades",
    )

    nom = models.CharField(
        max_length=100,
    )

    ordre = models.PositiveIntegerField()

    duree_jours = models.PositiveIntegerField()

    kc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["referentiel_id", "ordre"]

        constraints = [
            models.UniqueConstraint(
                fields=["referentiel", "ordre"],
                name="unique_ordre_stade_referentiel",
            )
        ]

    def __str__(self):
        return f"{self.referentiel.culture.nom} - {self.nom}"


#Regle de calculs:
class RegleOperationAgricole(models.Model):
    """
    Règle interne à Agri-Conseil permettant de transformer
    les données agronomiques en dates de calendrier.
    """

    DECLENCHEUR_CHOICES = [
        ("semis", "Date de semis"),
        ("debut_stade", "Début du stade"),
        ("fin_stade", "Fin du stade"),
        ("fin_cycle", "Fin du cycle"),
    ]

    culture = models.ForeignKey(
        CultureRef,
        on_delete=models.CASCADE,
        related_name="regles_operations",
    )

    stade_reference = models.ForeignKey(
        StadeReference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regles_operations",
    )

    nom = models.CharField(
        max_length=120,
    )

    description = models.TextField(
        blank=True,
    )

    declencheur = models.CharField(
        max_length=30,
        choices=DECLENCHEUR_CHOICES,
    )

    decalage_jours = models.IntegerField(
        default=0,
    )

    duree_jours = models.PositiveIntegerField(
        default=1,
    )

    ordre = models.PositiveIntegerField(
        default=0,
    )

    actif = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["culture_id", "ordre", "id"]

    def __str__(self):
        return f"{self.culture.nom} - {self.nom}"        

class Stade(models.Model):
    """
    Stade utilisé par le moteur de calendrier.
    Il est généré à partir du référentiel agronomique.
    """

    culture = models.ForeignKey(
        CultureRef,
        on_delete=models.CASCADE,
        related_name="stades_calcul",
    )

    reference = models.ForeignKey(
        StadeReference,
        on_delete=models.PROTECT,
        related_name="stades_calcules",
    )
    
    
    nom = models.CharField(
        max_length=100,
    )

    ordre = models.PositiveIntegerField()

    duree_jours = models.PositiveIntegerField()

    date_debut = models.DateField(
        null=True,
        blank=True,
    )

    date_fin = models.DateField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.culture.nom} - {self.nom}"

    class Meta:
        ordering = ["culture_id", "ordre"]

class CalendrierAgricole(models.Model):
    culture_suivie = models.OneToOneField(
    CultureSuivie,
    on_delete=models.CASCADE,
    related_name="calendrier",
            )

    date_generation = models.DateTimeField(
         auto_now=True,
     )

    def __str__(self):
         return f"Calendrier {self.culture_suivie}"

class OperationAgricole(models.Model):
    calendrier = models.ForeignKey(
        CalendrierAgricole,
        on_delete=models.CASCADE,
        related_name="operations",
    )

    stade = models.ForeignKey(
        Stade,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    nom = models.CharField(
        max_length=120,
    )

    description = models.TextField(
        blank=True,
    )

    date_debut = models.DateField()

    date_fin = models.DateField()

    statut = models.CharField(
        max_length=30,
        default="a_faire",
    )

    def __str__(self):
        return self.nom

    class Meta:
        ordering = ["date_debut", "id"]



#TESTTTTTE BASS DIEYE


# class CalendrierAgricole(models.Model):
#     culture_suivie = models.OneToOneField(
#         CultureSuivie,
#         on_delete=models.CASCADE,
#         related_name="calendrier",
#     )

#     date_generation = models.DateTimeField(
#         auto_now=True,
#     )

#     def __str__(self):
#         return f"Calendrier {self.culture_suivie}"



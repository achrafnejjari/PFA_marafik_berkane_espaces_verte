from django.db import models
from django.contrib.auth.models import User

# Modèle pour les rôles
class Role(models.Model):
    nom = models.CharField(max_length=50, default="Employé")

    def __str__(self):
        return self.nom

    class Meta:
        default_related_name = "roles"

# Modèle pour les utilisateurs (lié à django.contrib.auth.models.User)
class Utilisateur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='utilisateur', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    actif = models.BooleanField(default=True)
    email = models.EmailField(max_length=254, unique=True  , null=True)  

    def __str__(self):
        return self.user.username if self.user else "Utilisateur sans compte"

    class Meta:
        default_related_name = "utilisateurs"

# Modèle pour les types de tâches
class TaskType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        default_related_name = "task_types"




# Modèle pour les tâches
class Task(models.Model):
    task_type = models.ForeignKey(TaskType, on_delete=models.CASCADE)
    quartier = models.CharField(max_length=200)
    date = models.CharField(max_length=7)
    jour_1 = models.IntegerField(default=0)
    jour_2 = models.IntegerField(default=0)
    jour_3 = models.IntegerField(default=0)
    jour_4 = models.IntegerField(default=0)
    jour_5 = models.IntegerField(default=0)
    jour_6 = models.IntegerField(default=0)
    jour_7 = models.IntegerField(default=0)
    jour_8 = models.IntegerField(default=0)
    jour_9 = models.IntegerField(default=0)
    jour_10 = models.IntegerField(default=0)
    jour_11 = models.IntegerField(default=0)
    jour_12 = models.IntegerField(default=0)
    jour_13 = models.IntegerField(default=0)
    jour_14 = models.IntegerField(default=0)
    jour_15 = models.IntegerField(default=0)
    jour_16 = models.IntegerField(default=0)
    jour_17 = models.IntegerField(default=0)
    jour_18 = models.IntegerField(default=0)
    jour_19 = models.IntegerField(default=0)
    jour_20 = models.IntegerField(default=0)
    jour_21 = models.IntegerField(default=0)
    jour_22 = models.IntegerField(default=0)
    jour_23 = models.IntegerField(default=0)
    jour_24 = models.IntegerField(default=0)
    jour_25 = models.IntegerField(default=0)
    jour_26 = models.IntegerField(default=0)
    jour_27 = models.IntegerField(default=0)
    jour_28 = models.IntegerField(default=0)
    jour_29 = models.IntegerField(default=0)
    jour_30 = models.IntegerField(default=0)
    jour_31 = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="tasks_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


    def __str__(self):
        return f"Tâche {self.id} - {self.task_type.name} - {self.date}"

    def save(self, *args, **kwargs):
        self.total = sum(getattr(self, f"jour_{i}") for i in range(1, 32))
        super().save(*args, **kwargs)

    class Meta:
        default_related_name = "tasks"

# Modèle pour l'historique
class TaskHistory(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Création"),
        ("UPDATE", "Modification"),
        ("DELETE", "Suppression"),
    ]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.timestamp}"

    class Meta:
        default_related_name = "task_histories"

# Modèle pour les fichiers Excel
class FichierExcel(models.Model):
    nom_fichier = models.CharField(max_length=200)
    fichier_path = models.CharField(max_length=500)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_envoi = models.DateTimeField(auto_now_add=True)
    type_utilisation = models.CharField(max_length=100)

    def __str__(self):
        return self.nom_fichier

    class Meta:
        default_related_name = "fichiers_excel"




# cette fonction pour la button vide l'afichage de page employee task
class HiddenTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_hidden = models.BooleanField(default=False)
    hidden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'task')

    def __str__(self):
        return f"Hidden: {self.task} for {self.user}"

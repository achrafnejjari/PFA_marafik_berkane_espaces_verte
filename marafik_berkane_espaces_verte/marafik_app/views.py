from django.shortcuts import render, redirect 
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.http import HttpResponse
from marafik_app.models import Role, Utilisateur
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.utils import timezone
import logging
from marafik_app.models import TaskType, Task , HiddenTask , TaskHistory
from django.db.models import Sum , Q
from datetime import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse
import re
from django.views.decorators.cache import never_cache
from django.db import transaction




# Configurer le logging
logger = logging.getLogger(__name__)

# Fonction pour supprimer toutes les sessions d'un utilisateur
def delete_user_sessions(user):
    try:
        # Récupérer toutes les sessions actives
        all_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in all_sessions:
            session_data = session.get_decoded()
            if str(user.id) == session_data.get('_auth_user_id'):
                session.delete()
                logger.info(f"Session supprimée pour l'utilisateur {user.username} (user_id={user.id})")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des sessions pour user_id={user.id}: {str(e)}")

# Vérifie si l'utilisateur a le rôle spécifié ou si c'est un Super Admin
def role_required(role_name):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Vous devez être connecté pour accéder à cette page.")
                logger.warning("Accès non authentifié à une page protégée")
                return redirect('login')  # marafik_app__login
            try:
                utilisateur = Utilisateur.objects.get(user=request.user)
                # Vérifier si l'utilisateur est actif
                if not utilisateur.actif:
                    logger.warning(f"Utilisateur {request.user.username} (user_id={request.user.id}) est désactivé, déconnexion forcée")
                    auth_logout(request)
                    messages.error(request, "Votre compte est désactivé. Contactez l'administrateur.")
                    return redirect('login')
                logger.info(f"Utilisateur {request.user.username} (user_id={request.user.id}) trouvé avec rôle {utilisateur.role.nom}")
                # Autoriser l'accès si l'utilisateur a le rôle requis OU si c'est un Super Admin pour les rôles Admin ou Employé
                if utilisateur.role.nom == role_name or (role_name in ["Admin", "Employé"] and utilisateur.role.nom == "Super Admin"):
                    return view_func(request, *args, **kwargs)
                messages.error(request, "Vous n'avez pas les autorisations nécessaires.")
                logger.warning(f"Utilisateur {request.user.username} n'a pas le rôle {role_name}")
                return redirect('home')  # marafik_app__home
            except Utilisateur.DoesNotExist:
                logger.error(f"Aucune entrée Utilisateur pour {request.user.username} (user_id={request.user.id})")
                messages.error(request, "Utilisateur non trouvé dans la table Utilisateur.")
                return redirect('home')
        return wrapper
    return decorator

def home(request):
    if request.user.is_authenticated:
        logger.info(f"Accès à home par {request.user.username} (user_id={request.user.id})")
        try:
            utilisateur = Utilisateur.objects.get(user=request.user)
            logger.info(f"Rôle de l'utilisateur : {utilisateur.role.nom}")
        except Utilisateur.DoesNotExist:
            logger.error(f"Aucune entrée Utilisateur pour {request.user.username} (user_id={request.user.id})")
    return render(request, 'marafik_app/home.html')

def about(request):
    return render(request, 'marafik_app/about.html')

def register(request):
    try:
        if request.method == 'POST':
            nom = request.POST.get('nom')
            email = request.POST.get('email')
            mot_de_passe = request.POST.get('mot_de_passe')
            mot_de_passe_confirm = request.POST.get('mot_de_passe_confirm')

            # Vérifier si les mots de passe correspondent
            if mot_de_passe != mot_de_passe_confirm:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                logger.warning("Les mots de passe ne correspondent pas lors de l'inscription")
                return render(request, 'marafik_app/register.html')

            # Vérifier si l'email est déjà utilisé
            if User.objects.filter(email=email).exists():
                messages.error(request, "Cet email est déjà utilisé.")
                logger.warning(f"Email {email} déjà utilisé lors de l'inscription")
                return render(request, 'marafik_app/register.html')

            # Créer l'utilisateur dans django.contrib.auth.models.User
            user = User.objects.create_user(
                username=email,
                email=email,
                password=mot_de_passe,
                last_name=nom
            )
            logger.info(f"Utilisateur {email} (user_id={user.id}) créé")

            # Récupérer le rôle "Employé"
            role, created = Role.objects.get_or_create(nom="Employé")
            logger.info(f"Rôle Employé {'créé' if created else 'récupéré'} pour user_id={user.id}")

            # Créer l'instance dans le modèle Utilisateur
            Utilisateur.objects.create(
                user=user,
                role=role,
                actif=True,
                email=email
            )
            logger.info(f"Entrée Utilisateur créée pour {email} avec rôle Employé")

            # Message de succès et redirection
            messages.success(request, "Inscription réussie ! Veuillez vous connecter.")
            return redirect('login')  # marafik_app__login

        return render(request, 'marafik_app/register.html')
    except Exception as e:
        logger.error(f"Erreur dans register: {str(e)}")
        return HttpResponse(f"Erreur dans register: {str(e)}")

def login_view(request):
    try:
        if request.method == 'POST':
            email = request.POST.get('email')
            mot_de_passe = request.POST.get('mot_de_passe')

            # Authentifier l'utilisateur
            user = authenticate(request, username=email, password=mot_de_passe)
            if user is not None:
                # Vérifier si l'utilisateur a une entrée dans Utilisateur et s'il est actif
                try:
                    utilisateur = Utilisateur.objects.get(user=user)
                    if not utilisateur.actif:
                        messages.error(request, "Votre compte est désactivé. Contactez l'administrateur.")
                        logger.warning(f"Échec de connexion pour {email} : compte désactivé")
                        return render(request, 'marafik_app/login.html')
                    auth_login(request, user)
                    logger.info(f"Connexion réussie pour {user.username} (user_id={user.id})")
                    logger.info(f"Entrée Utilisateur trouvée pour {user.username} avec rôle {utilisateur.role.nom}")
                    messages.success(request, "Connexion réussie !")
                    return redirect('home')  # marafik_app__home
                except Utilisateur.DoesNotExist:
                    logger.warning(f"Aucune entrée Utilisateur pour {user.username} (user_id={user.id}), création d'une nouvelle entrée")
                    role, created = Role.objects.get_or_create(nom="Employé")
                    Utilisateur.objects.create(user=user, role=role, actif=True)
                    auth_login(request, user)
                    logger.info(f"Entrée Utilisateur créée pour {user.username} avec rôle Employé")
                    messages.success(request, "Connexion réussie !")
                    return redirect('home')  # marafik_app__home
            else:
                messages.error(request, "Email ou mot de passe incorrect.")
                logger.warning(f"Échec de connexion pour {email}")
                return render(request, 'marafik_app/login.html')

        return render(request, 'marafik_app/login.html')
    except Exception as e:
        logger.error(f"Erreur dans login: {str(e)}")
        return HttpResponse(f"Erreur dans login: {str(e)}")

@login_required
def logout_view(request):
    logger.info(f"Déconnexion de {request.user.username} (user_id={request.user.id})")
    auth_logout(request)
    messages.success(request, "Déconnexion réussie.")
    return redirect('home')  # marafik_app__home

@login_required
@role_required("Employé")
@never_cache
def employee_task(request):
    task_types = TaskType.objects.all()
    task_data = {}

    for task_type in task_types:
        try:
            # Récupérer les tâches masquées par l'utilisateur
            hidden_task_ids = HiddenTask.objects.filter(
                user=request.user,
                is_hidden=True
            ).values_list('task_id', flat=True)

            # Charger les tâches non supprimées et non masquées
            tasks = Task.objects.filter(
                task_type=task_type,
                created_by=request.user,
                is_deleted=False
            ).exclude(id__in=hidden_task_ids)

            # Calculer les totaux
            totals = tasks.aggregate(
                **{f'jour_{i}': Sum(f'jour_{i}') for i in range(1, 32)},
                total=Sum('total')
            )

            # Préparer les données des tâches
            task_list = []
            for task in tasks:
                task_dict = {
                    'id': task.id,
                    'quartier': task.quartier or '-',
                    'date': task.date or '-',
                    'total': task.total or 0,
                    'jours': [getattr(task, f'jour_{i}', 0) or 0 for i in range(1, 32)]
                }
                task_list.append(task_dict)

            # Totaux
            totals_list = [totals.get(f'jour_{i}', 0) or 0 for i in range(1, 32)]
            total_sum = totals.get('total', 0) or 0

            task_data[task_type.name] = {
                'tasks': task_list,
                'totals': {
                    'jours': totals_list,
                    'total': total_sum
                },
                'task_type_id': task_type.id
            }

        except Exception as e:
            messages.error(request, f"Erreur pour {task_type.name} : {str(e)}")
            logger.error(f"Error loading tasks for {task_type.name}: {str(e)}", exc_info=True)
            task_data[task_type.name] = {
                'tasks': [],
                'totals': {'jours': [0] * 31, 'total': 0},
                'task_type_id': task_type.id
            }

    # Gestion des actions POST
    if request.method == "POST":
        try:
            # === Masquer les tâches ===
            if "hide_tasks" in request.POST:
                task_ids = request.POST.getlist('task_ids[]')
                if task_ids:
                    success_count = 0
                    for task_id in task_ids:
                        try:
                            task = Task.objects.get(
                                id=task_id,
                                created_by=request.user,
                                is_deleted=False
                            )
                            hidden_task, created = HiddenTask.objects.get_or_create(
                                user=request.user,
                                task=task,
                                defaults={'is_hidden': True}
                            )
                            if not created:
                                hidden_task.is_hidden = True
                                hidden_task.save()
                            success_count += 1
                        except Task.DoesNotExist:
                            continue  # Ignore les tâches introuvables ou non autorisées
                        except Exception as e:
                            logger.error(f"Failed to hide task {task_id}: {str(e)}")
                            continue
                    messages.success(request, f"{success_count} tâche(s) masquée(s) avec succès.")
                else:
                    messages.info(request, "Aucune tâche à masquer.")
                return redirect("employee_task")

            # === Ajouter une tâche ===
            elif "add_task" in request.POST:
                task_type_id = request.POST.get("task_type_id")
                quartier = request.POST.get("adresse", "").strip()
                date = request.POST.get("date", "").strip()

                if not task_type_id or not quartier or not date:
                    messages.error(request, "Le type de tâche, le quartier et la date sont obligatoires.")
                    return redirect("employee_task")

                # Normaliser la date
                try:
                    year, month = date.split('-')
                    date = f"{int(year):04d}-{int(month):02d}"
                except (ValueError, AttributeError):
                    messages.error(request, "Format de date invalide. Utilisez AAAA-MM (ex: 2025-07).")
                    return redirect("employee_task")

                # Vérifier le type de tâche
                try:
                    task_type = TaskType.objects.get(id=task_type_id)
                except TaskType.DoesNotExist:
                    messages.error(request, "Type de tâche invalide.")
                    return redirect("employee_task")

                # Calculer les jours et le total
                total = 0
                task_data = {
                    'task_type': task_type,
                    'quartier': quartier,
                    'date': date,
                    'created_by': request.user,
                    'is_deleted': False
                }

                for day in range(1, 32):
                    try:
                        value = int(request.POST.get(f'jour_{day}', 0))
                        task_data[f'jour_{day}'] = max(0, value)
                        total += value
                    except (ValueError, TypeError):
                        task_data[f'jour_{day}'] = 0
                task_data['total'] = total

                # Créer la tâche
                task = Task.objects.create(**task_data)
                messages.success(request, f"Entrée ajoutée pour {task_type.name} (ID={task.id}).")
                return redirect("employee_task")

            # === Modifier une tâche ===
            elif "edit_task" in request.POST:
                task_id = request.POST.get("task_id")
                quartier = request.POST.get("adresse", "").strip()
                date = request.POST.get("date", "").strip()

                if not task_id or not quartier or not date:
                    messages.error(request, "L'ID de tâche, le quartier et la date sont obligatoires.")
                    return redirect("employee_task")

                # Normaliser la date
                try:
                    year, month = date.split('-')
                    date = f"{int(year):04d}-{int(month):02d}"
                except (ValueError, AttributeError):
                    messages.error(request, "Format de date invalide.")
                    return redirect("employee_task")

                # Charger la tâche
                try:
                    task = Task.objects.get(id=task_id, created_by=request.user, is_deleted=False)
                except Task.DoesNotExist:
                    messages.error(request, "Tâche introuvable ou non autorisée.")
                    return redirect("employee_task")

                # Mettre à jour les champs
                task.quartier = quartier
                task.date = date
                total = 0
                for day in range(1, 32):
                    try:
                        value = int(request.POST.get(f'jour_{day}', 0))
                        setattr(task, f'jour_{day}', max(0, value))
                        total += value
                    except (ValueError, TypeError):
                        setattr(task, f'jour_{day}', 0)
                task.total = total
                task.save()
                messages.success(request, f"Entrée modifiée pour {task.task_type.name}.")
                return redirect("employee_task")

            # === Supprimer une tâche ===
            elif "delete_task" in request.POST:
                task_id = request.POST.get("task_id")
                try:
                    task = Task.objects.get(id=task_id, created_by=request.user, is_deleted=False)
                    task_type_name = task.task_type.name
                    task.is_deleted = True
                    task.save()
                    HiddenTask.objects.filter(user=request.user, task=task).delete()
                    messages.success(request, f"Entrée supprimée pour {task_type_name}.")
                except Task.DoesNotExist:
                    messages.error(request, "Tâche introuvable ou non autorisée.")
                return redirect("employee_task")

        except Exception as e:
            messages.error(request, f"Erreur interne : {str(e)}")
            logger.error(f"POST error in employee_task: {str(e)}", exc_info=True)
            return redirect("employee_task")

    # Préparer les jours pour le template
    days = list(range(1, 32))

    return render(request, 'marafik_app/employee_task.html', {
        'task_data': task_data,
        'days': days,
        'current_date': request.GET.get('year_month', '2025-07')
    })

######### Configuration Admin ###############
@login_required
@role_required("Admin")
def admin_setup(request):
    # Filtre par date
    year_month = request.GET.get('year_month', '').strip()
    if year_month:
        try:
            year, month = year_month.split('-')
            year_month = f"{int(year):04d}-{int(month):02d}"
        except (ValueError, AttributeError):
            messages.error(request, "Format de date invalide. Utilisez AAAA-MM.")
            year_month = None
    else:
        year_month = None

    task_types = TaskType.objects.all()
    task_data = {}
    filter_errors = []

    for task_type in task_types:
        try:
            tasks = Task.objects.filter(task_type=task_type, is_deleted=False)
            if year_month:
                tasks = tasks.filter(date=year_month)
                if not tasks.exists():
                    filter_errors.append(f"Aucune tâche trouvée pour {task_type.name} en {year_month}.")

            totals = tasks.aggregate(
                **{f'jour_{i}': Sum(f'jour_{i}') for i in range(1, 32)},
                total=Sum('total')
            )

            task_list = []
            for task in tasks:
                task_dict = {
                    'id': task.id,
                    'quartier': task.quartier or '-',
                    'date': task.date or '-',
                    'total': task.total or 0,
                    'jours': [getattr(task, f'jour_{i}', 0) or 0 for i in range(1, 32)]
                }
                task_list.append(task_dict)

            totals_list = [totals.get(f'jour_{i}', 0) or 0 for i in range(1, 32)]
            total_sum = totals.get('total', 0) or 0

            task_data[task_type.name] = {
                'tasks': task_list,
                'totals': {'jours': totals_list, 'total': total_sum},
                'task_type_id': task_type.id
            }

        except Exception as e:
            messages.error(request, f"Erreur pour {task_type.name} : {str(e)}")
            logger.error(f"Error in admin_setup: {str(e)}", exc_info=True)
            task_data[task_type.name] = {
                'tasks': [],
                'totals': {'jours': [0] * 31, 'total': 0},
                'task_type_id': task_type.id
            }

    for error in filter_errors:
        messages.info(request, error)

    # Gestion POST
    if request.method == "POST":
        try:
            if "add_task" in request.POST:
                task_type_id = request.POST.get("task_type_id")
                quartier = request.POST.get("adresse", "").strip()
                date = request.POST.get("date", "").strip()

                if not quartier or not date:
                    messages.error(request, "Le quartier et la date sont obligatoires.")
                    return redirect(reverse('admin_setup') + (f'?year_month={year_month}' if year_month else ''))

                try:
                    year, month = date.split('-')
                    date = f"{int(year):04d}-{int(month):02d}"
                except (ValueError, AttributeError):
                    messages.error(request, "Format de date invalide.")
                    return redirect(reverse('admin_setup') + (f'?year_month={year_month}' if year_month else ''))

                try:
                    task_type = TaskType.objects.get(id=task_type_id)
                except TaskType.DoesNotExist:
                    messages.error(request, "Type de tâche invalide.")
                    return redirect(reverse('admin_setup') + (f'?year_month={year_month}' if year_month else ''))

                total = 0
                task_data = {
                    'task_type': task_type,
                    'quartier': quartier,
                    'date': date,
                    'created_by': request.user
                }

                for day in range(1, 32):
                    try:
                        value = int(request.POST.get(f'jour_{day}', 0))
                        task_data[f'jour_{day}'] = max(0, value)
                        total += value
                    except (ValueError, TypeError):
                        task_data[f'jour_{day}'] = 0
                task_data['total'] = total

                Task.objects.create(**task_data)
                messages.success(request, f"Entrée ajoutée pour {task_type.name}.")
                return redirect(reverse('admin_setup') + f'?year_month={date}')

            elif "edit_task" in request.POST:
                task_id = request.POST.get("task_id")
                quartier = request.POST.get("adresse", "").strip()
                date = request.POST.get("date", "").strip()

                if not quartier or not date:
                    messages.error(request, "Le quartier et la date sont obligatoires.")
                    return redirect(reverse('admin_setup') + (f'?year_month={year_month}' if year_month else ''))

                try:
                    year, month = date.split('-')
                    date = f"{int(year):04d}-{int(month):02d}"
                except (ValueError, AttributeError):
                    messages.error(request, "Format de date invalide.")
                    return redirect(reverse('admin_setup') + (f'?year_month={year_month}' if year_month else ''))

                try:
                    task = Task.objects.get(id=task_id, is_deleted=False)
                except Task.DoesNotExist:
                    messages.error(request, "Tâche introuvable.")
                    return redirect(reverse('admin_setup') + (f'?year_month={year_month}' if year_month else ''))

                task.quartier = quartier
                task.date = date
                total = 0
                for day in range(1, 32):
                    try:
                        value = int(request.POST.get(f'jour_{day}', 0))
                        setattr(task, f'jour_{day}', max(0, value))
                        total += value
                    except (ValueError, TypeError):
                        setattr(task, f'jour_{day}', 0)
                task.total = total
                task.save()
                messages.success(request, f"Entrée modifiée pour {task.task_type.name}.")
                return redirect(reverse('admin_setup') + f'?year_month={date}')

            elif "delete_task" in request.POST:
                task_id = request.POST.get("task_id")
                try:
                    task = Task.objects.get(id=task_id, is_deleted=False)
                    task_type_name = task.task_type.name
                    task.delete()
                    messages.success(request, f"Entrée supprimée pour {task_type_name}.")
                except Task.DoesNotExist:
                    messages.error(request, "Tâche introuvable.")
                return redirect(reverse('admin_setup') + (f'?year_month={year_month}' if year_month else ''))

        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
            logger.error(f"Admin setup POST error: {str(e)}", exc_info=True)
            return redirect(reverse('admin_setup') + (f'?year_month={year_month}' if year_month else ''))

    days = list(range(1, 32))
    return render(request, 'marafik_app/admin_setup.html', {
        'task_data': task_data,
        'days': days,
        'year_month': year_month
    })





##T##### ACHE EMPLOYEES #############"
@login_required
@role_required("Super Admin")
def super_admin_users(request):
    try:
        # Charger tous les rôles pour le menu déroulant
        roles = Role.objects.all().order_by('nom')

        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            action = request.POST.get('action')

            try:
                utilisateur = Utilisateur.objects.get(user__id=user_id)

                # 🔒 Empêcher la modification de soi-même
                if utilisateur.user == request.user:
                    messages.error(request, "Vous ne pouvez pas modifier votre propre compte.")
                    logger.warning(f"Tentative de modification de soi-même par {request.user.username}")
                    return redirect('super_admin_users')

                if action == 'toggle_status':
                    # Changer le statut (actif/inactif)
                    utilisateur.actif = not utilisateur.actif
                    utilisateur.save()
                    if not utilisateur.actif:
                        delete_user_sessions(utilisateur.user)
                    status = "activé" if utilisateur.actif else "désactivé"
                    messages.success(request, f"Utilisateur {utilisateur.user.username} {status}.")
                    logger.info(f"Statut changé pour {utilisateur.user.username} → {status}")

                elif action == 'change_role':
                    # Changer le rôle
                    new_role_id = request.POST.get('new_role_id')
                    if not new_role_id:
                        messages.error(request, "Aucun rôle sélectionné.")
                    else:
                        new_role = Role.objects.get(id=new_role_id)
                        old_role = utilisateur.role.nom
                        utilisateur.role = new_role
                        utilisateur.save()
                        messages.success(request, f"Rôle de {utilisateur.user.username} mis à jour : {old_role} → {new_role.nom}.")
                        logger.info(f"Rôle changé pour {utilisateur.user.username}: {old_role} → {new_role.nom}")

                else:
                    messages.error(request, "Action non reconnue.")
                    logger.warning(f"Action inconnue: {action} pour user_id={user_id}")

            except Utilisateur.DoesNotExist:
                messages.error(request, "Utilisateur non trouvé.")
                logger.error(f"Utilisateur non trouvé pour user_id={user_id}")
            except Role.DoesNotExist:
                messages.error(request, "Rôle invalide.")
                logger.error(f"Rôle non trouvé pour new_role_id={request.POST.get('new_role_id')}")
            except Exception as e:
                messages.error(request, "Erreur lors de la modification.")
                logger.error(f"Erreur dans super_admin_users (POST): {str(e)}")

            return redirect('super_admin_users')

        # Charger tous les utilisateurs
        utilisateurs = Utilisateur.objects.all().select_related('user', 'role')
        total_utilisateurs = utilisateurs.count()
        employes = utilisateurs.filter(role__nom="Employé").count()
        admins = utilisateurs.filter(role__nom="Admin").count()
        super_admins = utilisateurs.filter(role__nom="Super Admin").count()

        context = {
            'utilisateurs': utilisateurs,
            'roles': roles,
            'total_utilisateurs': total_utilisateurs,
            'employes': employes,
            'admins': admins,
            'super_admins': super_admins,
        }

        logger.info(f"Page super_admin_users affichée pour {request.user.username}")
        return render(request, 'marafik_app/super_admin_users.html', context)

    except Exception as e:
        logger.error(f"Erreur critique dans super_admin_users: {str(e)}")
        messages.error(request, "Une erreur est survenue lors du chargement de la page.")
        return render(request, 'marafik_app/super_admin_users.html')


@login_required
@role_required("Admin")
def admin_task_types(request):
    # Récupérer tous les types de tâches pour affichage
    task_types = TaskType.objects.all()

    if request.method == "POST":
        # Gestion de l'ajout d'un type de tâche
        if "add_task_type" in request.POST:
            task_type_name = request.POST.get("task_type_name")
            if task_type_name:
                try:
                    TaskType.objects.create(name=task_type_name)
                    messages.success(request, "Type de tâche ajouté avec succès.")
                except:
                    messages.error(request, "Erreur : Ce nom de type de tâche existe déjà.")
            else:
                messages.error(request, "Erreur : Le nom du type de tâche est requis.")
            return redirect("admin_task_types")

        # Gestion de la modification d'un type de tâche
        elif "edit_task_type" in request.POST:
            task_type_id = request.POST.get("task_type_id")
            task_type_name = request.POST.get("task_type_name")
            if task_type_id and task_type_name:
                try:
                    task_type = TaskType.objects.get(id=task_type_id)
                    task_type.name = task_type_name
                    task_type.save()
                    messages.success(request, "Type de tâche modifié avec succès.")
                except TaskType.DoesNotExist:
                    messages.error(request, "Erreur : Type de tâche introuvable.")
                except:
                    messages.error(request, "Erreur : Ce nom de type de tâche existe déjà.")
            else:
                messages.error(request, "Erreur : Les champs requis sont manquants.")
            return redirect("admin_task_types")

        # Gestion de la suppression d'un type de tâche
        elif "delete_task_type" in request.POST:
            task_type_id = request.POST.get("task_type_id")
            try:
                task_type = TaskType.objects.get(id=task_type_id)
                task_type.delete()
                messages.success(request, "Type de tâche supprimé avec succès.")
            except TaskType.DoesNotExist:
                messages.error(request, "Erreur : Type de tâche introuvable.")
            return redirect("admin_task_types")

    # Affichage de la page avec les données
    return render(request, 'marafik_app/admin_task_types.html', {'task_types': task_types})


def navbar(request):
    return render(request, 'partials/navbar.html')

def footer(request):
    return render(request, 'partials/footer.html')


@never_cache
@role_required("Admin")
def historique_view(request):
    try:
        # Récupérer toutes les tâches avec is_deleted=True
        tasks = Task.objects.filter(is_deleted=True).select_related('task_type', 'created_by').order_by('-updated_at')
        task_data = []

        for task in tasks:
            task_data.append({
                'id': task.id,
                'task_type': task.task_type.name if task.task_type else 'N/A',
                'quartier': task.quartier or 'N/A',
                'date': task.date or 'N/A',
                'user': task.created_by.username if task.created_by else 'Utilisateur inconnu',
                'updated_at': task.updated_at,
            })

        if request.method == "POST":
            try:
                if "confirm_delete" in request.POST:
                    task_id = request.POST.get("task_id")
                    try:
                        with transaction.atomic():
                            task = Task.objects.get(id=task_id, is_deleted=True)
                            task.delete()
                            TaskHistory.objects.create(
                                task=None,  # Tâche supprimée définitivement
                                user=request.user,
                                action="DELETE"
                            )
                            messages.success(request, f"Tâche {task_id} supprimée définitivement.")
                            logger.debug(f"Task {task_id} permanently deleted by {request.user.username}")
                    except Task.DoesNotExist:
                        messages.error(request, f"Tâche {task_id} introuvable ou déjà supprimée.")
                        logger.error(f"Task {task_id} not found for permanent deletion")
                    return HttpResponseRedirect('/marafik_app/marafik_app__admin_historique/')  # URL directe

                elif "restore_task" in request.POST:
                    task_id = request.POST.get("task_id")
                    try:
                        with transaction.atomic():
                            task = Task.objects.get(id=task_id, is_deleted=True)
                            task.is_deleted = False
                            task.save()
                            TaskHistory.objects.create(
                                task=task,
                                user=request.user,
                                action="UPDATE"
                            )
                            messages.success(request, f"Tâche {task_id} restaurée.")
                            logger.debug(f"Task {task_id} restored by {request.user.username}")
                    except Task.DoesNotExist:
                        messages.error(request, f"Tâche {task_id} introuvable.")
                        logger.error(f"Task {task_id} not found for restoration")
                    return HttpResponseRedirect('/marafik_app/marafik_app__admin_historique/')  # URL directe

            except Exception as e:
                messages.error(request, f"Erreur lors de l'opération : {str(e)}")
                logger.error(f"POST error in historique_view: {str(e)}")
                return HttpResponseRedirect('/marafik_app/marafik_app__admin_historique/')  # URL directe

        return render(request, 'marafik_app/historique.html', {
            'task_data': task_data,
        })

    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des tâches supprimées : {str(e)}")
        logger.error(f"Error in historique_view: {str(e)}")
        return render(request, 'marafik_app/historique.html', {'task_data': []})
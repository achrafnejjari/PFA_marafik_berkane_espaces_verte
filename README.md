# 🌿 Application de Gestion des Espaces Verts – Marafik Berkane
## 📌 Description du projet

Ce projet a été développé dans le cadre de mon stage PFA de deux mois au sein de la Société de Développement Local “Marafik Berkane”.
Il s’agit d’une application web destinée à digitaliser et optimiser la gestion des espaces verts dans la ville de Berkane.

L’application permet :

La gestion centralisée des employés et des sociétés partenaires.

Le suivi des activités annuelles (création, modification, suppression des données).

La génération automatique de rapports PDF à partir des tables de données.

La mise en place de profils utilisateurs sécurisés (Super Admin, Admin, Employés).

Cette solution contribue à améliorer la traçabilité, la transparence et l’efficacité de la gestion publique des espaces verts.

# ⚙️ Architecture

Le projet suit une architecture en trois tiers :

Couche Présentation : HTML, CSS, JavaScript (interface responsive et ergonomique).

Couche Métier : Django (logique applicative, gestion des règles métiers, sécurité).

Couche Données : MySQL avec ORM Django (stockage et manipulation des données).

# 🛠️ Technologies utilisées

Backend : Django (Python)

Frontend : HTML, CSS, JavaScript, Bootstrap

Base de données : MySQL

Outils de développement : Git, GitHub, Docker, VS Code

# 👥 Rôles utilisateurs

Super Admin : gestion complète (employés, sociétés, supervision globale, rapports PDF).

Admin : suivi des employés et sociétés, validation/modification des interventions.

Employés : consultation de leurs tâches, saisie et mise à jour de leurs activités.


# 🚀 Installation et exécution
Prérequis

Python 3.10+

Docker et Docker Compose installés

### Étapes

#### Cloner le dépôt

git clone https://github.com/achrafnejjari/PFA_marafik_berkane_espaces_verte.git
cd PFA_marafik_berkane_espaces_verte


#### Construire les images Docker

docker-compose build


#### Lancer les conteneurs

docker-compose up -d


##### Accéder à l’application

http://127.0.0.1:8000

# 📂 Liens utiles

🔗 Dépôt GitHub : PFA_marafik_berkane_espaces_verte

📘 Documentation Django : https://docs.djangoproject.com

🐳 Documentation Docker : https://docs.docker.com

🗄️ Documentation MySQL : https://dev.mysql.com/doc

# 📝 Auteur

👨‍💻 Réalisé par Achraf Nejjari
Dans le cadre du Stage PFA Juillet – Septembre 2025

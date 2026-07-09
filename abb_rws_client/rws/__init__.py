# abb_rws_client/rws/__init__.py
"""
Couche miroir RWS — fonctions atomiques 1:1 avec les endpoints HTTP ABB RWS.

Chaque sous-module correspond à un domaine RWS :
    mastership  → /rw/mastership/*
    rapid/      → /rw/rapid/*

Règle absolue : aucune logique composée ici.
Toute composition appartient à highlevel/.
"""
